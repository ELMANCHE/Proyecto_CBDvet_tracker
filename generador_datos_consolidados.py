import pandas as pd
from faker import Faker
import random
import numpy as np
from datetime import datetime, timedelta

# Configurar Faker para datos en español
fake = Faker('es_ES')

# Configuraciones
CANTIDAD_REGISTROS = 10000  # Número de registros de tratamientos (filas finales)

print("Generando datos consolidados para minería de datos...")
print("=" * 60)

def generar_datos_consolidados(cantidad):
    """Genera un dataset consolidado para minería de datos"""
    
    # Listas de datos realistas
    especialidades_vet = [
        'Medicina General', 'Cirugía', 'Dermatología', 'Cardiología',
        'Oncología', 'Neurología', 'Oftalmología', 'Traumatología'
    ]
    
    especies_info = {
        'Perro': {
            'razas': ['Golden Retriever', 'Labrador', 'Pastor Alemán', 'Bulldog Francés',
                     'Chihuahua', 'Poodle', 'Beagle', 'Rottweiler', 'Yorkshire', 'Mestizo'],
            'peso_min': 2.0, 'peso_max': 45.0, 'edad_max': 15.0
        },
        'Gato': {
            'razas': ['Persa', 'Siamés', 'Maine Coon', 'Mestizo', 'British Shorthair'],
            'peso_min': 2.5, 'peso_max': 8.0, 'edad_max': 18.0
        },
        'Conejo': {
            'razas': ['Holandés', 'Angora', 'Rex', 'Mestizo'],
            'peso_min': 1.0, 'peso_max': 3.5, 'edad_max': 10.0
        }
    }
    
    productos_cbd = [
        {'nombre': 'CannaPet Oil', 'concentracion': 5.0, 'fabricante': 'VetPharma Solutions'},
        {'nombre': 'CBD Vet Plus', 'concentracion': 10.0, 'fabricante': 'Natural Pet Remedies'},
        {'nombre': 'Hemp4Pets', 'concentracion': 2.5, 'fabricante': 'CBD Animal Labs'},
        {'nombre': 'VetCBD Premium', 'concentracion': 15.0, 'fabricante': 'Hemp4Animals Inc.'},
        {'nombre': 'PurePaws CBD', 'concentracion': 7.5, 'fabricante': 'Therapeutic Pets Co.'}
    ]
    
    motivos_diagnosticos = [
        {'motivo': 'Dolor crónico', 'diagnostico': 'Artritis degenerativa'},
        {'motivo': 'Epilepsia', 'diagnostico': 'Epilepsia idiopática'},
        {'motivo': 'Ansiedad', 'diagnostico': 'Ansiedad por separación'},
        {'motivo': 'Cáncer', 'diagnostico': 'Linfoma canino'},
        {'motivo': 'Inflamación', 'diagnostico': 'Enfermedad inflamatoria intestinal'},
        {'motivo': 'Artritis', 'diagnostico': 'Displasia de cadera'},
        {'motivo': 'Dolor post-operatorio', 'diagnostico': 'Dolor post-traumático'},
        {'motivo': 'Convulsiones', 'diagnostico': 'Trastorno convulsivo'},
        {'motivo': 'Pérdida de apetito', 'diagnostico': 'Síndrome de disfunción cognitiva'},
        {'motivo': 'Dermatitis', 'diagnostico': 'Dermatitis atópica'}
    ]
    
    efectos_secundarios = [
        'Somnolencia leve', 'Disminución del apetito', 'Sequedad en boca',
        'Ligera sedación', 'Malestar gastrointestinal', 'Letargo temporal',
        'Sin efectos observados', 'Vómitos ocasionales', 'Diarrea leve'
    ]
    
    frecuencias = ['1 vez al día', '2 veces al día', '3 veces al día', 'Cada 12 horas']
    sexos = ['Macho', 'Hembra']
    severidades = ['Leve', 'Moderado', 'Sin efectos']
    
    nombres_mascotas = ['Max', 'Luna', 'Rocky', 'Bella', 'Charlie', 'Daisy', 'Cooper', 'Lucy', 'Milo', 'Lola']
    
    datos_consolidados = []
    
    print(f"Generando {cantidad} registros consolidados...")
    
    for i in range(cantidad):
        # Seleccionar especie y datos relacionados
        especie = random.choices(['Perro', 'Gato', 'Conejo'], weights=[75, 20, 5])[0]
        info_especie = especies_info[especie]
        
        # Generar datos del paciente
        raza = random.choice(info_especie['razas'])
        sexo = random.choice(sexos)
        edad = round(random.uniform(0.5, info_especie['edad_max']), 1)
        peso = round(random.uniform(info_especie['peso_min'], info_especie['peso_max']), 2)
        
        # Generar datos del propietario
        propietario_nombre = fake.name()
        propietario_telefono = fake.phone_number()
        propietario_email = fake.email()
        propietario_direccion = fake.address()
        
        # Generar datos del veterinario
        veterinario_nombre = f"Dr. {fake.name()}"
        especialidad = random.choice(especialidades_vet)
        licencia = f"VET-{random.randint(10000, 99999)}"
        
        # Generar datos de consulta
        fecha_consulta = fake.date_between(start_date='-2y', end_date='today')
        motivo_diagnostico = random.choice(motivos_diagnosticos)
        
        # Generar parámetros clínicos (valores antes y después del tratamiento)
        dolor_inicial = round(random.uniform(6.0, 10.0), 1)
        dolor_final = round(random.uniform(2.0, dolor_inicial), 1)
        
        movilidad_inicial = round(random.uniform(20.0, 60.0), 1)
        movilidad_final = round(random.uniform(movilidad_inicial, 95.0), 1)
        
        apetito_inicial = round(random.uniform(2.0, 7.0), 1)
        apetito_final = round(random.uniform(apetito_inicial, 10.0), 1)
        
        actividad_inicial = round(random.uniform(20.0, 60.0), 1)
        actividad_final = round(random.uniform(actividad_inicial, 95.0), 1)
        
        ansiedad_inicial = round(random.uniform(5.0, 10.0), 1)
        ansiedad_final = round(random.uniform(0.0, ansiedad_inicial), 1)
        
        # Generar datos del producto CBD
        producto = random.choice(productos_cbd)
        
        # Calcular dosis basada en peso (0.1-0.5 mg/kg)
        dosis_mg_kg = round(random.uniform(0.1, 0.5), 2)
        dosis_total = round(dosis_mg_kg * peso, 2)
        
        frecuencia = random.choice(frecuencias)
        duracion_dias = random.choice([30, 60, 90, 120])
        
        # Efectos secundarios (80% sin efectos)
        efecto_secundario = random.choices(efectos_secundarios, 
                                         weights=[5, 3, 3, 4, 2, 2, 70, 3, 3])[0]
        severidad = 'Sin efectos' if efecto_secundario == 'Sin efectos observados' else random.choice(['Leve', 'Moderado'])
        
        # Calcular mejorías
        mejoria_dolor = round(((dolor_inicial - dolor_final) / dolor_inicial) * 100, 1)
        mejoria_movilidad = round(((movilidad_final - movilidad_inicial) / movilidad_inicial) * 100, 1)
        mejoria_apetito = round(((apetito_final - apetito_inicial) / apetito_inicial) * 100, 1)
        mejoria_actividad = round(((actividad_final - actividad_inicial) / actividad_inicial) * 100, 1)
        mejoria_ansiedad = round(((ansiedad_inicial - ansiedad_final) / ansiedad_inicial) * 100, 1)
        
        # Generar fecha de seguimiento (1-3 meses después)
        fecha_seguimiento = fecha_consulta + timedelta(days=random.randint(30, 90))
        
        registro = {
            # Datos del propietario
            'propietario_nombre': propietario_nombre,
            'propietario_telefono': propietario_telefono,
            'propietario_email': propietario_email,
            'propietario_direccion': propietario_direccion,
            
            # Datos del paciente
            'paciente_nombre': random.choice(nombres_mascotas),
            'especie': especie,
            'raza': raza,
            'sexo': sexo,
            'edad_anios': edad,
            'peso_kg': peso,
            
            # Datos del veterinario
            'veterinario_nombre': veterinario_nombre,
            'veterinario_especialidad': especialidad,
            'veterinario_licencia': licencia,
            
            # Datos de la consulta
            'fecha_consulta': fecha_consulta.strftime('%Y-%m-%d'),
            'motivo_consulta': motivo_diagnostico['motivo'],
            'diagnostico': motivo_diagnostico['diagnostico'],
            
            # Parámetros clínicos iniciales
            'dolor_inicial_escala_10': dolor_inicial,
            'movilidad_inicial_porcentaje': movilidad_inicial,
            'apetito_inicial_escala_10': apetito_inicial,
            'actividad_inicial_porcentaje': actividad_inicial,
            'ansiedad_inicial_escala_10': ansiedad_inicial,
            
            # Datos del tratamiento CBD
            'producto_cbd_nombre': producto['nombre'],
            'concentracion_mg_ml': producto['concentracion'],
            'fabricante': producto['fabricante'],
            'dosis_mg_kg': dosis_mg_kg,
            'dosis_total_mg': dosis_total,
            'frecuencia_administracion': frecuencia,
            'duracion_tratamiento_dias': duracion_dias,
            
            # Efectos secundarios
            'efecto_secundario': efecto_secundario,
            'severidad_efecto': severidad,
            
            # Parámetros clínicos finales (después del tratamiento)
            'fecha_seguimiento': fecha_seguimiento.strftime('%Y-%m-%d'),
            'dolor_final_escala_10': dolor_final,
            'movilidad_final_porcentaje': movilidad_final,
            'apetito_final_escala_10': apetito_final,
            'actividad_final_porcentaje': actividad_final,
            'ansiedad_final_escala_10': ansiedad_final,
            
            # Mejorías calculadas (%)
            'mejoria_dolor_porcentaje': mejoria_dolor,
            'mejoria_movilidad_porcentaje': mejoria_movilidad,
            'mejoria_apetito_porcentaje': mejoria_apetito,
            'mejoria_actividad_porcentaje': mejoria_actividad,
            'mejoria_ansiedad_porcentaje': mejoria_ansiedad,
            
            # Indicador de éxito del tratamiento
            'tratamiento_exitoso': 'Sí' if (mejoria_dolor > 30 or mejoria_movilidad > 25) and severidad != 'Severo' else 'No'
        }
        
        datos_consolidados.append(registro)
    
    return datos_consolidados

# Generar datos
datos = generar_datos_consolidados(CANTIDAD_REGISTROS)

# Crear DataFrame y guardar
df = pd.DataFrame(datos)
archivo_csv = "datos_consolidados_cbd_veterinaria.csv"
df.to_csv(archivo_csv, index=False, encoding='utf-8')

print("=" * 60)
print("🎉 GENERACIÓN COMPLETADA!")
print(f"✓ Archivo creado: {archivo_csv}")
print(f"✓ Total de registros: {len(datos)}")
print(f"✓ Total de columnas: {len(df.columns)}")
print("=" * 60)
print("Columnas incluidas:")
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")
print("=" * 60)
print("¡Dataset listo ")

# Mostrar estadísticas básicas
print("\n ESTADÍSTICAS BÁSICAS:")
print(f"• Especies: {df['especie'].value_counts().to_dict()}")
print(f"• Tratamientos exitosos: {df['tratamiento_exitoso'].value_counts().to_dict()}")
print(f"• Efectos secundarios sin efectos: {(df['efecto_secundario'] == 'Sin efectos observados').sum()}")
print(f"• Mejora promedio en dolor: {df['mejoria_dolor_porcentaje'].mean():.1f}%")
print(f"• Mejora promedio en movilidad: {df['mejoria_movilidad_porcentaje'].mean():.1f}%")