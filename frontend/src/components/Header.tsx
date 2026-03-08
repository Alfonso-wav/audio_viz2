import { Music } from "lucide-react";
import VersionSelector from "./VersionSelector.tsx";

interface HeaderProps {
  onReset: () => void;
}

export default function Header({ onReset }: HeaderProps) {
  return (
    <header className="border-b border-dark-600 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <button
          onClick={onReset}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-purple to-accent-pink flex items-center justify-center">
            <Music size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">Audio Visualizer</h1>
            <p className="text-xs text-gray-400">YouTube → MP4 in seconds</p>
          </div>
        </button>

        <VersionSelector />
      </div>
    </header>
  );
}
