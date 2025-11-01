"""Módulo para exportar quinielas en diferentes formatos"""
import csv
import logging
from pathlib import Path
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

class ExportadorQuiniela:
    """Gestor de exportación de quinielas"""
    
    def __init__(self):
        """Inicializar exportador"""
        pass
    
    def exportar_csv(self, combinaciones: List[str], partidos: List[Dict], 
                    output_path: Path, temporada: str = "", jornada: int = 0):
        """
        Exportar quiniela a CSV
        
        Args:
            combinaciones: Lista de combinaciones como strings
            partidos: Lista de partidos con sus datos
            output_path: Path del archivo de salida
            temporada: Temporada de la quiniela
            jornada: Número de jornada
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Cabeceras
                writer.writerow(["Quiniela - Temporada", temporada, "Jornada", jornada])
                writer.writerow([])
                writer.writerow(["N°", "Combinación", "Coste (€)"])
                
                # Combinaciones
                for i, comb in enumerate(combinaciones, 1):
                    writer.writerow([i, comb, 0.75])
                
                # Resumen
                writer.writerow([])
                writer.writerow(["Total combinaciones:", len(combinaciones)])
                writer.writerow(["Coste total:", f"{len(combinaciones) * 0.75:.2f} €"])
            
            logger.info(f"Exportado CSV: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")
            raise
    
    def exportar_txt(self, combinaciones: List[str], output_path: Path,
                     temporada: str = "", jornada: int = 0):
        """
        Exportar quiniela a TXT (formato legible)
        
        Args:
            combinaciones: Lista de combinaciones como strings
            output_path: Path del archivo de salida
            temporada: Temporada
            jornada: Número de jornada
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"QUINIELA - Temporada {temporada} - Jornada {jornada}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, comb in enumerate(combinaciones, 1):
                    f.write(f"{i:3d}. {comb}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Total: {len(combinaciones)} combinaciones\n")
                f.write(f"Coste: {len(combinaciones) * 0.75:.2f} €\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"Exportado TXT: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exportando TXT: {e}")
            raise
    
    def exportar_pdf(self, combinaciones: List[str], partidos: List[Dict], 
                    output_path: Path, temporada: str = "", jornada: int = 0,
                    dobles: int = 0, triples: int = 0):
        """
        Exportar quiniela a PDF con diseño profesional
        
        Args:
            combinaciones: Lista de combinaciones
            partidos: Datos de partidos
            output_path: Path del archivo PDF
            temporada: Temporada
            jornada: Jornada
            dobles: Número de dobles
            triples: Número de triples
        """
        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1a237e'),
                alignment=TA_CENTER,
                spaceAfter=30
            )
            title = Paragraph(f"QUINIELA - Temporada {temporada} - Jornada {jornada}", title_style)
            elements.append(title)
            
            # Información de reducción
            info_text = f"Dobles: {dobles} | Triples: {triples} | Total: {len(combinaciones)} apuestas"
            info = Paragraph(info_text, styles['Normal'])
            elements.append(info)
            elements.append(Spacer(1, 12))
            
            # Tabla de combinaciones
            # Dividir en columnas para mejor presentación
            data = [['N°', 'Combinación', 'N°', 'Combinación', 'N°', 'Combinación']]
            
            # Añadir combinaciones en filas de 3 columnas
            for i in range(0, len(combinaciones), 3):
                row = []
                for j in range(3):
                    idx = i + j
                    if idx < len(combinaciones):
                        row.append(f"{idx + 1}")
                        row.append(combinaciones[idx])
                    else:
                        row.extend(['', ''])
                data.append(row)
            
            # Crear tabla
            table = Table(data, colWidths=[20*mm, 45*mm, 20*mm, 45*mm, 20*mm, 45*mm])
            
            # Estilos de tabla
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ])
            
            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Resumen
            total_cost = len(combinaciones) * 0.75
            summary_text = f"<b>Total combinaciones:</b> {len(combinaciones)}<br/>"
            summary_text += f"<b>Coste total:</b> {total_cost:.2f} €"
            summary = Paragraph(summary_text, styles['Normal'])
            elements.append(summary)
            
            # Construir PDF
            doc.build(elements)
            
            logger.info(f"Exportado PDF: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exportando PDF: {e}")
            raise

