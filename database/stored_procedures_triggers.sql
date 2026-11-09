-- ============================================================
-- MercAPP — Procedimientos Almacenados y Triggers
-- Compatible con MySQL 8.0+ / TiDB Cloud
-- Criterio H de Sustentación: 5 SPs + 5 Triggers funcionales
-- ============================================================

-- ============================================================
-- STORED PROCEDURES (5)
-- ============================================================

-- SP1: Registrar venta POS con descuento atómico de stock
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_registrar_venta_pos(
    IN p_store_id INT,
    IN p_user_id INT,
    IN p_cash_session_id INT,
    IN p_receipt_number VARCHAR(30),
    IN p_product_id INT,
    IN p_quantity INT,
    IN p_unit_price INT,
    IN p_payment_method VARCHAR(20),
    IN p_amount_received INT
)
BEGIN
    DECLARE v_stock INT;
    DECLARE v_total INT;
    DECLARE v_sale_id INT;

    SELECT stock INTO v_stock FROM producto WHERE id = p_product_id AND store_id = p_store_id FOR UPDATE;

    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Producto no encontrado en esta tienda.';
    END IF;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45001' SET MESSAGE_TEXT = 'Stock insuficiente para completar la venta.';
    END IF;

    SET v_total = p_quantity * p_unit_price;

    INSERT INTO venta (store_id, cash_session_id, receipt_number, user_id, subtotal, total, payment_method, amount_received, change_given, status)
    VALUES (p_store_id, p_cash_session_id, p_receipt_number, p_user_id, v_total, v_total, p_payment_method, p_amount_received, p_amount_received - v_total, 'completada');

    SET v_sale_id = LAST_INSERT_ID();

    INSERT INTO detalle_venta (sale_id, product_id, quantity, unit_price, subtotal)
    VALUES (v_sale_id, p_product_id, p_quantity, p_unit_price, v_total);

    UPDATE producto SET stock = stock - p_quantity, sale_count = sale_count + p_quantity WHERE id = p_product_id;

    IF p_payment_method = 'efectivo' THEN
        UPDATE sesion_caja SET cash_sales = cash_sales + v_total WHERE id = p_cash_session_id;
    ELSEIF p_payment_method = 'tarjeta' THEN
        UPDATE sesion_caja SET card_sales = card_sales + v_total WHERE id = p_cash_session_id;
    ELSEIF p_payment_method = 'transferencia' THEN
        UPDATE sesion_caja SET transfer_sales = transfer_sales + v_total WHERE id = p_cash_session_id;
    END IF;
END //
DELIMITER ;

-- SP2: Cerrar turno de caja con cálculo de arqueo
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_cerrar_turno_caja(
    IN p_session_id INT,
    IN p_actual_cash INT
)
BEGIN
    DECLARE v_base INT;
    DECLARE v_cash_sales INT;
    DECLARE v_supplier_cash_out INT;
    DECLARE v_expected INT;

    SELECT base_amount, COALESCE(cash_sales, 0)
    INTO v_base, v_cash_sales
    FROM sesion_caja WHERE id = p_session_id AND status = 'abierta';

    IF v_base IS NULL THEN
        SIGNAL SQLSTATE '45002' SET MESSAGE_TEXT = 'Sesión de caja no encontrada o ya está cerrada.';
    END IF;

    SELECT COALESCE(SUM(amount_cash), 0) INTO v_supplier_cash_out
    FROM supplier_delivery WHERE cash_session_id = p_session_id;

    SET v_expected = v_base + v_cash_sales - v_supplier_cash_out;

    UPDATE sesion_caja
    SET status = 'cerrada',
        closed_at = NOW(),
        actual_cash = p_actual_cash,
        expected_cash = v_expected
    WHERE id = p_session_id;
END //
DELIMITER ;

-- SP3: Reporte consolidado de ventas diarias por categoría
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_reporte_ventas_diarias(
    IN p_store_id INT,
    IN p_fecha DATE
)
BEGIN
    SELECT
        c.name AS categoria,
        COUNT(DISTINCT v.id) AS total_ventas,
        COALESCE(SUM(dv.subtotal), 0) AS ingresos_totales,
        COALESCE(SUM(dv.quantity), 0) AS unidades_vendidas
    FROM venta v
    JOIN detalle_venta dv ON dv.sale_id = v.id
    JOIN producto p ON p.id = dv.product_id
    JOIN categoria c ON c.id = p.category_id
    WHERE v.store_id = p_store_id
      AND DATE(v.sale_date) = p_fecha
      AND v.status = 'completada'
    GROUP BY c.id, c.name
    ORDER BY ingresos_totales DESC;
END //
DELIMITER ;

-- SP4: Registrar abono a deuda de cliente (fiado)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_abonar_deuda_cliente(
    IN p_client_id INT,
    IN p_amount INT,
    IN p_payment_method VARCHAR(20),
    IN p_notes VARCHAR(200)
)
BEGIN
    DECLARE v_total_debt INT;

    SELECT COALESCE(SUM(balance), 0) INTO v_total_debt
    FROM venta_credito WHERE client_id = p_client_id AND status = 'pendiente';

    IF v_total_debt <= 0 THEN
        SIGNAL SQLSTATE '45003' SET MESSAGE_TEXT = 'El cliente no tiene deuda pendiente.';
    END IF;

    IF p_amount > v_total_debt THEN
        SET p_amount = v_total_debt;
    END IF;

    INSERT INTO pago_credito (client_id, amount, payment_method, payment_date, notes)
    VALUES (p_client_id, p_amount, p_payment_method, NOW(), p_notes);

    UPDATE venta_credito
    SET balance = GREATEST(balance - p_amount, 0),
        status = CASE WHEN balance - p_amount <= 0 THEN 'pagado' ELSE 'pendiente' END
    WHERE client_id = p_client_id AND status = 'pendiente'
    ORDER BY created_at ASC
    LIMIT 1;
END //
DELIMITER ;

-- SP5: Alertar productos con stock crítico (reorden)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_reorden_stock_minimo(
    IN p_store_id INT,
    IN p_umbral INT
)
BEGIN
    SELECT
        p.id,
        p.name AS producto,
        p.barcode,
        c.name AS categoria,
        p.stock AS stock_actual,
        p.price AS precio,
        p_umbral AS umbral_minimo,
        CASE
            WHEN p.stock <= 0 THEN 'AGOTADO'
            WHEN p.stock <= p_umbral THEN 'CRÍTICO'
            ELSE 'OK'
        END AS estado
    FROM producto p
    LEFT JOIN categoria c ON c.id = p.category_id
    WHERE p.store_id = p_store_id
      AND p.is_active = 1
      AND (p.stock IS NOT NULL AND p.stock <= p_umbral)
    ORDER BY p.stock ASC;
END //
DELIMITER ;


-- ============================================================
-- TRIGGERS (5)
-- ============================================================

-- TRG1: Auditar cambios de precio de productos
DELIMITER //
CREATE TRIGGER IF NOT EXISTS trg_auditoria_cambio_precio
BEFORE UPDATE ON producto
FOR EACH ROW
BEGIN
    IF OLD.price <> NEW.price THEN
        INSERT INTO auditoria (action, description, severity, created_at)
        VALUES (
            'PRICE_CHANGE',
            CONCAT('Producto #', OLD.id, ' "', OLD.name, '": precio cambió de $', OLD.price, ' a $', NEW.price),
            'WARNING',
            NOW()
        );
    END IF;
END //
DELIMITER ;

-- TRG2: Prevenir stock negativo en productos
DELIMITER //
CREATE TRIGGER IF NOT EXISTS trg_evitar_stock_negativo
BEFORE UPDATE ON producto
FOR EACH ROW
BEGIN
    IF NEW.stock IS NOT NULL AND NEW.stock < 0 THEN
        SIGNAL SQLSTATE '45004' SET MESSAGE_TEXT = 'Error: el stock no puede ser negativo.';
    END IF;
END //
DELIMITER ;

-- TRG3: Registrar auditoría al crear una venta
DELIMITER //
CREATE TRIGGER IF NOT EXISTS trg_auditoria_nueva_venta
AFTER INSERT ON venta
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (user_id, action, description, severity, created_at)
    VALUES (
        NEW.user_id,
        'SALE_CREATED',
        CONCAT('Venta #', NEW.receipt_number, ' por $', NEW.total, ' (', NEW.payment_method, ') en tienda #', NEW.store_id),
        'INFO',
        NOW()
    );
END //
DELIMITER ;

-- TRG4: Actualizar saldo de crédito al registrar un abono
DELIMITER //
CREATE TRIGGER IF NOT EXISTS trg_actualizar_saldo_credito
AFTER INSERT ON pago_credito
FOR EACH ROW
BEGIN
    DECLARE v_remaining INT;
    SET v_remaining = NEW.amount;

    UPDATE venta_credito
    SET balance = GREATEST(balance - v_remaining, 0),
        status = CASE WHEN GREATEST(balance - v_remaining, 0) = 0 THEN 'pagado' ELSE status END
    WHERE client_id = NEW.client_id AND status = 'pendiente'
    ORDER BY created_at ASC;
END //
DELIMITER ;

-- TRG5: Auditar eliminación de usuarios
DELIMITER //
CREATE TRIGGER IF NOT EXISTS trg_auditoria_eliminar_usuario
BEFORE DELETE ON usuario
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (user_id, action, description, severity, created_at)
    VALUES (
        OLD.id,
        'USER_DELETED',
        CONCAT('Usuario eliminado: ', OLD.name, ' (', OLD.email, ') - Admin: ', OLD.is_admin),
        'CRITICAL',
        NOW()
    );
END //
DELIMITER ;
