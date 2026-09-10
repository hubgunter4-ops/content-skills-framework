"""Plugin de ejemplo para el framework Content Skills Toolkit."""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from toolkit import ExecutionRequest, ExecutionResult, ToolMetadata


class AnalizadorDeLegibilidad:
    """Herramienta local, determinista y sin acceso a red."""

    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            id="community/analizador-de-legibilidad",
            version="1.0.0",
            name="Analizador de legibilidad",
            description="Calcula indicadores simples de longitud y legibilidad sobre texto proporcionado.",
            input_schema="schemas/input.schema.json",
            output_schema="schemas/output.schema.json",
            capabilities=frozenset(),
            contract_version="1.0",
        )

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        content = str(request.payload.get("content", "")).strip()
        words = re.findall(r"[\wÁÉÍÓÚÜÑáéíóúüñ'-]+", content, flags=re.UNICODE)
        sentences = [part for part in re.split(r"[.!?]+", content) if part.strip()]
        characters = len(content)
        word_count = len(words)
        sentence_count = len(sentences)
        average_words_per_sentence = round(word_count / sentence_count, 2) if sentence_count else 0.0

        # La fórmula es deliberadamente simple: el framework no debe presentar
        # este indicador como una evaluación lingüística completa.
        score = round(max(0.0, 100.0 - average_words_per_sentence * 2.5), 2)
        return ExecutionResult(
            status="ready",
            analysis={
                "characters": characters,
                "words": word_count,
                "sentences": sentence_count,
                "average_words_per_sentence": average_words_per_sentence,
                "readability_score": score,
            },
            deliverable={
                "title": request.payload.get("objective", "Análisis de legibilidad"),
                "format": request.payload.get("format", "json"),
                "content": "Indicador heurístico calculado localmente.",
            },
            warnings=["El indicador es heurístico y no sustituye una revisión editorial."],
            provenance={"external_calls": [], "plugin": self.metadata().id},
        )


def create_tool() -> AnalizadorDeLegibilidad:
    """Factory referenciada por el entry point del paquete."""
    return AnalizadorDeLegibilidad()
