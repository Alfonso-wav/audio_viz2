import type { WizardStep } from "../types";

const STEPS: { key: WizardStep; label: string }[] = [
  { key: "url", label: "URL" },
  { key: "processing", label: "Processing" },
  { key: "images", label: "Images" },
  { key: "preview", label: "Preview" },
  { key: "export", label: "Export" },
];

const STEP_ORDER: WizardStep[] = STEPS.map((s) => s.key);

export default function StepIndicator({ currentStep }: { currentStep: WizardStep }) {
  const currentIdx = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="px-6 py-4">
      <div className="max-w-2xl mx-auto flex items-center gap-2">
        {STEPS.map((s, i) => {
          const isActive = i === currentIdx;
          const isDone = i < currentIdx;
          return (
            <div key={s.key} className="flex items-center gap-2 flex-1">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0
                  transition-all duration-300
                  ${isActive ? "bg-accent-purple text-white scale-110" : ""}
                  ${isDone ? "bg-accent-purple/30 text-accent-purple" : ""}
                  ${!isActive && !isDone ? "bg-dark-600 text-gray-500" : ""}
                `}
              >
                {isDone ? "✓" : i + 1}
              </div>
              <span
                className={`text-xs hidden sm:block ${
                  isActive ? "text-white font-semibold" : "text-gray-500"
                }`}
              >
                {s.label}
              </span>
              {i < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-px ${
                    isDone ? "bg-accent-purple/40" : "bg-dark-600"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
