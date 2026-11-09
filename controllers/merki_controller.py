import io
import speech_recognition as sr
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from services.merki_service import MerkiService
from utilities.response_helper import success_response, error_response

merki_controller = Blueprint('merki_controller', __name__, url_prefix='/api')

# Reconocedor de voz preconfigurado a nivel de módulo para máxima velocidad
_recognizer = sr.Recognizer()
_recognizer.operation_timeout = 3.5
_recognizer.energy_threshold = 260
_recognizer.dynamic_energy_threshold = False


@merki_controller.route('/merki/ask', methods=['POST'])
@login_required
def ask_merki():
    """
    POST /api/merki/ask
    Recibe la pregunta en lenguaje natural y retorna la respuesta procesada por Merki.
    P0-4 FIX: Requiere autenticación y vincula estrictamente la consulta a la tienda del usuario.
    """
    user_store_id = getattr(current_user, 'store_id', None)
    if not user_store_id:
        return jsonify({
            "success": False,
            "error": "Acceso denegado. Se requiere una tienda asociada.",
            "data": None
        }), 403

    data = request.get_json() or {}
    question = data.get('question', '').strip()

    if not question:
        return jsonify({
            "success": True,
            "intent": "empty",
            "response": "No alcancé a escucharte bien. ¿Puedes repetirme tu pregunta?",
            "data": None
        })

    # P0-4 FIX: store_id se deriva estrictamente del usuario autenticado
    store_id = user_store_id

    try:
        result = MerkiService.process_question(store_id=store_id, raw_question=question)
        return jsonify(result)
    except Exception as e:
        import logging
        logging.getLogger("merki").warning(f"Error en ask_merki: {e}")
        return jsonify({
            "success": False,
            "intent": "error",
            "response": "Disculpa, de momento no cuento con esa información pero puedes consultar con uno de nuestros administradores.",
            "data": None
        }), 200


@merki_controller.route('/merki/suggestions', methods=['GET'])
def get_merki_suggestions():
    """
    GET /api/merki/suggestions?store_id=X
    Retorna chips de sugerencias dinámicas adaptadas al negocio activo.
    """
    store_id = None
    if current_user and current_user.is_authenticated:
        store_id = getattr(current_user, 'store_id', None)
    if not store_id:
        store_id = request.args.get('store_id', 1, type=int)

    suggestions = MerkiService.get_dynamic_suggestions(store_id)
    return jsonify({
        "success": True,
        "store_id": store_id,
        "suggestions": suggestions
    })


@merki_controller.route('/merki/transcribe', methods=['POST'])
@login_required
def transcribe_merki_audio():
    """
    POST /api/merki/transcribe
    Recibe un archivo de audio WAV en form-data 'audio' o body binario,
    lo transcribe a texto en español y procesa la respuesta inteligente de Merki.
    P0-4 FIX: Requiere autenticación y deriva store_id del usuario en sesión.
    """
    user_store_id = getattr(current_user, 'store_id', None)
    if not user_store_id:
        return jsonify({
            "success": False,
            "error": "Acceso denegado. Se requiere una tienda asociada.",
            "data": None
        }), 403

    store_id = user_store_id

    audio_file = request.files.get('audio')
    audio_bytes = None
    if audio_file:
        audio_bytes = audio_file.read()
    elif request.data:
        audio_bytes = request.data

    if not audio_bytes or len(audio_bytes) < 600:
        return jsonify({"success": True, "text": "", "empty": True, "message": "Audio muy corto o vacío"})

    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = _recognizer.record(source)

        transcript = ""
        try:
            transcript = _recognizer.recognize_google(audio_data, language='es-CO')
        except sr.UnknownValueError:
            transcript = ""
        except Exception as stt_err:
            import logging
            logging.getLogger("merki").warning(f"[Merki STT error] {stt_err}")
            transcript = ""

        transcript = transcript.strip()
        if not transcript:
            return jsonify({
                "success": True,
                "text": "",
                "empty": True
            })

        result = MerkiService.process_question(store_id=store_id, raw_question=transcript)

        return jsonify({
            "success": True,
            "text": transcript,
            "empty": False,
            "response": result.get("response"),
            "intent": result.get("intent"),
            "data": result.get("data")
        })
    except Exception as e:
        import logging
        logging.getLogger("merki").warning(f"Error procesando audio Merki: {e}")
        return jsonify({
            "success": False,
            "error": "No fue posible procesar el audio. Por favor intenta de nuevo.",
            "text": ""
        }), 200
