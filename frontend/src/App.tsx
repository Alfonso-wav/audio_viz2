/**
 * Main App — Wizard-based flow through the audio visualizer steps.
 */

import { useState, useCallback } from "react";
import type { Job, WizardStep, LayerConfig } from "./types";
import StepUrl from "./components/StepUrl.tsx";
import StepProcessing from "./components/StepProcessing.tsx";
import StepImages from "./components/StepImages.tsx";
import StepPreview from "./components/StepPreview.tsx";
import StepExport from "./components/StepExport.tsx";
import Header from "./components/Header";
import StepIndicator from "./components/StepIndicator";

const BAND_DEFAULTS: LayerConfig[] = [
  { image_index: 0, band: "low", effect: "pulse", intensity: 1.2, blend_mode: "normal", z_index: 0 },
  { image_index: 1, band: "low_mid", effect: "distort", intensity: 1.0, blend_mode: "normal", z_index: 1 },
  { image_index: 2, band: "mid", effect: "glow", intensity: 1.0, blend_mode: "normal", z_index: 2 },
  { image_index: 3, band: "high_mid", effect: "rotate", intensity: 0.8, blend_mode: "normal", z_index: 3 },
  { image_index: 4, band: "high", effect: "pulse", intensity: 0.9, blend_mode: "normal", z_index: 4 },
];

export default function App() {
  const [step, setStep] = useState<WizardStep>("url");
  const [job, setJob] = useState<Job | null>(null);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [layers, setLayers] = useState<LayerConfig[]>(BAND_DEFAULTS);

  const handleJobCreated = useCallback((newJob: Job) => {
    setJob(newJob);
    setStep("processing");
  }, []);

  const handleProcessingDone = useCallback((updatedJob: Job) => {
    setJob(updatedJob);
    setStep("images");
  }, []);

  const handleImagesUploaded = useCallback(
    (updatedJob: Job, files: File[]) => {
      setJob(updatedJob);
      setImageFiles(files);
      setStep("preview");
    },
    []
  );

  const handleExportStart = useCallback(() => {
    setStep("export");
  }, []);

  const handleReset = useCallback(() => {
    setJob(null);
    setImageFiles([]);
    setLayers(BAND_DEFAULTS);
    setStep("url");
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Header onReset={handleReset} />

      <StepIndicator currentStep={step} />

      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-4xl">
          {step === "url" && <StepUrl onJobCreated={handleJobCreated} />}

          {step === "processing" && job && (
            <StepProcessing job={job} onDone={handleProcessingDone} />
          )}

          {step === "images" && job && (
            <StepImages job={job} onUploaded={handleImagesUploaded} />
          )}

          {step === "preview" && job && (
            <StepPreview
              job={job}
              imageFiles={imageFiles}
              layers={layers}
              onLayersChange={setLayers}
              onExport={handleExportStart}
            />
          )}

          {step === "export" && job && (
            <StepExport
              job={job}
              layers={layers}
              onReset={handleReset}
            />
          )}
        </div>
      </main>
    </div>
  );
}
