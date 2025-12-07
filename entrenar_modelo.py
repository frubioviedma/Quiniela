#!/usr/bin/env python3
"""
Script para entrenar el modelo de Machine Learning
Uso: python entrenar_modelo.py [--epochs 50] [--batch-size 32]
"""
import argparse
import logging
from pathlib import Path
from src.database import DatabaseManager
from src.ml_autolearning import SistemaAutoAprendizaje

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Entrenar modelo ML de quiniela')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Número de épocas de entrenamiento (default: 50)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Tamaño del batch (default: 32)')
    parser.add_argument('--max-partidos', type=int, default=5000,
                       help='Máximo número de partidos históricos (default: 5000)')
    parser.add_argument('--db-path', type=str, default='historical.db',
                       help='Path a la base de datos (default: historical.db)')

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("ENTRENAMIENTO DEL MODELO DE MACHINE LEARNING")
    logger.info("="*60)
    logger.info(f"Configuración:")
    logger.info(f"  - Épocas: {args.epochs}")
    logger.info(f"  - Batch size: {args.batch_size}")
    logger.info(f"  - Max partidos: {args.max_partidos}")
    logger.info(f"  - Base de datos: {args.db_path}")
    logger.info("="*60)

    # Inicializar base de datos
    db_path = Path(args.db_path)
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada en {db_path}")
        logger.error("Por favor, ejecuta primero el scraping de datos históricos")
        return

    db_manager = DatabaseManager(db_path)
    logger.info("✓ Base de datos cargada")

    # Inicializar sistema ML
    modelo_path = Path("models/quiniela_model.pkl")
    ml_system = SistemaAutoAprendizaje(db_manager, modelo_path)
    logger.info("✓ Sistema ML inicializado")

    # Entrenar
    logger.info("\nIniciando entrenamiento...")
    ml_system.entrenar_inicial(epochs=args.epochs, batch_size=args.batch_size)

    # Mostrar métricas finales
    metricas = ml_system.get_metricas()
    logger.info("\n" + "="*60)
    logger.info("RESULTADOS DEL ENTRENAMIENTO")
    logger.info("="*60)
    logger.info(f"Épocas completadas: {metricas['num_epochs']}")
    logger.info(f"Accuracy final: {metricas['ultima_accuracy']:.3f}")
    logger.info(f"Loss final: {metricas['ultima_loss']:.4f}")
    logger.info(f"Mejor accuracy alcanzada: {metricas['mejor_accuracy']:.3f}")
    logger.info("="*60)

    logger.info("\n✓ Modelo guardado en: models/quiniela_model.pkl")
    logger.info("✓ Entrenamiento completado exitosamente")


if __name__ == '__main__':
    main()
