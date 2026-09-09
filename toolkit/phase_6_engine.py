from __future__ import annotations

import html
import json
import re
from typing import Any

REQUIRED = ('objective', 'audience', 'content', 'format')


def sec(title: str, body: str) -> str:
    return f'## {title}\n{body}\n'


def storyboard(objective: str, text: str) -> dict[str, Any]:
    return {'title': objective, 'scenes': [{'number': 1, 'duration_seconds': 3, 'visual': text or '[visual pendiente]', 'camera': 'plano medio estable', 'audio': '[audio autorizado pendiente]', 'transition': 'corte limpio'}], 'rights': 'Verificar derechos de material, música, voz y personas.'}


def build(skill: dict[str, str], payload: dict[str, Any]) -> tuple[str, list[str]]:
    name = skill['name']; low = (name + ' ' + skill['description']).lower(); text = str(payload.get('content', '')).strip(); objective = str(payload.get('objective', name))
    if 'tts' in low or 'voz' in low:
        return f"# Prompt TTS\n\n{sec('Texto', text or '[Texto hablado]')}{sec('Dirección vocal', 'Voz: [describir]\nEdad percibida: [describir]\nRitmo: [lento/medio/rápido]\nEnergía: [describir]\nPronunciación: [notas]\nPausas: [marcas]')}{sec('Marcado', '<break time=\"300ms\"/> y etiquetas del proveedor solo después de confirmar su formato.')}{sec('Control', 'Revisar consentimiento, pronunciación de nombres, derechos de voz y uso final.')}", ['No se generó audio ni se llamó un servicio TTS.']
    if 'subtítulo' in low or 'subtitulo' in low or 'caption' in low:
        return 'WEBVTT\n\n00:00:00.000 --> 00:00:03.000\n' + (text or '[Subtítulo pendiente]') + '\n', ['Revisar sincronización, legibilidad, idioma y nombres propios con el material final.']
    if 'transcrip' in low or 'resumen de subtítulos' in low:
        return f"# Transcripción y resumen\n\n{sec('Material requerido', text or '[Ruta a audio o video autorizado]')}{sec('Flujo', '1. Detectar pista o transcribir localmente.\n2. Conservar marcas de tiempo.\n3. Revisar nombres y términos.\n4. Generar resumen separado de la transcripción.\n5. Eliminar o proteger material sensible.')}", ['No se procesó ningún archivo ni se llamó faster-whisper automáticamente.']
    if 'storyboard' in low or 'video' in low or 'cine' in low or 'anuncio' in low or 'campaña' in low or 'shorts' in low or 'clipper' in low or 'ugc' in low or 'drón' in low or 'dron' in low:
        data = storyboard(objective, text)
        return f"# {name}\n\n{sec('Storyboard', '```json\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n```')}{sec('Continuidad', 'Mantener identidad, vestuario, iluminación, lente, relación de aspecto y audio consistentes entre escenas.')}{sec('Exportación', 'Definir codec, resolución, fps, bitrate, subtítulos, miniatura y plataforma antes de renderizar.')}", ['No se generó video; revisar storyboard y derechos antes de renderizar.']
    if 'prompt' in low or 'director' in low or 'seedance' in low or 'kling' in low or 'modelo' in low:
        return f"# Prompt audiovisual\n\n{sec('Idea', text or '[Idea de video]')}{sec('Prompt estructurado', 'Sujeto + acción + entorno + composición + cámara + iluminación + textura + ritmo + audio + restricciones negativas.')}{sec('Parámetros', 'Duración: [segundos]\nRelación: [16:9 / 9:16 / 1:1]\nMovimiento: [describir]\nContinuidad: [describir]')}{sec('Seguridad', 'No imitar personas, voces, marcas o estilos protegidos sin permiso; no presentar el prompt como video generado.')}", ['Adaptar al proveedor solo tras confirmar modelo, política y credenciales.']
    if 'manim' in low or 'motion' in low or 'animación' in low or 'hyperframes' in low or 'remotion' in low:
        return f"# Plan de animación\n\n{sec('Escenas', text or '[Contenido o ecuación pendiente]')}{sec('Timeline', 'Definir duración, keyframes, easing, entradas, salidas y sincronización de audio.')}{sec('Render', 'Especificar resolución, fps, transparencia, codec, assets y comando reproducible.')}{sec('Accesibilidad', 'Añadir subtítulos, contraste suficiente y alternativa estática o movimiento reducido.')}", ['No se ejecutó un render ni se generó un archivo de video.']
    if 'música' in low or 'music' in low or 'ace-step' in low or 'álbum' in low or 'generador de memes' in low:
        return f"# Diseño de contenido audiovisual\n\n{sec('Brief', text or '[Tema, género o mensaje pendiente]')}{sec('Estructura', 'Definir tono, duración, secciones, instrumentación, letra o texto, mezcla y uso final.')}{sec('Derechos', 'Confirmar licencia de modelo, samples, voces, obras de referencia, imagen y distribución.')}", ['No se generó música ni imagen ni se consultó Memegen.link.']
    if 'imagemagick' in low or 'restauración' in low or 'foto' in low:
        return f"# Flujo de imagen\n\n{sec('Entrada', text or '[Ruta de imagen autorizada]')}{sec('Operaciones', 'Inspección de formato y metadatos, copia de seguridad, transformación, exportación y revisión visual.')}{sec('Comando propuesto', '```bash\nmagick input.jpg -auto-orient -strip output.png\n```')}{sec('Privacidad', 'Revisar EXIF, rostros, identidad y permisos antes de compartir.')}", ['El comando es una propuesta; no se modificó ninguna imagen.']
    return f"# {name}\n\n{sec('Objetivo', objective)}{sec('Entrada', text or '[Brief o material pendiente]')}{sec('Producción', 'Definir guion, storyboard, assets, audio, cámara, edición, subtítulos, exportación y revisión.')}{sec('Límites', 'No se activaron generadores, TTS, transcriptores, APIs ni renders externos.')}", ['Completar el brief y verificar derechos antes de producir.']


def run_tool(skill: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if not str(payload.get(key, '')).strip()]
    text = str(payload.get('content', '')).strip()
    if missing:
        return {'skill': skill, 'status': 'needs_input', 'analysis': {'missing_fields': missing, 'input_characters': len(text)}, 'deliverable': {'title': skill['name'], 'format': payload.get('format', 'markdown'), 'content': '', 'next_steps': ['Completar: ' + ', '.join(missing)]}, 'warnings': ['Faltan entradas obligatorias: ' + ', '.join(missing)]}
    content, next_steps = build(skill, payload)
    return {'skill': skill, 'status': 'ready', 'analysis': {'missing_fields': [], 'input_characters': len(text), 'input_words': len(text.split()), 'assumptions': ['Ejecución local y revisable.', 'No se generaron medios binarios ni se hicieron llamadas de red.']}, 'deliverable': {'title': skill['name'] + ' — ' + str(payload['objective']), 'format': payload.get('format', 'markdown'), 'content': content, 'next_steps': next_steps}, 'warnings': []}
