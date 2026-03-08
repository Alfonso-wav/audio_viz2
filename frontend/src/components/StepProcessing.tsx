import { useEffect, useRef, useState } from "react";
import { Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { getJob } from "../api";
import type { Job, JobStatus } from "../types";

interface StepProcessingProps {
  job: Job;
  onDone: (job: Job) => void;
}

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued...",
  downloading: "Downloading audio from YouTube...",
  separating: "Separating into 5 stems with Spleeter...",
  analyzing: "Analyzing frequency bands...",
  waiting_images: "Ready! Upload your images.",
};

export default function StepProcessing({ job, onDone }: StepProcessingProps) {
  const [currentJob, setCurrentJob] = useState<Job>(job);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const updated = await getJob(job.job_id);
        setCurrentJob(updated);

        if (
          updated.status === "waiting_images" ||
          updated.status === "done"
        ) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          onDone(updated);
        }

        if (updated.status === "error") {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch {
        // Continue polling on transient errors
      }
    };

    intervalRef.current = window.setInterval(poll, 1500);
    poll(); // Initial fetch

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [job.job_id, onDone]);

  const isError = currentJob.status === "error";
  const progress = Math.round(currentJob.progress * 100);

  return (
    <div className="text-center space-y-8 max-w-lg mx-auto">
      <div className="space-y-3">
        <h2 className="text-2xl font-bold">Processing Your Audio</h2>
        <p className="text-gray-400 text-sm">
          This usually takes 15-30 seconds.
        </p>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="w-full h-3 bg-dark-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isError ? "bg-red-500" : "progress-bar"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>{STATUS_LABELS[currentJob.status] || currentJob.status}</span>
          <span>{progress}%</span>
        </div>
      </div>

      {/* Status icon */}
      <div className="flex justify-center">
        {isError ? (
          <div className="text-center space-y-2">
            <AlertCircle size={48} className="mx-auto text-red-400" />
            <p className="text-red-400 text-sm">{currentJob.error}</p>
          </div>
        ) : (
          <Loader2 size={48} className="animate-spin text-accent-purple" />
        )}
      </div>

      {/* Step indicators */}
      <div className="space-y-2 text-left">
        {["downloading", "separating", "analyzing"].map((s) => {
          const stepOrder = ["queued", "downloading", "separating", "analyzing", "waiting_images"];
          const currentIdx = stepOrder.indexOf(currentJob.status);
          const thisIdx = stepOrder.indexOf(s);
          const isDone = thisIdx < currentIdx;
          const isActive = thisIdx === currentIdx;

          return (
            <div
              key={s}
              className={`flex items-center gap-3 py-2 px-4 rounded-lg ${
                isActive ? "bg-dark-700" : ""
              }`}
            >
              {isDone ? (
                <CheckCircle size={16} className="text-green-400" />
              ) : isActive ? (
                <Loader2 size={16} className="animate-spin text-accent-purple" />
              ) : (
                <div className="w-4 h-4 rounded-full border border-gray-600" />
              )}
              <span
                className={`text-sm ${
                  isDone
                    ? "text-green-400"
                    : isActive
                    ? "text-white"
                    : "text-gray-600"
                }`}
              >
                {STATUS_LABELS[s]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
