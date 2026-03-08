/**
 * Step 4: Live Preview — plays the mix audio, analyzes with Web Audio API,
 * and renders the p5.js canvas visualizer in real-time.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { Play, Pause, Download, Settings2 } from "lucide-react";
import { getAudioUrl } from "../api";
import { AudioAnalyzer } from "../audioAnalyzer";
import Visualizer from "./Visualizer";
import LayerEditor from "./LayerEditor";
import type { Job, LayerConfig } from "../types";

interface StepPreviewProps {
  job: Job;
  imageFiles: File[];
  layers: LayerConfig[];
  onLayersChange: (layers: LayerConfig[]) => void;
  onExport: () => void;
}

export default function StepPreview({
  job,
  imageFiles,
  layers,
  onLayersChange,
  onExport,
}: StepPreviewProps) {
  const analyzerRef = useRef<AudioAnalyzer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [ready, setReady] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const audioDataRef = useRef({ rms: 0, bands: { low: 0, low_mid: 0, mid: 0, high_mid: 0, high: 0 } });

  useEffect(() => {
    const analyzer = new AudioAnalyzer();
    analyzerRef.current = analyzer;

    analyzer.init(getAudioUrl(job.job_id)).then((audioEl) => {
      audioEl.addEventListener("canplaythrough", () => setReady(true), { once: true });
      audioEl.addEventListener("ended", () => setPlaying(false));
    });

    // Animation loop to update audio data
    let rafId: number;
    const update = () => {
      if (analyzerRef.current) {
        audioDataRef.current = {
          rms: analyzerRef.current.getRMS(),
          bands: analyzerRef.current.getBands(),
        };
      }
      rafId = requestAnimationFrame(update);
    };
    rafId = requestAnimationFrame(update);

    return () => {
      cancelAnimationFrame(rafId);
      analyzer.destroy();
    };
  }, [job.job_id]);

  const togglePlay = async () => {
    if (!analyzerRef.current) return;
    if (playing) {
      analyzerRef.current.pause();
      setPlaying(false);
    } else {
      await analyzerRef.current.play();
      setPlaying(true);
    }
  };

  const getAudioData = useCallback(() => audioDataRef.current, []);

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Live Preview</h2>
        <p className="text-gray-400 text-sm">
          Play the audio and see your visualizer react in real-time.
          Tweak layers before exporting.
        </p>
      </div>

      {/* Canvas */}
      <div className="flex justify-center">
        <Visualizer
          imageFiles={imageFiles}
          layers={layers}
          getAudioData={getAudioData}
          width={1280}
          height={720}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={togglePlay}
          disabled={!ready}
          className="w-14 h-14 rounded-full bg-gradient-to-r from-accent-purple to-accent-pink flex items-center justify-center hover:opacity-90 disabled:opacity-50 transition-all"
        >
          {playing ? <Pause size={24} /> : <Play size={24} className="ml-1" />}
        </button>

        <button
          onClick={() => setShowEditor(!showEditor)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${
            showEditor
              ? "border-accent-purple text-accent-purple bg-accent-purple/10"
              : "border-dark-600 text-gray-400 hover:text-white"
          }`}
        >
          <Settings2 size={16} />
          <span className="text-sm">Edit Layers</span>
        </button>

        <button
          onClick={onExport}
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-accent-purple to-accent-pink hover:opacity-90 transition-all"
        >
          <Download size={18} />
          Export MP4
        </button>
      </div>

      {/* Layer editor panel */}
      {showEditor && (
        <LayerEditor layers={layers} onChange={onLayersChange} />
      )}
    </div>
  );
}
