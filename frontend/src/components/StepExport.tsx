/**
 * Step 5: Export — sends visual spec to backend, polls for render progress,
 * and provides download link when done.
 */

import { useEffect, useRef, useState } from "react";
import { Loader2, Download, RotateCcw, CheckCircle, AlertCircle } from "lucide-react";
import { startExport, getJob, getDownloadUrl } from "../api";
import type { Job, LayerConfig } from "../types";

interface StepExportProps {
  job: Job;
  layers: LayerConfig[];
  onReset: () => void;
}

export default function StepExport({ job, layers, onReset }: StepExportProps) {
  const [currentJob, setCurrentJob] = useState<Job>(job);
  const [started, setStarted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  // Start export on mount
  useEffect(() => {
    if (started) return;
    setStarted(true);

    startExport(job.job_id, {
      preset: "default",
      layers,
    }).catch((err) => {
      setError(err.message || "Failed to start export");
    });
  }, [job.job_id, layers, started]);

  // Poll for progress
  useEffect(() => {
    const poll = async () => {
      try {
        const updated = await getJob(job.job_id);
        setCurrentJob(updated);

        if (updated.status === "done" || updated.status === "error") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          if (updated.status === "error") {
            setError(updated.error || "Render failed");
          }
        }
      } catch {
        // Continue polling
      }
    };

    intervalRef.current = window.setInterval(poll, 2000);
    poll();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [job.job_id]);

  const isDone = currentJob.status === "done";
  const isError = currentJob.status === "error" || !!error;
  const progress = Math.round(currentJob.progress * 100);

  return (
    <div className="text-center space-y-8 max-w-lg mx-auto">
      <div className="space-y-3">
        <h2 className="text-2xl font-bold">
          {isDone ? "Your Video is Ready!" : isError ? "Export Failed" : "Rendering MP4..."}
        </h2>
        <p className="text-gray-400 text-sm">
          {isDone
            ? "Download your custom audio visualizer video."
            : isError
            ? "Something went wrong during the render."
            : "Rendering frames and encoding video. This takes ~30 seconds."}
        </p>
      </div>

      {/* Progress */}
      {!isDone && !isError && (
        <div className="space-y-2">
          <div className="w-full h-3 bg-dark-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full progress-bar transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Rendering frames + encoding...</span>
            <span>{progress}%</span>
          </div>
        </div>
      )}

      {/* Icon */}
      <div className="flex justify-center">
        {isDone ? (
          <CheckCircle size={64} className="text-green-400" />
        ) : isError ? (
          <AlertCircle size={64} className="text-red-400" />
        ) : (
          <Loader2 size={64} className="animate-spin text-accent-purple" />
        )}
      </div>

      {/* Error message */}
      {isError && error && (
        <p className="text-red-400 text-sm">{error}</p>
      )}

      {/* Actions */}
      <div className="flex items-center justify-center gap-4">
        {isDone && (
          <a
            href={getDownloadUrl(job.job_id)}
            download
            className="flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-white bg-gradient-to-r from-green-500 to-emerald-500 hover:opacity-90 transition-all text-lg"
          >
            <Download size={22} />
            Download MP4
          </a>
        )}

        <button
          onClick={onReset}
          className="flex items-center gap-2 px-6 py-3 rounded-xl border border-dark-600 text-gray-400 hover:text-white hover:border-gray-500 transition-all"
        >
          <RotateCcw size={16} />
          Start Over
        </button>
      </div>
    </div>
  );
}
