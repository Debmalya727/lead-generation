import React, { useState } from "react";

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (file: File) => Promise<{ inserted_count: number }>;
}

export const ImportModal: React.FC<ImportModalProps> = ({
  isOpen,
  onClose,
  onImport,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith(".csv")) {
        setFile(selectedFile);
      } else {
        setError("Invalid file format. Please select an Excel-compatible CSV file.");
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      if (selectedFile.name.endsWith(".csv")) {
        setFile(selectedFile);
      } else {
        setError("Invalid file format. Please drop a valid CSV file.");
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const res = await onImport(file);
      setSuccess(`Import completed! Successfully imported ${res.inserted_count} new leads.`);
      setFile(null);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        "Failed to import leads. Ensure CSV layout contains a name field."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      {/* Modal Container */}
      <div className="w-full max-w-md rounded-2xl border border-glass bg-[#0a0a0a]/90 backdrop-blur-xl p-8 shadow-glass animate-hologram-glow text-white">
        <header className="mb-6 flex justify-between items-center">
          <h2 className="text-xl font-display font-extrabold tracking-tight">
            Import Leads from CSV
          </h2>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white font-mono text-sm"
          >
            ESC ✕
          </button>
        </header>

        {error && (
          <div className="mb-4 p-3 rounded-lg border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-mono">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-xs font-mono">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-glass hover:border-persian-turquoise/50 bg-black/30 rounded-xl p-8 text-center cursor-pointer transition-colors group relative"
          >
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            <div className="space-y-2">
              <div className="text-2xl">📥</div>
              <p className="text-sm text-neutral-300">
                {file ? (
                  <span className="text-persian-turquoise font-mono">{file.name}</span>
                ) : (
                  "Drag & Drop CSV file here, or click to browse"
                )}
              </p>
              <p className="text-neutral-500 text-[10px] font-mono uppercase tracking-wider">
                Only .csv files supported. Headers must map to Name, Website, Phone, Email, Location, Score, Status.
              </p>
            </div>
          </div>

          <div className="flex gap-3 mt-6 pt-4 border-t border-glass">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 py-2.5 border border-glass bg-transparent hover:bg-glass text-neutral-300 hover:text-white text-sm font-semibold rounded-lg transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !file}
              className="flex-1 py-2.5 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black disabled:opacity-40 disabled:cursor-not-allowed font-semibold text-sm rounded-lg transition-all active:scale-[0.98] duration-300 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                "UPLOAD AND IMPORT"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default ImportModal;
