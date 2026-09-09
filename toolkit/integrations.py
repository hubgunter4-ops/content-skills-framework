from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class IntegrationSpec:
    name: str
    service: str
    description: str
    credential_env: tuple[str, ...]
    skill_slugs: tuple[str, ...]


INTEGRATIONS: dict[str, IntegrationSpec] = {
    "youtube": IntegrationSpec(
        name="youtube",
        service="YouTube Data API v3",
        description="Metadatos públicos de videos y canales; requiere una API key de Google/YouTube.",
        credential_env=("YOUTUBE_API_KEY",),
        skill_slugs=("investigacion-de-videos-de-youtube", "transcripcion-de-youtube", "resumen-de-subtitulos-de-video"),
    ),
    "serp": IntegrationSpec(
        name="serp",
        service="Proveedor SERP compatible",
        description="Resultados de búsqueda y consultas de palabras clave para análisis SEO.",
        credential_env=("SERP_API_KEY",),
        skill_slugs=("investigacion-de-palabras-clave", "analisis-de-competidores-seo", "analisis-de-brechas-de-contenido", "estratega-de-seo-y-aeo", "optimizador-de-seo-para-ia", "optimizador-de-contenido-de-blog", "redactor-de-blogs-seo", "escritor-de-blogs-de-listas", "escritor-de-blogs-de-alternativas", "redactor-de-articulos-comparativos"),
    ),
    "ahrefs": IntegrationSpec(
        name="ahrefs",
        service="Ahrefs API",
        description="Keywords, backlinks y métricas SEO de competidores.",
        credential_env=("AHREFS_API_TOKEN",),
        skill_slugs=("analisis-de-competidores-seo", "analisis-de-brechas-de-contenido", "investigacion-de-palabras-clave"),
    ),
    "semrush": IntegrationSpec(
        name="semrush",
        service="Semrush API",
        description="Keywords, dominios competidores y datos de búsqueda orgánica.",
        credential_env=("SEMRUSH_API_KEY",),
        skill_slugs=("analisis-de-competidores-seo", "analisis-de-brechas-de-contenido", "investigacion-de-palabras-clave"),
    ),
    "search-console": IntegrationSpec(
        name="search-console",
        service="Google Search Console API",
        description="Consultas, páginas y rendimiento de búsqueda de una propiedad autorizada.",
        credential_env=("GOOGLE_APPLICATION_CREDENTIALS", "GSC_ACCESS_TOKEN"),
        skill_slugs=("generador-de-informes-de-auditoria-seo", "optimizador-de-contenido-de-blog", "estratega-de-seo-y-aeo"),
    ),
    "openai": IntegrationSpec(
        name="openai",
        service="OpenAI API",
        description="Transcripción, traducción o generación asistida cuando el usuario la solicita.",
        credential_env=("OPENAI_API_KEY",),
        skill_slugs=("transcripcion-de-youtube", "resumen-de-subtitulos-de-video", "traductor-seo-de-blogs", "sintetizador-de-conocimiento", "tts-prompter"),
    ),
    "web": IntegrationSpec(
        name="web",
        service="HTTP/HTTPS autorizado",
        description="Obtención de URLs proporcionadas por el usuario para auditoría o verificación.",
        credential_env=(),
        skill_slugs=("verificador-de-hechos-para-blogs", "disenador-de-articulos-editoriales", "sintetizador-de-conocimiento", "adaptador-de-estilo-de-revista"),
    ),
}


def catalog() -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "service": spec.service,
            "description": spec.description,
            "credential_env": list(spec.credential_env),
            "skills": list(spec.skill_slugs),
        }
        for spec in INTEGRATIONS.values()
    ]


def _requested(payload: dict[str, Any]) -> dict[str, Any] | None:
    requested = payload.get("integration", payload.get("integrations"))
    if not requested:
        return None
    if isinstance(requested, str):
        return {"provider": requested}
    if isinstance(requested, list):
        first = requested[0] if requested else None
        return {"provider": first} if isinstance(first, str) else first
    return requested if isinstance(requested, dict) else None


def _safe_public_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _safe_public_payload(item) for key, item in value.items() if key.lower() not in {"api_key", "token", "secret", "authorization"}}
    if isinstance(value, list):
        return [_safe_public_payload(item) for item in value]
    return value


def _credential(spec: IntegrationSpec) -> tuple[str | None, str | None]:
    for env_name in spec.credential_env:
        value = os.getenv(env_name)
        if value:
            return env_name, value
    return None, None


def _youtube(request: dict[str, Any], api_key: str) -> dict[str, Any]:
    video_id = str(request.get("video_id", "")).strip()
    if not video_id:
        url = str(request.get("url", ""))
        match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})", url)
        video_id = match.group(1) if match else ""
    if not video_id:
        return {"status": "needs_input", "message": "youtube requiere video_id o una URL de YouTube."}
    query = urlencode({"part": "snippet,contentDetails,statistics", "id": video_id, "key": api_key})
    request_url = f"https://www.googleapis.com/youtube/v3/videos?{query}"
    with urlopen(Request(request_url, headers={"Accept": "application/json"}), timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {"status": "ok", "service": "YouTube Data API v3", "video_id": video_id, "data": _safe_public_payload(data)}


def _generic_http(request: dict[str, Any], spec: IntegrationSpec, credential: str) -> dict[str, Any]:
    base_url = str(request.get("endpoint", "")).strip()
    if not base_url.startswith(("https://", "http://")):
        return {"status": "needs_input", "message": f"{spec.name} requiere endpoint HTTP explícito en integration.endpoint."}
    headers = {"Accept": "application/json"}
    if spec.name in {"ahrefs", "semrush"}:
        headers["Authorization"] = f"Bearer {credential}"
    else:
        headers["X-API-Key"] = credential
    with urlopen(Request(base_url, headers=headers), timeout=15) as response:
        raw = response.read().decode("utf-8")
    try:
        body: Any = json.loads(raw)
    except json.JSONDecodeError:
        body = raw[:20000]
    return {"status": "ok", "service": spec.service, "data": _safe_public_payload(body)}


def run_requested(payload: dict[str, Any]) -> dict[str, Any] | None:
    request = _requested(payload)
    if not request:
        return None
    provider = str(request.get("provider", request.get("name", ""))).strip().lower()
    spec = INTEGRATIONS.get(provider)
    if spec is None:
        return {"status": "error", "message": f"Integración no registrada: {provider or 'vacía'}", "available": sorted(INTEGRATIONS)}
    env_name, credential = _credential(spec)
    if spec.credential_env and not credential:
        return {"status": "not_loaded", "service": spec.service, "message": "No se cargó la integración porque falta una credencial configurada.", "required_env": list(spec.credential_env)}
    try:
        if provider == "youtube":
            return _youtube(request, credential or "")
        if provider == "web" and not str(request.get("endpoint", "")).startswith(("https://", "http://")):
            return {"status": "needs_input", "message": "web requiere una URL HTTPS/HTTP explícita en integration.endpoint."}
        return _generic_http(request, spec, credential or "")
    except Exception as exc:  # external services are isolated from local skill execution
        return {"status": "error", "service": spec.service, "message": f"La integración no pudo completarse: {type(exc).__name__}: {exc}"}
