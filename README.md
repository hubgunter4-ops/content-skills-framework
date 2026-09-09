# Content Skills Toolkit

Repositorio modular de herramientas y guías para investigación, edición, SEO, documentación, formatos de contenido y productividad. Cada capacidad vive en su propia carpeta para poder revisarse, copiarse o extenderse de manera independiente. Cada carpeta incluye `run.py`, `input.example.json` y `output.schema.json`; el runner es local, determinista y escribe JSON.

Los runners utilizan `toolkit/skill_engine.py`, un motor sin dependencias externas con adaptadores por skill. Los adaptadores realizan transformaciones locales como Markdown a HTML, fuentes Typst y Marp, JSON Canvas de Obsidian, limpieza editorial, matrices SEO, plantillas PRD/README, reutilización multicanal y tablas de verificación. No consultan servicios externos ni publican resultados automáticamente.

## Instalación

No requiere dependencias externas para consultar las habilidades. Requiere Python 3.10+ para usar el CLI:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## Uso guiado

El punto de entrada conserva una ruta CLI directa y ofrece un menú breve cuando se ejecuta sin argumentos. El registro unificado contiene **304 herramientas**: 52 de Content Toolkit y 252 especializadas distribuidas entre Datos, Programming, Automatización, Negocios y Medios.

```bash
python3 -m toolkit
python3 -m toolkit list
python3 -m toolkit show phase-1-content-toolkit/estratega-de-seo-y-aeo
python3 -m toolkit show phase-2-datos/validacion-de-datos
python3 -m toolkit validate
python3 -m toolkit integrations
python3 -m toolkit run phase-2-datos/validacion-de-datos \
  -i toolkit/phase-2-datos/validacion-de-datos/input.example.json
```

`list` muestra siempre `fase/slug`. `show` y `run` aceptan identificadores cualificados y también slugs cortos cuando no hay colisión. Si un slug se repite, el CLI exige indicar la fase. En el menú: `1` lista habilidades, `2` muestra una habilidad, `3` valida la colección y `q` cancela. Las acciones son locales, no envían datos y no modifican archivos salvo que el usuario lo haga explícitamente.

## Integraciones externas bajo demanda

Las integraciones están implementadas con carga diferida. Ningún servicio externo ni credencial se consulta cuando el usuario no incluye `integration` o `integrations` en la entrada JSON. Para inspeccionar el catálogo sin cargar servicios, usa `python3 -m toolkit integrations`.

Cuando una entrada solicita una integración, el motor busca únicamente la credencial correspondiente en la variable de entorno documentada y devuelve un estado explícito si falta. Las credenciales nunca se incluyen en la salida. Actualmente se contemplan YouTube Data API v3 (`YOUTUBE_API_KEY`), proveedores SERP (`SERP_API_KEY`), Ahrefs (`AHREFS_API_TOKEN`), Semrush (`SEMRUSH_API_KEY`), Google Search Console (`GOOGLE_APPLICATION_CREDENTIALS` o `GSC_ACCESS_TOKEN`), OpenAI (`OPENAI_API_KEY`) y URLs HTTP/HTTPS autorizadas sin credencial obligatoria.

Ejemplo de solicitud explícita, sin ejecutar si no existe la credencial:

```json
{
  "objective": "Investigar un video",
  "audience": "Equipo editorial",
  "content": "Analizar el video indicado",
  "format": "markdown",
  "integration": {
    "provider": "youtube",
    "video_id": "VIDEO_ID"
  }
}
```

## Arquitectura y estructura

El flujo completo es:

```text
CLI → registro → SKILL.md → runner → motor de fase → JSON → pruebas
```

Las 304 entradas se organizan así:

| Fase | Ruta | Herramientas |
| --- | --- | ---: |
| Fase 1 | `toolkit/phase-1-content-toolkit/` | 52 |
| Fase 2 | `toolkit/phase-2-datos/` | 57 |
| Fase 3 | `toolkit/phase-3-programming/` | 89 |
| Fase 4 | `toolkit/phase-4-automatizacion/` | 23 |
| Fase 5 | `toolkit/phase-5-negocios/` | 34 |
| Fase 6 | `toolkit/phase-6-medios/` | 49 |

Cada herramienta tiene documentación, runner, ejemplo de entrada, esquema de salida, recursos y prueba smoke. El registro (`toolkit/registry.py`) es de solo lectura y evita que el CLI dependa de rutas codificadas por comando.

```text
content-skills-toolkit/
├── toolkit/phase-1-content-toolkit/       # 52 herramientas de contenido
├── toolkit/phase-2-datos/                  # 57 herramientas de datos
├── toolkit/phase-3-programming/            # 89 herramientas de programación
├── toolkit/phase-4-automatizacion/         # 23 herramientas de automatización
├── toolkit/phase-5-negocios/               # 34 herramientas de negocios y diseño
├── toolkit/phase-6-medios/                 # 49 herramientas de medios
├── toolkit/registry.py                     # Registro unificado
├── toolkit/__main__.py                     # CLI
├── tests/                  # Pruebas unitarias y smoke tests del menú
├── docs/                   # Plan y decisiones del proyecto
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
└── SECURITY.md
```

Para validar el conjunto completo se usan `python3 -m unittest discover -s tests -v`, `python3 -m compileall -q toolkit`, `python3 -m toolkit validate` y las pruebas `test_documentation.py` y `test_phase*.py` de cada fase.

## Automatización recomendada

Consulta las [recomendaciones de automatización para Claude Code](docs/claude-automation-recommendations.md) para el perfil del repositorio, el flujo local de calidad y una propuesta gradual de CI, skills, hooks y subagentes. El informe es prescriptivo y no activa integraciones externas por sí mismo.

El workflow [`validate.yml`](.github/workflows/validate.yml) ejecuta en cada push a `main` y en cada pull request las pruebas unitarias, la compilación, la validación del catálogo, las pruebas documentales de las seis fases, los runners de fase y `git diff --check`. Solo necesita acceso de lectura al contenido del repositorio; no usa secretos, consulta APIs, publica resultados ni despliega servicios.

## Catálogo

| Habilidad | Descripción |
| --- | --- |
| [Investigación de videos de YouTube](toolkit/phase-1-content-toolkit/investigacion-de-videos-de-youtube/SKILL.md) | Mejore las investigaciones profundas y los informes con evidencia de videos de YouTube de primera mano, entrevistas a expertos y presentaciones de conferencias |
| [TTS Prompter](toolkit/phase-1-content-toolkit/tts-prompter/SKILL.md) | Domina la creación de prompts de texto a voz con marcos estructurados, separación de estilos y etiquetas de marcado expresivas |
| [Análisis de competidores SEO](toolkit/phase-1-content-toolkit/analisis-de-competidores-seo/SKILL.md) | Cree informes simplificados de competidores orgánicos de SEO centrados en los objetivos, modelados según el estilo de informe aprobado de hix.ai, con gráficos de apoyo y prioridades a 90 días |
| [Generador de informes de auditoría SEO](toolkit/phase-1-content-toolkit/generador-de-informes-de-auditoria-seo/SKILL.md) | Cree informes de auditoría SEO en lenguaje sencillo y basados en pruebas, con resúmenes ejecutivos estructurados y listas de correcciones priorizadas basadas estrictamente en los datos del informe |
| [Redactor de artículos comparativos](toolkit/phase-1-content-toolkit/redactor-de-articulos-comparativos/SKILL.md) | Investiga y redacta publicaciones de blog comparativas 'X vs Y' de alta calidad y equilibradas, resúmenes de alternativas de productos y guías de compra con tablas de características estructuradas |
| [Creador de PDF Typst](toolkit/phase-1-content-toolkit/creador-de-pdf-typst/SKILL.md) | Genera documentos PDF profesionales y de alta calidad utilizando Typst con tipografía precisa, fórmulas matemáticas y resaltado de código |
| [Escritor de blogs de listas](toolkit/phase-1-content-toolkit/escritor-de-blogs-de-listas/SKILL.md) | Redacte artículos de blog tipo listicle y publicaciones recopilatorias optimizados para SEO y GEO/AEO para posicionarse en los motores de búsqueda y obtener citas de motores de IA |
| [Escritor de blogs de alternativas](toolkit/phase-1-content-toolkit/escritor-de-blogs-de-alternativas/SKILL.md) | Escribe artículos de blog de comparación de competidores y alternativas optimizados para SEO para captar tráfico de búsqueda orgánica |
| [Redactor publicitario de marketing](toolkit/phase-1-content-toolkit/redactor-publicitario-de-marketing/SKILL.md) | Este kit de herramientas de marketing profesional le ayuda a escribir y reescribir textos persuasivos para páginas de destino, páginas de inicio y anuncios. Cubre múltiples escenarios de marketing en un solo flujo de trabajo, ayudando a los equipos a generar rápidamente variaciones creativas, optimizar el SEO y producir contenido de alta conversión con menos esfuerzo |
| [Estratega de Contenidos Pro](toolkit/phase-1-content-toolkit/estratega-de-contenidos-pro/SKILL.md) | Este kit de herramientas de marketing profesional le ayuda a planificar estrategias de contenido al decidir qué temas y formatos priorizar. Proporciona orientación práctica para diversos escenarios de marketing, permitiendo que los equipos alineen sus esfuerzos de contenido con los objetivos comerciales y ejecuten campañas de manera más efectiva |
| [Motor de Estilo de Marca](toolkit/phase-1-content-toolkit/motor-de-estilo-de-marca/SKILL.md) | Esta herramienta aplica automáticamente su imagen de marca corporativa —colores, fuentes, diseños y mensajes— a documentos y plantillas generados por IA para garantizar una identidad visual coherente. Acelera la producción al aplicar reglas de estilo en hojas de una página, presentaciones, correos electrónicos y otros materiales para que cada activo coincida con sus directrices de marca |
| [Humanizador de texto con IA](toolkit/phase-1-content-toolkit/humanizador-de-texto-con-ia/SKILL.md) | Esta herramienta elimina los rastros de escritura generada por IA del texto para que suene más natural y humano. Te ayuda a perfeccionar borradores automatizados para convertirlos en contenido auténtico y cercano, asegurando que tu escritura evite los detectores de IA y conecte mejor con tu audiencia |
| [Humanizador de textos](toolkit/phase-1-content-toolkit/humanizador-de-textos/SKILL.md) | Esta herramienta de refinamiento de texto elimina los patrones generados por IA de la escritura mediante la identificación y corrección de simbolismos inflados, estructuras mecánicas y vocabulario excesivo. Ayuda a editores y escritores a transformar borradores robóticos en contenido natural con sonido humano que resuena mejor con los lectores |
| [Optimizador de SEO para IA](toolkit/phase-1-content-toolkit/optimizador-de-seo-para-ia/SKILL.md) | Esta herramienta de SEO para IA ayuda a los especialistas en marketing a optimizar el contenido para que aparezca en respuestas generadas por IA y resultados de búsqueda de LLM. Adapta las estrategias de SEO tradicionales para la era de la IA, ayudándole a estructurar el contenido y a dirigir las consultas para que su marca sea recomendada por los motores de búsqueda de IA modernos |
| [Sin relleno de IA](toolkit/phase-1-content-toolkit/sin-relleno-de-ia/SKILL.md) | Una habilidad de edición que elimina más de 20 patrones reveladores de relleno de IA de tus borradores mientras preserva tu voz personal. Consigue una redacción que se lea más nítida, más humana y sea inconfundiblemente tuya |
| [Creador de contenido multicanal](toolkit/phase-1-content-toolkit/creador-de-contenido-multicanal/SKILL.md) | Esta herramienta/habilidad le ayuda a redactar contenido de marketing pulido en diversos canales: blogs, redes sociales, correos electrónicos, páginas de destino, comunicados de prensa y estudios de caso. Ofrece formatos específicos para cada canal, textos optimizados para SEO, variantes de titulares y llamadas a la acción persuasivas para acelerar la producción y aumentar la interacción de la audiencia |
| [Sintetizador de Conocimiento](toolkit/phase-1-content-toolkit/sintetizador-de-conocimiento/SKILL.md) | Esta herramienta sintetiza los resultados de búsqueda de múltiples fuentes en respuestas coherentes y sin duplicados, con una clara atribución de fuentes y puntuación de confianza. Pondera la actualidad y la autoridad para mostrar la información más fiable y comprime grandes conjuntos de resultados en resúmenes concisos y prácticos para informes, agentes o sesiones informativas para las partes interesadas |
| [Copy Editor Pro](toolkit/phase-1-content-toolkit/copy-editor-pro/SKILL.md) | Esta herramienta de edición de textos de marketing te ayuda a perfeccionar y mejorar textos existentes para lograr una mayor claridad e impacto en diversas campañas. Agiliza el proceso de revisión, asegurando que tu mensaje sea persuasivo y coherente sin necesidad de una reescritura exhaustiva |
| [Transcripción de YouTube](toolkit/phase-1-content-toolkit/transcripcion-de-youtube/SKILL.md) | Este es un descargador de transcripciones de videos de YouTube que extrae subtítulos existentes o recurre automáticamente al reconocimiento de voz por IA si no hay ninguno disponible. Incluye scripts de limpieza de formato para proporcionar texto limpio, lo que le permite leer y procesar rápidamente el contenido del video sin tener que verlo completo |
| [Estratega de SEO & AEO](toolkit/phase-1-content-toolkit/estratega-de-seo-y-aeo/SKILL.md) | Esta guía de mejores prácticas para sitios web de contenido cubre tanto la Optimización de Motores de Búsqueda SEO tradicional como la Optimización de Motores de Respuesta AEO. Proporciona patrones accionables para ayudar a que su contenido se posicione mejor en los resultados de búsqueda estándar, al tiempo que garantiza que sea fácilmente detectable y citado con precisión por los motores de respuesta impulsados por IA |
| [Generador de diapositivas Marp](toolkit/phase-1-content-toolkit/generador-de-diapositivas-marp/SKILL.md) | Esta habilidad proporciona un generador de presentaciones basado en Marp con 7 temas integrados y guías de diseño detalladas. Transforma requisitos vagos o contenido sin procesar en código de diapositivas Markdown bien estructurado y con un formato atractivo, lo que lo hace ideal para crear rápidamente presentaciones técnicas profesionales o de negocios |
| [Pulidor de gramática](toolkit/phase-1-content-toolkit/pulidor-de-gramatica/SKILL.md) | Esta herramienta de corrección de textos identifica con precisión errores gramaticales y frases poco naturales en su escritura, proporcionando sugerencias específicas para mejorar. Le ayuda a pulir correos electrónicos, documentos y otros contenidos escritos, garantizando una comunicación profesional y evitando errores básicos antes de publicar o enviar |
| [Diseñador de artículos editoriales](toolkit/phase-1-content-toolkit/disenador-de-articulos-editoriales/SKILL.md) | Esta herramienta de diseño editorial transforma cualquier material de origen —como PDF, Markdown o páginas web— en un hermoso artículo HTML de un solo archivo con componentes interactivos. Al aplicar restricciones de tema estrictas y un proceso de construcción estructurado, garantiza la retención del 100% de la información mientras ofrece una experiencia de lectura pul para compartir |
| [Markdown a HTML](toolkit/phase-1-content-toolkit/markdown-a-html/SKILL.md) | Esta herramienta convierte archivos Markdown en HTML limpio y compatible con los estándares para su uso en sitios web, documentación o generadores de sitios estáticos. Admite flujos de trabajo de CLI y Node.js, GitHub Flavored Markdown GFM, CommonMark y los sabores típicos de Markdown, y se integra con sistemas de plantillas como Jekyll o Hugo para producir una salida HTML lista para desplegar |
| [Motor de Word de Marca](toolkit/phase-1-content-toolkit/motor-de-word-de-marca/SKILL.md) | Este motor de Word con reconocimiento de marca extrae pautas de diseño como fuentes, colores y estilos de plantillas existentes para crear un perfil de marca reutilizable. Al automatizar la generación de nuevos documentos .docx basados en estos perfiles guardados, garantiza una identidad corporativa coherente en todos los resultados y elimina el formato manual repetitivo |
| [Redactor de Blogs SEO](toolkit/phase-1-content-toolkit/redactor-de-blogs-seo/SKILL.md) | Este asistente de redacción de blogs genera artículos completos desde cero, incorporando imágenes, gráficos, preguntas frecuentes y enlaces internos, mientras optimiza para los rankings de Google y las citas de IA. Automatiza la estructuración y el formato del contenido, ayudando a creadores y especialistas en marketing a producir publicaciones de alta calidad y optimizadas para motores de búsqueda con mayor rapidez y sin trabajo de diseño manual |
| [Auditor de calidad de contenido](toolkit/phase-1-content-toolkit/auditor-de-calidad-de-contenido/SKILL.md) | Esta es la habilidad oficial de auditoría de calidad de contenido E-E-A-T y CITE de SE Ranking para artículos existentes. Te ayuda a calificar la experiencia, el conocimiento, la autoridad, la confiabilidad y la preparación de citas para búsquedas de IA, a identificar problemas de veto que bloquean la publicación y a obtener un veredicto claro de publicar / corregir / no publicar |
| [Creador de Obsidian Canvas](toolkit/phase-1-content-toolkit/creador-de-obsidian-canvas/SKILL.md) | Esta habilidad convierte texto, artículos o esquemas en archivos estructurados de Obsidian Canvas, admitiendo tanto mapas mentales como diseños espaciales de forma libre para la organización visual del conocimiento. Ayuda a los usuarios a convertir contenido lineal en lienzos visuales editables de forma más rápida, reduciendo el trabajo de disposición manual y facilitando la revisión y reorganización de ideas, estructuras de proyectos y relaciones |
| [Coach de oratoria](toolkit/phase-1-content-toolkit/coach-de-oratoria/SKILL.md) | Esta habilidad sintetiza las lecciones de oratoria de 12 invitados destacados del pódcast de Lenny en 10 marcos de trabajo prácticos, como los métodos del Arco y la Flecha y el Momento de 5 Segundos. Te ayuda a preparar charlas, perfeccionar la comunicación y transmitir ideas con confianza en cualquier escenario |
| [Academic Writing Pro](toolkit/phase-1-content-toolkit/academic-writing-pro/SKILL.md) | Este es un asistente de escritura académica enfocado principalmente en el chino, diseñado para ayudar a investigadores a redactar, revisar y pulir secciones de manuscritos, así como a redactar réplicas para revisiones por pares. Al proporcionar pautas de escritura detalladas y listas de verificación, ayuda a los usuarios a construir marcos lógicos rigurosos y a elevar su prosa académica a estándares profesionales |
| [Markdown & Mermaid Pro](toolkit/phase-1-content-toolkit/markdown-y-mermaid-pro/SKILL.md) | Esta habilidad proporciona pautas y plantillas de escritura de Markdown y Mermaid para crear documentos técnicos, diagramas de arquitectura e informes de investigación. Establece los diagramas basados en texto como el estándar de documentación predeterminado, ayudándole a generar documentos y visualizaciones estandarizados con un formato consistente |
| [Arquitecto de Modelos de Contenido](toolkit/phase-1-content-toolkit/arquitecto-de-modelos-de-contenido/SKILL.md) | Esta guía proporciona las mejores prácticas para diseñar modelos de contenido estructurado escalables y eficientes en Sanity. Traduce los principios arquitectónicos en pautas prácticas, ayudando a los desarrolladores y equipos de contenido a construir estructuras de contenido robustas que mejoren el rendimiento de las consultas, reduzcan la deuda técnica y garanticen la mantenibilidad a largo plazo |
| [Stop Slop](toolkit/phase-1-content-toolkit/stop-slop/SKILL.md) | Esta es una habilidad de edición ampliamente adoptada que elimina los patrones predecibles de escritura de IA de tu prosa, respaldada por una lista negra de más de 300 líneas de frases de relleno y estructuras formulaicas. Ayuda a que tus borradores se lean como los de un escritor humano perspicaz, con una rúbrica de puntuación de 5 dimensiones incorporada para verificar cada revisión |
| [Reutilizador de contenido](toolkit/phase-1-content-toolkit/reutilizador-de-contenido/SKILL.md) | Esta herramienta de reutilización de contenido transforma una sola entrada de blog en formatos adaptados para Twitter, LinkedIn, YouTube, Reddit y boletines informativos por correo electrónico. Adapta automáticamente el tono y la estructura para cada plataforma, ayudando a los creadores y especialistas en marketing a distribuir contenido de manera más eficiente a través de múltiples canales |
| [Corrector de textos](toolkit/phase-1-content-toolkit/corrector-de-textos/SKILL.md) | Esta herramienta de corrección de textos en chino y documentos oficiales detecta y corrige 27 tipos de errores, incluidos errores tipográficos, gramaticales, problemas de puntuación, imprecisiones fácticas y contenido sensible. Ayuda a los usuarios a identificar fallos de escritura rápidamente, garantizando que los documentos y artículos sigan siendo rigurosos, estandarizados y libres de errores |
| [Resumen de subtítulos de vídeo](toolkit/phase-1-content-toolkit/resumen-de-subtitulos-de-video/SKILL.md) | Esta habilidad convierte vídeos de Douyin, Xiaohongshu, Bilibili, YouTube o archivos locales en subtítulos y resúmenes de IA utilizando la transcripción local faster-whisper. Obtiene los subtítulos de YouTube directamente cuando están disponibles, para que puedas obtener texto en el que se pueden realizar búsquedas y puntos clave de cualquier vídeo en cuestión de minutos |
| [Optimizador de Contenido de Blog](toolkit/phase-1-content-toolkit/optimizador-de-contenido-de-blog/SKILL.md) | Esta habilidad reescribe y optimiza entradas de blog existentes para mejorar tanto el posicionamiento en Google como las citas de asistentes de IA. Reemplaza automáticamente estadísticas inventadas con datos reales de fuentes, genera gráficos SVG y aplica un formato de respuesta primero, ayudando a los creadores de contenido a actualizar fácilmente artículos obsoletos y aumentar su visibilidad en motores de búsqueda y plataformas de IA |
| [Email Deliverability Pro](toolkit/phase-1-content-toolkit/email-deliverability-pro/SKILL.md) | Esta es una guía de mejores prácticas de diseño y entregabilidad de correo electrónico basada en la experiencia oficial de Resend. Le ayuda a optimizar el contenido del correo electrónico para evitar los filtros de spam y garantiza que sus diseños sigan los estándares de la industria, mejorando en última instancia la efectividad de su marketing por correo electrónico |
| [Generador de cartas de presentación](toolkit/phase-1-content-toolkit/generador-de-cartas-de-presentacion/SKILL.md) | Este generador de cartas de presentación proporciona un marco estructurado para crear cartas de presentación profesionales y personalizadas mediante el análisis de su currículum y la descripción del puesto objetivo. Combina estructuras de párrafos específicas, estrategias de apertura y consejos específicos de la industria para ayudarle a producir mensajes adaptados y de alto impacto que aumenten sus posibilidades de una entrevista exitosa |
| [Seguimiento de reuniones](toolkit/phase-1-content-toolkit/seguimiento-de-reuniones/SKILL.md) | Un flujo de trabajo de seguimiento de reuniones ejecutivas de código abierto del CEO de Zapier que convierte cualquier reunión finalizada en un informe conciso, decisiones, tareas pendientes y borradores de seguimiento listos para enviar. Garantiza que no se pierda nada importante después de una reunión sin enviar nunca nada automáticamente sin su aprobación |
| [Refactorización de Markdown](toolkit/phase-1-content-toolkit/refactorizacion-de-markdown/SKILL.md) | Esta herramienta de refactorización reorganiza archivos de instrucciones de IA monolíticos como CLAUDE.md o AGENTS.md en documentación estructurada basada en temas utilizando principios de divulgación progresiva. Al separar las directivas principales de las guías detalladas, reduce la carga de mantenimiento para proyectos complejos y mejora la precisión con la que los agentes de IA siguen las reglas del proyecto |
| [Arquitecto de PRD](toolkit/phase-1-content-toolkit/arquitecto-de-prd/SKILL.md) | Esta herramienta proporciona una plantilla profesional con 8 módulos principales para ayudar a los gerentes de producto a generar rápidamente Documentos de Requisitos del Producto PRD claros y estructurados. Estandariza el proceso de documentación desde la definición del problema hasta el lanzamiento, mejorando la eficiencia de la comunicación en todo el equipo |
| [Verificador de hechos para blogs](toolkit/phase-1-content-toolkit/verificador-de-hechos-para-blogs/SKILL.md) | Esta habilidad verifica los hechos de las publicaciones de blog extrayendo automáticamente afirmaciones y declaraciones estadísticas, y visitando las URL de las fuentes citadas para verificar su exactitud. Estandariza el flujo de trabajo de verificación de contenido, ayudando a los creadores y editores a asegurar la autenticidad y fiabilidad antes de publicar, mejorando así la calidad y credibilidad del contenido |
| [Adaptador de estilo de revista](toolkit/phase-1-content-toolkit/adaptador-de-estilo-de-revista/SKILL.md) | Este asistente dinámico de escritura académica extrae el estilo de redacción de revistas objetivo o artículos de conferencias de primer nivel para generar reglas de revisión personalizadas. Al aplicar estas reglas basadas en el corpus para revisar su manuscrito sección por sección, ayuda a los investigadores a alinear su trabajo con estándares de publicación específicos, protegiendo estrictamente las fórmulas y los datos |
| [Arquitecto de README](toolkit/phase-1-content-toolkit/arquitecto-de-readme/SKILL.md) | Este asistente de documentación proporciona plantillas profesionales de README y guías de escritura estructuradas adaptadas a diferentes tipos de proyectos y audiencias. Convierte detalles dispersos del proyecto en documentación clara y bien organizada, ayudando a los desarrolladores a crear READMEs específicos y profesionales, personales o internos |
| [Arquitecto de PRD](toolkit/phase-1-content-toolkit/arquitecto-de-prd/SKILL.md) | Esta Skill es un asistente estructurado para redactar Documentos de Requisitos del Producto PRD, incorporando conocimientos de expertos en productos. Te guía desde la definición del problema hasta los criterios de éxito, haciendo que la planificación del producto sea más clara y ejecutable para los equipos de ingeniería |
| [Traductor SEO de Blogs](toolkit/phase-1-content-toolkit/traductor-seo-de-blogs/SKILL.md) | Esta es una herramienta profesional de traducción de blogs y localización SEO que traduce publicaciones a múltiples idiomas manteniendo la estructura de markdown, los metadatos y los archivos multimedia incrustados. Localiza automáticamente las palabras clave y el formato para el público objetivo, ayudando a los creadores de contenido a expandirse globalmente sin la molestia de reformatear manualmente o perder valor SEO |
| [Profesional de Experimentación de Contenido](toolkit/phase-1-content-toolkit/profesional-de-experimentacion-de-contenido/SKILL.md) | Esta es una guía oficial para flujos de trabajo de experimentación y pruebas A/B de contenido en Sanity, que ayuda a los equipos a diseñar hipótesis y estrategias de optimización. Traduce los principios de pruebas basados en datos en pasos prácticos, permitiendo a los equipos comparar sistemáticamente variaciones de contenido y mejorar las tasas de conversión de las páginas de destino |
| [Arquitecto de Notas de Obsidian](toolkit/phase-1-content-toolkit/arquitecto-de-notas-de-obsidian/SKILL.md) | Esta habilidad permite a la IA generar y editar notas utilizando la sintaxis Markdown única de Obsidian, incluyendo wikilinks, embeds y callouts. Agiliza la creación de contenido al producir archivos Markdown estructurados e interoperables, directamente compatibles con las potentes funciones de gestión del conocimiento de Obsidian |
| [Dev Comm Pro](toolkit/phase-1-content-toolkit/dev-comm-pro/SKILL.md) | . Esta guía de comunicación profesional proporciona a los desarrolladores de software marcos prácticos, plantillas de correo electrónico, etiqueta de mensajería y agendas de reuniones. Le ayuda a adaptar conceptos técnicos complejos para audiencias no técnicas y a redactar mensajes claros, haciendo que la comunicación en el lugar de trabajo sea más eficiente y profesional |
| [Investigación de palabras clave](toolkit/phase-1-content-toolkit/investigacion-de-palabras-clave/SKILL.md) | . Realice una investigación profesional de palabras |
| [Análisis de brechas de contenido](toolkit/phase-1-content-toolkit/analisis-de-brechas-de-contenido/SKILL.md) | . Identifica y prioriza las brechas de contenido del sitio web comparándolas con los competidores y la demanda de búsqueda utilizando Ahrefs, Semrush o datos públicos de las SERP |

## Límites

Este repositorio proporciona instrucciones y validadores locales; no incluye credenciales, scraping automático, publicación externa, envío de correos ni acceso a cuentas. Las habilidades que requieren fuentes externas deben recibirlas como entrada o ejecutarse en un entorno con autorización y trazabilidad.
