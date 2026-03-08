/**
 * API client for the Audio Visualizer backend.
 */

import type { Job, AudioFeatures, ExportRequest, VersionData, CreateVersionRequest } from "./types";

const API_BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail || "Request failed", res.status);
  }

  return res.json();
}

/** Create a new job from a YouTube URL. */
export async function createJob(youtubeUrl: string): Promise<Job> {
  return request<Job>("/jobs", {
    method: "POST",
    body: JSON.stringify({ youtube_url: youtubeUrl }),
  });
}

/** Get job status. */
export async function getJob(jobId: string): Promise<Job> {
  return request<Job>(`/jobs/${jobId}`);
}

/** Upload images for a job. */
export async function uploadImages(
  jobId: string,
  files: File[]
): Promise<Job> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const res = await fetch(`${API_BASE}/jobs/${jobId}/images`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail || "Upload failed", res.status);
  }

  return res.json();
}

/** Get precomputed audio features for live preview. */
export async function getPreviewData(
  jobId: string
): Promise<AudioFeatures> {
  return request<AudioFeatures>(`/jobs/${jobId}/preview-data`);
}

/** Get audio URL for streaming. */
export function getAudioUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/audio`;
}

/** Start MP4 export. */
export async function startExport(
  jobId: string,
  exportReq: ExportRequest
): Promise<Job> {
  return request<Job>(`/jobs/${jobId}/export`, {
    method: "POST",
    body: JSON.stringify(exportReq),
  });
}

/** Get download URL for finished MP4. */
export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/download`;
}

/** Get version history — falls back to static file if backend unavailable. */
export async function getVersions(): Promise<VersionData> {
  try {
    return await request<VersionData>("/versions");
  } catch {
    // Fallback: load from static public/versions.json
    const res = await fetch("/versions.json");
    if (res.ok) return res.json();
    return { current: "0.0.0", versions: [] };
  }
}

/** Create a new version via backend. */
export async function createVersion(data: CreateVersionRequest): Promise<VersionData> {
  return request<VersionData>("/versions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
