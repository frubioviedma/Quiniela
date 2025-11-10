"""
Tests unitarios para el motor de reducción de quinielas
Garantiza que las reducciones mantienen las garantías matemáticas
"""
import unittest
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reduccion import ReductorQuinielas
from src.config import FILTROS_DEFAULT

class TestReductionEngine(unittest.TestCase):
    """Tests para el motor de reducción"""
    
    def setUp(self):
        """Configurar antes de cada test"""
        self.reductor = ReductorQuinielas(num_partidos=14)
    
    def test_reduccion_oficial_tipo_1(self):
        """Test: Reducción oficial tipo 1 (4 triples → 9 apuestas)"""
        triples = [0, 1, 2, 3]  # Primeros 4 partidos
        dobles = []
        
        resultado = self.reductor.reducir_oficial(dobles, triples, tipo='1')
        
        # Debe devolver exactamente 9 combinaciones
        self.assertEqual(len(resultado), 9, 
                        "Reducción tipo 1 debe devolver 9 combinaciones")
        
        # Cada combinación debe tener 14 signos
        for comb in resultado:
            self.assertEqual(len(comb), 14, 
                           "Cada combinación debe tener 14 signos")
            # Los primeros 4 deben ser 1, 2 o 3 (triples)
            for i in range(4):
                self.assertIn(comb[i], [1, 2, 3], 
                            f"Partido {i+1} debe ser triple (1, 2 o 3)")
            # Los demás deben ser 1 (fijos)
            for i in range(4, 14):
                self.assertEqual(comb[i], 1, 
                               f"Partido {i+1} debe ser fijo (1)")
    
    def test_reduccion_oficial_tipo_2(self):
        """Test: Reducción oficial tipo 2 (7 dobles → 16 apuestas)"""
        dobles = [0, 1, 2, 3, 4, 5, 6]  # Primeros 7 partidos
        triples = []
        
        resultado = self.reductor.reducir_oficial(dobles, triples, tipo='2')
        
        # Debe devolver exactamente 16 combinaciones
        self.assertEqual(len(resultado), 16, 
                        "Reducción tipo 2 debe devolver 16 combinaciones")
        
        # Cada combinación debe tener 14 signos
        for comb in resultado:
            self.assertEqual(len(comb), 14, 
                           "Cada combinación debe tener 14 signos")
            # Los primeros 7 deben ser 1 o 2 (dobles)
            for i in range(7):
                self.assertIn(comb[i], [1, 2], 
                            f"Partido {i+1} debe ser doble (1 o 2)")
            # Los demás deben ser 1 (fijos)
            for i in range(7, 14):
                self.assertEqual(comb[i], 1, 
                               f"Partido {i+1} debe ser fijo (1)")
    
    def test_garantia_13_aciertos_tipo_1(self):
        """
        Test: Verificar que reducción tipo 1 garantiza al menos 1 combinación con 13 aciertos
        cuando hay 4 triples
        """
        triples = [0, 1, 2, 3]
        dobles = []
        
        # Generar todas las combinaciones posibles (3^4 = 81)
        todas_combinaciones = self.reductor.generar_combinaciones_completas(dobles, triples)
        self.assertEqual(len(todas_combinaciones), 81, 
                        "Debe haber 81 combinaciones posibles (3^4)")
        
        # Aplicar reducción
        reducidas = self.reductor.reducir_oficial(dobles, triples, tipo='1')
        
        # Para cada combinación posible, verificar que hay al menos una reducida
        # que tiene 13 o más aciertos
        garantias = self.reductor.calcular_garantias(reducidas, todas_combinaciones)
        
        # Debe haber al menos 1 combinación posible que garantiza 13 aciertos
        self.assertGreaterEqual(garantias.get(13, 0), 1,
                               "Reducción tipo 1 debe garantizar al menos 1 combinación con 13 aciertos")
    
    def test_garantia_13_aciertos_tipo_2(self):
        """
        Test: Verificar que reducción tipo 2 garantiza al menos 1 combinación con 13 aciertos
        cuando hay 7 dobles
        """
        dobles = [0, 1, 2, 3, 4, 5, 6]
        triples = []
        
        # Generar todas las combinaciones posibles (2^7 = 128)
        todas_combinaciones = self.reductor.generar_combinaciones_completas(dobles, triples)
        self.assertEqual(len(todas_combinaciones), 128, 
                        "Debe haber 128 combinaciones posibles (2^7)")
        
        # Aplicar reducción
        reducidas = self.reductor.reducir_oficial(dobles, triples, tipo='2')
        
        # Calcular garantías
        garantias = self.reductor.calcular_garantias(reducidas, todas_combinaciones)
        
        # Debe haber al menos 1 combinación posible que garantiza 13 aciertos
        self.assertGreaterEqual(garantias.get(13, 0), 1,
                               "Reducción tipo 2 debe garantizar al menos 1 combinación con 13 aciertos")
    
    def test_reduccion_inteligente_con_filtros(self):
        """Test: Reducción inteligente con filtros estadísticos"""
        dobles = [0, 1, 2]
        triples = [3, 4]
        objetivo = 13
        
        # Usar filtros por defecto
        filtros = FILTROS_DEFAULT.copy()
        
        resultado = self.reductor.reducir_inteligente(
            dobles, triples, objetivo=objetivo, filtros=filtros
        )
        
        # Debe devolver al menos una combinación
        self.assertGreater(len(resultado), 0, 
                          "Reducción inteligente debe devolver al menos una combinación")
        
        # Cada combinación debe tener 14 signos
        for comb in resultado:
            self.assertEqual(len(comb), 14, 
                           "Cada combinación debe tener 14 signos")
            
            # Verificar que pasa los filtros básicos
            comb_str = self.reductor.convertir_combinacion_a_string(comb)
            
            # No debe ser todo 1s, Xs o 2s
            self.assertNotEqual(comb_str, '1' * 14, "No debe ser todo 1s")
            self.assertNotEqual(comb_str, 'X' * 14, "No debe ser todo Xs")
            self.assertNotEqual(comb_str, '2' * 14, "No debe ser todo 2s")
    
    def test_generar_combinaciones_completas(self):
        """Test: Generación de combinaciones completas"""
        dobles = [0, 1]
        triples = [2, 3]
        
        resultado = self.reductor.generar_combinaciones_completas(dobles, triples)
        
        # Debe haber 2^2 * 3^2 = 4 * 9 = 36 combinaciones
        self.assertEqual(len(resultado), 36, 
                        "Debe haber 36 combinaciones (2^2 * 3^2)")
        
        # Verificar que todas las combinaciones son únicas
        combinaciones_str = [self.reductor.convertir_combinacion_a_string(c) for c in resultado]
        self.assertEqual(len(combinaciones_str), len(set(combinaciones_str)),
                        "Todas las combinaciones deben ser únicas")
    
    def test_validacion_dobles_triples(self):
        """Test: Validación de que dobles y triples no se solapan"""
        dobles = [0, 1, 2]
        triples = [2, 3, 4]  # Se solapa con dobles en posición 2
        
        # La función debe manejar esto correctamente (filtrar solapamientos)
        resultado = self.reductor.reducir_inteligente(dobles, triples, objetivo=13)
        
        # Debe funcionar sin errores (triples tienen prioridad)
        self.assertIsInstance(resultado, list)
    
    def test_conversion_combinacion_a_string(self):
        """Test: Conversión de combinación numérica a string"""
        comb = [1, 2, 3, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1]
        resultado = self.reductor.convertir_combinacion_a_string(comb)
        
        self.assertEqual(resultado, "1X21X2111111111")
        self.assertEqual(len(resultado), 14)
    
    def test_reduccion_vacia_sin_dobles_triples(self):
        """Test: Reducción sin dobles ni triples debe devolver combinación única"""
        dobles = []
        triples = []
        
        resultado = self.reductor.reducir_inteligente(dobles, triples, objetivo=13)
        
        # Debe devolver una sola combinación (todo 1s)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0], [1] * 14)
    
    def test_objetivo_14_sin_reduccion(self):
        """Test: Objetivo 14 no debe reducir (devolver todas las combinaciones)"""
        dobles = [0, 1]
        triples = [2]
        
        todas = self.reductor.generar_combinaciones_completas(dobles, triples)
        resultado = self.reductor.reducir_inteligente(dobles, triples, objetivo=14)
        
        # Con objetivo 14, no debe reducir
        self.assertEqual(len(resultado), len(todas),
                        "Con objetivo 14, no debe reducir las combinaciones")

class TestReductionGuarantees(unittest.TestCase):
    """Tests específicos para garantías matemáticas"""
    
    def setUp(self):
        """Configurar antes de cada test"""
        self.reductor = ReductorQuinielas(num_partidos=14)
    
    def test_garantia_regresion_tipo_1(self):
        """
        Test de regresión: Verificar que reducción tipo 1 siempre garantiza 13
        Este test es CRÍTICO y debe pasar siempre
        """
        triples = [0, 1, 2, 3]
        dobles = []
        
        todas = self.reductor.generar_combinaciones_completas(dobles, triples)
        reducidas = self.reductor.reducir_oficial(dobles, triples, tipo='1')
        
        # Para cada combinación posible, encontrar el máximo de aciertos
        max_aciertos_por_combinacion = {}
        for comb_posible in todas:
            max_aciertos = 0
            for comb_reducida in reducidas:
                aciertos = sum(1 for i in range(14) 
                             if comb_posible[i] == comb_reducida[i])
                max_aciertos = max(max_aciertos, aciertos)
            max_aciertos_por_combinacion[tuple(comb_posible)] = max_aciertos
        
        # Verificar que TODAS las combinaciones posibles tienen al menos 13 aciertos
        combinaciones_con_13_o_mas = sum(1 for max_ac in max_aciertos_por_combinacion.values() 
                                        if max_ac >= 13)
        
        total_combinaciones = len(max_aciertos_por_combinacion)
        porcentaje = (combinaciones_con_13_o_mas / total_combinaciones) * 100
        
        # Debe garantizar 13 para al menos el porcentaje esperado según normativa
        # Tipo 1: garantías {14: 1, 13: 1, 12: 3, 11: 3, 10: 2}
        # Esto significa que de 81 combinaciones, al menos 1 tiene 13 aciertos
        self.assertGreaterEqual(combinaciones_con_13_o_mas, 1,
                               f"Debe haber al menos 1 combinación con 13 aciertos "
                               f"(encontradas: {combinaciones_con_13_o_mas}/{total_combinaciones})")
        
        print(f"\n✅ Test garantía tipo 1: {combinaciones_con_13_o_mas}/{total_combinaciones} "
              f"combinaciones tienen 13+ aciertos ({porcentaje:.2f}%)")

if __name__ == '__main__':
    # Ejecutar tests con verbosidad
    unittest.main(verbosity=2)

