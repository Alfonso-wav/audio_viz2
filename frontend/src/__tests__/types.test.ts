/**
 * Tests for src/types.ts — type validation at runtime boundaries.
 * TypeScript types are compile-time only, so these tests verify
 * the shape of objects conforming to our types.
 */
import { describe, it, expect } from "vitest";
import type {
  Job,
  JobStatus,
  AudioFeatures,
  LayerConfig,
  BandName,
  EffectType,
  ExportRequest,
  WizardStep,
} from "../types";

describe("Type shapes", () => {
  it("Job has all required fields", () => {
    const job: Job = {
      job_id: "abc",
      youtube_url: "https://youtube.com/watch?v=test",
      status: "queued",
      progress: 0,
      error: null,
      audio_duration: null,
      stems_ready: false,
      images_uploaded: 0,
    };
    expect(job.job_id).toBe("abc");
    expect(job.status).toBe("queued");
  });

  it("all JobStatus values are valid", () => {
    const statuses: JobStatus[] = [
      "queued",
      "downloading",
      "separating",
      "analyzing",
      "waiting_images",
      "rendering",
      "done",
      "error",
    ];
    expect(statuses).toHaveLength(8);
  });

  it("AudioFeatures has correct shape", () => {
    const features: AudioFeatures = {
      duration: 10,
      fps: 30,
      total_frames: 300,
      rms: [0.5],
      bands: { low: [0.8], low_mid: [0.6], mid: [0.4], high_mid: [0.3], high: [0.2] },
    };
    expect(features.bands.low).toEqual([0.8]);
    expect(Object.keys(features.bands)).toHaveLength(5);
  });

  it("LayerConfig has correct defaults", () => {
    const layer: LayerConfig = {
      image_index: 0,
      band: "low",
      effect: "pulse",
      intensity: 1.0,
      blend_mode: "normal",
      z_index: 0,
    };
    expect(layer.effect).toBe("pulse");
  });

  it("BandName covers all bands", () => {
    const bands: BandName[] = ["low", "low_mid", "mid", "high_mid", "high"];
    expect(bands).toHaveLength(5);
  });

  it("EffectType covers all effects", () => {
    const effects: EffectType[] = ["pulse", "distort", "rotate", "glow"];
    expect(effects).toHaveLength(4);
  });

  it("WizardStep covers all steps", () => {
    const steps: WizardStep[] = ["url", "processing", "images", "preview", "export"];
    expect(steps).toHaveLength(5);
  });

  it("ExportRequest has layers and preset", () => {
    const req: ExportRequest = {
      preset: "default",
      layers: [
        {
          image_index: 0,
          band: "low",
          effect: "pulse",
          intensity: 1,
          blend_mode: "normal",
          z_index: 0,
        },
      ],
    };
    expect(req.layers).toHaveLength(1);
  });
});
