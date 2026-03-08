/**
 * Layer editor panel — lets users tweak effect, band, and intensity per layer.
 */

import type { LayerConfig, BandName, EffectType } from "../types";

const STEM_LABELS = ["Vocals", "Drums", "Bass", "Piano", "Other"];
const BANDS: BandName[] = ["low", "low_mid", "mid", "high_mid", "high"];
const EFFECTS: EffectType[] = ["pulse", "distort", "rotate", "glow"];
const BAND_LABELS: Record<BandName, string> = {
  low: "Low (Sub)",
  low_mid: "Low-Mid",
  mid: "Mid",
  high_mid: "High-Mid",
  high: "High (Treble)",
};

interface LayerEditorProps {
  layers: LayerConfig[];
  onChange: (layers: LayerConfig[]) => void;
}

export default function LayerEditor({ layers, onChange }: LayerEditorProps) {
  const updateLayer = (index: number, field: keyof LayerConfig, value: any) => {
    const newLayers = layers.map((l, i) =>
      i === index ? { ...l, [field]: value } : l
    );
    onChange(newLayers);
  };

  return (
    <div className="bg-dark-800 rounded-xl border border-dark-600 p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-300">Layer Settings</h3>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {layers.map((layer, i) => (
          <div
            key={i}
            className="bg-dark-700 rounded-lg p-3 space-y-3"
          >
            <div className="text-xs font-bold text-accent-purple">
              {STEM_LABELS[i]}
            </div>

            {/* Band select */}
            <label className="block">
              <span className="text-xs text-gray-500">Freq Band</span>
              <select
                value={layer.band}
                onChange={(e) => updateLayer(i, "band", e.target.value)}
                className="w-full mt-1 bg-dark-900 border border-dark-600 rounded px-2 py-1 text-xs text-white"
              >
                {BANDS.map((b) => (
                  <option key={b} value={b}>
                    {BAND_LABELS[b]}
                  </option>
                ))}
              </select>
            </label>

            {/* Effect select */}
            <label className="block">
              <span className="text-xs text-gray-500">Effect</span>
              <select
                value={layer.effect}
                onChange={(e) => updateLayer(i, "effect", e.target.value)}
                className="w-full mt-1 bg-dark-900 border border-dark-600 rounded px-2 py-1 text-xs text-white"
              >
                {EFFECTS.map((ef) => (
                  <option key={ef} value={ef}>
                    {ef.charAt(0).toUpperCase() + ef.slice(1)}
                  </option>
                ))}
              </select>
            </label>

            {/* Intensity slider */}
            <label className="block">
              <span className="text-xs text-gray-500">
                Intensity: {layer.intensity.toFixed(1)}
              </span>
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.1"
                value={layer.intensity}
                onChange={(e) =>
                  updateLayer(i, "intensity", parseFloat(e.target.value))
                }
                className="w-full mt-1 accent-accent-purple"
              />
            </label>
          </div>
        ))}
      </div>
    </div>
  );
}
