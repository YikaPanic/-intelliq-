# encoding=utf-8
from models.chatbot_model import ChatbotModel
from utils.app_init import before_init
from utils.helpers import load_all_scene_configs
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize ChatbotModel instance
# ChatbotModelのインスタンスを初期化
chatbot_model = ChatbotModel(load_all_scene_configs())

# Research direction: Let AI write request headers and modify request formats based on responses
# to achieve efficient interaction with minimal communication rounds.
# 研究方向：AIにリクエストヘッダーを書かせ、レスポンスに基づいてリクエスト形式を修正させ、
# 最小限の通信回数で効率的な対話を実現する

# AI is responsible for modifying request formats and writing React debug log information,
# then refining request formats based on returned log information
# AIはリクエスト形式の修正とReactのデバッグログ情報の作成を担当し、
# 返されたログ情報に基づいてリクエスト形式を改善する

@app.route('/multi_question', methods=['POST'])
def api_multi_question():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    response = chatbot_model.process_multi_question(question)
    return jsonify({"answer": response})

@app.route('/update_slots', methods=['POST'])
def api_update_slots():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    response = chatbot_model.process_slot_update(question)
    return jsonify(response)

@app.route('/', methods=['GET'])
def index():
    return send_file('./demo/user_input.html')

if __name__ == '__main__':
    before_init()
    app.run(port=5000, debug=True)
