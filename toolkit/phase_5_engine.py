from __future__ import annotations

import html
import json
import re
from typing import Any

REQUIRED = ('objective', 'audience', 'content', 'format')


def sec(title: str, body: str) -> str:
    return f'## {title}\n{body}\n'


def hex_color(text: str) -> str:
    match = re.search(r'#[0-9a-fA-F]{6}', text)
    return match.group(0) if match else '#2563eb'


def canvas_payload(title: str) -> dict[str, Any]:
    return {'nodes': [{'id': 'node-1', 'type': 'text', 'x': 80, 'y': 80, 'width': 240, 'height': 80, 'text': title}], 'edges': [], 'metadata': {'generated_locally': True}}


def build(skill: dict[str, str], payload: dict[str, Any]) -> tuple[str, list[str]]:
    name = skill['name']; low = (name + ' ' + skill['description']).lower(); text = str(payload.get('content', '')).strip(); objective = html.escape(str(payload.get('objective', name)))
    if 'accesibilidad' in low:
        return f"# Auditoría de accesibilidad\n\n{sec('Entrada', text or '[HTML, URL o código pendiente]')}{sec('WCAG 2.2', '- Contraste de texto y componentes.\n- Navegación completa por teclado y foco visible.\n- Objetivos táctiles y zoom.\n- Nombres accesibles, roles y estados.\n- Mensajes de error y orden de lectura.\n- Preferencia `prefers-reduced-motion`.')}{sec('Informe', 'Priorizar por impacto, frecuencia, criterio WCAG, evidencia, corrección y prueba de regresión.')}", ['Ejecutar pruebas con teclado, lector de pantalla y herramientas automatizadas autorizadas.']
    if 'paleta' in low:
        base = hex_color(text); colors = [f'{base} / paso {step}' for step in range(1, 12)]
        scale = '\n'.join('- ' + color for color in colors)
        tokens = ':root { --color-brand: ' + base + '; --color-focus: ' + base + '; }'
        contrast = 'Comprobar texto normal, texto grande, controles, estados hover/focus y modo oscuro contra WCAG 2.2.'
        return f"# Paleta de colores inteligente\n\n{sec('Color base', base)}{sec('Escala', scale)}{sec('Tokens', tokens)}{sec('Contraste', contrast)}", ['Medir contraste con los colores finales; no asumir que una escala cumple sin cálculo.']
    if 'mermaid' in low:
        return f"flowchart TD\n  A[Brief: {objective}] --> B[Diseño]\n  B --> C[Accesibilidad]\n  C --> D[Revisión]", ['Renderizar el diagrama y revisar sintaxis, labels y relaciones.']
    if 'plantuml' in low:
        return '@startuml\nactor Usuario\nrectangle "' + str(payload.get('objective', 'Sistema')) + '" as Sistema\nUsuario --> Sistema\n@enduml', ['Renderizar con PlantUML y revisar el resultado ASCII o Unicode.']
    if 'canvas' in low or 'obsidian' in low:
        return json.dumps(canvas_payload(str(payload.get('objective', name))), ensure_ascii=False, indent=2), ['Abrir el JSON en el editor compatible y ajustar posiciones y conexiones.']
    if 'excalidraw' in low:
        data = {'type': 'excalidraw', 'version': 2, 'source': 'content-skills-toolkit', 'elements': [{'id': 'root', 'type': 'rectangle', 'x': 100, 'y': 100, 'width': 300, 'height': 100, 'text': str(payload.get('objective', name))}], 'appState': {}, 'files': {}}
        return json.dumps(data, ensure_ascii=False, indent=2), ['Abrir el JSON en Excalidraw y revisar dimensiones, texto y conexiones.']
    if 'merp' in low or 'marp' in low or 'diapositiva' in low:
        return f"---\nmarp: true\ntheme: default\npaginate: true\n---\n\n# {payload.get('objective', name)}\n\n{ text or '[Contenido de la presentación]' }\n\n---\n\n## Próximo paso\n\n- Validar jerarquía, contraste y densidad antes de exportar.", ['Renderizar con Marp solo en el entorno autorizado y revisar el PDF resultante.']
    if 'favicon' in low:
        return f'''<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='18' fill='{hex_color(text)}'/><text x='50' y='64' text-anchor='middle' font-size='55' fill='white'>A</text></svg>">''', ['Probar tamaños y navegadores; sustituir el SVG por assets licenciados si se requiere un paquete completo.']
    if 'panel' in low or 'playground' in low:
        return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{objective}</title><style>body{{font-family:system-ui;max-width:900px;margin:2rem auto;padding:1rem}}.card{{padding:1rem;border:1px solid #ddd;border-radius:12px}}button,input{{padding:.6rem;margin:.3rem}}</style></head><body><h1>{objective}</h1><div class="card"><label>Filtro <input id="filter"></label><pre id="preview">{html.escape(text or 'Sin datos')}</pre></div><script>filter.oninput=()=>preview.hidden=!preview.textContent.toLowerCase().includes(filter.value.toLowerCase())</script></body></html>''', ['Abrir localmente, probar teclado y revisar contenido antes de compartir.']
    if 'sistema de diseño' in low or 'tailwind' in low or 'nothing' in low or 'marca' in low or 'word' in low:
        return f"# {name}\n\n{sec('Principios', 'Definir tokens de color, tipografía, espaciado, radios, sombras, estados y componentes.')}{sec('Entrada', text or '[Guía de marca o template pendiente]')}{sec('Tokens iniciales', '```css\n:root { --color-brand: #2563eb; --space-1: 0.25rem; --radius-md: 0.5rem; }\n```')}{sec('Aplicación', 'Mantener una fuente de verdad, documentar variantes y probar contraste, responsive y estados.')}", ['Validar tokens contra la marca y los componentes reales.']
    if 'animación' in low or 'gsap' in low or 'cut the curve' in low:
        return f"# Revisión de animación\n\n{sec('Intención', 'Definir qué comunica el movimiento y cuándo puede omitirse.')}{sec('Parámetros', 'Duración, easing, origen, stagger, interrupción, rendimiento y sincronización.')}{sec('Accesibilidad', 'Respetar `prefers-reduced-motion` y evitar movimiento que impida leer o interactuar.')}{sec('Entrada', text or '[Código o storyboard pendiente]')}", ['Medir rendimiento y probar interacción con movimiento reducido.']
    if 'diseño web' in low or 'ui' in low or 'editorial' in low or 'circuit' in low:
        return f"# {name}\n\n{sec('Brief', text or '[Brief pendiente]')}{sec('Estructura', 'Definir jerarquía, layout, responsive, estados, componentes y contenido realista.')}{sec('Entrega local', 'HTML, CSS, SVG o Markdown editable; sin assets externos no autorizados.')}{sec('Revisión', 'Contraste, teclado, tamaños, viewport, legibilidad y coherencia visual.')}", ['Revisar en viewport móvil y escritorio antes de publicar.']
    return f"# {name}\n\n{sec('Objetivo', payload.get('objective', name))}{sec('Entrada', text or '[Contenido pendiente]')}{sec('Método', 'Analizar referencias, definir estructura, producir un artefacto editable y verificar accesibilidad.')}{sec('Límites', 'No se usaron APIs, navegadores, MCP ni assets externos automáticamente.')}", ['Completar con referencias y archivos autorizados.']


def run_tool(skill: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if not str(payload.get(key, '')).strip()]
    text = str(payload.get('content', '')).strip()
    if missing:
        return {'skill': skill, 'status': 'needs_input', 'analysis': {'missing_fields': missing, 'input_characters': len(text)}, 'deliverable': {'title': skill['name'], 'format': payload.get('format', 'markdown'), 'content': '', 'next_steps': ['Completar: ' + ', '.join(missing)]}, 'warnings': ['Faltan entradas obligatorias: ' + ', '.join(missing)]}
    content, next_steps = build(skill, payload)
    return {'skill': skill, 'status': 'ready', 'analysis': {'missing_fields': [], 'input_characters': len(text), 'input_words': len(text.split()), 'assumptions': ['Ejecución local y revisable.', 'No se generaron assets externos ni se hicieron llamadas de red.']}, 'deliverable': {'title': skill['name'] + ' — ' + str(payload['objective']), 'format': payload.get('format', 'html'), 'content': content, 'next_steps': next_steps}, 'warnings': []}
