/**
 * Tests for src/api.ts — API client functions.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createJob, getJob, uploadImages, getPreviewData, startExport, getDownloadUrl, getAudioUrl, getVersions, createVersion } from "../api";

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

describe("createJob", () => {
  it("sends POST with youtube_url and returns job", async () => {
    const fakeJob = {
      job_id: "abc123",
      youtube_url: "https://youtube.com/watch?v=test",
      status: "queued",
      progress: 0,
      error: null,
      audio_duration: null,
      stems_ready: false,
      images_uploaded: 0,
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeJob),
    });

    const result = await createJob("https://youtube.com/watch?v=test");
    expect(result).toEqual(fakeJob);
    expect(mockFetch).toHaveBeenCalledWith("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_url: "https://youtube.com/watch?v=test" }),
    });
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: "Bad Request" }),
    });

    await expect(createJob("bad")).rejects.toThrow();
  });
});

describe("getJob", () => {
  it("fetches job by id", async () => {
    const fakeJob = { job_id: "x", status: "downloading", progress: 0.3 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeJob),
    });

    const result = await getJob("x");
    expect(result.status).toBe("downloading");
    expect(mockFetch).toHaveBeenCalledWith("/api/jobs/x", {
      headers: { "Content-Type": "application/json" },
    });
  });
});

describe("uploadImages", () => {
  it("sends FormData with files", async () => {
    const fakeJob = { job_id: "x", images_uploaded: 5 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeJob),
    });

    const files = [
      new File(["png"], "img1.png", { type: "image/png" }),
      new File(["png"], "img2.png", { type: "image/png" }),
    ];

    const result = await uploadImages("x", files);
    expect(result.images_uploaded).toBe(5);
    const call = mockFetch.mock.calls[0];
    expect(call[0]).toBe("/api/jobs/x/images");
    expect(call[1].method).toBe("POST");
    expect(call[1].body).toBeInstanceOf(FormData);
  });
});

describe("getPreviewData", () => {
  it("returns audio features", async () => {
    const fakeFeatures = {
      duration: 10,
      fps: 30,
      total_frames: 300,
      rms: [0.5],
      bands: { low: [0.8], low_mid: [0.6], mid: [0.4], high_mid: [0.3], high: [0.2] },
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeFeatures),
    });

    const result = await getPreviewData("x");
    expect(result.fps).toBe(30);
    expect(result.bands.low).toEqual([0.8]);
  });
});

describe("startExport", () => {
  it("sends POST with export request", async () => {
    const fakeJob = { job_id: "x", status: "rendering" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeJob),
    });

    const layers = [
      { image_index: 0, band: "low" as const, effect: "pulse" as const, intensity: 1, blend_mode: "normal", z_index: 0 },
    ];
    await startExport("x", { preset: "default", layers });

    const call = mockFetch.mock.calls[0];
    expect(call[0]).toBe("/api/jobs/x/export");
    const body = JSON.parse(call[1].body);
    expect(body.preset).toBe("default");
    expect(body.layers).toHaveLength(1);
  });
});

describe("getDownloadUrl", () => {
  it("returns correct URL", () => {
    expect(getDownloadUrl("abc")).toBe("/api/jobs/abc/download");
  });
});

describe("getAudioUrl", () => {
  it("returns correct URL", () => {
    expect(getAudioUrl("abc")).toBe("/api/jobs/abc/audio");
  });
});

describe("getVersions", () => {
  it("fetches version data from /api/versions", async () => {
    const fakeVersions = {
      current: "0.2.0",
      versions: [
        { version: "0.2.0", date: "2026-03-10", description: "V2", changes: ["New feature"] },
        { version: "0.1.0", date: "2026-03-02", description: "MVP", changes: ["Initial"] },
      ],
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeVersions),
    });

    const result = await getVersions();
    expect(result.current).toBe("0.2.0");
    expect(result.versions).toHaveLength(2);
    expect(mockFetch).toHaveBeenCalledWith("/api/versions", {
      headers: { "Content-Type": "application/json" },
    });
  });

  it("falls back to static file when API fails", async () => {
    const fallbackData = { current: "0.1.0", versions: [{ version: "0.1.0", date: "2026-01-01", description: "MVP", changes: [] }] };
    // First call (API) fails
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: "Not Found" }),
    });
    // Second call (static fallback) succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fallbackData),
    });

    const result = await getVersions();
    expect(result.current).toBe("0.1.0");
    // Second fetch should be to /versions.json (static)
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch.mock.calls[1][0]).toBe("/versions.json");
  });

  it("returns empty data when both API and static fail", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: "err" }),
    });
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({}),
    });

    const result = await getVersions();
    expect(result.current).toBe("0.0.0");
    expect(result.versions).toEqual([]);
  });
});

describe("createVersion", () => {
  it("sends POST with version data", async () => {
    const responseData = {
      current: "0.2.0",
      versions: [
        { version: "0.2.0", date: "2026-03-02", description: "New", changes: ["A"] },
      ],
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(responseData),
    });

    const result = await createVersion({ version: "0.2.0", description: "New", changes: ["A"] });
    expect(result.current).toBe("0.2.0");
    expect(mockFetch).toHaveBeenCalledWith("/api/versions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version: "0.2.0", description: "New", changes: ["A"] }),
    });
  });

  it("throws on duplicate version (409)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: "Version 0.1.0 already exists" }),
    });

    await expect(
      createVersion({ version: "0.1.0", description: "dup", changes: [] })
    ).rejects.toThrow("already exists");
  });
});
