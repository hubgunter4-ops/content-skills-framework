# Fase 2 — Registro, descubrimiento e índice persistente

## Alcance implementado

La Fase 2 añade `toolkit/persistent_index.py`, un índice SQLite reconstruible que consume el registro local actual y descubre plugins declarados mediante el grupo de entry points `content_skills_toolkit.tools`.

El descubrimiento utiliza `importlib.metadata.entry_points()` y lee únicamente:

- nombre del entry point;
- referencia del objeto (`module:object`);
- nombre y versión de la distribución;
- ubicación declarada de la distribución.

No se llama a `entry_point.load()`, no se importan fábricas y no se ejecutan plugins durante el descubrimiento.

## Registros indexados

Las 304 herramientas actuales se almacenan como `status = available` y conservan `ToolMetadata` suficiente para convertir el registro indexado en el contrato de Fase 1.

Un entry point externo se almacena inicialmente como `status = discovered`. Su referencia queda registrada, pero sus esquemas, capacidades y formatos se completarán cuando exista un adaptador de metadatos seguro. En consecuencia, `IndexedTool.to_metadata()` rechaza correctamente un entry point externo aún no enriquecido.

## Esquema SQLite

La base contiene:

- `registry_state`: versión del esquema, huella del entorno y fecha de indexación;
- `tools`: identidad, distribución, entry point, contrato, capacidades, formatos, etiquetas, estado y digest de metadatos;
- índices por fase, distribución, estado y grupo de entry points.

La reconstrucción escribe primero en un archivo temporal, ejecuta `PRAGMA integrity_check`, confirma la transacción y reemplaza el archivo destino de forma atómica.

## Invalidación

`environment_fingerprint()` combina:

- ejecutable y versión de Python;
- versión de contrato;
- grupo de entry points;
- tamaño y `mtime_ns` de catálogos y `SKILL.md` locales;
- declaraciones de entry points descubiertas.

`ensure_index()` reconstruye solo cuando la base no existe, está dañada o la huella almacenada difiere de la huella actual.

## Uso

```bash
python3 -m toolkit index --phase phase-2-datos
python3 -m toolkit index phase-2-datos/validacion-de-datos
python3 -m toolkit index --db /ruta/registry.sqlite3
```

El archivo local predeterminado `.content-skills-index.sqlite3` está excluido de Git. La API programática expone `rebuild_index`, `ensure_index`, `index_is_current`, `lookup`, `list_index` y `discover_external_entry_points`.

## Límites deliberados

La Fase 2 no carga plugins ni ejecuta entry points. Tampoco sustituye todavía el registro histórico utilizado por todos los runners; ofrece un adaptador persistente compatible y verificable. La selección, carga segura, supervisor y ejecución aislada se implementarán en las fases posteriores.
