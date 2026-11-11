# busqueda-de-conocimiento-en-git

Skill en formato content-skills-framework que envuelve `hybrid.py` de
Frijol: busca en el índice local (registros públicos de git) y devuelve
fragmentos con procedencia.

- `run.py` — ejecutable, stdlib. Lee JSON por `-i` o stdin, escribe por
  `-o` o stdout. Acepta `query` (o `content`) y `k`.
- Dependencia: requiere un checkout de Frijol (`frijol-code-hybrid`) con
  su índice construido (`python3 hybrid.py index`). `run.py` lo busca en
  el repo padre, en `FRIJOL_HOME` o en
  `~/workspace/ops/code-model-hybrid`. Sin Frijol, la skill no puede
  buscar: devuelve error, no inventa resultados.
- Para registrarla en el framework: copiar esta carpeta a
  `toolkit/phase-3-programming/` y añadir la entrada en
  `toolkit/phase-3-programming/catalog.json`.
