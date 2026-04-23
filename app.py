import json
import uuid
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for
from psycopg2.extras import RealDictCursor
from database import get_connection
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ================= CONFIG UPLOAD =================
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# cria pasta se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= ROTAS =================

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API de catalogo de filmes"}), 200


@app.route('/ping', methods=['GET'])
def ping():
    conn = get_connection()
    if conn:
        conn.close()
    return jsonify({"message": "pong! API Rodando!"}), 200


# LISTAR FILMES
@app.route('/filmes', methods=['GET'])
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()

        if conn is None:
            return jsonify({"erro": "falha na conexão com banco"}), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()

        print('filmes----', filmes)

        conn.close()
        return render_template("index.html", filmes=filmes)

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": str(ex)}), 500


# NOVO FILME
@app.route("/novo", methods=["GET", "POST"])
def novo_filme():
    sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"

    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            file = request.files.get("capa")

            if not file or file.filename == "":
                return jsonify({"erro": "arquivo não enviado"}), 400

            if not allowed_file(file.filename):
                return jsonify({"erro": "formato inválido (use jpg, jpeg, png)"}), 400

            # nome seguro + único
            ext = file.filename.rsplit('.', 1)[1].lower()
            nome_arquivo = f"{uuid.uuid4()}.{ext}"
            nome_arquivo = secure_filename(nome_arquivo)

            caminho = f'{app.config['UPLOAD_FOLDER']}/{nome_arquivo}'

            # caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)

            file.save(caminho)

            url_capa = caminho  # salva caminho no banco

            params = [titulo, genero, ano, url_capa]

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        return render_template("novo_filme.html")

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": str(ex)}), 500


# EDITAR FILME
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    try:
        conn = get_connection()

        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            file = request.files.get("capa")

            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                nome_arquivo = f"{uuid.uuid4()}.{ext}"
                nome_arquivo = secure_filename(nome_arquivo)

                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                file.save(caminho)

                url_capa = caminho
            else:
                url_capa = request.form["url_capa"]

            sql_update = """
                UPDATE filmes 
                SET titulo = %s, genero = %s, ano = %s, url_capa = %s 
                WHERE id = %s
            """

            params = [titulo, genero, ano, url_capa, id]

            cursor = conn.cursor()
            cursor.execute(sql_update, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM filmes WHERE id = %s", [id])
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))

        return render_template("editar_filme.html", filme=filme)

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": str(ex)}), 500


# DELETAR
@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM filmes WHERE id = %s", [id])
        conn.commit()
        conn.close()

        return redirect(url_for("listar_filmes"))

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": str(ex)}), 500


if __name__ == '__main__':
    app.run(debug=True)