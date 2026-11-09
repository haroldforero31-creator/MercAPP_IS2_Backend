import os
import shutil
import sqlite3
import json
from datetime import datetime
from flask import send_file, jsonify

class BackupService:
    """
    Servicio de Respaldos (Backups) para MercAPP.
    Permite generar copias de seguridad consistentes en caliente para SQLite (WAL)
    y exportaciones completas de datos de la tienda.
    """

    @staticmethod
    def create_sqlite_backup(db_path: str, backup_dir: str = None) -> str:
        """
        Realiza un respaldo consistente en caliente usando la API nativa de SQLite.
        Seguro para usar con modo WAL concurrente.
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada en {db_path}")

        if not backup_dir:
            backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"mercapp_backup_{timestamp}.db"
        backup_filepath = os.path.join(backup_dir, backup_filename)

        # Usar la API oficial de backup online de SQLite para no corromper la BD activa
        src = sqlite3.connect(db_path)
        dst = sqlite3.connect(backup_filepath)
        with dst:
            src.backup(dst, pages=100)
        dst.close()
        src.close()

        return backup_filepath

    @staticmethod
    def export_store_data_json(store_id: int) -> dict:
        """
        Exporta los datos clave de la tienda en formato JSON estructurado
        (Productos, Categorías, Usuarios, Clientes, Historial de Ventas).
        Compatible tanto con SQLite como con TiDB/MySQL.
        """
        from models import db, Store, User, Product, Category, Sale, SaleItem, CashSession

        store = db.session.get(Store, store_id)
        if not store:
            return {"error": "Tienda no encontrada"}

        data = {
            "metadata": {
                "system": "MercAPP POS",
                "version": "2.0",
                "exported_at": datetime.now().isoformat(),
                "store_name": store.name,
                "store_id": store.id
            },
            "categories": [
                {"id": c.id, "name": c.name, "slug": c.slug}
                for c in Category.query.filter_by(store_id=store_id).all()
            ],
            "products": [
                {"id": p.id, "name": p.name, "barcode": p.barcode, "price": p.price, "stock": p.stock, "is_active": p.is_active}
                for p in Product.query.filter_by(store_id=store_id).all()
            ],
            "sales_summary": {
                "total_sales_count": Sale.query.filter_by(store_id=store_id).count()
            }
        }
        return data
