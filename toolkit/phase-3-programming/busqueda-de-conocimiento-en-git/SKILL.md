---
name: busqueda-de-conocimiento-en-git
description: Busca conocimiento en registros públicos de git (índice local de Frijol) y lo integra con procedencia citada: repo, archivo, línea y licencia. Solo lectura, sin ejecutar código recuperado.
---

# Búsqueda de conocimiento en git

## Propósito
Buscar en el índice local de Frijol (CodeSearchNet + muestra MIT, solo
registros públicos de git) y devolver los fragmentos relevantes con su
procedencia, listos para que el generador o el orquestador los integre.

## Flujo de trabajo
1. Recibir la consulta y el número de resultados (`k`, por defecto 5).
2. Recuperar con el índice BM25 de `hybrid.py` (solo lectura local).
3. Devolver cada fragmento con repo, archivo, línea, licencia y URL.
4. No ejecutar el código recuperado; la verificación la hace el Validador.

## Entradas aceptadas
- `query`: pregunta o descripción del código buscado.
- `k`: número máximo de fragmentos (1-10).

## Salida esperada
JSON con `skill`, `status`, `analysis`, `deliverable` (lista de fragmentos
con procedencia) y `warnings`.

## Guardrails
- Solo registros públicos de git; nunca repos privados sin autorización.
- No afirmar que un fragmento funciona sin verificarlo con `py_compile`.
- No ejecutar código recuperado sin pasar por el Validador.
- Citar siempre la fuente de cada fragmento usado.

## Plantilla de solicitud
```json
{
  "query": "extract video id from url",
  "k": 3
}
```

## Lista de control
- [ ] La consulta nombra el conocimiento buscado.
- [ ] Cada fragmento entregado cita repo, archivo, línea y licencia.
- [ ] Ningún fragmento se ejecuta sin pasar por el Validador.
- [ ] Si no hay coincidencias, la salida lo dice en `warnings`.
