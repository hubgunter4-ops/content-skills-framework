from __future__ import annotations

import html
import json
import re
from collections import Counter
from typing import Callable


Handler = Callable[[str, dict], tuple[str, list[str]]]


def _text(payload: dict) -> str:
    return str(payload.get("content", "")).strip()


def _objective(payload: dict) -> str:
    return str(payload.get("objective", "Solicitud sin objetivo")).strip() or "Solicitud sin objetivo"


def _audience(payload: dict) -> str:
    return str(payload.get("audience", "Audiencia no especificada")).strip() or "Audiencia no especificada"


def _words(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ'-]+", text.lower(), flags=re.UNICODE)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _title(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value[:1].upper() + value[1:] if value else "Resultado"


def _markdown_to_html(text: str) -> str:
    escaped = html.escape(text)
    lines = escaped.splitlines() or [""]
    out: list[str] = []
    in_list = False
    for line in lines:
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        item = re.match(r"^[-*]\s+(.+)$", line)
        if heading:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(heading.group(1))
            out.append(f"<h{level}>{heading.group(2)}</h{level}>")
        elif item:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{item.group(1)}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\*([^*]+?)\*", r"<em>\1</em>", line)
            out.append(f"<p>{line}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _plain_markdown(text: str) -> str:
    text = re.sub(r"```(?:\w+)?\s*", "", text)
    text = text.replace("```", "")
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*_`~-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _table(rows: list[tuple[str, str]]) -> str:
    result = ["| Campo | Resultado |", "| --- | --- |"]
    result.extend(f"| {key} | {value.replace('|', '/')} |" for key, value in rows)
    return "\n".join(result)


def _structured(slug: str, payload: dict, instruction: str, sections: list[str] | None = None) -> tuple[str, list[str]]:
    text = _text(payload)
    sections = sections or ["Contexto", "Propuesta", "Validación"]
    paragraphs = text or "No se proporcionó contenido fuente; el resultado queda como plantilla editable."
    body = [f"# {_title(_objective(payload))}", "", f"**Skill:** `{slug}`", f"**Audiencia:** {_audience(payload)}", "", instruction, ""]
    body.extend(f"## {section}\n{paragraphs if index == 0 else '[Completar con información verificable].'}" for index, section in enumerate(sections))
    body.extend(["", "## Supuestos y límites", "- La ejecución es local.", "- No se consultaron fuentes externas ni se inventaron datos."])
    return "\n".join(body), ["Revisar el resultado con datos y fuentes autorizadas antes de publicarlo."]


def _clean_ai(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _text(payload)
    replacements = {
        r"\bEn el mundo actual\b[:,]?\s*": "",
        r"\bEs importante destacar que\b[:,]?\s*": "",
        r"\bCabe señalar que\b[:,]?\s*": "",
        r"\bEn conclusión\b[:,]?\s*": "Conclusión: ",
        r"\bSin lugar a dudas\b[:,]?\s*": "",
        r"\bNo solo\b": "No solo",
        r"\s{2,}": " ",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        text = "[Introduzca aquí el texto que desea humanizar o depurar.]"
    label = "Humanización" if "humanizador" in slug else "Edición sin relleno"
    return f"# {label}\n\n{text}\n\n## Cambios aplicados\n- Eliminación de fórmulas previsibles y conectores innecesarios.\n- Conservación del significado y de la voz original.\n- Revisión humana recomendada para matices y hechos.", ["Comprobar que el tono final representa a la persona autora."]


def _grammar(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _text(payload)
    text = re.sub(r"\s+([,.;!?])", r"\1", text)
    text = re.sub(r"([,.;!?])(?=[A-Za-zÁ-ÿ])", r"\1 ", text)
    text = re.sub(r" {2,}", " ", text).strip()
    if not text:
        text = "[Introduzca el texto que desea corregir.]"
    return f"# Texto revisado\n\n{text}\n\n## Registro de revisión\n- Espaciado y puntuación normalizados.\n- Frases potencialmente poco naturales: revisar manualmente.\n- No se verificaron hechos externos.", ["Validar las correcciones según el idioma y la guía editorial objetivo."]


def _seo(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _plain_markdown(_text(payload))
    words = _words(text)
    counts = Counter(words)
    keywords = [word for word, count in counts.most_common(8) if len(word) > 3]
    keyword_text = ", ".join(keywords) or "pendiente de investigación"
    if slug == "investigacion-de-palabras-clave":
        content = "# Libro de investigación de palabras clave\n\n" + _table([
            ("Tema", _objective(payload)),
            ("Audiencia", _audience(payload)),
            ("Palabras detectadas", keyword_text),
            ("Pestañas propuestas", "Grupos de temas; Palabras prioritarias; Brechas competitivas"),
        ]) + "\n\n## Grupos de temas\n\n| Grupo | Palabra clave | Prioridad |\n| --- | --- | --- |\n| Principal | " + (keywords[0] if keywords else "pendiente") + " | Alta |\n"
    elif slug == "analisis-de-competidores-seo":
        content = f"# Análisis de competidores SEO\n\n{_table([('Objetivo', _objective(payload)), ('Temas detectados', keyword_text), ('Horizonte', '90 días')])}\n\n## Prioridades\n1. Validar las consultas con datos SERP autorizados.\n2. Comparar cobertura, intención y formato frente a competidores.\n3. Priorizar oportunidades por impacto y esfuerzo."
    elif slug == "analisis-de-brechas-de-contenido":
        content = f"# Análisis de brechas de contenido\n\n{_table([('Objetivo', _objective(payload)), ('Temas del corpus', keyword_text), ('Datos externos', 'No consultados automáticamente')])}\n\n## Matriz de brechas\n\n| Tema | Evidencia disponible | Acción |\n| --- | --- | --- |\n| {keywords[0] if keywords else 'Tema pendiente'} | Corpus proporcionado | Investigar y priorizar |"
    else:
        content = f"# {_title(_objective(payload))}\n\n## Diagnóstico SEO/AEO\n\n{_table([('Skill', slug), ('Tema principal', keywords[0] if keywords else 'pendiente'), ('Términos relacionados', keyword_text), ('Audiencia', _audience(payload))])}\n\n## Acciones priorizadas\n- Responder la intención principal en la primera sección.\n- Añadir encabezados descriptivos, preguntas frecuentes y enlaces verificables.\n- Separar datos observados de hipótesis y recomendaciones."
    return content, ["Validar keywords, SERP, competencia y métricas con fuentes autorizadas."]


def _markdown_format(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _text(payload)
    if slug == "markdown-a-html":
        content = "<!doctype html>\n<html lang=\"es\">\n<head><meta charset=\"utf-8\"><title>Documento</title></head>\n<body>\n" + _markdown_to_html(text) + "\n</body>\n</html>"
    elif slug == "creador-de-pdf-typst":
        content = "#set page(margin: 2cm)\n#set text(lang: \"es\")\n\n= " + _title(_objective(payload)) + "\n\n" + _plain_markdown(text) + "\n\n#emph[Generado como fuente Typst local.]"
    elif slug == "generador-de-diapositivas-marp":
        content = "---\nmarp: true\ntheme: default\n paginate: true\n---\n\n# " + _title(_objective(payload)) + "\n\n---\n\n## Mensaje principal\n\n" + (text or "[Contenido pendiente]")
    elif slug == "markdown-y-mermaid-pro":
        content = f"# {_title(_objective(payload))}\n\n{text}\n\n```mermaid\nflowchart LR\n  A[Entrada] --> B[Proceso]\n  B --> C[Salida revisable]\n```"
    else:
        content = f"# {_title(_objective(payload))}\n\n{text or '[Contenido pendiente]'}\n\n## Formato y control\n- Estructura Markdown preservada.\n- Información no verificada marcada como pendiente."
    return content, ["Renderizar o compilar el formato generado en el entorno de destino."]


def _channel(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _text(payload) or "[Contenido fuente pendiente]"
    if slug == "reutilizador-de-contenido":
        content = "# Reutilización multicanal\n\n" + "\n\n".join([
            f"## X / Twitter\n{_plain_markdown(text)[:280]}",
            f"## LinkedIn\n{_plain_markdown(text)}\n\n¿Cuál es tu experiencia?",
            f"## YouTube\n**Título:** {_title(_objective(payload))}\n**Descripción:** {_plain_markdown(text)}",
            f"## Reddit\n**Título:** {_title(_objective(payload))}\n\n{text}",
            f"## Newsletter\n**Asunto:** {_title(_objective(payload))}\n\n{text}",
        ])
    elif slug == "creador-de-contenido-multicanal":
        content = "# Paquete de contenido multicanal\n\n" + "\n\n".join(f"## {channel}\n{text}\n\n**CTA:** Conocer más." for channel in ("Blog", "Redes sociales", "Email", "Landing page", "Comunicado de prensa", "Caso de estudio"))
    else:
        content = f"# {_title(_objective(payload))}\n\n{text}\n\n## Variantes\n- Titular informativo\n- Titular orientado al beneficio\n- Titular basado en una pregunta\n\n## CTA\nDefinir una llamada a la acción medible y coherente con la audiencia."
    return content, ["Revisar tono, claims, enlaces y llamada a la acción antes de publicar."]


def _knowledge(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _text(payload) or "[Sin fuentes proporcionadas]"
    if slug == "sintetizador-de-conocimiento":
        content = f"# Síntesis de conocimiento\n\n## Resumen\n{_plain_markdown(text)}\n\n## Evidencia y confianza\n\n| Fuente o entrada | Hallazgo | Confianza |\n| --- | --- | --- |\n| Material proporcionado | Requiere revisión de atribución | Pendiente |\n\n## Duplicados y conflictos\nRegistrar aquí coincidencias, contradicciones y fecha de cada fuente."
    elif slug == "verificador-de-hechos-para-blogs":
        claims = _sentences(text)[:8] or ["Afirmación pendiente"]
        rows = "\n".join(f"| {i} | {claim} | Pendiente de fuente | No verificado |" for i, claim in enumerate(claims, 1))
        content = "# Verificación de hechos\n\n| # | Afirmación | Fuente | Estado |\n| --- | --- | --- | --- |\n" + rows
    elif slug == "transcripcion-de-youtube":
        content = "# Transcripción limpia\n\n" + re.sub(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?", "", text).strip()
    else:
        content = f"# {_title(_objective(payload))}\n\n{text}\n\n## Síntesis estructurada\n- Hallazgo principal: pendiente de separar de la evidencia.\n- Fuentes: registrar URL, autoría y fecha.\n- Confianza: no asignada sin trazabilidad."
    return content, ["Completar atribuciones, fechas y verificación de cada afirmación."]


def _template(slug: str, payload: dict) -> tuple[str, list[str]]:
    templates = {
        "arquitecto-de-prd": ("PRD", ["Problema", "Usuarios y necesidades", "Alcance", "Requisitos", "Métricas de éxito", "Riesgos", "Plan de lanzamiento"]),
        "arquitecto-de-prd-2": ("PRD ejecutable", ["Problema", "Objetivo", "Historias de usuario", "Criterios de aceptación", "Dependencias", "Métricas", "Lanzamiento"]),
        "arquitecto-de-readme": ("README", ["Descripción", "Instalación", "Uso", "Configuración", "Pruebas", "Contribución", "Seguridad"]),
        "generador-de-cartas-de-presentacion": ("Carta de presentación", ["Apertura", "Ajuste al puesto", "Evidencia relevante", "Cierre"]),
        "seguimiento-de-reuniones": ("Seguimiento de reunión", ["Resumen", "Decisiones", "Tareas y responsables", "Preguntas abiertas", "Borradores para aprobación"]),
        "dev-comm-pro": ("Comunicación para desarrollo", ["Contexto", "Mensaje para audiencia no técnica", "Decisión solicitada", "Próximos pasos"]),
        "coach-de-oratoria": ("Plan de oratoria", ["Mensaje central", "Arco narrativo", "Apertura", "Momento memorable", "Ensayo y control del tiempo"]),
        "academic-writing-pro": ("Revisión académica", ["Tesis", "Estructura lógica", "Evidencia", "Redacción", "Respuesta a revisores"]),
        "adaptador-de-estilo-de-revista": ("Adaptación de estilo", ["Rasgos de estilo", "Reglas de revisión", "Aplicación por sección", "Datos y fórmulas protegidos"]),
        "arquitecto-de-modelos-de-contenido": ("Modelo de contenido", ["Entidades", "Campos", "Relaciones", "Consultas", "Migración y mantenimiento"]),
        "arquitecto-de-notas-de-obsidian": ("Nota de Obsidian", ["Resumen", "Ideas relacionadas", "Próximas acciones", "Enlaces internos"]),
        "refactorizacion-de-markdown": ("Refactorización Markdown", ["Directivas principales", "Guías temáticas", "Reglas heredadas", "Estructura de archivos"]),
        "profesional-de-experimentacion-de-contenido": ("Experimento de contenido", ["Hipótesis", "Variantes", "Métrica primaria", "Segmento", "Criterio de decisión"]),
        "email-deliverability-pro": ("Revisión de entregabilidad", ["Asunto", "Cuerpo", "Enlaces", "Consentimiento", "Prueba y monitoreo"]),
    }
    label, sections = templates.get(slug, (_title(slug.replace('-', ' ')), ["Entrada", "Transformación", "Salida", "Revisión"]))
    return _structured(slug, payload, f"Plantilla local de {label} para {_audience(payload)}.", sections)


def _canvas(slug: str, payload: dict) -> tuple[str, list[str]]:
    text = _text(payload) or "Contenido pendiente"
    nodes = [
        {"id": "root", "type": "text", "text": _title(_objective(payload)), "x": 0, "y": 0, "width": 320, "height": 100},
        {"id": "content", "type": "text", "text": text[:1000], "x": 0, "y": 160, "width": 500, "height": 180},
        {"id": "next", "type": "text", "text": "Revisar y conectar ideas", "x": 400, "y": 0, "width": 300, "height": 100},
    ]
    edges = [{"id": "edge-1", "fromNode": "root", "toNode": "content", "fromSide": "bottom", "toSide": "top"}, {"id": "edge-2", "fromNode": "root", "toNode": "next", "fromSide": "right", "toSide": "left"}]
    if slug == "creador-de-obsidian-canvas":
        content = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2)
    else:
        content = "---\ntags: [nota, generado]\n---\n\n# " + _title(_objective(payload)) + "\n\n" + text + "\n\n## Enlaces relacionados\n- [[Revisar después]]\n- [[Fuentes]]"
    return content, ["Abrir el JSON en Obsidian Canvas o revisar los wikilinks en el vault correspondiente."]


def _dispatch(slug: str, payload: dict) -> tuple[str, list[str]]:
    if slug in {"markdown-a-html", "creador-de-pdf-typst", "generador-de-diapositivas-marp", "markdown-y-mermaid-pro"}:
        return _markdown_format(slug, payload)
    if slug in {"analisis-de-competidores-seo", "analisis-de-brechas-de-contenido", "investigacion-de-palabras-clave", "estratega-de-seo-y-aeo", "optimizador-de-seo-para-ia", "optimizador-de-contenido-de-blog", "generador-de-informes-de-auditoria-seo", "redactor-de-blogs-seo", "escritor-de-blogs-de-listas", "escritor-de-blogs-de-alternativas", "redactor-de-articulos-comparativos"}:
        return _seo(slug, payload)
    if slug in {"humanizador-de-texto-con-ia", "humanizador-de-textos", "sin-relleno-de-ia", "stop-slop"}:
        return _clean_ai(slug, payload)
    if slug in {"pulidor-de-gramatica", "corrector-de-textos", "copy-editor-pro"}:
        return _grammar(slug, payload)
    if slug in {"reutilizador-de-contenido", "creador-de-contenido-multicanal", "redactor-publicitario-de-marketing"}:
        return _channel(slug, payload)
    if slug in {"sintetizador-de-conocimiento", "verificador-de-hechos-para-blogs", "transcripcion-de-youtube", "investigacion-de-videos-de-youtube", "resumen-de-subtitulos-de-video"}:
        return _knowledge(slug, payload)
    if slug in {"creador-de-obsidian-canvas", "arquitecto-de-notas-de-obsidian"}:
        return _canvas(slug, payload)
    if slug in {"arquitecto-de-prd", "arquitecto-de-prd-2", "arquitecto-de-readme", "generador-de-cartas-de-presentacion", "seguimiento-de-reuniones", "dev-comm-pro", "coach-de-oratoria", "academic-writing-pro", "adaptador-de-estilo-de-revista", "arquitecto-de-modelos-de-contenido", "refactorizacion-de-markdown", "profesional-de-experimentacion-de-contenido", "email-deliverability-pro", "motor-de-estilo-de-marca", "motor-de-word-de-marca", "disenador-de-articulos-editoriales", "tts-prompter", "auditor-de-calidad-de-contenido", "estratega-de-contenidos-pro"}:
        return _template(slug, payload)
    return _structured(slug, payload, f"Transformación local especializada para {_audience(payload)}.")


def build_result(slug: str, name: str, description: str, payload: dict) -> dict:
    required = ("objective", "audience", "content", "format")
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    content = _text(payload)
    status = "ready" if not missing else "needs_input"
    if status == "ready":
        deliverable, next_steps = _dispatch(slug, payload)
    else:
        deliverable = ""
        next_steps = ["Completar los campos indicados en missing_fields."]
    return {
        "skill": {"name": name, "slug": slug, "description": description},
        "status": status,
        "request": {"objective": _objective(payload) if status == "ready" else str(payload.get("objective", "")).strip(), "audience": _audience(payload) if status == "ready" else str(payload.get("audience", "")).strip(), "format": str(payload.get("format", "markdown")).strip()},
        "analysis": {"input_characters": len(content), "input_words": len(content.split()), "missing_fields": missing, "assumptions": ["La ejecución es local y no consulta fuentes externas.", f"Se aplicó el adaptador funcional de {slug}."]},
        "deliverable": {"title": f"{name} — {_objective(payload)}", "format": str(payload.get("format", "markdown")).strip() or "markdown", "content": deliverable, "next_steps": next_steps},
        "warnings": (["Faltan entradas obligatorias: " + ", ".join(missing)] if missing else []),
    }
