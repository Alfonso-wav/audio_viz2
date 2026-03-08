import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Image as ImageIcon, Loader2, X } from "lucide-react";
import { uploadImages } from "../api";
import type { Job } from "../types";

interface StepImagesProps {
  job: Job;
  onUploaded: (job: Job, files: File[]) => void;
}

const STEM_LABELS = [
  { name: "Vocals", color: "from-red-500 to-orange-500", band: "low" },
  { name: "Drums", color: "from-orange-500 to-yellow-500", band: "low_mid" },
  { name: "Bass", color: "from-green-500 to-emerald-500", band: "mid" },
  { name: "Piano", color: "from-blue-500 to-cyan-500", band: "high_mid" },
  { name: "Other", color: "from-purple-500 to-pink-500", band: "high" },
];

export default function StepImages({ job, onUploaded }: StepImagesProps) {
  const [files, setFiles] = useState<(File | null)[]>([null, null, null, null, null]);
  const [previews, setPreviews] = useState<(string | null)[]>([null, null, null, null, null]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback(
    (index: number) => (accepted: File[]) => {
      if (accepted.length === 0) return;
      const file = accepted[0];

      const newFiles = [...files];
      newFiles[index] = file;
      setFiles(newFiles);

      const newPreviews = [...previews];
      if (newPreviews[index]) URL.revokeObjectURL(newPreviews[index]!);
      newPreviews[index] = URL.createObjectURL(file);
      setPreviews(newPreviews);
    },
    [files, previews]
  );

  const handleRemove = (index: number) => {
    const newFiles = [...files];
    newFiles[index] = null;
    setFiles(newFiles);

    const newPreviews = [...previews];
    if (newPreviews[index]) URL.revokeObjectURL(newPreviews[index]!);
    newPreviews[index] = null;
    setPreviews(newPreviews);
  };

  const allFilled = files.every((f) => f !== null);

  const handleUpload = async () => {
    if (!allFilled) return;
    setUploading(true);
    setError(null);

    try {
      const validFiles = files.filter((f): f is File => f !== null);
      const updatedJob = await uploadImages(job.job_id, validFiles);
      onUploaded(updatedJob, validFiles);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Upload 5 Images</h2>
        <p className="text-gray-400 text-sm">
          One image per stem layer. Each will react to a different frequency band.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        {STEM_LABELS.map((stem, i) => (
          <ImageSlot
            key={i}
            index={i}
            stem={stem}
            file={files[i]}
            preview={previews[i]}
            onDrop={handleDrop(i)}
            onRemove={() => handleRemove(i)}
          />
        ))}
      </div>

      {error && <p className="text-red-400 text-sm text-center">{error}</p>}

      <div className="flex justify-center">
        <button
          onClick={handleUpload}
          disabled={!allFilled || uploading}
          className="px-8 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-accent-purple to-accent-pink hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          {uploading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload size={18} />
              Continue to Preview
            </>
          )}
        </button>
      </div>
    </div>
  );
}

function ImageSlot({
  index,
  stem,
  file,
  preview,
  onDrop,
  onRemove,
}: {
  index: number;
  stem: (typeof STEM_LABELS)[0];
  file: File | null;
  preview: string | null;
  onDrop: (files: File[]) => void;
  onRemove: () => void;
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg", ".webp", ".gif"] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${stem.color}`} />
        <span className="text-xs font-semibold">{stem.name}</span>
      </div>

      <div
        {...getRootProps()}
        className={`
          relative aspect-square rounded-xl border-2 border-dashed cursor-pointer
          flex items-center justify-center overflow-hidden transition-all
          ${isDragActive ? "border-accent-purple bg-accent-purple/10" : "border-dark-600 hover:border-gray-500"}
          ${preview ? "border-solid border-accent-purple/50" : ""}
        `}
      >
        <input {...getInputProps()} />
        {preview ? (
          <>
            <img
              src={preview}
              alt={`Layer ${index + 1}`}
              className="w-full h-full object-cover"
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="absolute top-1 right-1 w-6 h-6 bg-black/70 rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
            >
              <X size={12} />
            </button>
          </>
        ) : (
          <div className="text-center p-2">
            <ImageIcon size={24} className="mx-auto text-gray-600 mb-1" />
            <p className="text-xs text-gray-500">Drop image</p>
          </div>
        )}
      </div>
    </div>
  );
}
