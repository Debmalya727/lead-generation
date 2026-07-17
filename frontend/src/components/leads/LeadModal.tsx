import React, { useEffect, useState } from "react";
import { Lead, LeadCreate } from "../../api/leads";

interface LeadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (leadData: LeadCreate) => Promise<void>;
  lead?: Lead | null;
}

export const LeadModal: React.FC<LeadModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  lead,
}) => {
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [location, setLocation] = useState("");
  const [score, setScore] = useState<number | "">("");
  const [statusVal, setStatusVal] = useState("discovered");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (lead) {
      setName(lead.name);
      setWebsite(lead.website || "");
      setPhone(lead.phone || "");
      setEmail(lead.email || "");
      setLocation(lead.location || "");
      setScore(lead.score !== undefined && lead.score !== null ? lead.score : "");
      setStatusVal(lead.status);
    } else {
      setName("");
      setWebsite("");
      setPhone("");
      setEmail("");
      setLocation("");
      setScore("");
      setStatusVal("discovered");
    }
    setError(null);
  }, [lead, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const payload: LeadCreate = {
      name: name.trim(),
      website: website.trim() || undefined,
      phone: phone.trim() || undefined,
      email: email.trim() || undefined,
      location: location.trim() || undefined,
      score: score !== "" ? Number(score) : undefined,
      status: statusVal,
    };

    try {
      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        "Failed to save lead record. Please check field inputs."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      {/* Modal Container */}
      <div className="w-full max-w-lg rounded-2xl border border-glass bg-[#0a0a0a]/90 backdrop-blur-xl p-8 shadow-glass animate-hologram-glow text-white">
        <header className="mb-6 flex justify-between items-center">
          <h2 className="text-xl font-display font-extrabold tracking-tight">
            {lead ? "Modify Lead Record" : "Add New Lead"}
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

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5 text-left col-span-2">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Company Name *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Innovate Tech Corp"
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Website
              </label>
              <input
                type="text"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="https://innovate.tech"
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="contact@innovate.tech"
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Phone
              </label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1-555-0199"
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="San Francisco, CA"
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Score (0-100)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={score}
                onChange={(e) => setScore(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="85"
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                Status
              </label>
              <select
                value={statusVal}
                onChange={(e) => setStatusVal(e.target.value)}
                className="w-full px-3 py-2 bg-[#0d0d0d] border border-glass rounded-lg text-sm text-white focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
              >
                <option value="discovered">Discovered</option>
                <option value="contacted">Contacted</option>
                <option value="converted">Converted</option>
                <option value="lost">Lost</option>
              </select>
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
              disabled={loading}
              className="flex-1 py-2.5 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black font-semibold text-sm rounded-lg transition-all active:scale-[0.98] duration-300 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default LeadModal;
