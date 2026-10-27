import random
import string

def round_to_50(value):
    """Round a value to the nearest $50 COP."""
    return int(round(value / 50.0) * 50)

def format_weight(grams, unit='kg'):
    """Format grams to display string: 1400, 'kg' -> '1.400 kg' / 1400, 'lb' -> '2.800 lb'"""
    if not unit:
        unit = 'kg'
    if grams is None:
        return '0 lb' if unit == 'lb' else '0 kg'
    try:
        grams = float(grams)
    except (ValueError, TypeError):
        return str(grams)
        
    if unit == 'lb':
        libras = grams / 500.0
        return f"{libras:,.3f} lb".replace(',', '.')
    else:
        kilos = grams / 1000.0
        return f"{kilos:,.3f} kg".replace(',', '.')

def generate_verification_code():
    """Generate a random 6-digit numeric verification code."""
    return str(random.randint(100000, 999999))

def validate_payment(payment_method, total, amount_received=None, card_last4=None, 
                     card_approval=None, transfer_bank=None, transfer_ref=None, transfer_name=None,
                     amount_cash=None, amount_card=None, amount_transfer=None):
    """Validate payment fields. Returns (errors_list, cleaned_data_dict)."""
    errors = []
    data = {'payment_method': payment_method}
    
    if payment_method == 'efectivo':
        if not amount_received:
            errors.append('Debes ingresar el monto recibido.')
        else:
            amount_str = str(amount_received).strip()
            if '.' in amount_str or ',' in amount_str:
                errors.append('El monto debe ser un número entero sin puntos ni comas.')
            elif not amount_str.isdigit():
                errors.append('El monto recibido solo puede contener números.')
            else:
                amount = int(amount_str)
                if amount < total:
                    errors.append(f'El monto recibido (${amount:,}) es menor al total (${total:,}).'.replace(',', '.'))
                elif amount > 10000000:
                    errors.append('El monto recibido no puede superar $10.000.000.')
                else:
                    data['amount_received'] = amount
                    data['change_given'] = amount - total
                    data['payment_ref'] = None
                    data['amount_cash'] = total
                    data['amount_card'] = 0
                    data['amount_transfer'] = 0
    
    elif payment_method == 'tarjeta':
        data['amount_received'] = total
        data['change_given'] = 0
        ref_parts = []
        if card_last4 and card_last4.strip():
            ref_parts.append(f"****{card_last4.strip()}")
        if card_approval and card_approval.strip():
            ref_parts.append(f"Aprob:{card_approval.strip()}")
        data['payment_ref'] = ' '.join(ref_parts) if ref_parts else 'Pago con tarjeta'
        data['amount_cash'] = 0
        data['amount_card'] = total
        data['amount_transfer'] = 0
    
    elif payment_method == 'transferencia':
        data['amount_received'] = total
        data['change_given'] = 0
        ref_parts = []
        if transfer_bank and transfer_bank.strip():
            ref_parts.append(transfer_bank.strip())
        if transfer_ref and transfer_ref.strip():
            ref_parts.append(f"#{transfer_ref.strip()}")
        if transfer_name and transfer_name.strip():
            ref_parts.append(f"({transfer_name.strip()})")
        data['payment_ref'] = ' '.join(ref_parts) if ref_parts else 'Pago por transferencia'
        data['amount_cash'] = 0
        data['amount_card'] = 0
        data['amount_transfer'] = total
        
    elif payment_method == 'mixto':
        try:
            val_cash = int(amount_cash or 0)
            val_card = int(amount_card or 0)
            val_transfer = int(amount_transfer or 0)
        except ValueError:
            errors.append('Los montos deben ser valores numéricos enteros.')
            return errors, data
            
        if val_cash < 0 or val_card < 0 or val_transfer < 0:
            errors.append('Los montos no pueden ser negativos.')
            return errors, data
            
        split_sum = val_cash + val_card + val_transfer
        if split_sum < total:
            errors.append(f'La suma de pagos (${split_sum:,}) es menor al total (${total:,}).'.replace(',', '.'))
        elif split_sum > total and (val_card > 0 or val_transfer > 0) and val_cash == 0:
            errors.append('No se puede dar cambio sobre pagos electrónicos.')
        else:
            change = split_sum - total if val_cash > 0 else 0
            data['amount_received'] = split_sum
            data['change_given'] = change
            data['amount_cash'] = val_cash - change if val_cash >= change else val_cash
            data['amount_card'] = val_card
            data['amount_transfer'] = val_transfer
            parts = []
            if val_cash > 0: parts.append(f"Efectivo: ${val_cash:,}".replace(',', '.'))
            if val_card > 0: parts.append(f"Tarjeta: ${val_card:,}".replace(',', '.'))
            if val_transfer > 0: parts.append(f"Transf: ${val_transfer:,}".replace(',', '.'))
            data['payment_ref'] = ' | '.join(parts)
            
    elif payment_method == 'fiado':
        data['amount_received'] = 0
        data['change_given'] = 0
        data['payment_ref'] = 'Crédito a cliente'
        data['amount_cash'] = 0
        data['amount_card'] = 0
        data['amount_transfer'] = 0
        
    else:
        errors.append('Método de pago no válido.')
        
    return errors, data
