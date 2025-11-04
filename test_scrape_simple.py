"""Test simple para scrapear quiniela - 15 partidos"""
import requests
from bs4 import BeautifulSoup
import re

def scrape_eduardolosilla_simple():
    """Método simple y directo para obtener los 15 partidos"""
    url = "https://www.eduardolosilla.es/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"📡 Obteniendo desde: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar la sección de quiniela - puede estar en varios sitios
        # Intentar encontrar donde dice "JORNADA" o números del 1-15
        
        # Método 1: Buscar tabla con clase específica
        tablas = soup.find_all('table')
        print(f"✅ Encontradas {len(tablas)} tablas en la página")
        
        # Método 2: Buscar divs que contengan "JORNADA"
        jornada_divs = soup.find_all(string=re.compile(r'JORNADA\s+\d+', re.I))
        print(f"✅ Encontrados {len(jornada_divs)} elementos con 'JORNADA'")
        
        # Método 3: Buscar números del 1 al 15 seguidos de equipos
        texto_completo = soup.get_text()
        
        # Buscar patrón: número + equipo - equipo
        patron = r'(\d{1,2})\s+([A-Z][A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*[-–]\s*([A-Z][A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)(?:\s+(?:MAR|MIE|JUE|VIE|SAB|DOM|LUN)\s+\d{1,2}:\d{2}|\s+\d+-\d+)'
        
        matches = re.findall(patron, texto_completo, re.MULTILINE)
        
        print(f"\n📋 Encontrados {len(matches)} posibles partidos:")
        partidos = []
        for num, local, visitante in matches[:15]:  # Solo primeros 15
            num_int = int(num)
            if 1 <= num_int <= 15:
                local = local.strip()
                visitante = visitante.strip()
                print(f"  {num_int:2d}. {local} - {visitante}")
                partidos.append({
                    'partido_numero': num_int,
                    'local': local,
                    'visitante': visitante
                })
        
        # Asegurar que tenemos exactamente 15
        if len(partidos) != 15:
            print(f"\n⚠️ ADVERTENCIA: Solo se encontraron {len(partidos)} partidos, deben ser 15")
        else:
            print(f"\n✅✅✅ ÉXITO: Se encontraron TODOS los 15 partidos")
        
        return partidos
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_loteriasyapuestas_simple():
    """Scraping desde la web oficial"""
    url = "https://www.loteriasyapuestas.es/es/quiniela"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"\n📡 Intentando web oficial: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar tabla de partidos
        tablas = soup.find_all('table')
        print(f"✅ Encontradas {len(tablas)} tablas")
        
        partidos = []
        
        # Buscar filas con partidos
        for tabla in tablas:
            filas = tabla.find_all('tr')
            for fila in filas:
                celdas = fila.find_all(['td', 'th'])
                if len(celdas) >= 3:
                    texto = ' '.join([c.get_text(' ', strip=True) for c in celdas])
                    # Buscar patrón de partido
                    match = re.search(r'(\d{1,2})\s+(.+?)\s*[-–]\s*(.+?)(?:\s+(?:MAR|MIE|JUE|VIE|SAB|DOM|LUN)|$)', texto)
                    if match:
                        num = int(match.group(1))
                        if 1 <= num <= 15:
                            local = match.group(2).strip()
                            visitante = match.group(3).strip()
                            if local and visitante and len(local) > 2 and len(visitante) > 2:
                                print(f"  {num:2d}. {local} - {visitante}")
                                partidos.append({
                                    'partido_numero': num,
                                    'local': local,
                                    'visitante': visitante
                                })
        
        if len(partidos) == 15:
            print(f"\n✅✅✅ ÉXITO: Se encontraron TODOS los 15 partidos")
        else:
            print(f"\n⚠️ Solo {len(partidos)} partidos encontrados")
        
        return partidos
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE SCRAPING SIMPLE - QUINIELA")
    print("=" * 60)
    
    # Intentar eduardolosilla primero
    partidos = scrape_eduardolosilla_simple()
    
    # Si no funciona, intentar web oficial
    if len(partidos) < 15:
        print("\n🔄 Intentando fuente alternativa...")
        partidos = scrape_loteriasyapuestas_simple()
    
    # Mostrar resumen final
    print("\n" + "=" * 60)
    print(f"RESUMEN FINAL: {len(partidos)}/15 partidos obtenidos")
    print("=" * 60)
    
    if len(partidos) == 15:
        print("✅ TODO CORRECTO")
    else:
        print("❌ FALTAN PARTIDOS")
        print(f"   Partidos encontrados: {[p['partido_numero'] for p in partidos]}")
        faltantes = [i for i in range(1, 16) if i not in [p['partido_numero'] for p in partidos]]
        if faltantes:
            print(f"   Partidos faltantes: {faltantes}")

