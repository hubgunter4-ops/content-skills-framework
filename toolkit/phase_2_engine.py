from __future__ import annotations

import csv
import io
import json
import math
import re
from collections import Counter
from statistics import mean, median, pstdev
from typing import Any


REQUIRED = ("objective", "audience", "content", "format")


def words(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ'-]+", text, flags=re.UNICODE)


def numbers(text: str) -> list[float]:
    found = re.findall(r"(?<![\w])[-+]?\d+(?:[.,]\d+)?", text)
    return [float(value.replace(',', '.')) for value in found]


def table(rows: list[tuple[str, Any]]) -> str:
    return "| Campo | Resultado |\n| --- | --- |\n" + "\n".join(f"| {key} | {str(value).replace('|', '/')} |" for key, value in rows)


def parse_rows(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    delimiter = ',' if ',' in lines[0] else ('\t' if '\t' in lines[0] else None)
    if not delimiter:
        return []
    reader = csv.DictReader(io.StringIO('\n'.join(lines)), delimiter=delimiter)
    return [dict(row) for row in reader]


def data_summary(text: str) -> str:
    rows = parse_rows(text)
    nums = numbers(text)
    if not rows and not nums:
        return table([("filas detectadas", 0), ("valores numéricos", 0), ("nota", "Se requieren datos proporcionados por el usuario")])
    parts = [("filas detectadas", len(rows)), ("valores numéricos", len(nums))]
    if nums:
        parts.extend([("mínimo", min(nums)), ("máximo", max(nums)), ("media", round(mean(nums), 4)), ("mediana", round(median(nums), 4))])
    if rows:
        parts.append(("columnas", ', '.join(rows[0].keys())))
    return table(parts)


def quality_checks(text: str) -> str:
    rows = parse_rows(text)
    checks = [
        ("Entrada no vacía", bool(text.strip())),
        ("Filas estructuradas", bool(rows)),
        ("Valores faltantes", "Requiere inspección por columna" if rows else "No evaluado"),
        ("Duplicados", "Requiere clave definida" if rows else "No evaluado"),
        ("Sesgo de supervivencia", "Revisar población excluida y periodo"),
        ("Reproducibilidad", "Registrar fuente, fecha, transformación y versión"),
    ]
    return "| Control | Resultado |\n| --- | --- |\n" + "\n".join(f"| {key} | {value} |" for key, value in checks)


def _template(skill: dict[str, str], payload: dict[str, Any], sections: list[str], instruction: str) -> str:
    text = str(payload.get("content", "")).strip()
    body = [f"# {payload.get('objective', skill['name'])}", "", f"**Herramienta:** `{skill['slug']}`", f"**Audiencia:** {payload.get('audience', 'no especificada')}", "", instruction, ""]
    for index, section in enumerate(sections):
        body.extend([f"## {section}", text if index == 0 and text else "[Completar con datos verificables y trazables.]", ""])
    body.extend(["## Supuestos y límites", "- No se consultaron servicios externos automáticamente.", "- No se generaron datos ficticios ni se sustituyeron datos faltantes."])
    return "\n".join(body)


def _svg_bars(values: list[float]) -> str:
    if not values:
        values = [0]
    scale = 160 / max(max(values), 1)
    bars = []
    for index, value in enumerate(values[:12]):
        height = max(1, int(value * scale))
        bars.append(f'<rect x="{index * 42 + 20}" y="{190 - height}" width="28" height="{height}" />')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="220" role="img" aria-label="Gráfico de barras"><line x1="15" y1="190" x2="540" y2="190" stroke="black"/>' + ''.join(bars) + '</svg>'


def build_content(skill: dict[str, str], payload: dict[str, Any]) -> tuple[str, list[str]]:
    slug = skill['slug']
    text = str(payload.get('content', '')).strip()
    nums = numbers(text)
    summary = data_summary(text)
    if slug in {'analisis-de-acciones', 'analisis-financiero'}:
        content = f"# {skill['name']}\n\n## Resumen del corpus\n{summary}\n\n## Marco de análisis\n- Mercado y periodo de corte.\n- Ingresos, márgenes, deuda, flujo de caja y valoración.\n- Propiedad, presentaciones regulatorias y riesgos.\n\n## Datos externos requeridos\nPrecios, SEC y APIs financieras deben solicitarse explícitamente y citarse con fecha.\n\n## Entrada recibida\n{text or '[Pendiente]'}"
        return content, ["Añadir fuentes financieras autorizadas antes de tomar decisiones de inversión."]
    if slug in {'generador-de-excel', 'flujo-de-trabajo-de-analisis-de-excel', 'motor-de-excel-para-grandes-volumenes'}:
        content = f"# {skill['name']}\n\n## Libro propuesto\n{summary}\n\n## Hojas\n1. `raw_data`: datos originales sin modificar.\n2. `clean_data`: tipos, faltantes y duplicados documentados.\n3. `analysis`: agregaciones y métricas.\n4. `readme`: fuente, fecha, supuestos y diccionario.\n\n## Entrada\n{text or '[Proporcionar CSV, XLSX o tabla]'}"
        return content, ["Exportar a XLSX solo después de recibir un archivo o dataset real."]
    if slug == 'constructor-de-paneles-interactivos':
        data = json.dumps(nums[:20], ensure_ascii=False)
        content = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{payload.get('objective', 'Dashboard')}</title>
<style>body{{font-family:system-ui;margin:2rem}}svg{{border:1px solid #ddd;max-width:100%}}rect{{fill:#2563eb}}</style></head>
<body><h1>{payload.get('objective', 'Dashboard')}</h1><label>Filtro <input id="filter" placeholder="Filtrar texto"></label><div id="data">{text or 'Sin datos'}</div>{_svg_bars(nums)}</body>
<script>const chartData={data}; document.querySelector('#filter').addEventListener('input', event => document.querySelector('#data').hidden = !document.querySelector('#data').textContent.toLowerCase().includes(event.target.value.toLowerCase()));</script>
</html>'''
        return content, ["Abrir el HTML localmente y reemplazar chartData con datos reales si se requiere un dashboard completo."]
    if slug in {'analitica-de-trafico-web', 'verificador-de-trafico-web'}:
        return f"# {skill['name']}\n\n{table([('sesiones', 'Requiere exportación autorizada'), ('fuentes', 'orgánico, directo, referral y social'), ('geografía', 'Requiere datos por país'), ('periodo', 'Definir fecha de corte')])}\n\n## Datos recibidos\n{text or '[Pendiente]'}\n\n## Integraciones opcionales\nSimilarweb, Ahrefs, Semrush, DataForSEO o exportaciones de analítica; no se cargan sin solicitud explícita.", ["Solicitar credenciales o exportación autorizada solo si el usuario lo pide."]
    if slug == 'extractor-web-inteligente':
        return f"# Extractor Web Inteligente\n\n## Entrada\n{text or '[Proporcionar URL autorizada]'}\n\n## Plan de extracción\n1. Validar URL y permiso.\n2. Usar HTML estático o API oficial.\n3. Respetar robots, límites y términos del sitio.\n4. Guardar fuente, fecha y selectores.\n\nNo se evaden protecciones anti-bot ni se ejecutan técnicas de bypass.", ["Proporcionar una URL y autorización; no se ejecutó scraping automático."]
    if slug in {'validacion-de-datos', 'control-de-calidad-de-arn-de-celula-unica'}:
        return f"# {skill['name']}\n\n## Resumen\n{summary}\n\n## QA\n{quality_checks(text)}\n\n## Decisión\nPublicar solo después de revisar faltantes, outliers, metodología, sesgos y trazabilidad.", ["Revisar los controles con un responsable del dominio antes de compartir resultados."]
    if slug in {'visualizacion-estadistica', 'estudio-de-visualizacion-de-datos', 'graficos-cientificos', 'creador-de-graficos-antv'}:
        return f"# {skill['name']}\n\n## Gráfico reproducible\n{_svg_bars(nums)}\n\n## Datos\n{summary}\n\n## Accesibilidad\n- Etiquetar ejes y unidades.\n- No depender solo del color.\n- Exportar con texto alternativo y fuente.", ["Revisar la figura con los datos reales y elegir el tipo de gráfico según la variable."]
    if slug == 'risk-metrics-pro':
        returns = nums
        if len(returns) > 1:
            avg = mean(returns)
            deviation = pstdev(returns) or 0
            sharpe = avg / deviation if deviation else 0
            drawdown = min(returns) if returns else 0
            metrics = table([('observaciones', len(returns)), ('media', round(avg, 6)), ('volatilidad poblacional', round(deviation, 6)), ('Sharpe sin tasa libre', round(sharpe, 6)), ('drawdown aproximado', drawdown)])
        else:
            metrics = 'No hay suficientes retornos para calcular métricas.'
        return f"# Risk Metrics Pro\n\n{metrics}\n\n## Metodología\nDefinir frecuencia, horizonte, tasa libre, nivel de confianza y si los valores son retornos o precios antes de calcular VaR/CVaR/Sortino.", ["No usar estas métricas con una serie ambigua o insuficiente."]
    if slug in {'optimizador-de-consultas-sql', 'experto-en-consultas-sql', 'motor-sql-de-clickhouse', 'mejores-practicas-de-postgres', 'mongo-query-pro'}:
        query = text or '[Proporcionar consulta]'
        return f"# {skill['name']}\n\n## Consulta recibida\n```sql\n{query}\n```\n\n## Revisión\n- Ejecutar `EXPLAIN`/`EXPLAIN ANALYZE` solo en un entorno autorizado.\n- Revisar filtros, joins, cardinalidad, índices y columnas proyectadas.\n- Confirmar dialecto y permisos antes de reescribir.\n\n## Propuesta\n[Registrar la consulta optimizada y la mejora medida; no inventar tiempos.]", ["Comparar el plan antes y después con datos representativos."]
    if slug in {'potencia-estadistica-pro', 'modelado-estadistico', 'diseno-experimental'}:
        return _template(skill, payload, ['Pregunta y estimando', 'Diseño', 'Supuestos', 'Métricas', 'Diagnósticos', 'Reproducibilidad'], 'Marco de análisis estadístico sin ejecutar un modelo con datos no proporcionados.') , ["Definir diseño, supuestos y datos antes de interpretar resultados."]
    if slug == 'analisis-de-redes':
        edges = re.findall(r'([\w-]+)\s*(?:->|—|-)\s*([\w-]+)', text)
        nodes = sorted({node for edge in edges for node in edge})
        return f"# Análisis de Redes\n\n{table([('nodos', len(nodes)), ('aristas', len(edges)), ('densidad', round(len(edges) / max(len(nodes) * max(len(nodes) - 1, 1), 1), 6))])}\n\n## Edges detectadas\n" + ('\n'.join(f'- {a} → {b}' for a, b in edges) or '[Formato esperado: A -> B]') + "\n\n## Algoritmos\nCalcular centralidad, rutas y comunidades después de validar la dirección y el peso de cada arista.", ["Validar el modelo de red y la semántica de las relaciones."]
    if slug == 'solucionador-de-matematicas-simbolicas':
        return f"# Solucionador de matemáticas simbólicas\n\n## Expresión recibida\n`{text or '[x^2 + 2x + 1]'}`\n\n## Flujo seguro\n1. Parsear la expresión.\n2. Simplificar o resolver simbólicamente.\n3. Verificar sustituyendo en la ecuación original.\n4. Exportar a LaTeX o código numérico.\n\nNo se afirmó una solución sin un motor simbólico ejecutado.", ["Instalar o habilitar SymPy explícitamente si se requiere cálculo automático."]
    if slug in {'datos-fiscales-de-ee-uu', 'buscador-de-datos-cientificos', 'extractor-de-hacker-news', 'agent-reach'}:
        return f"# {skill['name']}\n\n## Consulta\n{text or '[Proporcionar consulta]'}\n\n## Fuente externa requerida\nLa herramienta prepara una consulta reproducible, pero no descarga datos sin que el usuario solicite explícitamente la integración correspondiente.\n\n## Salida esperada\nRegistrar endpoint, parámetros, fecha UTC, respuesta cruda y transformación aplicada.", ["Solicitar la fuente o credencial antes de consultar datos externos."]
    if slug in {'arquitecto-de-pipelines-de-ml', 'entrenador-de-modelos-de-rl', 'redes-neuronales-de-grafos', 'explicador-shap', 'explorador-de-datos-umap'}:
        return _template(skill, payload, ['Datos y esquema', 'Preprocesamiento', 'Modelo', 'Evaluación', 'Reproducibilidad', 'Riesgos'], 'Plan técnico de aprendizaje automático sin entrenar un modelo con datos ausentes.') , ["Separar entrenamiento, validación y prueba; no usar datos simulados como evidencia."]
    if slug in {'analitica-de-big-data', 'motor-de-datos-polars', 'escalador-de-datos-dask', 'chdb-data-store'}:
        return f"# {skill['name']}\n\n{summary}\n\n## Pipeline escalable\n- Leer por lotes o streaming.\n- Proyectar columnas necesarias.\n- Filtrar antes de agregar.\n- Medir memoria, tiempo y particiones.\n- Registrar versión y formato de salida.\n\n## Entrada\n{text or '[Proporcionar archivo o dataset]'}", ["Medir rendimiento con un dataset real; no se simuló una carga masiva."]
    if slug in {'patrones-de-busqueda-hibrida', 'patrones-de-busqueda-vectorial', 'optimizador-de-indices-vectoriales'}:
        return f"# {skill['name']}\n\n## Diseño\n- Búsqueda lexical: BM25 o equivalente.\n- Búsqueda vectorial: definir embedding y métrica.\n- Fusión: RRF o combinación lineal.\n- Evaluación: recall@k, MRR, nDCG y latencia.\n\n## Consulta\n{text or '[Pendiente]'}", ["Medir recuperación y latencia con un conjunto de evaluación real."]
    if slug in {'asistente-de-modelado-de-power-bi', 'disenador-de-esquemas-de-mongodb', 'busqueda-y-ia-de-mongodb', 'arquitecto-de-clickhouse'}:
        return _template(skill, payload, ['Modelo actual', 'Esquema recomendado', 'Relaciones e índices', 'Seguridad', 'Rendimiento', 'Validación'], 'Diseño de modelo basado en la información recibida; no se conectó a una instancia.') , ["Probar el esquema en un entorno de desarrollo autorizado."]
    if slug == 'revision-de-tabla-de-contratos':
        columns = ['partes', 'vigencia', 'precio', 'renovación', 'terminación', 'responsabilidad', 'indemnización', 'confidencialidad', 'jurisdicción']
        return f"# Revisión de tabla de contratos\n\n## Campos extraídos\n" + table([(column, 'Pendiente de extracción desde el contrato') for column in columns]) + f"\n\n## Texto recibido\n{text or '[Cargar contratos autorizados]'}", ["Revisar cada extracción contra el documento original antes de exportar."]
    if slug == 'extractor-de-datos-de-documentos':
        return f"# Extractor de Datos de Documentos\n\n## Archivos esperados\nPDF, DOCX o PPTX proporcionados por el usuario.\n\n## Elementos a extraer\nTablas, números, gráficos, texto, formato, páginas y metadatos.\n\n## Entrada\n{text or '[Adjuntar documento autorizado]'}", ["Verificar OCR, páginas y tablas contra el documento original."]
    return _template(skill, payload, ['Entrada', 'Método', 'Resultados esperados', 'Validación'], 'Herramienta de análisis de datos con ejecución local y trazabilidad de supuestos.'), ["Completar con datos reales y registrar fuentes, fecha y transformaciones."]


def run_tool(skill: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if not str(payload.get(key, '')).strip()]
    text = str(payload.get('content', '')).strip()
    integration = payload.get('integration', payload.get('integrations'))
    warnings: list[str] = []
    assumptions = []
    if integration:
        assumptions.append('Integración externa solicitada explícitamente; no se ejecuta sin conector y credencial autorizados.')
        warnings.append('La integración de Datos se mantiene en modo seguro y requiere configuración específica del proveedor.')
    else:
        assumptions.append('No se cargaron integraciones externas; se trabajó solo con la entrada proporcionada.')
    if missing:
        return {'skill': skill, 'status': 'needs_input', 'analysis': {'missing_fields': missing, 'input_characters': len(text), 'input_words': len(words(text)), 'assumptions': assumptions}, 'deliverable': {'title': skill['name'], 'format': payload.get('format', 'markdown'), 'content': '', 'next_steps': ['Completar: ' + ', '.join(missing)]}, 'warnings': ['Faltan entradas obligatorias: ' + ', '.join(missing)] + warnings}
    content, next_steps = build_content(skill, payload)
    return {'skill': skill, 'status': 'ready', 'analysis': {'missing_fields': [], 'input_characters': len(text), 'input_words': len(words(text)), 'assumptions': assumptions + ['No se inventaron datos ni métricas.']}, 'deliverable': {'title': skill['name'] + ' — ' + str(payload['objective']), 'format': payload.get('format', 'markdown'), 'content': content, 'next_steps': next_steps}, 'warnings': warnings}
