# Plan de normalización estructural de la Fase 2

*Propuesta para alinear las herramientas de Datos con las convenciones de las Fases 3–6 sin romper el contrato de ejecución existente.*

---

## 📋 Objetivo

La Fase 2 tiene 57 herramientas funcionales con `run.py`, ejemplos JSON, esquemas, recursos, smoke tests y pruebas agregadas. Su diferencia principal frente a las Fases 3–6 es la ausencia de un `SKILL.md` por herramienta. La corrección recomendada es añadir una capa documental uniforme sin duplicar innecesariamente la lógica de `toolkit/phase_2_engine.py` ni modificar el comportamiento seguro de los runners.

La normalización debe conservar:

- los 57 slugs actuales;
- los nombres y descripciones del catálogo;
- la entrada y salida JSON existentes;
- los códigos de salida de los runners;
- la ejecución local y las integraciones diferidas;
- la posibilidad de usar el catálogo central como índice.

## 🏗️ Estructura objetivo

Cada herramienta de la Fase 2 debería quedar así:

```text
toolkit/phase-2-datos/<slug>/
├── SKILL.md
├── run.py
├── input.example.json
├── output.schema.json
├── resources/
│   └── README.md
└── tests/
    └── test_smoke.py
```

La estructura de la fase completa debería ser:

```text
toolkit/
├── phase_2_engine.py
├── phase-2-datos/
│   ├── README.md
│   ├── catalog.json
│   ├── tests/
│   │   └── test_phase2.py
│   └── <57 herramientas con contrato uniforme>/
├── phase_3_engine.py
├── phase-3-programming/
├── phase_4_engine.py
├── phase-4-automatizacion/
├── phase_5_engine.py
├── phase-5-negocios/
├── phase_6_engine.py
└── phase-6-medios/
```

## 🔧 Correcciones requeridas

### Añadir `SKILL.md` a las 57 herramientas

Cada archivo debe derivarse del registro correspondiente de `catalog.json` y documentar sólo el comportamiento que el runner realmente implementa.

Plantilla mínima recomendada:

```markdown
---
name: <slug>
description: <description exacta del catálogo>
---

# <Nombre de la herramienta>

## Propósito
<Qué prepara, analiza o transforma el runner localmente.>

## Flujo de trabajo
1. Definir objetivo, audiencia, contenido y formato.
2. Inspeccionar la entrada recibida y sus límites.
3. Aplicar el adaptador local de Datos correspondiente.
4. Separar datos observados, supuestos y resultados pendientes.
5. Revisar la salida antes de usarla en un entorno externo.

## Entradas
- `objective`: objetivo de la solicitud.
- `audience`: audiencia o usuario final.
- `content`: texto, tabla, consulta o referencia proporcionada.
- `format`: formato esperado de salida.
- `integration`: opcional; sólo cuando el usuario solicite una integración autorizada.

## Salida
Resultado JSON con `skill`, `status`, `analysis`, `deliverable` y `warnings`.

## Guardrails
- No inventar datos, métricas, fuentes ni resultados.
- No consultar servicios externos sin solicitud explícita y configuración autorizada.
- No presentar plantillas como análisis ejecutado.
- Registrar fuentes, fecha, transformaciones y supuestos cuando corresponda.
- No tomar decisiones financieras, legales o de negocio basándose sólo en una plantilla.

## Plantilla de solicitud
```text
Objetivo: [resultado deseado]
Audiencia: [usuario o equipo]
Contenido: [texto, tabla, consulta o archivo descrito]
Formato: [markdown, html, svg, json u otro]
Fuentes y fecha de corte: [si aplica]
Restricciones: [permisos, límites y criterios de éxito]
```

## Lista de control
- [ ] Se proporcionaron las entradas obligatorias.
- [ ] Los datos observados están separados de los supuestos.
- [ ] Las fuentes, fechas y transformaciones están registradas cuando aplican.
- [ ] No se afirmó una consulta, exportación o cálculo que no se ejecutó.
- [ ] La salida fue revisada en el formato solicitado.
```

La plantilla debe adaptarse por dominio. Por ejemplo, una herramienta financiera debe añadir periodo, instrumento y fuentes regulatorias; una herramienta SQL debe añadir dialecto, permisos y entorno; una herramienta de visualización debe añadir unidades, accesibilidad y datos de origen.

### Sincronizar metadatos

El `name` y la `description` de cada `SKILL.md` deben coincidir con `catalog.json`. El `slug` debe ser siempre el nombre de la carpeta.

No se recomienda cambiar el catálogo para introducir campos nuevos en esta fase. Si se necesitan metadatos adicionales, primero deben definirse en todos los catálogos con una migración separada.

### Mejorar la validación estructural

Extender el validador para aceptar dos niveles:

| Nivel | Aplicación | Reglas |
| --- | --- | --- |
| Contrato ejecutable | Todas las fases | Runner, ejemplo JSON, esquema, salida JSON y smoke test |
| Contrato documental | Fase 2 normalizada y Fases 3–6 | `SKILL.md`, frontmatter, nombre, descripción y secciones obligatorias |

El validador debe comprobar además:

- que cada carpeta del catálogo tenga un runner;
- que no existan runners fuera del catálogo;
- que `SKILL.md` y `catalog.json` compartan nombre y descripción;
- que el esquema declare los campos que el runner produce;
- que los ejemplos JSON sean objetos válidos;
- que las pruebas smoke devuelvan `status: "ready"` con el ejemplo;
- que no aparezcan credenciales, métricas de popularidad ni afirmaciones de ejecución externa.

### Agregar una prueba agregada de documentación

Además de `test_phase2.py`, añadir una prueba que recorra las 57 carpetas y compruebe el contrato documental. La prueba debe producir un informe con:

```json
{
  "phase": "phase-2-datos",
  "tools": 57,
  "documented": 57,
  "passed": 57,
  "failures": []
}
```

### Corregir la documentación de fase

Actualizar `toolkit/phase-2-datos/README.md` para indicar explícitamente la estructura final:

- cada herramienta tiene `SKILL.md`;
- `catalog.json` funciona como índice;
- `phase_2_engine.py` contiene los adaptadores compartidos;
- las integraciones siguen siendo diferidas;
- la validación incluye contrato ejecutable y documental.

También debe añadirse una tabla breve de las categorías cubiertas y la relación entre slug, runner y adaptador.

### Actualizar el README raíz

La sección de estructura del README raíz debe distinguir:

```text
skills/content-toolkit/       # 52 skills base

toolkit/phase-2-datos/        # 57 herramientas de Datos
...
```

Debe evitar describir todas las fases como si fueran idénticas antes de completar la migración.

## 🔄 Estrategia de implementación

### Fase A: inventario y generación

1. Leer `catalog.json`.
2. Confirmar los 57 slugs y nombres.
3. Clasificar cada herramienta por dominio.
4. Generar un borrador de `SKILL.md` por carpeta.
5. Marcar como pendiente cualquier descripción incompleta, como `Mongo Query Pro` si su fuente no tiene suficiente detalle.

### Fase B: adaptación humana

1. Revisar cada descripción generada contra el runner real.
2. Ajustar entradas y salidas por categoría.
3. Confirmar que los guardrails no prometan funcionalidades ausentes.
4. Revisar términos financieros, científicos, legales y de datos sensibles.
5. Mantener las descripciones en el idioma original del catálogo.

### Fase C: validación

Ejecutar:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q toolkit skills
python3 -m toolkit validate
python3 toolkit/phase-2-datos/tests/test_phase2.py
python3 toolkit/phase-2-datos/tests/test_documentation.py
```

Después, repetir las pruebas agregadas de las Fases 3–6 para comprobar que la nueva validación no rompe convenciones existentes.

### Fase D: revisión de diferencias

Antes de integrar:

```bash
git diff --check
git status --short
git diff --stat
```

La revisión debe verificar que sólo se añadieron documentos, validadores, pruebas y actualizaciones de README previstas. No debe haber llamadas a APIs, cambios de credenciales ni cambios en el comportamiento externo de los runners.

## ⚖️ Decisión recomendada

Se recomienda la **normalización completa**, no una solución híbrida permanente. Mantener la Fase 2 sin `SKILL.md` deja dos modelos documentales dentro del mismo toolkit y obliga a que futuros agentes conozcan una excepción estructural.

La normalización no requiere reescribir `phase_2_engine.py` ni modificar los 57 runners. El cambio debe centrarse en documentación, validación y sincronización de metadatos.

## 🚫 Cambios que no deben hacerse en esta corrección

- No renombrar slugs existentes.
- No mover las herramientas de Fase 2 a `skills/content-toolkit/`.
- No duplicar la lógica de `phase_2_engine.py` dentro de cada runner.
- No activar integraciones externas.
- No añadir credenciales o archivos `.env`.
- No afirmar que se generaron gráficos, dashboards, consultas o modelos reales si sólo se produjo una plantilla.
- No crear commits ni hacer push durante la preparación local.

## ✅ Criterios de aceptación

La corrección estará completa cuando:

- las 57 herramientas de Fase 2 tengan `SKILL.md`;
- cada `SKILL.md` tenga frontmatter válido y secciones obligatorias;
- nombre y descripción coincidan con `catalog.json`;
- los 57 runners sigan pasando sus smoke tests;
- la prueba agregada de Fase 2 pase sin fallos;
- las pruebas base y de Fases 3–6 sigan pasando;
- `python3 -m toolkit validate` reconozca la nueva documentación;
- `git diff --check` no reporte errores;
- no se hayan ejecutado llamadas externas, commits ni push.
