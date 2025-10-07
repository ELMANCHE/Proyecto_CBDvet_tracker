from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path

from flask import Flask, current_app, flash, redirect, render_template, request, url_for

from database import SessionLocal, init_db, session_scope
from models import (
    Consulta,
    Paciente,
    ParametroClinico,
    ProductoCBD,
    Propietario,
    TratamientoCBD,
    Veterinario,
)


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/cbdvet_uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _parse_decimal(value: str | None) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: str | None) -> date | None:
    if value is None or value == "":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


try:
    with app.app_context():
        init_db()
except Exception as exc:  # pragma: no cover - logging de inicialización
    app.logger.exception("Error inicializando la base de datos: %s", exc)


@app.teardown_appcontext
def remove_session(_: Exception | None) -> None:
    SessionLocal.remove()


@app.route("/", methods=["GET"])
def form():
    """Renderiza el formulario principal."""
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    form_data = request.form

    consulta_fecha = _parse_date(form_data.get("consulta_fecha"))
    if consulta_fecha is None:
        flash("La fecha de la consulta es obligatoria.", "danger")
        return redirect(url_for("form"))

    valoracion_mejora = _parse_int(form_data.get("valoracion_mejora"))
    if valoracion_mejora is not None and not (1 <= valoracion_mejora <= 10):
        flash("La valoración de mejora debe estar entre 1 y 10.", "danger")
        return redirect(url_for("form"))

    try:
        with session_scope() as session:
            propietario = Propietario(
                nombre=form_data.get("prop_nombre", "").strip(),
                telefono=form_data.get("prop_telefono"),
                correo=form_data.get("prop_correo"),
                direccion=form_data.get("prop_direccion"),
            )
            if not propietario.nombre:
                raise ValueError("El nombre del propietario es obligatorio.")
            session.add(propietario)
            session.flush()

            paciente = Paciente(
                nombre=form_data.get("pac_nombre", "").strip(),
                especie=form_data.get("pac_especie", "").strip(),
                raza=form_data.get("pac_raza"),
                sexo=form_data.get("pac_sexo"),
                edad_anios=_parse_decimal(form_data.get("pac_edad")),
                peso_kg=_parse_decimal(form_data.get("pac_peso")),
                propietario=propietario,
            )
            if not paciente.nombre or not paciente.especie:
                raise ValueError("Los datos del paciente son obligatorios.")
            session.add(paciente)
            session.flush()

            vet_nombre = (form_data.get("vet_nombre") or "").strip()
            vet_especialidad = form_data.get("vet_especialidad")

            veterinarian = None
            if vet_nombre:
                veterinarian = (
                    session.query(Veterinario)
                    .filter_by(nombre=vet_nombre, especialidad=vet_especialidad)
                    .one_or_none()
                )

            if veterinarian is None:
                veterinarian = Veterinario(
                    nombre=vet_nombre or "Sin nombre",
                    especialidad=vet_especialidad,
                )
                session.add(veterinarian)
                session.flush()

            consulta = Consulta(
                fecha=consulta_fecha,
                motivo=form_data.get("consulta_motivo"),
                diagnostico=form_data.get("consulta_diagnostico"),
                valoracion_mejora=valoracion_mejora,
                paciente=paciente,
                veterinario=veterinarian,
            )
            session.add(consulta)
            session.flush()

            nombre_producto = (form_data.get("prod_nombre") or "").strip()
            if not nombre_producto:
                raise ValueError("El nombre del producto CBD es obligatorio para registrar el tratamiento.")

            producto = session.query(ProductoCBD).filter_by(nombre_comercial=nombre_producto).one_or_none()
            if producto is None:
                producto = ProductoCBD(
                    nombre_comercial=nombre_producto,
                    concentracion_mg_ml=_parse_decimal(form_data.get("prod_concentracion")),
                    fabricante=form_data.get("prod_fabricante"),
                )
                session.add(producto)
                session.flush()

            nombres_param = form_data.getlist("param_nombre[]")
            valores_param = form_data.getlist("param_valor[]")
            unidades_param = form_data.getlist("param_unidad[]")

            for nombre, valor, unidad in zip(nombres_param, valores_param, unidades_param):
                nombre_limpio = (nombre or "").strip()
                valor_decimal = _parse_decimal(valor)
                if not nombre_limpio or valor_decimal is None:
                    continue
                parametro = ParametroClinico(
                    consulta=consulta,
                    nombre_parametro=nombre_limpio,
                    valor=valor_decimal,
                    unidad=(unidad or "").strip() or None,
                )
                session.add(parametro)

            dosis_list = form_data.getlist("trat_dosis_mg[]")
            frec_list = form_data.getlist("trat_frecuencia[]")
            duracion_list = form_data.getlist("trat_duracion[]")
            obs_list = form_data.getlist("trat_observaciones[]")

            tratamientos_creados = 0
            for dosis, frecuencia, duracion, obs in zip(dosis_list, frec_list, duracion_list, obs_list):
                dosis_decimal = _parse_decimal(dosis)
                if dosis_decimal is None:
                    continue
                tratamiento = TratamientoCBD(
                    consulta=consulta,
                    producto=producto,
                    dosis_mg=dosis_decimal,
                    frecuencia=(frecuencia or "").strip() or None,
                    duracion_dias=_parse_int(duracion),
                    observaciones=(obs or "").strip() or None,
                )
                session.add(tratamiento)
                tratamientos_creados += 1

            if tratamientos_creados == 0:
                raise ValueError("Debes registrar al menos una dosis para el tratamiento CBD.")

    except Exception as exc:
        current_app.logger.exception("Error al guardar el registro: %s", exc)
        flash(str(exc), "danger")
        return redirect(url_for("form"))

    flash("Registro guardado correctamente.", "success")
    data = form_data.to_dict(flat=False)
    return render_template("confirm.html", data=data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
