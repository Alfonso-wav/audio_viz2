/**
 * TypeScript types for the Audio Visualizer app.
 */

export interface Job {
  job_id: string;
  youtube_url: string;
  status: JobStatus;
  progress: number;
  error: string | null;
  audio_duration: number | null;
  stems_ready: boolean;
  images_uploaded: number;
}

export type JobStatus =
  | "queued"
  | "downloading"
  | "separating"
  | "analyzing"
  | "waiting_images"
  | "rendering"
  | "done"
  | "error";

export interface AudioFeatures {
  duration: number;
  fps: number;
  total_frames: number;
  rms: number[];
  bands: {
    low: number[];
    low_mid: number[];
    mid: number[];
    high_mid: number[];
    high: number[];
  };
}

export interface LayerConfig {
  image_index: number;
  band: BandName;
  effect: EffectType;
  intensity: number;
  blend_mode: string;
  z_index: number;
}

export type BandName = "low" | "low_mid" | "mid" | "high_mid" | "high";
export type EffectType = "pulse" | "distort" | "rotate" | "glow";

export interface ExportRequest {
  preset: string;
  layers: LayerConfig[];
}

export type WizardStep = "url" | "processing" | "images" | "preview" | "export";

export interface VersionEntry {
  version: string;
  date: string;
  description: string;
  changes: string[];
}

export interface VersionData {
  current: string;
  versions: VersionEntry[];
}

export interface CreateVersionRequest {
  version: string;
  description: string;
  changes: string[];
}
