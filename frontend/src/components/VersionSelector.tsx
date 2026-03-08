import { useState, useEffect, useRef } from "react";
import { Tag, ChevronDown, X, Plus, Save, Trash2 } from "lucide-react";
import { getVersions, createVersion } from "../api";
import type { VersionData, VersionEntry } from "../types";

export default function VersionSelector() {
  const [data, setData] = useState<VersionData | null>(null);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<VersionEntry | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Form state
  const [newVersion, setNewVersion] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newChanges, setNewChanges] = useState<string[]>([""]);

  const loadVersions = () => {
    getVersions()
      .then((d) => setData(d))
      .catch(() => setData({ current: "?", versions: [] }));
  };

  useEffect(() => { loadVersions(); }, []);

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSelected(null);
        setShowForm(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const resetForm = () => {
    setNewVersion("");
    setNewDescription("");
    setNewChanges([""]);
    setError(null);
  };

  const handleSave = async () => {
    if (!newVersion.trim() || !newDescription.trim()) {
      setError("Version and description are required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const updated = await createVersion({
        version: newVersion.trim(),
        description: newDescription.trim(),
        changes: newChanges.filter((c) => c.trim()),
      });
      setData(updated);
      setShowForm(false);
      resetForm();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save version";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const addChangeRow = () => setNewChanges([...newChanges, ""]);
  const removeChangeRow = (i: number) => {
    const next = newChanges.filter((_, idx) => idx !== i);
    setNewChanges(next.length ? next : [""]);
  };
  const updateChangeRow = (i: number, val: string) => {
    const next = [...newChanges];
    next[i] = val;
    setNewChanges(next);
  };

  // Always render the badge — show "?" if no data yet
  const currentVersion = data?.current ?? "…";

  return (
    <div className="relative" ref={panelRef}>
      {/* Version badge button */}
      <button
        onClick={() => { setOpen(!open); setSelected(null); setShowForm(false); }}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-dark-700 hover:bg-dark-600 
                   border border-dark-500 text-xs text-gray-400 hover:text-gray-200 transition-all"
        title="Version history"
      >
        <Tag size={12} />
        <span className="font-mono">v{currentVersion}</span>
        <ChevronDown size={12} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-96 max-h-[500px] overflow-y-auto
                        bg-dark-800 border border-dark-500 rounded-xl shadow-2xl z-50">
          {/* Header */}
          <div className="sticky top-0 bg-dark-800 px-4 py-3 border-b border-dark-600 flex items-center justify-between z-10">
            <h3 className="text-sm font-semibold text-white">Version History</h3>
            <div className="flex items-center gap-2">
              {!showForm && (
                <button
                  onClick={() => { setShowForm(true); setSelected(null); resetForm(); }}
                  className="flex items-center gap-1 px-2 py-1 rounded-md bg-accent-purple/20 hover:bg-accent-purple/30 
                             text-accent-purple text-[11px] font-semibold transition-colors"
                  title="New version"
                >
                  <Plus size={12} />
                  New
                </button>
              )}
              <button onClick={() => { setOpen(false); setSelected(null); setShowForm(false); }} className="text-gray-500 hover:text-gray-300">
                <X size={14} />
              </button>
            </div>
          </div>

          {/* ── New version form ── */}
          {showForm && (
            <div className="p-4 border-b border-dark-600 bg-dark-750 space-y-3">
              <h4 className="text-xs font-bold text-accent-pink uppercase tracking-wide">Create New Version</h4>

              {error && (
                <div className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}

              {/* Version number */}
              <div>
                <label className="block text-[11px] text-gray-400 mb-1">Version *</label>
                <input
                  type="text"
                  value={newVersion}
                  onChange={(e) => setNewVersion(e.target.value)}
                  placeholder="e.g. 0.2.0"
                  className="w-full px-3 py-1.5 rounded-lg bg-dark-700 border border-dark-500 text-sm text-white
                             placeholder-gray-600 focus:outline-none focus:border-accent-purple/50 transition-colors"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-[11px] text-gray-400 mb-1">Description *</label>
                <input
                  type="text"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="e.g. Layer editor + presets"
                  className="w-full px-3 py-1.5 rounded-lg bg-dark-700 border border-dark-500 text-sm text-white
                             placeholder-gray-600 focus:outline-none focus:border-accent-purple/50 transition-colors"
                />
              </div>

              {/* Changes list */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] text-gray-400">Changes</label>
                  <button onClick={addChangeRow} className="text-[10px] text-accent-purple hover:text-accent-pink transition-colors">
                    + Add change
                  </button>
                </div>
                <div className="space-y-1.5">
                  {newChanges.map((c, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="text-accent-pink text-xs">•</span>
                      <input
                        type="text"
                        value={c}
                        onChange={(e) => updateChangeRow(i, e.target.value)}
                        placeholder={`Change ${i + 1}`}
                        className="flex-1 px-2 py-1 rounded-md bg-dark-700 border border-dark-500 text-xs text-white
                                   placeholder-gray-600 focus:outline-none focus:border-accent-purple/50 transition-colors"
                      />
                      {newChanges.length > 1 && (
                        <button onClick={() => removeChangeRow(i)} className="text-gray-600 hover:text-red-400 transition-colors">
                          <Trash2 size={11} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-purple hover:bg-accent-purple/80 
                             text-white text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save size={12} />
                  {saving ? "Saving…" : "Save Version"}
                </button>
                <button
                  onClick={() => { setShowForm(false); resetForm(); }}
                  className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-gray-400 text-xs transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* ── Version list ── */}
          <div className="p-2">
            {data && data.versions.length === 0 && !showForm && (
              <p className="text-center text-xs text-gray-500 py-4">No versions yet. Click "New" to create one.</p>
            )}
            {data?.versions.map((v) => (
              <button
                key={v.version}
                onClick={() => setSelected(selected?.version === v.version ? null : v)}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
                  selected?.version === v.version
                    ? "bg-accent-purple/20 border border-accent-purple/40"
                    : "hover:bg-dark-700 border border-transparent"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-white">v{v.version}</span>
                    {v.version === data.current && (
                      <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-accent-purple/30 text-accent-purple">
                        CURRENT
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-gray-500">{v.date}</span>
                </div>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">{v.description}</p>

                {/* Expanded changes */}
                {selected?.version === v.version && v.changes.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {v.changes.map((c, i) => (
                      <li key={i} className="text-[11px] text-gray-500 flex items-start gap-1.5">
                        <span className="text-accent-pink mt-0.5">•</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
