from flask import jsonify

def success_response(data=None, message=None, status_code=200):
    """
    Formato estándar de respuesta exitosa para la API REST.
    """
    response = {
        "success": True,
        "status_code": status_code
    }
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code

def error_response(message="Ha ocurrido un error", errors=None, status_code=400):
    """
    Formato estándar de respuesta de error para la API REST.
    """
    response = {
        "success": False,
        "status_code": status_code,
        "error": message
    }
    if errors:
        response["details"] = errors
    return jsonify(response), status_code
