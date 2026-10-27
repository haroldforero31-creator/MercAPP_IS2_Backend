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
def ask_merki():
    """
    POST /api/merki/ask
    Recibe la pregunta en lenguaje natural y retorna la respuesta procesada por Merki.
    Payload: { "question": "¿Cuánto cuesta el arroz Diana?" }
    """
    data = request.get_json() or {}
    question = data.get('question', '').strip()

    if not question:
        return jsonify({
            "success": True,
            "intent": "empty",
            "response": "No alcancé a escucharte bien. ¿Puedes repetirme tu pregunta?",
            "data": None
        })

    # Determinar store_id: del usuario en sesión o del payload
    store_id = None
    if current_user and current_user.is_authenticated:
        store_id = getattr(current_user, 'store_id', None)

    if not store_id:
        store_id = data.get('store_id', 1)

    try:
        result = MerkiService.process_question(store_id=store_id, raw_question=question)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "intent": "error",
            "response": "Disculpa, de momento no cuento con esa información pero puedes consultar con uno de nuestros administradores.",
            "error": str(e),
            "data": None
        }), 200


@merki_controller.route('/merki/suggestions', methods=['GET'])
def get_merki_suggestions():
    """
    GET /api/merki/suggestions?store_id=X
    Retorna chips de sugerencias dinámicas adaptadas al negocio activo.
    """
    store_id = request.args.get('store_id', type=int)
    if not store_id and current_user and current_user.is_authenticated:
        store_id = getattr(current_user, 'store_id', None)
    if not store_id:
        store_id = 1

    suggestions = MerkiService.get_dynamic_suggestions(store_id)
    return jsonify({
        "success": True,
        "store_id": store_id,
        "suggestions": suggestions
    })


@merki_controller.route('/merki/transcribe', methods=['POST'])
def transcribe_merki_audio():
    """
    POST /api/merki/transcribe
    Recibe un archivo de audio WAV en form-data 'audio' o body binario,
    lo transcribe a texto en español y, en una sola llamada de ultra baja latencia,
    procesa y retorna la respuesta inteligente de Merki.
    """
    audio_file = request.files.get('audio')
    audio_bytes = None
    if audio_file:
        audio_bytes = audio_file.read()
    elif request.data:
        audio_bytes = request.data

    if not audio_bytes or len(audio_bytes) < 600:
        return jsonify({"success": True, "text": "", "empty": True, "message": "Audio muy corto o vacío"})

    # Determinar store_id
    store_id = request.form.get('store_id', type=int) or request.args.get('store_id', type=int)
    if not store_id and current_user and current_user.is_authenticated:
        store_id = getattr(current_user, 'store_id', None)
    if not store_id:
        store_id = 1

    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = _recognizer.record(source)

        transcript = ""
        try:
            # Reconocimiento directo de un solo paso en español colombiano (es-CO)
            transcript = _recognizer.recognize_google(audio_data, language='es-CO')
        except sr.UnknownValueError:
            transcript = ""
        except Exception as stt_err:
            print(f"[Merki STT recognize_google error] {stt_err}")
            transcript = ""

        transcript = transcript.strip()
        if not transcript:
            return jsonify({
                "success": True,
                "text": "",
                "empty": True
            })

        # Procesar de inmediato la pregunta en el backend para recortar la latencia a la mitad
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
        print(f"[Merki Transcribe Error] {type(e).__name__}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "text": ""
        }), 200



