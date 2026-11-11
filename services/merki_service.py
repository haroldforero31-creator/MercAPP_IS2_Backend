"""
Merki Service — Motor de Procesamiento de Lenguaje Natural (NLP)
================================================================
Interpreta preguntas en lenguaje natural sobre la tienda, ejecuta las
consultas correspondientes y genera respuestas amigables y conversacionales.
"""
import re
import unicodedata
from datetime import datetime, date, timedelta
from services.merki_queries import MerkiQueries
from models.product import Product, Category

MONTHS = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12
}

CANONICAL_MONTH_NAMES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]



def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, sin tildes ni caracteres especiales repetidos."""
    if not text:
        return ""
    text = text.lower().strip()
    # Eliminar acentos y diacríticos
    nfkd_form = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Limpiar puntuación extra manteniendo letras, números y espacios
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Colapsar espacios múltiples
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_currency(value) -> str:
    """Formatea valores numéricos como moneda colombiana en pesos ($1.000 pesos)."""
    try:
        val = float(value or 0)
        return f"${val:,.0f} pesos".replace(",", ".")
    except Exception:
        return f"${value} pesos"


def parse_date_query(text: str):
    """Interpreta fechas o periodos temporales específicos dentro del texto."""
    if not text:
        return None
    t = text.lower().strip()
    now = datetime.now()
    cur_year = now.year

    # 1. Periodos relativos semanales y mensuales
    if "la semana pasada" in t or "semana pasada" in t:
        monday_this_week = (now - timedelta(days=now.weekday())).date()
        monday_last_week = monday_this_week - timedelta(days=7)
        sunday_last_week = monday_this_week - timedelta(days=1)
        return {'type': 'range', 'start': monday_last_week, 'end': sunday_last_week, 'label': 'la semana pasada'}

    if "esta semana" in t:
        monday_this_week = (now - timedelta(days=now.weekday())).date()
        return {'type': 'range', 'start': monday_this_week, 'end': now.date(), 'label': 'esta semana'}

    if "el mes pasado" in t or "mes pasado" in t:
        first_this_month = now.replace(day=1).date()
        last_prev_month = first_this_month - timedelta(days=1)
        first_prev_month = last_prev_month.replace(day=1)
        prev_month_name = CANONICAL_MONTH_NAMES[first_prev_month.month - 1]
        return {'type': 'range', 'start': first_prev_month, 'end': last_prev_month, 'label': f'el mes pasado ({prev_month_name})'}

    if "este mes" in t:
        first_this_month = now.replace(day=1).date()
        this_month_name = CANONICAL_MONTH_NAMES[now.month - 1]
        return {'type': 'range', 'start': first_this_month, 'end': now.date(), 'label': f'este mes ({this_month_name})'}

    # 2. Días de la semana relativos (ej: "el lunes", "del martes pasado")
    weekdays_map = {
        'lunes': 0, 'martes': 1, 'miercoles': 2, 'jueves': 3,
        'viernes': 4, 'sabado': 5, 'domingo': 6
    }
    for d_name, d_idx in weekdays_map.items():
        if f"el {d_name}" in t or f"del {d_name}" in t or f"pasado {d_name}" in t:
            days_back = (now.weekday() - d_idx) % 7
            if days_back == 0 and ("pasado" in t or "anterior" in t):
                days_back = 7
            elif days_back == 0:
                days_back = 0
            target_d = (now - timedelta(days=days_back)).date()
            label_d = f"el {d_name} ({target_d.strftime('%d/%m')})"
            return {'type': 'exact', 'date': target_d, 'label': label_d}

    # 3. Fechas relativas inmediatas
    if "antier" in t or "anteayer" in t:
        return {'type': 'exact', 'date': (now - timedelta(days=2)).date(), 'label': 'antier'}
    if "ayer" in t:
        return {'type': 'exact', 'date': (now - timedelta(days=1)).date(), 'label': 'ayer'}

    # 4. "dia X del mes Y [del ano Z | este ano]" o "dia X mes Y"
    m_dia_mes = re.search(r'dia\s+(\d{1,2})\s+(?:del?\s+mes\s+|mes\s+)(\d{1,2})(?:\s+(?:del?\s+ano\s+|del?\s+a[ñn]o\s+|del?\s+)(\d{4}|este\s+ano|este\s+a[ñn]o))?', t)
    if m_dia_mes:
        day = int(m_dia_mes.group(1))
        month = int(m_dia_mes.group(2))
        yr_str = m_dia_mes.group(3)
        yr = cur_year if (not yr_str or "este" in yr_str) else int(yr_str)
        try:
            d = date(yr, month, day)
            return {'type': 'exact', 'date': d, 'label': f"el día {day} del mes {month} de {yr}"}
        except ValueError:
            pass

    # 5. "X de <nombre_mes> [del ano Z | este ano]" (ej: "7 de octubre", "17 de octubre de 2026")
    m_named = re.search(r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)(?:\s+(?:del?\s+ano\s+|del?\s+a[ñn]o\s+|del?\s+)(\d{4}|este\s+ano|este\s+a[ñn]o))?', t)
    if m_named:
        day = int(m_named.group(1))
        month_name = m_named.group(2)
        month = MONTHS[month_name]
        yr_str = m_named.group(3)
        yr = cur_year if (not yr_str or "este" in yr_str) else int(yr_str)
        try:
            d = date(yr, month, day)
            return {'type': 'exact', 'date': d, 'label': f"el {day} de {month_name} de {yr}"}
        except ValueError:
            pass

    # 6. Formato "DD MM YYYY" o "DD/MM/YYYY" o "DD-MM-YYYY"
    m_slash = re.search(r'\b(\d{1,2})[\s/.-](\d{1,2})[\s/.-](\d{2,4})\b', t)
    if m_slash:
        day = int(m_slash.group(1))
        month = int(m_slash.group(2))
        yr_val = int(m_slash.group(3))
        yr = (yr_val + 2000) if yr_val < 100 else yr_val
        try:
            d = date(yr, month, day)
            return {'type': 'exact', 'date': d, 'label': f"el {day}/{month}/{yr}"}
        except ValueError:
            pass

    # 7. Rango de mes completo: "en el mes de <mes>" / "mes de <mes>" / "del mes de <mes>"
    m_month_only = re.search(r'(?:en\s+(?:el\s+mes\s+de\s+)?|del\s+mes\s+de\s+|mes\s+de\s+)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)(?:\s+(?:del?\s+ano\s+|del?\s+a[ñn]o\s+|del?\s+)(\d{4}))?', t)
    if m_month_only:
        m_name = m_month_only.group(1)
        month = MONTHS[m_name]
        yr = int(m_month_only.group(2)) if m_month_only.group(2) else cur_year
        start_d = date(yr, month, 1)
        next_month = month + 1 if month < 12 else 1
        next_yr = yr if month < 12 else yr + 1
        end_d = date(next_yr, next_month, 1) - timedelta(days=1)
        return {'type': 'range', 'start': start_d, 'end': end_d, 'label': f"el mes de {m_name} de {yr}"}

    return None


class MerkiService:
    """Motor de intenciones y respuestas para Merki."""

    FALLBACK_MESSAGE = (
        "Disculpa, de momento no cuento con esa información pero puedes consultar con uno de nuestros administradores."
    )

    @classmethod
    def process_question(cls, store_id: int, raw_question: str) -> dict:
        """
        Punto de entrada principal:
        Recibe la pregunta en crudo, la interpreta y retorna respuesta estructurada.
        """
        if not raw_question or not raw_question.strip():
            return {
                "success": True,
                "intent": "empty",
                "response": "¡Hola! Dime en qué te puedo ayudar hoy.",
                "data": None
            }

        text = normalize_text(raw_question)

        # 1. Comandos de cortesía y generales
        courtesy_res = cls._handle_courtesy(text)
        if courtesy_res:
            return courtesy_res

        # 2. Consultas de Ventas
        sales_res = cls._handle_sales(store_id, text)
        if sales_res:
            return sales_res

        # 3. Consultas de Deudas / Clientes
        debt_res = cls._handle_debts(store_id, text)
        if debt_res:
            return debt_res

        # 4. Consultas de Stock General (agotados, bajo stock, total)
        stock_res = cls._handle_stock_general(store_id, text)
        if stock_res:
            return stock_res

        # 5. Consultas de Productos (precio, existencia, más barato/caro, variantes)
        prod_res = cls._handle_products(store_id, text)
        if prod_res:
            return prod_res

        # Si no coincidió con ninguna regla entendible
        return {
            "success": True,
            "intent": "unknown",
            "response": cls.FALLBACK_MESSAGE,
            "data": None
        }

    # ============================================================
    # HANDLERS ESPECÍFICOS
    # ============================================================

    @classmethod
    def _handle_courtesy(cls, text: str):
        # Llamados directos por nombre / Wake-word
        if any(text == w or text == f"oye {w}" for w in ["merki", "merqui", "merky", "hola merki", "hola merqui", "oye merki", "oye merqui"]):
            return {
                "success": True,
                "intent": "wake_call",
                "response": "¡Hola! Te escucho atento. ¿Qué deseas consultar de tu negocio?",
                "data": None
            }

        # Saludos
        if any(w in text for w in ["hola", "buenos dias", "buenas tardes", "buenas noches", "que hubo", "que mas"]):
            return {
                "success": True,
                "intent": "greeting",
                "response": "¡Hola! Con mucho gusto estoy aquí para ayudarte con cualquier consulta de tu negocio.",
                "data": None
            }

        # Agradecimientos
        if any(w in text for w in ["gracias", "muchas gracias", "te lo agradezco", "vale gracias"]):
            return {
                "success": True,
                "intent": "thanks",
                "response": "¡Con todo el gusto! Recuerda que siempre estoy aquí para apoyarte en la tienda.",
                "data": None
            }

        # Despedidas
        if any(w in text for w in ["adios", "chao", "hasta luego", "nos vemos", "descansa"]):
            return {
                "success": True,
                "intent": "farewell",
                "response": "¡Hasta luego! Estaré atento cada vez que me llames diciendo Oye Merki.",
                "data": None
            }

        # Identidad
        if any(w in text for w in ["quien eres", "como te llamas", "que eres", "presentate"]):
            return {
                "success": True,
                "intent": "identity",
                "response": "Soy Merki, tu asistente de voz en MercAPP. Puedo responderte sobre tus productos, precios, ventas del día, deudas y stock.",
                "data": None
            }

        # Hora
        if "que hora es" in text or "dime la hora" in text or "la hora" in text:
            now = datetime.now().strftime("%I:%M %p")
            return {
                "success": True,
                "intent": "time",
                "response": f"Son las {now}.",
                "data": {"time": now}
            }

        return None

    @classmethod
    def _handle_sales(cls, store_id: int, text: str):
        # 1. Última venta
        if any(k in text for k in ["ultima venta", "ultimo que se vendio", "que fue lo ultimo", "que se vendio"]):
            sale = MerkiQueries.last_sale(store_id)
            if sale:
                total_str = format_currency(sale.get("total", 0))
                receipt = sale.get("receipt", "")
                items = sale.get("items", [])
                items_str = ", ".join([f"{it['qty']}x {it['name']}" for it in items])
                resp = f"La última venta fue la {receipt} por {total_str} ({sale.get('payment_method', 'efectivo')})."
                if items_str:
                    resp += f" Incluyó: {items_str}."
                return {
                    "success": True,
                    "intent": "last_sale",
                    "response": resp,
                    "data": sale
                }
            return {
                "success": True,
                "intent": "last_sale",
                "response": "Aún no se registran ventas en el sistema.",
                "data": None
            }

        # 2. Consultas de ventas por FECHA ESPECÍFICA o RANGO TEMPORAL
        # (ej: "cuanto fueron las ventas de el dia 7 del mes 10", "ventas del 17 de octubre", "ventas de ayer", "ventas en el mes de octubre")
        date_info = parse_date_query(text)
        if date_info:
            label = date_info.get("label", "la fecha consultada")
            if date_info.get("type") == "exact":
                data = MerkiQueries.sales_on_date(store_id, date_info["date"])
                count = data.get("count", 0)
                total = data.get("total", 0)
                if count == 0:
                    resp = f"{label.capitalize()} no se registraron ventas en tu tienda."
                elif count == 1:
                    resp = f"{label.capitalize()} se registró 1 venta por un total de {format_currency(total)}."
                else:
                    resp = f"{label.capitalize()} se registraron {count} ventas por un total de {format_currency(total)}."
                return {
                    "success": True,
                    "intent": "sales_by_date",
                    "response": resp,
                    "data": data
                }
            elif date_info.get("type") == "range":
                data = MerkiQueries.sales_in_date_range(store_id, date_info["start"], date_info["end"], label=label)
                count = data.get("count", 0)
                total = data.get("total", 0)
                if count == 0:
                    resp = f"En {label} no se registraron ventas."
                elif count == 1:
                    resp = f"En {label} se registró 1 venta por un total de {format_currency(total)}."
                else:
                    resp = f"En {label} se registraron {count} ventas por un total de {format_currency(total)}."
                return {
                    "success": True,
                    "intent": "sales_by_date_range",
                    "response": resp,
                    "data": data
                }

        # 3. Producto más vendido
        if any(k in text for k in ["mas vendido", "producto estrella", "mas sale", "lo que mas se vende"]):
            best = MerkiQueries.best_seller(store_id)
            if best:
                return {
                    "success": True,
                    "intent": "top_selling",
                    "response": f"El producto más vendido es {best['name']} con {best['total_sold']} unidades vendidas.",
                    "data": best
                }
            return {
                "success": True,
                "intent": "top_selling",
                "response": "Aún no hay suficientes ventas registradas para determinar el producto más vendido.",
                "data": None
            }

        # 4. Estado de caja
        if any(k in text for k in ["estado de caja", "como va la caja", "cuanto hay en caja", "caja actual", "dinero en caja", "plata en caja"]):
            session = MerkiQueries.active_session(store_id)
            if session.get("active"):
                base = format_currency(session.get("base", 0))
                efectivo = format_currency(session.get("cash_sales", 0))
                total_esperado = format_currency(session.get("base", 0) + session.get("cash_sales", 0))
                return {
                    "success": True,
                    "intent": "cash_session",
                    "response": f"La caja está abierta desde las {session.get('opened_at')}. Base inicial {base}, ventas en efectivo por {efectivo}, para un total de {total_esperado} en caja.",
                    "data": session
                }
            else:
                return {
                    "success": True,
                    "intent": "cash_session",
                    "response": "En este momento no hay una sesión de caja activa abierta.",
                    "data": None
                }

        # 5. Ventas del turno / hoy
        if any(k in text for k in [
            "ventas de hoy", "vendio hoy", "venta hoy", "cuanto llevamos hoy", "ventas hoy",
            "hice una venta", "hicimos una venta", "hubo una venta", "se hizo una venta",
            "acabo de vender", "cuanto vendi", "cuanto se ha vendido", "como van las ventas",
            "total ventas", "ventas del turno", "cuantas ventas van", "ventas"
        ]):
            session = MerkiQueries.active_session(store_id)
            today_total = session.get("total_sales", 0)
            count = session.get("sales_count", 0)

            if session.get("active"):
                if count == 0:
                    resp = f"En el turno actual no se registran ventas todavía. La base en caja es de {format_currency(session.get('base', 0))}."
                elif count == 1:
                    resp = f"En el turno actual se ha registrado 1 venta por un total de {format_currency(today_total)}."
                else:
                    resp = f"En el turno actual se han registrado {count} ventas por un total de {format_currency(today_total)}."
                return {
                    "success": True,
                    "intent": "sales_today",
                    "response": resp,
                    "data": {"total": today_total, "count": count, "session": session}
                }
            else:
                if count > 0:
                    resp = f"Hoy se han registrado {count} ventas por un total de {format_currency(today_total)}."
                else:
                    resp = "No hay una caja abierta actualmente y no se registran ventas hoy."
                return {
                    "success": True,
                    "intent": "sales_today",
                    "response": resp,
                    "data": {"total": today_total, "count": count}
                }

        return None

    @classmethod
    def _extract_client_name(cls, text: str):
        """Extrae el nombre de un cliente para consultas individuales de deuda/crédito."""
        t = text.lower().strip()
        patterns = [
            r'(?:cuanto\s+(?:nos\s+|me\s+)?debe|cuanto\s+deben?\s+de|que\s+debe)\s+(?:el\s+cliente\s+|la\s+clienta\s+|don\s+|dona\s+|el\s+senor\s+|la\s+senora\s+|el\s+|la\s+)?([a-z0-9\s]+)',
            r'(?:deuda|saldo|estado\s+de\s+cuenta|cuenta|abonos?|pagos?|fiado)\s+(?:del?\s+(?:cliente\s+|senor\s+|senora\s+|don\s+|dona\s+)?)([a-z0-9\s]+)',
            r'(?:cuanto\s+ha\s+(?:abonado|pagado))\s+(?:el\s+cliente\s+|la\s+clienta\s+|don\s+|dona\s+|el\s+|la\s+)?([a-z0-9\s]+)',
            r'(?:como\s+va\s+(?:la\s+cuenta|el\s+saldo|la\s+deuda)\s+de)\s+(?:el\s+cliente\s+|la\s+clienta\s+|don\s+|dona\s+|el\s+|la\s+)?([a-z0-9\s]+)',
            r'(?:cliente\s+)([a-z0-9\s]+?)\s+(?:cuanto\s+debe|que\s+debe|su\s+deuda|su\s+saldo)'
        ]
        excluded = [
            'total', 'clientes', 'la tienda', 'el negocio', 'todos', 'mas',
            'mayor', 'mas grande', 'los clientes', 'las deudas', 'hoy', 'ayer', 'ahora'
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                name = m.group(1).strip()
                # Quitar muletillas
                name = re.sub(r'\s+(?:y\s+ha\s+abonado|y\s+cuanto|por\s+favor|dime|etc).*$', '', name).strip()
                name = re.sub(r'^(?:el|la|los|las|de|del|a|al)\s+', '', name).strip()
                if len(name) >= 2 and name not in excluded and not any(name == ex for ex in excluded):
                    return name
        return None

    @classmethod
    def _handle_debts(cls, store_id: int, text: str):
        # 1. Consulta individual de un cliente específico
        # (ej: "¿cuánto debe Juan Garavito?", "¿cuánto ha abonado Carlos?", "saldo de Santiago")
        client_name = cls._extract_client_name(text)
        if client_name:
            detail = MerkiQueries.client_debt_detail(store_id, client_name)
            if not detail or not detail.get("found"):
                return {
                    "success": True,
                    "intent": "client_debt_not_found",
                    "response": f"No encontré a ningún cliente de crédito registrado con el nombre '{client_name}'.",
                    "data": {"name": client_name}
                }

            nombre = detail['name'].title()
            deuda = detail['total_debt']
            abonado = detail['total_paid']
            total_compras = detail['total_purchased']
            dias = detail['days_without_payment']

            if deuda == 0:
                if total_compras > 0:
                    resp = f"{nombre} se encuentra al día y no debe nada. Ha realizado compras a crédito por {format_currency(total_compras)} y ha abonado {format_currency(abonado)} en su totalidad."
                else:
                    resp = f"{nombre} se encuentra al día y no tiene deudas pendientes."
            else:
                resp = f"{nombre} debe {format_currency(deuda)} de un total fiado de {format_currency(total_compras)}, y ha abonado {format_currency(abonado)}."
                if dias > 0:
                    resp += f" Registra {dias} días desde su última actividad de pago."
                if detail.get('is_blocked'):
                    resp += " Nota: Este cliente se encuentra en mora."

            return {
                "success": True,
                "intent": "client_debt_detail",
                "response": resp,
                "data": detail
            }

        # 2. ¿Quién debe más? / cliente con mayor deuda
        if any(k in text for k in ["quien debe mas", "mayor deuda", "el que mas debe", "deudor mas grande"]):
            top = MerkiQueries.who_owes_most(store_id)
            if not top or top.get("no_debt"):
                return {
                    "success": True,
                    "intent": "top_debtor",
                    "response": "No hay clientes con deuda activa registrada.",
                    "data": None
                }
            nombre = top.get("name", "Cliente").title()
            deuda = format_currency(top.get("debt", 0))
            return {
                "success": True,
                "intent": "top_debtor",
                "response": f"El cliente con mayor saldo pendiente es {nombre}, con una deuda de {deuda}.",
                "data": top
            }

        # 3. ¿Cuánto deben en total los clientes? / total deudas / fiados
        if any(k in text for k in ["cuanto deben", "total deudas", "deuda total", "cuanta plata nos deben", "cuanto nos deben", "fiados", "cartera"]):
            debt_info = MerkiQueries.total_debt(store_id)
            if not debt_info or debt_info.get("clients_with_debt", 0) == 0:
                return {
                    "success": True,
                    "intent": "debt_summary",
                    "response": "¡Excelentes noticias! Actualmente ningún cliente tiene saldo pendiente por pagar.",
                    "data": {"total_clients_with_debt": 0}
                }
            total_val = format_currency(debt_info.get("total", 0))
            count = debt_info.get("clients_with_debt", 0)
            return {
                "success": True,
                "intent": "debt_summary",
                "response": f"Hay {count} clientes con saldo pendiente por un valor total de {total_val}.",
                "data": debt_info
            }

        return None

    @classmethod
    def _handle_stock_general(cls, store_id: int, text: str):
        # 1. ¿Qué categorías hay?
        if any(k in text for k in ["que categorias hay", "cuales son las categorias", "que categorias tenemos", "categorias de la tienda", "categorias hay", "lista de categorias"]):
            cat_info = MerkiQueries.list_categories(store_id)
            cats = cat_info.get("categories", [])
            if cats:
                names = ", ".join([f"{c['name']} ({c['product_count']} prods)" for c in cats[:5]])
                total_cats = len(cats)
                if total_cats > 5:
                    names += f" y {total_cats - 5} más"
                return {
                    "success": True,
                    "intent": "list_categories",
                    "response": f"Tu tienda cuenta con {total_cats} categorías: {names}.",
                    "data": cat_info
                }
            return {
                "success": True,
                "intent": "list_categories",
                "response": "No tienes categorías registradas aún en tu tienda.",
                "data": None
            }

        # 2. ¿Qué productos están agotados?
        if any(k in text for k in ["agotados", "se acabaron", "sin stock", "cero unidades", "no hay nada"]):
            out = MerkiQueries.out_of_stock(store_id)
            count = out.get("count", 0)
            if count == 0:
                return {
                    "success": True,
                    "intent": "out_of_stock",
                    "response": "¡Buenas noticias! No tienes productos agotados en cero unidades en el inventario.",
                    "data": out
                }
            ejemplos = ", ".join([p["name"] for p in out.get("products", [])[:3]])
            resp = f"Tienes {count} productos agotados."
            if ejemplos:
                resp += f" Entre ellos: {ejemplos}."
            return {
                "success": True,
                "intent": "out_of_stock",
                "response": resp,
                "data": out
            }

        # 3. ¿Qué productos tienen poco stock?
        if any(k in text for k in ["poco stock", "por agotarse", "escasos", "stock bajo", "por terminar"]):
            low = MerkiQueries.low_stock(store_id, threshold=5)
            count = low.get("count", 0)
            if count == 0:
                return {
                    "success": True,
                    "intent": "low_stock",
                    "response": "Todos tus productos cuentan con buen nivel de existencias (más de 5 unidades).",
                    "data": low
                }
            ejemplos = ", ".join([f"{p['name']} ({p['stock']} un)" for p in low.get("products", [])[:3]])
            return {
                "success": True,
                "intent": "low_stock",
                "response": f"Hay {count} productos con 5 unidades o menos. Por ejemplo: {ejemplos}.",
                "data": low
            }

        # 4. ¿Cuántos productos hay en total en la tienda?
        if any(k in text for k in [
            "cuantos productos hay", "cuantos productos tenemos", "cuantos productos tengo",
            "total de productos", "cuantos productos tiene la tienda", "inventario total",
            "cuantos articulos hay", "que productos hay", "total productos"
        ]):
            prods = MerkiQueries.search_product(store_id, "")
            total = len(prods)
            return {
                "success": True,
                "intent": "total_products",
                "response": f"Actualmente tienes {total} productos activos registrados en tu catálogo.",
                "data": {"total": total}
            }

        return None

    @classmethod
    def get_dynamic_suggestions(cls, store_id: int) -> list:
        """Genera sugerencias rápidas inteligentes según los datos reales de la tienda."""
        chips = [
            {"label": "💰 Más barato", "q": "¿Cuál es el producto más barato?"},
            {"label": "📊 Ventas hoy", "q": "¿Cuánto se vendió hoy?"},
            {"label": "⚠️ Poco stock", "q": "¿Qué productos tienen poco stock?"}
        ]

        # Agregar sugerencia contextual de un producto real del negocio
        try:
            sample_prod = Product.query.filter_by(store_id=store_id, is_active=True).first()
            if sample_prod:
                chips.append({
                    "label": f"🔍 {sample_prod.name[:16]}",
                    "q": f"¿Hay {sample_prod.name} en la tienda?"
                })
            else:
                chips.append({
                    "label": "📂 Categorías",
                    "q": "¿Qué categorías tenemos?"
                })
        except Exception:
            pass

        # Agregar sugerencia contextual de un cliente de crédito si existe
        try:
            from models.sale import CreditClient
            sample_client = CreditClient.query.filter(
                CreditClient.store_id == store_id,
                CreditClient.is_active == True
            ).first()
            if sample_client:
                first_name = sample_client.name.strip().split()[0].title()
                chips.append({
                    "label": f"👤 Deuda {first_name}",
                    "q": f"¿Cuánto debe {sample_client.name.title()}?"
                })
        except Exception:
            pass

        return chips


    @classmethod
    def _parse_comparison(cls, text: str):
        """Detecta si la pregunta solicita comparar dos productos."""
        t = text.lower().strip()
        comp_type = 'stock' if any(w in t for w in ['stock', 'unidades', 'existencias', 'queda mas', 'hay mas', 'menos stock']) else 'price'

        patterns = [
            r'(?:cual\s+es\s+mas\s+(?:caro|barato|economico|costoso)|que\s+cuesta\s+mas|que\s+vale\s+mas|que\s+es\s+mas\s+caro|que\s+es\s+mas\s+barato|cual\s+tiene\s+mas\s+stock|cual\s+tiene\s+menos\s+stock)\s+(?:entre\s+)?(.+?)\s+(?:o|versus|vs|con|y)\s+(.+)',
            r'compara(?:r)?\s+(.+?)\s+(?:con|y|versus|vs|o)\s+(.+)',
            r'diferencia\s+entre\s+(.+?)\s+(?:y|con|versus|vs|o)\s+(.+)'
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                item_a = m.group(1).strip()
                item_b = m.group(2).strip()
                for stop in ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas']:
                    if item_a.startswith(stop + ' '): item_a = item_a[len(stop)+1:].strip()
                    if item_b.startswith(stop + ' '): item_b = item_b[len(stop)+1:].strip()
                item_b = re.sub(r'[\?¿\.,!]', '', item_b).strip()
                item_b = re.sub(r'\s+(?:por\s+favor|dime|etc).*$', '', item_b).strip()
                if item_a and item_b and item_a != item_b:
                    return {'type': comp_type, 'item_a': item_a, 'item_b': item_b}
        return None

    @classmethod
    def _handle_products(cls, store_id: int, text: str):
        # 1. Comparación entre dos productos
        # (ej: "¿cuál es más caro, acetaminofén o bulto de papa pastusa?", "compara leche y café")
        comp = cls._parse_comparison(text)
        if comp:
            comp_res = MerkiQueries.compare_products(store_id, comp['item_a'], comp['item_b'])
            if not comp_res.get('found'):
                missing = []
                if comp_res.get('missing_a'): missing.append(f"'{comp['item_a']}'")
                if comp_res.get('missing_b'): missing.append(f"'{comp['item_b']}'")
                return {
                    "success": True,
                    "intent": "product_comparison_missing",
                    "response": f"No pude completar la comparación porque no encontré en el inventario: {', '.join(missing)}.",
                    "data": comp_res
                }

            pa = comp_res['prod_a']
            pb = comp_res['prod_b']
            p_diff = format_currency(comp_res['price_diff'])

            if comp['type'] == 'stock':
                stk_a = pa.get('stock')
                stk_b = pb.get('stock')
                stk_a_txt = f"{stk_a} unidades" if stk_a is not None else "al peso"
                stk_b_txt = f"{stk_b} unidades" if stk_b is not None else "al peso"
                if comp_res['more_stock'] == 'a':
                    resp = f"{pa['name']} tiene mayor disponibilidad ({stk_a_txt}) que {pb['name']} ({stk_b_txt})."
                elif comp_res['more_stock'] == 'b':
                    resp = f"{pb['name']} tiene mayor disponibilidad ({stk_b_txt}) que {pa['name']} ({stk_a_txt})."
                else:
                    resp = f"Ambos productos tienen el mismo nivel de inventario ({stk_a_txt})."
            else:
                if comp_res['cheaper'] == 'a':
                    if any(w in text for w in ["barato", "economico"]):
                        resp = f"{pa['name']} ({format_currency(pa['price'])}) es más económico que {pb['name']} ({format_currency(pb['price'])}), por una diferencia de {p_diff}."
                    else:
                        resp = f"{pb['name']} ({format_currency(pb['price'])}) es más costoso que {pa['name']} ({format_currency(pa['price'])}), por una diferencia de {p_diff}."
                elif comp_res['cheaper'] == 'b':
                    if any(w in text for w in ["barato", "economico"]):
                        resp = f"{pb['name']} ({format_currency(pb['price'])}) es más económico que {pa['name']} ({format_currency(pa['price'])}), por una diferencia de {p_diff}."
                    else:
                        resp = f"{pa['name']} ({format_currency(pa['price'])}) es más costoso que {pb['name']} ({format_currency(pb['price'])}), por una diferencia de {p_diff}."
                else:
                    resp = f"Ambos productos tienen exactamente el mismo precio: {format_currency(pa['price'])}."

            return {
                "success": True,
                "intent": "product_comparison",
                "response": resp,
                "data": comp_res
            }

        # Extraer el término del producto limpiando palabras operacionales
        clean_term = cls._extract_product_name(text)

        # 2. Búsqueda por código de barras o PLU
        m_code = re.search(r'(?:codigo|plu|barras)\s+([a-zA-Z0-9_\-]+)', text)
        if m_code:
            code_query = m_code.group(1).strip()
            by_code = MerkiQueries.search_by_code(store_id, code_query)
            if by_code:
                stk_str = f"{by_code.stock} unidades" if by_code.stock is not None else ("al peso" if by_code.sell_by_weight else "disponible")
                return {
                    "success": True,
                    "intent": "product_by_code",
                    "response": f"Código {code_query}: {by_code.name}, cuesta {format_currency(by_code.price)} y tiene {stk_str}.",
                    "data": {"name": by_code.name, "price": by_code.price, "stock": by_code.stock}
                }

        # 3. Información completa / Ficha técnica / Identificación de producto
        # (ej: "¿qué información tienes de acetaminofén?", "datos de arroz diana", "ficha técnica de carne de cerdo")
        if any(k in text for k in [
            "que informacion tienes de", "que informacion tienes del", "informacion sobre",
            "informacion de la", "informacion del", "informacion de",
            "datos de la", "datos del", "datos de",
            "ficha tecnica de", "ficha de la", "ficha del", "ficha de",
            "detalles de la", "detalles del", "detalles de",
            "identifica el producto", "identifica al producto", "identifica",
            "codigo de barras de", "codigo de", "que categoria es", "categoria de",
            "a que categoria pertenece", "en que categoria", "categoria pertenece", "categoria",
            "como se vende", "se vende por peso"
        ]):
            if clean_term:
                full_info = MerkiQueries.product_full_info(store_id, clean_term)
                if full_info and full_info.get("found"):
                    name = full_info['name']
                    price = format_currency(full_info['price'])
                    cat = full_info.get('category', 'Sin categoría')
                    stk = full_info.get('stock')
                    sell_weight = full_info.get('sell_by_weight')
                    unit = full_info.get('weight_unit', 'kg')
                    barcode = full_info.get('barcode')
                    plu = full_info.get('plu_code')

                    # Pregunta específica de categoría
                    if "categoria" in text:
                        resp = f"{name} pertenece a la categoría {cat}."
                    # Pregunta específica de código
                    elif "codigo" in text:
                        if barcode:
                            resp = f"El código de barras de {name} es {barcode}."
                        elif plu:
                            resp = f"El código PLU de {name} es {plu}."
                        else:
                            resp = f"{name} no tiene código de barras ni PLU asignado en el sistema."
                    # Pregunta específica de venta por peso
                    elif "peso" in text or "como se vende" in text:
                        if sell_weight:
                            resp = f"{name} se vende por peso en {unit}."
                        else:
                            resp = f"{name} se vende por unidad."
                    # Información completa general
                    else:
                        stk_desc = f"{stk} {unit}" if (sell_weight and stk is not None) else (f"{stk} unidades" if stk is not None else "disponible para la venta")
                        peso_desc = f" Se vende por peso ({unit})." if sell_weight else ""
                        code_desc = f" Código: {barcode}." if barcode else ""
                        resp = f"{name}: Cuesta {price}. Categoría {cat}. Stock: {stk_desc}.{peso_desc}{code_desc}"

                    return {
                        "success": True,
                        "intent": "product_full_info",
                        "response": resp.strip(),
                        "data": full_info
                    }
                return {
                    "success": True,
                    "intent": "product_full_info",
                    "response": f"Disculpa, de momento no cuento con información de '{clean_term}' en el inventario.",
                    "data": None
                }

        # 4. ¿Cuál es el más barato / económico?
        if any(k in text for k in ["mas barato", "menor costo", "mas economico", "menor precio"]):
            cheapest = MerkiQueries.cheapest_product(store_id, clean_term if clean_term else None)
            if cheapest:
                precio = format_currency(cheapest.get("price"))
                if clean_term:
                    resp = f"El más económico relacionado con '{clean_term}' es {cheapest.get('name')} a {precio}."
                else:
                    resp = f"El producto más económico de tu tienda es {cheapest.get('name')} a {precio}."
                return {
                    "success": True,
                    "intent": "cheapest_product",
                    "response": resp,
                    "data": cheapest
                }
            return {
                "success": True,
                "intent": "cheapest_product",
                "response": cls.FALLBACK_MESSAGE,
                "data": None
            }

        # 5. ¿Cuál es el más caro / mayor costo?
        if any(k in text for k in ["mas caro", "mayor costo", "mas costoso", "mayor precio"]):
            expensive = MerkiQueries.most_expensive_product(store_id, clean_term if clean_term else None)
            if expensive:
                precio = format_currency(expensive.get("price"))
                if clean_term:
                    resp = f"El más costoso de '{clean_term}' es {expensive.get('name')} a {precio}."
                else:
                    resp = f"El producto más costoso de la tienda es {expensive.get('name')} a {precio}."
                return {
                    "success": True,
                    "intent": "expensive_product",
                    "response": resp,
                    "data": expensive
                }
            return {
                "success": True,
                "intent": "expensive_product",
                "response": cls.FALLBACK_MESSAGE,
                "data": None
            }

        # 6. ¿Cuántos tipos / sabores / marcas / presentaciones hay de X?
        if any(k in text for k in ["cuantos tipos", "cuantas marcas", "cuantos sabores", "cuantas clases", "que tipos", "que sabores"]):
            if clean_term:
                matches = MerkiQueries.search_product(store_id, clean_term)
                if matches:
                    count = len(matches)
                    names = ", ".join([p.name for p in matches[:4]])
                    if count > 4:
                        names += f" y {count - 4} más"
                    return {
                        "success": True,
                        "intent": "product_varieties",
                        "response": f"Encontré {count} variedades de {clean_term}: {names}.",
                        "data": {"count": count, "items": [p.name for p in matches]}
                    }
                return {
                    "success": True,
                    "intent": "product_varieties",
                    "response": f"Disculpa, de momento no cuento con esa información de {clean_term} pero puedes consultar con uno de nuestros administradores.",
                    "data": None
                }

        # 7. ¿Cuánto cuesta / precio de X?
        if any(k in text for k in ["cuanto cuesta", "cuanto vale", "precio de", "valor de", "a como esta", "a como"]):
            if clean_term:
                prices = MerkiQueries.product_price(store_id, clean_term)
                if prices:
                    if len(prices) == 1:
                        p = prices[0]
                        stk_txt = f" y quedan {p['stock']} unidades" if p['stock'] is not None else " y está disponible para la venta"
                        return {
                            "success": True,
                            "intent": "product_price",
                            "response": f"El {p['name']} cuesta {format_currency(p['price'])}{stk_txt}.",
                            "data": p
                        }
                    else:
                        detalles = "; ".join([f"{p['name']} a {format_currency(p['price'])}" for p in prices[:3]])
                        return {
                            "success": True,
                            "intent": "product_price",
                            "response": f"Encontré varias opciones: {detalles}.",
                            "data": prices
                        }
                return {
                    "success": True,
                    "intent": "product_price",
                    "response": cls.FALLBACK_MESSAGE,
                    "data": None
                }

        # 8. ¿Hay X en la tienda? / ¿Queda X? / ¿Tienen X?
        if any(k in text for k in ["hay", "tienen", "queda", "quedan", "venden", "disponible"]):
            if clean_term:
                info = MerkiQueries.product_exists(store_id, clean_term)
                if info and info.get("found"):
                    items = info.get("products", [])
                    if len(items) == 1:
                        item = items[0]
                        stk = item.get('stock')
                        stock_txt = f"{stk} en stock" if (stk is not None and stk > 0) else "disponible para la venta"
                        return {
                            "success": True,
                            "intent": "product_exists",
                            "response": f"Sí, hay {item['name']}. Cuesta {format_currency(item['price'])} y está {stock_txt}.",
                            "data": item
                        }
                    else:
                        total_stock = sum((p.get('stock') or 0) for p in items)
                        stock_str = f" con {total_stock} unidades en total" if total_stock > 0 else ""
                        return {
                            "success": True,
                            "intent": "product_exists",
                            "response": f"Sí, hay {len(items)} presentaciones de {clean_term}{stock_str}.",
                            "data": items
                        }
                return {
                    "success": True,
                    "intent": "product_exists",
                    "response": f"Disculpa, de momento no cuento con esa información de {clean_term} pero puedes consultar con uno de nuestros administradores.",
                    "data": None
                }

        # 9. ¿Cuántas unidades / stock de X?
        if any(k in text for k in ["cuantas unidades", "cuanto stock", "cuanto queda", "existencias de"]):
            if clean_term:
                stocks = MerkiQueries.product_stock(store_id, clean_term)
                if stocks:
                    p = stocks[0]
                    stk_txt = f"Quedan {p['stock']} unidades de {p['name']}." if p['stock'] is not None else f"{p['name']} se encuentra disponible para la venta."
                    return {
                        "success": True,
                        "intent": "product_stock",
                        "response": stk_txt,
                        "data": p
                    }
                return {
                    "success": True,
                    "intent": "product_stock",
                    "response": cls.FALLBACK_MESSAGE,
                    "data": None
                }

        # 10. Si había un término pero ninguna palabra clave anterior coincidió, intentamos buscar si existe
        if clean_term and len(clean_term) >= 3:
            matches = MerkiQueries.search_product(store_id, clean_term)
            if matches:
                p = matches[0]
                stk_txt = f"hay {p.stock} unidades disponibles" if p.stock is not None else "está disponible para la venta"
                return {
                    "success": True,
                    "intent": "product_search_direct",
                    "response": f"Encontré {p.name}. Cuesta {format_currency(p.price)} y {stk_txt}.",
                    "data": {"name": p.name, "price": p.price, "stock": p.stock}
                }

        return None

    @classmethod
    def _extract_product_name(cls, text: str):
        """Limpia palabras de relleno y preguntas comunes para aislar el nombre del producto."""
        stopwords = [
            "oye", "merki", "merqui", "merky", "por favor", "dime", "sabes si", "puedes decirme",
            "que informacion tienes de la", "que informacion tienes del", "que informacion tienes de", "que informacion tienes sobre",
            "informacion sobre la", "informacion sobre el", "informacion sobre",
            "informacion de la", "informacion del", "informacion de",
            "datos de la", "datos del", "datos de",
            "ficha tecnica de la", "ficha tecnica del", "ficha tecnica de",
            "ficha de la", "ficha del", "ficha de",
            "detalles de la", "detalles del", "detalles de",
            "identifica el producto", "identifica al producto", "identifica la", "identifica el", "identifica",
            "codigo de barras de la", "codigo de barras del", "codigo de barras de", "codigo de",
            "a que categoria pertenece la", "a que categoria pertenece el", "a que categoria pertenece",
            "en que categoria esta la", "en que categoria esta el", "en que categoria esta",
            "categoria de la", "categoria del", "categoria de",
            "como se vende la", "como se vende el", "como se vende",
            "se vende por peso la", "se vende por peso el", "se vende por peso",
            "cual es el producto de menor costo", "cual es el producto de mayor costo",
            "cual es el de menor costo", "cual es el de mayor costo",
            "cual es el producto mas barato", "cual es el producto mas caro",
            "cual es el producto mas economico", "cual es el producto mas costoso",
            "cual es el mas barato", "cual es el mas caro", "cual es el mas economico", "cual es el mas costoso",
            "cuales son los mas baratos", "cuales son los mas caros",
            "el producto mas barato", "el producto mas caro", "producto mas barato", "producto mas caro",
            "mas barato", "mas baratos", "mas caro", "mas caros", "mas economico", "mas economica",
            "mas costoso", "mas costosa", "menor costo", "mayor costo", "menor precio", "mayor precio",
            "de todos los", "de todas las", "todos los", "todas las", "todos", "todas",
            "precio de la", "precio del", "precio de", "valor de la", "valor del", "valor de",
            "cuanto cuesta el", "cuanto cuesta la", "cuanto cuesta", "cuanto vale el", "cuanto vale la", "cuanto vale",
            "a como esta el", "a como esta la", "a como esta", "a como",
            "en la tienda", "en el negocio", "en el inventario", "en stock",
            "cuantos tipos de", "cuantas clases de", "cuantos sabores de", "cuantas marcas de", "cuantas presentaciones de",
            "cuantas unidades de", "cuantas unidades quedan de", "cuanto stock hay de", "cuanto stock de",
            "hay", "tienen", "venden", "queda", "quedan", "existe", "existen",
            "busca el producto", "busca el", "busca la", "busca",
            "producto", "productos", "articulo", "articulos", "item", "items",
            "cual es", "cuales son", "que es", "que son",
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al"
        ]

        # Ordenar por longitud descendente para reemplazar primero frases completas
        stopwords.sort(key=len, reverse=True)

        cleaned = text
        for stop in stopwords:
            cleaned = re.sub(r'\b' + re.escape(stop) + r'\b', ' ', cleaned)

        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        generic_words = {"", "producto", "productos", "articulo", "articulos", "item", "items", "todo", "todos"}
        if cleaned in generic_words or len(cleaned) <= 1:
            return None
        return cleaned
