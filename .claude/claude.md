Actúa como un Lead Full-Stack Engineer (Python backend) y Creative Coding Engineer (p5.js) especializado en aplicaciones de audio, procesamiento digital de señal y renderizado de vídeo.

Quiero que diseñes una web app full stack con estas características:

────────────────────────
🎯 OBJETIVO DEL PRODUCTO
────────────────────────

Web app divertida para crear audio visualizers personalizados y descargar un MP4 para compartir al momento.

No hay login.
No hay base de datos persistente de usuarios.
Todo el procesamiento es temporal.
El archivo final se descarga directamente.

────────────────────────
⚙️ STACK Y RESTRICCIONES
────────────────────────

Backend:
- Python
- FastAPI (salvo que justifiques otra opción mejor)
- Dockerizado
- yt-dlp ya disponible en backend
- Spleeter para separar audio en 5 pistas
- ffmpeg para generar el MP4

Infraestructura:
- Docker + docker-compose
- Se permiten workers (Celery + Redis o alternativa justificada)
- Sin base de datos persistente
- Se permite almacenamiento temporal en filesystem o Redis con TTL

Export:
- Generar archivo MP4 descargable
- Resolución por defecto: 1280x720
- 30 fps
- Tiempo total objetivo del proceso completo: < 60 segundos
- Mostrar barra de progreso o cuenta atrás

────────────────────────
🎵 FLUJO DE USUARIO
────────────────────────

1) Usuario pega URL de YouTube.
2) Backend descarga audio con yt-dlp.
3) Backend separa audio en 5 pistas con Spleeter.
4) Usuario sube 5 imágenes (una por pista).
5) Usuario entra en LIVE PREVIEW.
6) Usuario exporta y descarga MP4.

────────────────────────
🟢 DECISIÓN CLAVE: LIVE PREVIEW
────────────────────────

IMPORTANTE:

El live preview se hace SOLO con el audio mezclado (mix).
NO se usan los 5 stems en el navegador.

En frontend:
- Se reproduce el mix.
- Se usa Web Audio API (AnalyserNode).
- Se extrae:
  - Amplitud (RMS / envelope)
  - Frecuencias (FFT)
- Se dividen bandas (ej: low, low-mid, mid, high-mid, high).

Las 5 imágenes se animan dentro de UN SOLO canvas p5.js,
cada una como una capa distinta,
pero usando bandas distintas del mix para simular comportamiento multitrack.

NO reproducir 5 audios simultáneamente en frontend.

────────────────────────
🎥 EXPORT MP4
────────────────────────

El MP4 NO es grabación de pantalla.
Debe ser render offline determinista.

Pipeline recomendado:

1) Backend analiza el mix y precomputa features a 30fps:
   - RMS por frame
   - Bandas de frecuencia por frame
2) Se genera una "Visual Spec" (JSON) que contiene:
   - fps
   - resolución
   - duración
   - seed determinista
   - parámetros por capa
   - preset seleccionado
3) Backend renderiza frames (PNG) aplicando la misma lógica visual.
4) ffmpeg une frames + audio en MP4.
5) Se devuelve archivo descargable.

Optimizar para que todo el pipeline sea < 60s:
- Limitar duración máxima del audio (ej: 30-60s)
- Downsample features a 30fps
- 720p por defecto

────────────────────────
📦 LO QUE NECESITO QUE ME ENTREGUES
────────────────────────

1) Arquitectura completa (diagrama textual)
   - Componentes
   - Backend / Worker
   - Gestión de jobs
   - Almacenamiento temporal
   - Limpieza automática (TTL)

2) Pipeline técnico detallado paso a paso
   Desde URL hasta MP4 final.

3) Diseño del sistema de jobs
   Estados:
   - queued
   - downloading
   - separating
   - analyzing
   - rendering
   - done
   - error

4) Endpoints REST propuestos
   - POST /jobs
   - GET /jobs/{id}
   - GET /jobs/{id}/preview-data
   - GET /jobs/{id}/download

5) Backend (FastAPI)
   - Estructura de proyecto
   - Modelo de job
   - Worker
   - Cálculo de features
   - Render de frames
   - Uso de ffmpeg
   - Limpieza automática

6) Frontend
   - Stack sugerido (React + Vite recomendado)
   - Integración p5.js
   - Ejemplo de sketch con:
       - 5 capas de imagen
       - animación por RMS
       - distorsión por banda de frecuencia
   - Wizard UX por pasos
   - Barra de progreso con polling o websocket

7) Docker
   - Dockerfile backend
   - docker-compose
   - Dependencias del sistema necesarias
   - Volúmenes temporales

8) MVP vs V2
   - Qué construir primero
   - Qué dejar para versión 2

9) Snippets de código reales y utilizables:
   - Endpoint FastAPI
   - Worker básico
   - Función de extracción de RMS + FFT
   - Ejemplo de render frame
   - Ejemplo ffmpeg command
   - Sketch p5.js funcional

────────────────────────
📌 CONDICIONES IMPORTANTES
────────────────────────

- No usar screen recording para export.
- No usar base de datos persistente.
- Optimizar claridad técnica.
- Evitar texto genérico.
- Incluir decisiones y tradeoffs.
- Pensar como si esto fuera a producción.

Formato de respuesta:
Usar encabezados claros, bloques de código y explicaciones técnicas detalladas.