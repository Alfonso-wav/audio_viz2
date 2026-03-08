/**
 * Tests for src/audioAnalyzer.ts — AudioAnalyzer class.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AudioAnalyzer } from "../audioAnalyzer";

describe("AudioAnalyzer", () => {
  let analyzer: AudioAnalyzer;

  beforeEach(async () => {
    analyzer = new AudioAnalyzer();
    await analyzer.init("http://localhost/test.wav");
  });

  it("initializes without error", () => {
    expect(analyzer).toBeDefined();
  });

  it("getRMS returns a number between 0 and 1", () => {
    const rms = analyzer.getRMS();
    expect(typeof rms).toBe("number");
    expect(rms).toBeGreaterThanOrEqual(0);
    expect(rms).toBeLessThanOrEqual(1);
  });

  it("getBands returns all 5 bands", () => {
    const bands = analyzer.getBands();
    expect(bands).toHaveProperty("low");
    expect(bands).toHaveProperty("low_mid");
    expect(bands).toHaveProperty("mid");
    expect(bands).toHaveProperty("high_mid");
    expect(bands).toHaveProperty("high");
  });

  it("getBands returns values between 0 and 1", () => {
    const bands = analyzer.getBands();
    for (const key of Object.keys(bands)) {
      const val = bands[key as keyof typeof bands];
      expect(val).toBeGreaterThanOrEqual(0);
      expect(val).toBeLessThanOrEqual(1);
    }
  });

  it("destroy cleans up", () => {
    expect(() => analyzer.destroy()).not.toThrow();
  });

  it("can be created without init", () => {
    const a = new AudioAnalyzer();
    // Should not throw when calling methods without init
    expect(a.getRMS()).toBe(0);
  });
});
