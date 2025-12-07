#!/usr/bin/env python3
"""
Ejemplo de uso del Sistema de Machine Learning con Auto-Aprendizaje
Este script demuestra cómo usar el nuevo sistema ML v2.0
"""

import logging
from pathlib import Path
from src.database import DatabaseManager
from src.pronostico_ml import PronosticoEngineML

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def ejemplo_basico():
    """Ejemplo básico de uso del sistema ML"""
    print("="*70)
    print("EJEMPLO 1: Uso Básico del Sistema ML")
    print("="*70)

    # 1. Inicializar base de datos
    db = DatabaseManager(Path('historical.db'))
    print("✓ Base de datos cargada")

    # 2. Inicializar motor con ML
    engine = PronosticoEngineML(
        db,
        peso_historico=0.25,
        peso_cuotas=0.25,
        peso_forma=0.25,
        peso_ml=0.25,      # 25% para ML
        usar_ml=True       # Activar ML
    )
    print("✓ Motor ML inicializado")

    # 3. Hacer pronóstico de un partido
    print("\nPronosticando: Real Madrid vs Barcelona")
    pronostico = engine.pronostico_final(
        local="Real Madrid",
        visitante="Barcelona",
        cuotas={'1': 2.5, 'X': 3.2, '2': 2.8},
        division=1,
        temporada='2024-25'
    )

    # 4. Mostrar resultados
    print("\nRESULTADOS:")
    print(f"  Probabilidades finales: {pronostico['probabilidades']}")
    print(f"  Recomendación: {pronostico['recomendacion']}")
    print(f"  Confianza: {pronostico['confianza']:.2%}")

    print("\nDesglose por método:")
    for metodo, probs in pronostico['desglose'].items():
        print(f"  {metodo.capitalize():12}: 1={probs['1']:.2f}, X={probs['X']:.2f}, 2={probs['2']:.2f}")

    print("\nPesos utilizados:")
    for metodo, peso in pronostico['pesos_usados'].items():
        print(f"  {metodo.capitalize():12}: {peso:.2%}")


def ejemplo_entrenamiento():
    """Ejemplo de entrenamiento del modelo"""
    print("\n" + "="*70)
    print("EJEMPLO 2: Entrenar el Modelo")
    print("="*70)

    db = DatabaseManager(Path('historical.db'))
    engine = PronosticoEngineML(db, usar_ml=True)

    print("\nEntrenando modelo con 20 épocas...")
    print("(En producción usa más épocas: 50-100)")

    # Entrenar
    engine.entrenar_modelo(epochs=20, batch_size=32)

    # Obtener métricas
    metricas = engine.get_metricas_ml()
    print("\nMÉTRICAS DEL MODELO:")
    print(f"  Épocas entrenadas: {metricas['num_epochs']}")
    print(f"  Accuracy final: {metricas['ultima_accuracy']:.2%}")
    print(f"  Loss final: {metricas['ultima_loss']:.4f}")
    print(f"  Mejor accuracy: {metricas['mejor_accuracy']:.2%}")


def ejemplo_reentrenamiento():
    """Ejemplo de reentrenamiento con nuevos resultados"""
    print("\n" + "="*70)
    print("EJEMPLO 3: Reentrenar con Nuevos Resultados")
    print("="*70)

    db = DatabaseManager(Path('historical.db'))
    engine = PronosticoEngineML(db, usar_ml=True)

    # Simular resultados de una jornada
    resultados = [
        {
            'local': 'Real Madrid',
            'visitante': 'Barcelona',
            'resultado': '1',  # Victoria local
            'division': 1,
            'pred_historico': '1',
            'pred_cuotas': 'X',
            'pred_ml': '1',
            'real': '1'
        },
        {
            'local': 'Atlético Madrid',
            'visitante': 'Sevilla',
            'resultado': 'X',  # Empate
            'division': 1,
            'pred_historico': '1',
            'pred_cuotas': '1',
            'pred_ml': 'X',
            'real': 'X'
        },
        {
            'local': 'Valencia',
            'visitante': 'Athletic',
            'resultado': '2',  # Victoria visitante
            'division': 1,
            'pred_historico': '1',
            'pred_cuotas': '2',
            'pred_ml': '2',
            'real': '2'
        }
    ]

    print("\nReentrenando con resultados de la jornada...")
    engine.reentrenar_con_jornada(
        jornada=15,
        temporada='2024-25',
        resultados=resultados
    )
    print("✓ Modelo reentrenado")

    print("\nAjustando pesos según performance...")
    engine.ajustar_pesos_dinamicamente(resultados)
    print("✓ Pesos ajustados")

    # Mostrar nuevas métricas
    metricas = engine.get_metricas_ml()
    print("\nNUEVOS PESOS ADAPTATIVOS:")
    pesos = metricas.get('pesos_adaptativos', {})
    for metodo, peso in pesos.items():
        print(f"  {metodo.capitalize():12}: {peso:.2%}")


def ejemplo_comparacion_metodos():
    """Ejemplo comparando métodos clásicos vs ML"""
    print("\n" + "="*70)
    print("EJEMPLO 4: Comparación de Métodos")
    print("="*70)

    db = DatabaseManager(Path('historical.db'))

    # Motor solo clásico
    engine_clasico = PronosticoEngineML(
        db,
        peso_historico=0.4,
        peso_cuotas=0.4,
        peso_forma=0.2,
        peso_ml=0.0,
        usar_ml=False
    )

    # Motor con ML
    engine_ml = PronosticoEngineML(
        db,
        peso_historico=0.25,
        peso_cuotas=0.25,
        peso_forma=0.25,
        peso_ml=0.25,
        usar_ml=True
    )

    # Partido de prueba
    partido = {
        'local': 'Real Madrid',
        'visitante': 'Atlético Madrid',
        'cuotas': {'1': 2.2, 'X': 3.4, '2': 3.1},
        'division': 1,
        'temporada': '2024-25'
    }

    print(f"\nPartido: {partido['local']} vs {partido['visitante']}")

    # Pronóstico clásico
    print("\n1. MÉTODO CLÁSICO (sin ML):")
    p_clasico = engine_clasico.pronostico_final(**partido)
    print(f"   Predicción: {p_clasico['recomendacion']}")
    print(f"   Probabilidades: 1={p_clasico['probabilidades']['1']:.2f}, "
          f"X={p_clasico['probabilidades']['X']:.2f}, "
          f"2={p_clasico['probabilidades']['2']:.2f}")
    print(f"   Confianza: {p_clasico['confianza']:.2%}")

    # Pronóstico con ML
    print("\n2. MÉTODO CON ML:")
    p_ml = engine_ml.pronostico_final(**partido)
    print(f"   Predicción: {p_ml['recomendacion']}")
    print(f"   Probabilidades: 1={p_ml['probabilidades']['1']:.2f}, "
          f"X={p_ml['probabilidades']['X']:.2f}, "
          f"2={p_ml['probabilidades']['2']:.2f}")
    print(f"   Confianza: {p_ml['confianza']:.2%}")

    # Comparar
    print("\n3. COMPARACIÓN:")
    print(f"   Mismo resultado: {'✓' if p_clasico['recomendacion'] == p_ml['recomendacion'] else '✗'}")
    print(f"   Diferencia en confianza: {abs(p_ml['confianza'] - p_clasico['confianza']):.2%}")


def ejemplo_jornada_completa():
    """Ejemplo procesando una jornada completa"""
    print("\n" + "="*70)
    print("EJEMPLO 5: Procesar Jornada Completa")
    print("="*70)

    db = DatabaseManager(Path('historical.db'))
    engine = PronosticoEngineML(db, usar_ml=True)

    # Jornada de ejemplo
    jornada = [
        {'local': 'Real Madrid', 'visitante': 'Barcelona'},
        {'local': 'Atlético Madrid', 'visitante': 'Sevilla'},
        {'local': 'Valencia', 'visitante': 'Athletic'},
        {'local': 'Real Sociedad', 'visitante': 'Betis'},
        {'local': 'Villarreal', 'visitante': 'Getafe'},
    ]

    print(f"\nProcesando {len(jornada)} partidos de la jornada...\n")

    predicciones = []
    for i, partido in enumerate(jornada, 1):
        pronostico = engine.pronostico_final(
            local=partido['local'],
            visitante=partido['visitante'],
            division=1,
            temporada='2024-25'
        )

        print(f"{i}. {partido['local']:20} vs {partido['visitante']:20} → "
              f"{pronostico['recomendacion']} (conf: {pronostico['confianza']:.1%})")

        predicciones.append({
            **partido,
            'prediccion': pronostico['recomendacion'],
            'probabilidades': pronostico['probabilidades']
        })

    print(f"\n✓ {len(predicciones)} predicciones generadas")


def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "="*70)
    print("SISTEMA DE MACHINE LEARNING v2.0 - EJEMPLOS DE USO")
    print("="*70)

    try:
        # Ejemplo 1: Uso básico
        ejemplo_basico()

        # Ejemplo 4: Comparación
        ejemplo_comparacion_metodos()

        # Ejemplo 5: Jornada completa
        ejemplo_jornada_completa()

        # Los ejemplos 2 y 3 requieren tiempo de entrenamiento
        # Descoméntalos si quieres probarlos:
        # ejemplo_entrenamiento()
        # ejemplo_reentrenamiento()

        print("\n" + "="*70)
        print("EJEMPLOS COMPLETADOS")
        print("="*70)
        print("\nPara entrenar el modelo completo, ejecuta:")
        print("  python entrenar_modelo.py --epochs 50")
        print("\nPara más información, consulta:")
        print("  ML_AUTO_APRENDIZAJE.md")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nAsegúrate de que:")
        print("  1. Existe historical.db con datos")
        print("  2. Las dependencias están instaladas")
        print("  3. El modelo ha sido entrenado")


if __name__ == '__main__':
    main()
