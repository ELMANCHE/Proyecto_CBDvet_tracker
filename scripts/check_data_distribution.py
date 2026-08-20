"""Script para verificar la distribución de datos en la tabla resultado."""

from database import get_db_session, Resultado
from sqlalchemy import func
import pandas as pd

def check_distribution():
    """Verifica la distribución de nivel_mejora y el target"""
    db = get_db_session()
    
    try:
        # Obtener distribución de nivel_mejora
        print("=" * 60)
        print("DISTRIBUCIÓN DE nivel_mejora")
        print("=" * 60)
        
        nivel_dist = db.query(
            Resultado.nivel_mejora,
            func.count(Resultado.id)
        ).group_by(Resultado.nivel_mejora).order_by(Resultado.nivel_mejora).all()
        
        total = sum(count for _, count in nivel_dist)
        
        for nivel, count in nivel_dist:
            pct = (count / total) * 100 if total > 0 else 0
            print(f"nivel_mejora {nivel}: {count} registros ({pct:.1f}%)")
        
        print(f"\nTotal registros: {total}")
        
        # Verificar distribución del target (nivel_mejora >= 7)
        print("\n" + "=" * 60)
        print("DISTRIBUCIÓN DEL TARGET (nivel_mejora >= 7)")
        print("=" * 60)
        
        target_high = db.query(func.count(Resultado.id)).filter(Resultado.nivel_mejora >= 7).scalar()
        target_low = db.query(func.count(Resultado.id)).filter(Resultado.nivel_mejora < 7).scalar()
        
        print(f"Clase POSITIVA (>=7): {target_high} registros ({target_high/total*100:.1f}%)")
        print(f"Clase NEGATIVA (<7): {target_low} registros ({target_low/total*100:.1f}%)")
        
        # Evaluar balance
        ratio = target_high / target_low if target_low > 0 else 0
        print(f"\nRatio (positivo/negativo): {ratio:.2f}")
        
        if 0.5 <= ratio <= 2.0:
            print("✅ Datos bien balanceados para entrenamiento")
        elif ratio > 2.0:
            print("⚠️  Clase positiva dominante - considerar técnicas de balanceo")
        else:
            print("⚠️  Clase negativa dominante - considerar técnicas de balanceo")
            
        # Verificar registros actualizados (1-150)
        print("\n" + "=" * 60)
        print("VERIFICACIÓN DE REGISTROS ACTUALIZADOS (1-150)")
        print("=" * 60)
        
        updated_records = db.query(Resultado.nivel_mejora).filter(
            Resultado.id >= 1, Resultado.id <= 150
        ).all()
        
        updated_vals = [r[0] for r in updated_records]
        print(f"Registros actualizados: {len(updated_vals)}")
        print(f"Rango de valores: {min(updated_vals)} - {max(updated_vals)}")
        print(f"Promedio: {sum(updated_vals)/len(updated_vals):.2f}")
        
        # Verificar si hay valores fuera de rango
        out_of_range = db.query(func.count(Resultado.id)).filter(
            (Resultado.nivel_mejora < 1) | (Resultado.nivel_mejora > 10)
        ).scalar()
        
        if out_of_range > 0:
            print(f"⚠️  {out_of_range} registros con nivel_mejora fuera de rango (1-10)")
        else:
            print("✅ Todos los valores están en rango (1-10)")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_distribution()
