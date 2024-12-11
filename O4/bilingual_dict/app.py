from flask import Flask, request, jsonify, render_template
from model.model import load_embeddings, load_model, get_translation

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'message': 'API is running'})


@app.route('/load', methods=['GET'])
def load():
    load_model()
    return jsonify({'message': 'Model loaded successfully'})


@app.route('/translate', methods=['POST'])
def translate():
    word = request.json.get('word', '').strip()
    if not word:
        return jsonify({'error': 'Word is required'}), 400

    translation = get_translation(word)
    if not translation:
        return jsonify({'error': 'No translation found'}), 404

    return jsonify({'translation': translation})

if __name__ == '__main__':
    app.run(debug=True)

