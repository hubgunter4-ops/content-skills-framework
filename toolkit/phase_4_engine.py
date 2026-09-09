from __future__ import annotations

import html
import json
import re
from typing import Any

REQUIRED = ('objective', 'audience', 'content', 'format')


def sec(title: str, body: str) -> str:
    return f'## {title}\n{body}\n'


def generic(skill: dict[str, str], payload: dict[str, Any]) -> str:
    text = str(payload.get('content', '')).strip() or '[Entrada pendiente]'
    return f"# {payload.get('objective', skill['name'])}\n\n**Herramienta:** `{skill['name']}`\n\n{sec('Entrada', text)}{sec('Plan seguro', 'Definir disparador, permisos, allowlist, límites, reintentos, logs y criterio de parada.')}{sec('Verificación', 'Ejecutar pruebas locales y revisar los efectos antes de activar cualquier integración.')}{sec('Límites', 'No se ejecutan acciones externas ni cambios irreversibles automáticamente.')}"


def build(skill: dict[str, str], payload: dict[str, Any]) -> tuple[str, list[str]]:
    slug = skill['slug']; name = skill['name']; low = (name + ' ' + skill['description']).lower(); text = str(payload.get('content', '')).strip()
    if 'destructiv' in low:
        risky = re.findall(r'\b(?:rm\s+-rf|drop\s+table|git\s+push\s+--force|kubectl\s+delete|terraform\s+destroy|delete\s+from)\b[^\n]*', text, re.I)
        findings = '\n'.join('- `' + item + '`' for item in risky) or 'No se detectaron comandos peligrosos.'
        confirmation = 'Mostrar el comando exacto, el entorno, el alcance, la reversión y el respaldo; pedir aprobación explícita antes de ejecutar.'
        return f"# Protección contra comandos destructivos\n\n{sec('Hallazgos', findings)}{sec('Confirmación obligatoria', confirmation)}", ['No se ejecutó ningún comando.']
    if 'selenium' in low or 'puppeteer' in low or 'chrome devtools' in low:
        code = """// Código generado como propuesta; no ejecuta navegación automáticamente.\nconst target = process.env.TARGET_URL;\nif (!target || !/^https?:\\/\\//.test(target)) throw new Error('TARGET_URL debe ser una URL autorizada');\n// Añadir aquí selectores allowlisted, timeout, captura y teardown.\n"""
        code_block = '```javascript\n' + code + '\n```'
        return f"# {name}\n\n{sec('Alcance', 'Generar un script revisable para un dominio autorizado, con límites de tiempo y datos.')}{sec('Código propuesto', code_block)}{sec('Seguridad', 'No evade CAPTCHA, Cloudflare, robots, autenticación ni límites del sitio.')}", ['Revisar el dominio, permisos y selectores antes de ejecutar.']
    if 'buscador' in low or 'habilidades' in low or 'skills' in low:
        return f"# {name}\n\n{sec('Consulta', text or '[Definir tarea]')}{sec('Flujo de descubrimiento', '1. Definir criterios.\n2. Consultar únicamente repositorios permitidos.\n3. Revisar licencia, actividad, dependencias, permisos y pruebas.\n4. Recomendar sin instalar por defecto.')}{sec('Resultado', 'Lista de candidatos con URL, licencia, mantenimiento, riesgos y motivo de recomendación.')}", ['No se descargaron ni instalaron habilidades.']
    if 'búsqueda' in low or 'busqueda' in low or 'search' in low:
        return f"# Orquestación de búsqueda\n\n{sec('Pregunta', text or '[Pregunta del usuario]')}{sec('Subconsultas', '- Definición y alcance\n- Fuente primaria autorizada\n- Evidencia reciente\n- Contradicciones y límites')}{sec('Consolidación', 'Deduplicar, ponderar autoridad y actualidad, atribuir cada hallazgo y marcar confianza.')}", ['No se consultaron fuentes externas sin integración explícita.']
    if 'mcp' in low or 'fuentes empresariales' in low:
        return f"# {name}\n\n{sec('Inventario', 'Detectar servidores y herramientas solo después de una solicitud explícita.')}{sec('Configuración propuesta', 'Nombre, endpoint, transporte, autenticación, allowlist de herramientas y límites.')}{sec('Prueba', 'Ejecutar una llamada de lectura en entorno controlado y registrar resultado sin exponer secretos.')}", ['No se conectaron servidores MCP ni APIs.']
    if 'workflow' in low or 'flujo de trabajo' in low or 'n8n' in low or 'agentes' in low or 'paralelo' in low:
        flow = {'trigger': 'manual o autorizado', 'steps': ['validar_entrada', 'ejecutar_paso_idempotente', 'registrar_resultado', 'detener_o_reintentar'], 'retries': 2, 'requires_confirmation': True}
        flow_block = '```json\n' + json.dumps(flow, ensure_ascii=False, indent=2) + '\n```'
        return f"# {name}\n\n{sec('Flujo', flow_block)}{sec('Persistencia y reintentos', 'Guardar estado mínimo, usar claves idempotentes, limitar reintentos y detenerse ante cambios inesperados.')}{sec('Eventos externos', 'Requieren webhook o conector autorizado; no se habilitan automáticamente.')}", ['Validar el flujo con fixtures antes de conectarlo a producción.']
    if 'ci/cd' in low or 'pipeline' in low or 'slo' in low or 'grafana' in low or 'gcp' in low or 'azure' in low:
        return f"# {name}\n\n{sec('Diseño', 'Separar validación, pruebas, construcción y publicación en jobs visibles.')}{sec('Permisos', 'Comenzar con lectura mínima; exigir aprobación para despliegue, infraestructura, permisos o escritura.')}{sec('Observabilidad', 'Definir logs, métricas, alertas, SLI/SLO, presupuesto de errores y rollback.')}{sec('Estado', text or '[Configuración pendiente]')}", ['No se desplegó ni modificó infraestructura.']
    if 'verificar antes' in low or 'validación' in low:
        checklist = '- Ejecutar pruebas actualizadas.\n- Compilar o construir.\n- Revisar diff y secretos.\n- Validar artefactos y rutas.\n- Confirmar estado Git y resultado remoto solo si se solicita.'
        return f"# Verificación antes de terminar\n\n{sec('Checklist', checklist)}{sec('Evidencia', text or '[Registrar comandos y salidas]')}", ['No afirmar finalización sin evidencia ejecutada.']
    return generic(skill, payload), ['Revisar la automatización en modo simulación antes de habilitarla.']


def run_tool(skill: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if not str(payload.get(key, '')).strip()]
    text = str(payload.get('content', '')).strip()
    integration = payload.get('integration', payload.get('integrations'))
    warnings = ['La integración no se carga sin solicitud explícita.'] if not integration else ['La integración fue solicitada; requiere conector, credenciales y confirmación de alcance.']
    if missing:
        return {'skill': skill, 'status': 'needs_input', 'analysis': {'missing_fields': missing, 'input_characters': len(text), 'assumptions': ['No se ejecutaron acciones externas.']}, 'deliverable': {'title': skill['name'], 'format': payload.get('format', 'markdown'), 'content': '', 'next_steps': ['Completar: ' + ', '.join(missing)]}, 'warnings': ['Faltan entradas obligatorias: ' + ', '.join(missing)] + warnings}
    content, next_steps = build(skill, payload)
    return {'skill': skill, 'status': 'ready', 'analysis': {'missing_fields': [], 'input_characters': len(text), 'input_words': len(text.split()), 'assumptions': ['Ejecución local en modo seguro.', 'No se publicaron, instalaron ni desplegaron recursos.']}, 'deliverable': {'title': skill['name'] + ' — ' + str(payload['objective']), 'format': payload.get('format', 'markdown'), 'content': content, 'next_steps': next_steps}, 'warnings': warnings}
