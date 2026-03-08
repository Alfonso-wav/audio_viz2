/**
 * p5.js visualizer sketch.
 *
 * Renders 5 image layers on a single canvas, each reacting to a
 * different frequency band from the Web Audio API.
 *
 * This component is used for the live preview. The same visual logic
 * is replicated on the backend (Pillow renderer) for deterministic MP4 export.
 */

import { useRef, useEffect, useCallback } from "react";
import p5 from "p5";
import type { LayerConfig } from "../types";

interface VisualizerProps {
  imageFiles: File[];
  layers: LayerConfig[];
  getAudioData: () => { rms: number; bands: Record<string, number> };
  width?: number;
  height?: number;
}

export default function Visualizer({
  imageFiles,
  layers,
  getAudioData,
  width = 1280,
  height = 720,
}: VisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const p5Ref = useRef<p5 | null>(null);
  const imagesRef = useRef<p5.Image[]>([]);
  const layersRef = useRef(layers);

  // Keep layers ref updated
  useEffect(() => {
    layersRef.current = layers;
  }, [layers]);

  const sketch = useCallback(
    (p: p5) => {
      let loadedCount = 0;

      p.preload = () => {
        // Load images from File objects via createObjectURL
        imagesRef.current = [];
        imageFiles.forEach((file, i) => {
          const url = URL.createObjectURL(file);
          const img = p.loadImage(url, () => {
            loadedCount++;
            URL.revokeObjectURL(url);
          });
          imagesRef.current.push(img);
        });
      };

      p.setup = () => {
        const canvas = p.createCanvas(width, height);
        canvas.style("width", "100%");
        canvas.style("height", "auto");
        p.imageMode(p.CENTER);
        p.frameRate(30);
      };

      p.draw = () => {
        const { rms, bands } = getAudioData();

        // Background
        const bgR = 10 + rms * 30;
        const bgG = 10 + rms * 15;
        const bgB = 20 + rms * 40;
        p.background(bgR, bgG, bgB);

        // Sort layers by z_index
        const sorted = [...layersRef.current].sort(
          (a, b) => a.z_index - b.z_index
        );

        for (const layer of sorted) {
          const img = imagesRef.current[layer.image_index];
          if (!img || img.width === 0) continue;

          const energy = bands[layer.band] || 0;
          const intensity = layer.intensity;

          p.push();
          p.translate(width / 2, height / 2);

          // Apply opacity based on energy
          const opacity = Math.max(80, Math.min(255, 100 + energy * 200));
          p.tint(255, opacity);

          switch (layer.effect) {
            case "pulse": {
              const scale = 0.3 + energy * 0.4 * intensity;
              const w = width * scale;
              const h = height * scale;
              p.image(img, 0, 0, w, h);
              break;
            }

            case "distort": {
              const scale = 0.35 + energy * 0.2 * intensity;
              const w = width * scale;
              const h = height * scale;
              // Wave distortion simulation via shear
              const shearAmount = energy * 0.3 * intensity;
              // @ts-ignore - shearX exists in p5
              p.shearX(p.sin(p.frameCount * 0.1) * shearAmount);
              p.image(img, 0, 0, w, h);
              break;
            }

            case "rotate": {
              const scale = 0.3 + energy * 0.2 * intensity;
              const angle =
                p.frameCount * 0.008 * intensity + energy * 0.5 * intensity;
              p.rotate(angle);
              const w = width * scale;
              const h = height * scale;
              p.image(img, 0, 0, w, h);
              break;
            }

            case "glow": {
              const scale = 0.35 + energy * 0.3 * intensity;
              const w = width * scale;
              const h = height * scale;
              // Simulate glow with multiple semi-transparent draws
              const glowAlpha = Math.min(120, energy * 150 * intensity);
              p.tint(255, 255, 255, glowAlpha);
              p.image(img, 0, 0, w * 1.1, h * 1.1);
              p.tint(255, opacity);
              p.image(img, 0, 0, w, h);
              break;
            }

            default: {
              const scale = 0.3 + energy * 0.3;
              p.image(img, 0, 0, width * scale, height * scale);
            }
          }

          p.pop();
        }

        // Optional: draw RMS bar at bottom
        p.noStroke();
        p.fill(139, 92, 246, 150);
        p.rect(0, height - 4, width * rms, 4);
      };
    },
    [imageFiles, getAudioData, width, height]
  );

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up previous instance
    if (p5Ref.current) {
      p5Ref.current.remove();
    }

    p5Ref.current = new p5(sketch, containerRef.current);

    return () => {
      if (p5Ref.current) {
        p5Ref.current.remove();
        p5Ref.current = null;
      }
    };
  }, [sketch]);

  return (
    <div
      ref={containerRef}
      className="rounded-xl overflow-hidden border border-dark-600"
      style={{ maxWidth: width }}
    />
  );
}
