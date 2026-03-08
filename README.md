# Audio Visualizer

Web app para crear audio visualizers personalizados a partir de URLs de YouTube y descargar un MP4.

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend    │────▶│   Worker     │
│  React+Vite  │     │   FastAPI    │     │   Celery     │
│   p5.js      │     │   :8000      │     │              │
│   :3000      │     └──────┬───────┘     └──────┬───────┘
└─────────────┘            │                     │
                     ┌─────▼─────┐         ┌─────▼─────┐
                     │   Redis   │         │  Temp FS   │
                     │  Jobs+Msgs│         │  /tmp/...  │
                     └───────────┘         └───────────┘
```

### Componentes

| Componente | Rol |
|---|---|
| **Frontend** | React + Vite + TailwindCSS + p5.js. Wizard de 5 pasos. Live preview con Web Audio API |
| **Backend** | FastAPI. REST API. Sirve audio y features. Gestiona jobs en Redis |
| **Worker** | Celery. Descarga (yt-dlp), separa (Spleeter 5stems), analiza (librosa), renderiza (Pillow), codifica (ffmpeg) |
| **Redis** | Broker de Celery + almacen de estado de jobs (con TTL) |
| **Temp FS** | Volumen Docker compartido para archivos temporales (audio, stems, frames, mp4) |

## Pipeline Técnico

```
URL YouTube
  │
  ▼ yt-dlp (download + convert WAV mono 44100Hz, max 60s)
  │
  ▼ Spleeter 5stems (vocals, drums, bass, piano, other)
  │
  ▼ librosa (extract RMS + FFT 5 bands @ 30fps → features.json)
  │
  ▼ [Usuario sube 5 imágenes + configura layers]
  │
  ▼ Pillow (render PNG frames offline, determinista)
  │
  ▼ ffmpeg (frames + audio → MP4 H.264/AAC, 720p 30fps)
  │
  ▼ Descarga MP4
```

## Sistema de Jobs

Estados: `queued` → `downloading` → `separating` → `analyzing` → `waiting_images` → `rendering` → `done`

Error en cualquier punto → `error`

Almacenamiento en Redis con TTL de 1 hora. Cleanup automático de archivos cada 5 minutos.

## Endpoints REST

| Method | Path | Descripción |
|---|---|---|
| POST | `/api/jobs` | Crear job (URL YouTube) |
| GET | `/api/jobs/{id}` | Estado del job |
| POST | `/api/jobs/{id}/images` | Subir 5 imágenes |
| GET | `/api/jobs/{id}/preview-data` | Features JSON para live preview |
| GET | `/api/jobs/{id}/audio` | Stream WAV del mix |
| POST | `/api/jobs/{id}/export` | Iniciar render MP4 |
| GET | `/api/jobs/{id}/download` | Descargar MP4 terminado |

## Quick Start

```bash
# Clonar y arrancar
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Desarrollo Local

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Worker (Celery)
```bash
cd backend
celery -A app.celery_app:celery_app worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Requiere Redis corriendo en `localhost:6379`.

## Estructura del Proyecto

```
audio_viz2/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI app
│       ├── config.py         # Settings (env vars)
│       ├── models.py         # Job model + Redis helpers
│       ├── schemas.py        # Pydantic request/response
│       ├── routes.py         # API endpoints
│       ├── celery_app.py     # Celery config
│       ├── cleanup.py        # TTL file cleanup
│       └── worker/
│           ├── tasks.py      # Celery tasks
│           ├── audio.py      # yt-dlp + Spleeter + feature extraction
│           └── renderer.py   # Pillow frame renderer
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx           # Wizard flow
        ├── api.ts            # Backend API client
        ├── types.ts          # TypeScript types
        ├── audioAnalyzer.ts  # Web Audio API wrapper
        ├── index.css         # TailwindCSS + custom styles
        └── components/
            ├── Header.tsx
            ├── StepIndicator.tsx
            ├── StepUrl.tsx
            ├── StepProcessing.tsx
            ├── StepImages.tsx
            ├── StepPreview.tsx
            ├── StepExport.tsx
            ├── Visualizer.tsx    # p5.js canvas
            └── LayerEditor.tsx
```

## Decisiones y Tradeoffs

| Decisión | Razón |
|---|---|
| **Celery + Redis** vs async tasks | Celery permite retry, concurrency control, y aislamiento de procesos pesados (Spleeter leak de memoria) |
| **Pillow** vs headless browser para render | Pillow es 10x más rápido, determinista, sin dependencias de browser |
| **Web Audio API** para preview | Analiza el mix en real-time sin descargar 5 stems al navegador |
| **Redis** como único store | Sin DB persistente. Jobs tienen TTL. Simplicidad máxima |
| **ffmpeg ultrafast** preset | Prioriza velocidad sobre tamaño de archivo para target < 60s |
| **Max 60s audio** | Limita frames a ~1800. Rendering viable en < 30s |

## MVP vs V2

### MVP (este repo)
- [x] YouTube → audio download
- [x] Spleeter 5 stems
- [x] Feature extraction (RMS + 5 bands)
- [x] Upload 5 imágenes
- [x] Live preview con p5.js + Web Audio
- [x] 4 efectos (pulse, distort, rotate, glow)
- [x] Layer editor (band, effect, intensity)
- [x] Export MP4 offline determinista
- [x] Progress polling
- [x] Docker-compose full stack

### V2
- [ ] WebSocket para progress (reemplazar polling)
- [ ] Más efectos (particles, waveform, spectrum bars)
- [ ] Presets visuales predefinidos
- [ ] Preview de stems individuales
- [ ] Trim de audio en frontend
- [ ] Resolución configurable (1080p, 4K)
- [ ] Watermark optional
- [ ] Rate limiting + queue management
- [ ] CDN para archivos temporales
- [ ] Tests automatizados
