"""Test scraping de webprincipal.com para obtener los 15 partidos"""
import requests
from bs4 import BeautifulSoup
import re

def scrape_webprincipal():
    """Scrapear quiniela desde webprincipal.com"""
    # Los datos se cargan via AJAX desde leerquiniela.php
    url = "https://www.webprincipal.com/quiniela/leerquiniela.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://www.webprincipal.com/quiniela/quiniela.php'
    }
    
    try:
        # Llamar al endpoint AJAX que devuelve JSON
        # temporadaactual=2025, jornada=-1 para la actual
        data = {
            'temporada': 2025,
            'jornada': -1,  # -1 = jornada actual
            'eslive': 0
        }
        
        print(f"Obteniendo datos desde: {url}")
        print(f"POST data: {data}")
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        # Intentar parsear como JSON
        try:
            json_data = response.json()
            print(f"\nOK: Datos JSON recibidos")
            print(f"Estructura: {list(json_data.keys())}")
            
            if 'partidos' in json_data:
                partidos = json_data['partidos']
                print(f"\nEncontrados {len(partidos)} partidos en JSON")
                
                # Mostrar estructura del primer partido
                if partidos:
                    print(f"\nEstructura del primer partido:")
                    print(f"Claves: {list(partidos[0].keys())}")
                    print(f"Valores: {partidos[0]}")
                
                for i, partido in enumerate(partidos[:15], 1):
                    # Probar diferentes nombres de campos
                    local = (partido.get('local') or partido.get('equipo1') or 
                            partido.get('equipo_local') or partido.get('local_equipo') or 'N/A')
                    visitante = (partido.get('visitante') or partido.get('equipo2') or 
                               partido.get('equipo_visitante') or partido.get('visitante_equipo') or 'N/A')
                    print(f"  {i:2d}. {local} - {visitante}")
                
                return json_data
            else:
                print("ADVERTENCIA: No se encontró 'partidos' en JSON")
                print(f"Claves disponibles: {list(json_data.keys())}")
                return json_data
                
        except ValueError:
            # No es JSON, intentar HTML
            print("No es JSON, intentando parsear HTML...")
            soup = BeautifulSoup(response.text, 'html.parser')
        
        # Guardar HTML para inspección
        with open('webprincipal_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("OK: HTML guardado en webprincipal_debug.html")
        
        # Buscar partidos - varias estrategias
        partidos = []
        
        # Estrategia 1: Buscar tablas con partidos
        tablas = soup.find_all('table')
        print(f"\nEncontradas {len(tablas)} tablas")
        
        for i, tabla in enumerate(tablas):
            print(f"\n--- Tabla {i+1} ---")
            filas = tabla.find_all('tr')
            print(f"Filas: {len(filas)}")
            
            for j, fila in enumerate(filas[:5]):  # Primeras 5 filas
                texto = fila.get_text(strip=True)
                if texto:
                    print(f"  Fila {j+1}: {texto[:100]}")
            
            # Buscar patrones de partidos
            texto_tabla = tabla.get_text()
            matches = re.findall(r'(\d+)\s+([A-Z][A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*[-–]\s*([A-Z][A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+)', texto_tabla)
            if matches:
                print(f"  OK: Encontrados {len(matches)} posibles partidos en esta tabla")
                for match in matches[:3]:
                    print(f"    {match[0]}. {match[1]} - {match[2]}")
        
        # Estrategia 2: Buscar por texto "PRONOSTICO" o "GRUPOS"
        pronostico_sec = soup.find(string=re.compile(r'PRONOSTICO|PRONÓSTICO', re.I))
        if pronostico_sec:
            print(f"\nOK: Encontrada seccion PRONOSTICO")
            # Buscar tabla siguiente
            tabla_pronostico = pronostico_sec.find_parent('table')
            if not tabla_pronostico:
                # Buscar siguiente tabla
                for elem in pronostico_sec.find_all_next('table', limit=3):
                    print(f"  Tabla siguiente encontrada")
                    break
        
        # Estrategia 3: Buscar todos los partidos numerados
        texto_completo = soup.get_text()
        patron = r'(\d{1,2})\s+([A-Z][A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]{3,}?)\s*[-–]\s*([A-Z][A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]{3,})'
        matches = re.findall(patron, texto_completo, re.MULTILINE)
        
        print(f"\nTOTAL: {len(matches)} posibles partidos encontrados:")
        partidos_unicos = {}
        for num, local, visitante in matches:
            num_int = int(num)
            if 1 <= num_int <= 15 and num_int not in partidos_unicos:
                local_clean = local.strip()
                visitante_clean = visitante.strip()
                if len(local_clean) > 2 and len(visitante_clean) > 2:
                    partidos_unicos[num_int] = {
                        'num': num_int,
                        'local': local_clean,
                        'visitante': visitante_clean
                    }
                    print(f"  {num_int:2d}. {local_clean} - {visitante_clean}")
        
        print(f"\nRESULTADO FINAL: {len(partidos_unicos)}/15 partidos unicos")
        
        if len(partidos_unicos) == 15:
            print("PERFECTO: Todos los 15 partidos encontrados")
        else:
            print(f"ADVERTENCIA: Faltan {15 - len(partidos_unicos)} partidos")
            faltantes = [i for i in range(1, 16) if i not in partidos_unicos]
            print(f"   Partidos faltantes: {faltantes}")
        
            return list(partidos_unicos.values())
        
        # Si llegamos aquí, no se encontró nada
        return []
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 60)
    print("TEST SCRAPING WEBPRINCIPAL.COM")
    print("=" * 60)
    partidos = scrape_webprincipal()
    print("\n" + "=" * 60)
    print(f"RESUMEN: {len(partidos)} partidos extraídos")
    print("=" * 60)

