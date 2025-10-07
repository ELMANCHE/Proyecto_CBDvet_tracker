from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'dev-secret')

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.route('/', methods=['GET'])
def form():
    """Renderiza el formulario principal (frontend solo).
    No guarda en base de datos: por ahora recoge los datos y los muestra en pantalla.
    """
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Recolectar datos del formulario
    data = request.form.to_dict(flat=False)
    # Para parámetros clínicos y tratamientos que pueden repetirse, también
    

    # Mostrar por ahora en la página de confirmación
    return render_template('confirm.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
