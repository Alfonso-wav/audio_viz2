import { useState } from "react";
import { Link, Loader2 } from "lucide-react";
import { createJob } from "../api";
import type { Job } from "../types";

interface StepUrlProps {
  onJobCreated: (job: Job) => void;
}

export default function StepUrl({ onJobCreated }: StepUrlProps) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const job = await createJob(url.trim());
      onJobCreated(job);
    } catch (err: any) {
      setError(err.message || "Failed to create job");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="text-center space-y-8">
      <div className="space-y-3">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-accent-purple to-accent-pink bg-clip-text text-transparent">
          Paste a YouTube URL
        </h2>
        <p className="text-gray-400 max-w-md mx-auto">
          We'll download the audio, separate it into 5 stems, and let you create
          a custom audio visualizer.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-4">
        <div className="relative">
          <Link
            size={18}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
          />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full pl-12 pr-4 py-4 bg-dark-700 border border-dark-600 rounded-xl text-white placeholder-gray-500 focus:outline-none glow-input transition-all"
            disabled={loading}
            required
          />
        </div>

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-accent-purple to-accent-pink hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Creating job...
            </>
          ) : (
            "Start Processing"
          )}
        </button>
      </form>

      <p className="text-xs text-gray-600">
        Max duration: 60 seconds. Audio will be trimmed automatically.
      </p>
    </div>
  );
}
