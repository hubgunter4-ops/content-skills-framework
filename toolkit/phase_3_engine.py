from __future__ import annotations

import html
import json
import re
from typing import Any

REQUIRED = ('objective', 'audience', 'content', 'format')


def markdown_to_html(text: str) -> str:
    out = []
    for line in html.escape(text).splitlines() or ['']:
        heading = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading:
            level = len(heading.group(1)); out.append(f'<h{level}>{heading.group(2)}</h{level}>')
        elif re.match(r'^[-*]\s+', line):
            item = re.sub(r'^[-*]\s+', '', line)
            out.append(f'<li>{item}</li>')
        elif line.strip():
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            out.append(f'<p>{line}</p>')
    return '\n'.join(out)


def section(title: str, body: str) -> str:
    return f'## {title}\n{body}\n'


def generic(skill: dict[str, str], payload: dict[str, Any]) -> str:
    text = str(payload.get('content', '')).strip() or '[Entrada pendiente]'
    return f"# {payload.get('objective', skill['name'])}\n\n**Herramienta:** `{skill['name']}`\n\n{section('Entrada y contexto', text)}\n{section('Procedimiento', 'Inspeccionar, diseñar, implementar, probar y verificar sin modificar recursos fuera del alcance.')}\n{section('Entregable', 'Plan técnico, cambios propuestos, comandos reproducibles y criterios de aceptación.')}\n{section('Riesgos y límites', 'No se ejecutan despliegues, comandos destructivos, commits, pushes ni llamadas externas automáticamente.')}"


def build(skill: dict[str, str], payload: dict[str, Any]) -> tuple[str, list[str]]:
    slug = skill['slug']; text = str(payload.get('content', '')).strip(); low = (skill['name'] + ' ' + skill['description']).lower()
    if 'prompt' in low:
        return f"# Arquitectura de prompt\n\n{section('Objetivo', payload.get('objective', 'Definir objetivo'))}{section('Prompt base', 'Rol: [rol experto]\nContexto: [contexto verificable]\nTarea: ' + (text or '[tarea]') + '\nRestricciones: [límites]\nFormato de salida: [contrato]')}{section('Variantes', '- Zero-shot\n- Few-shot con ejemplos representativos\n- Razonamiento interno sin exponer cadenas privadas\n- Criterios de evaluación y casos límite')}", ['Evaluar las variantes con casos fijos y métricas antes de adoptar una versión.']
    if slug == 'markdown-a-html':
        return '<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Documento</title></head><body>' + markdown_to_html(text) + '</body></html>', ['Validar HTML y enlaces en el entorno de destino.']
    if 'excalidraw' in low:
        data = {'type': 'excalidraw', 'version': 2, 'source': 'content-skills-toolkit', 'elements': [{'id': 'root', 'type': 'rectangle', 'x': 100, 'y': 100, 'width': 280, 'height': 100, 'text': payload.get('objective', 'Elemento principal')}], 'appState': {}, 'files': {}}
        return json.dumps(data, ensure_ascii=False, indent=2), ['Abrir el JSON en Excalidraw y revisar el layout.']
    if 'mermaid' in low:
        return f"flowchart TD\n  A[Entrada: {payload.get('objective', 'objetivo')}] --> B[Proceso]\n  B --> C[Validación]\n  C --> D[Salida]", ['Renderizar el diagrama y revisar etiquetas y relaciones.']
    if 'destructiv' in low:
        risky = re.findall(r'\b(?:rm\s+-rf|DROP\s+TABLE|git\s+push\s+--force|kubectl\s+delete|terraform\s+destroy)\b[^\n]*', text, flags=re.I)
        detected = '\n'.join('- `' + command + '`' for command in risky) or 'No se detectaron patrones de alto riesgo.'
        confirmation = '1. Mostrar comando exacto.\n2. Identificar entorno y alcance.\n3. Confirmar respaldo y reversibilidad.\n4. Solicitar aprobación explícita.\n5. Ejecutar solo después de aprobación.'
        return f"# Protección contra comandos destructivos\n\n{section('Comandos detectados', detected)}{section('Flujo de confirmación', confirmation)}", ['No se ejecutó ningún comando.']
    if 'sql' in low or 'postgres' in low or 'mongodb' in low or 'clickhouse' in low:
        return f"# Revisión de consultas\n\n{section('Consulta recibida', '```sql\n' + (text or '[consulta pendiente]') + '\n```')}{section('Checklist', '- Confirmar dialecto.\n- Ejecutar EXPLAIN en entorno autorizado.\n- Revisar filtros, joins, cardinalidad e índices.\n- Medir antes y después con datos representativos.\n- Evitar afirmar mejoras sin medición.')}", ['Probar la propuesta en una copia o entorno de desarrollo.']
    if 'debug' in low or 'depur' in low or 'error' in low or 'diagnóstico' in low:
        return f"# Bucle de diagnóstico\n\n{section('Reproducir', text or '[pasos mínimos]')}{section('Minimizar', 'Reducir el caso a la entrada y componente más pequeños que conservan el fallo.')}{section('Hipotetizar e instrumentar', 'Registrar hipótesis, logs, métricas y observaciones; separar hechos de conjeturas.')}{section('Corregir y asegurar', 'Aplicar el cambio mínimo y añadir una prueba de regresión.')}", ['No se modificó código; validar la hipótesis con una prueba reproducible.']
    if 'api' in low or 'graphql' in low:
        openapi = "openapi: 3.0.3\ninfo:\n  title: API propuesta\n  version: 0.1.0\npaths: {}"
        return f"# Diseño de API\n\n{section('Contrato', 'Definir recursos, operaciones, versiones, autenticación, errores y límites.')}{section('OpenAPI inicial', openapi)}{section('Validación', 'Probar esquemas, compatibilidad, idempotencia y casos de error antes de implementar.')}", ['Convertir el contrato en pruebas de contrato antes de crear endpoints.']
    if 'git' in low or 'commit' in low or 'rama' in low:
        return f"# Flujo Git\n\n{section('Estado esperado', 'Revisar estado, diff, rama, upstream y reglas de contribución.')}{section('Opciones', '- Crear commit atómico.\n- Abrir pull request.\n- Fusionar según política del repositorio.\n- Limpiar rama solo con confirmación.')}{section('Verificación', 'Ejecutar pruebas, revisar diff, confirmar mensaje y comprobar el SHA remoto.')}", ['No se ejecutaron comandos Git de modificación desde esta herramienta.']
    if 'performance' in low or 'rendimiento' in low or 'web' in low or 'slo' in low or 'grafana' in low or 'observabilidad' in low:
        return f"# Diagnóstico de rendimiento y observabilidad\n\n{section('Medición', 'Definir baseline, p50/p95/p99, error rate, throughput, LCP/INP/CLS o SLI aplicables.')}{section('Perfilado', 'Separar CPU, memoria, I/O, red, consultas y dependencia externa; medir antes de optimizar.')}{section('Acciones', 'Priorizar por impacto, esfuerzo y riesgo; documentar rollback y alerta.')}{section('Validación', 'Comparar con la baseline y conservar evidencia reproducible.')}", ['No se afirmó una mejora sin mediciones actuales.']
    if 'gcp' in low or 'aws' in low or 'azure' in low or 'cloud' in low:
        return f"# Revisión de arquitectura cloud\n\n{section('Carga de trabajo', text or '[describir servicio, región y entorno]')}{section('Pilares', 'Fiabilidad, seguridad, rendimiento, costo, excelencia operativa y sostenibilidad.')}{section('Acciones seguras', 'Proponer cambios reversibles, permisos mínimos, presupuesto, monitoreo y plan de rollback.')}", ['No se conectaron cuentas cloud ni se modificaron recursos.']
    if 'test' in low or 'tdd' in low or 'especificacion' in low or 'especificación' in low:
        return f"# Desarrollo guiado por especificación y pruebas\n\n{section('Especificación', 'Definir comportamiento, entradas, salidas, errores y criterios de aceptación.')}{section('Pruebas primero', 'Escribir casos normales, límites, errores y regresiones antes de implementar.')}{section('Implementación mínima', 'Aplicar el cambio más pequeño que haga pasar las pruebas.')}{section('Verificación', 'Ejecutar suite actualizada y revisar diff y cobertura relevante.')}", ['No se declaró la tarea completa sin ejecutar pruebas.']
    if 'diagrama' in low or 'plantuml' in low:
        return f"# Diagramación\n\n{section('Fuente', text or '[descripción del sistema]')}{section('Estructura', 'Identificar entidades, relaciones, secuencia, límites y dirección del flujo.')}{section('Salida', 'Generar fuente editable y documentar cómo renderizarla.')}", ['Renderizar y revisar el diagrama antes de compartirlo.']
    return generic(skill, payload), ['Revisar el plan con el equipo y añadir pruebas específicas antes de desplegar.']


def run_tool(skill: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if not str(payload.get(key, '')).strip()]
    text = str(payload.get('content', '')).strip()
    if missing:
        return {'skill': skill, 'status': 'needs_input', 'analysis': {'missing_fields': missing, 'input_characters': len(text), 'assumptions': ['No se ejecutaron acciones externas.']}, 'deliverable': {'title': skill['name'], 'format': payload.get('format', 'markdown'), 'content': '', 'next_steps': ['Completar: ' + ', '.join(missing)]}, 'warnings': ['Faltan entradas obligatorias: ' + ', '.join(missing)]}
    content, next_steps = build(skill, payload)
    return {'skill': skill, 'status': 'ready', 'analysis': {'missing_fields': [], 'input_characters': len(text), 'input_words': len(text.split()), 'assumptions': ['Ejecución local, sin despliegue ni llamadas externas.', 'No se ejecutaron comandos destructivos ni cambios irreversibles.']}, 'deliverable': {'title': skill['name'] + ' — ' + str(payload['objective']), 'format': payload.get('format', 'markdown'), 'content': content, 'next_steps': next_steps}, 'warnings': []}
