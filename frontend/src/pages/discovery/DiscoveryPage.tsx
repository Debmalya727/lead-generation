import React, { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { DiscoveredLead, JobStatusResponse, discoveryApi } from "../../api/discovery";

export const DiscoveryPage: React.FC = () => {
  const { logout } = useAuth();

  // Search input parameters
  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("");
  const [selectedProviders, setSelectedProviders] = useState<string[]>(["google_maps"]);
  const [websiteFilter, setWebsiteFilter] = useState("all");
  const [limit, setLimit] = useState<number>(20);

  // Active scrape job states
  const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
  const [discoveredLeads, setDiscoveredLeads] = useState<DiscoveredLead[]>([]);
  const [selectedLeadIds, setSelectedLeadIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingLeads, setSavingLeads] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  // Poll loop reference
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const toggleProvider = (p: string) => {
    setSelectedProviders((prev) =>
      prev.includes(p) ? prev.filter((item) => item !== p) : [...prev, p]
    );
  };

  const handleStartDiscovery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedProviders.length === 0) {
      setError("Please select at least one lead discovery provider.");
      return;
    }

    setError(null);
    setInfoMessage(null);
    setLoading(true);
    setDiscoveredLeads([]);
    setSelectedLeadIds([]);

    try {
      const job = await discoveryApi.startDiscovery({
        keyword: keyword.trim(),
        location: location.trim(),
        providers: selectedProviders,
        website_filter: websiteFilter,
        limit: Number(limit) || 20,
      });
      setActiveJob(job);
      startPolling(job.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start lead discovery process.");
      setLoading(false);
    }
  };

  const startPolling = (jobId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const job = await discoveryApi.getJobStatus(jobId);
        setActiveJob(job);

        if (job.status === "completed") {
          stopPolling();
          const results = await discoveryApi.getJobResults(jobId);
          setDiscoveredLeads(results);
          setLoading(false);
        } else if (job.status === "failed") {
          stopPolling();
          setError(job.error_message || "Discovery job execution failed.");
          setLoading(false);
        } else if (job.status === "cancelled") {
          stopPolling();
          setInfoMessage("Discovery job was successfully cancelled.");
          setLoading(false);
        }
      } catch (err) {
        console.error("Error polling discovery status:", err);
      }
    }, 1500); // Poll every 1.5 seconds
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  const handleCancelJob = async () => {
    if (!activeJob) return;
    try {
      await discoveryApi.cancelJob(activeJob.id);
      setInfoMessage("Cancellation request submitted.");
    } catch (err) {
      alert("Failed to submit cancellation command.");
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedLeadIds(discoveredLeads.map((l) => l.id));
    } else {
      setSelectedLeadIds([]);
    }
  };

  const handleSelectLead = (id: string) => {
    setSelectedLeadIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSaveSelected = async () => {
    if (!activeJob || selectedLeadIds.length === 0) return;
    setSavingLeads(true);
    setError(null);
    setInfoMessage(null);

    try {
      const res = await discoveryApi.saveLeads(activeJob.id, selectedLeadIds);
      setInfoMessage(`Successfully saved ${res.saved_count} leads to your pipeline database! (Skipped ${res.skipped_count} duplicate entries).`);
      setSelectedLeadIds([]);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to persist selected leads.");
    } finally {
      setSavingLeads(false);
    }
  };

  const handleExportCsv = () => {
    if (discoveredLeads.length === 0) return;
    try {
      // Build raw CSV text
      const csvRows = [
        ["Name", "Website", "Phone", "Email", "Location", "Score", "Provider"],
        ...discoveredLeads.map((l) => [
          l.name,
          l.website || "",
          l.phone || "",
          l.email || "",
          l.location || "",
          l.score !== undefined ? String(l.score) : "",
          l.provider,
        ]),
      ];
      
      const csvContent = "data:text/csv;charset=utf-8," 
        + csvRows.map((e) => e.map(val => `"${val.replace(/"/g, '""')}"`).join(",")).join("\n");
        
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `discovery_results_${keyword.replace(/\s+/g, "_")}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Failed to export discovery leads to CSV file.");
    }
  };

  const getProviderLabel = (p: string) => {
    switch (p) {
      case "google_maps": return "Google Maps";
      case "justdial": return "JustDial";
      case "indiamart": return "IndiaMART";
      case "tradeindia": return "TradeIndia";
      default: return p;
    }
  };

  return (
    <div className="relative min-h-screen bg-[#030303] text-white font-sans overflow-x-hidden pb-12">
      {/* Decorative Persian hologram background glow */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-tr from-persian-indigo via-transparent to-persian-turquoise opacity-20 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-gradient-to-tr from-persian-indigo via-transparent to-persian-turquoise opacity-10 rounded-full blur-[130px] pointer-events-none" />
      
      {/* Dynamic Grid Layout */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.012)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.012)_1px,transparent_1px)] bg-[size:45px_45px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="relative z-10 border-b border-glass bg-black/40 backdrop-blur-md px-6 md:px-12 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-persian-indigo to-persian-turquoise flex items-center justify-center font-bold text-black font-display">
            LF
          </div>
          <div>
            <h1 className="text-lg font-display font-extrabold tracking-tight">
              LeadForge<span className="text-persian-turquoise">AI</span>
            </h1>
            <span className="text-[10px] text-neutral-500 font-mono tracking-widest uppercase">WORKSPACE PORTAL</span>
          </div>
        </div>

        <nav className="flex gap-3 items-center font-mono">
          <Link
            to="/"
            className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all"
          >
            ← LEADS
          </Link>
          <Link
            to="/intelligence"
            className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all"
          >
            🧠 INTELLIGENCE
          </Link>
          <Link
            to="/scoring"
            className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all"
          >
            🎯 SCORING
          </Link>
          <Link
            to="/outreach"
            className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all"
          >
            ✉️ OUTREACH
          </Link>
          <button
            onClick={logout}
            className="px-3.5 py-1.5 border border-glass hover:border-red-500/40 hover:bg-red-500/10 text-neutral-400 hover:text-red-400 text-xs rounded transition-all"
          >
            DISCONNECT
          </button>
        </nav>
      </header>

      {/* Main Workspace Layout */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 mt-8">
        <section className="mb-6">
          <h2 className="text-2xl font-display font-extrabold tracking-tight text-white">Lead Discovery Engine</h2>
          <p className="text-xs text-neutral-400 mt-1">
            Query global directory networks and download target leads in real-time
          </p>
        </section>

        {error && (
          <div className="mb-6 p-4 rounded-lg border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-mono">
            ⚠️ {error}
          </div>
        )}

        {infoMessage && (
          <div className="mb-6 p-4 rounded-lg border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-xs font-mono">
            ℹ️ {infoMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Query Form Section */}
          <aside className="lg:col-span-1 border border-glass rounded-xl bg-glass backdrop-blur-xl p-5 space-y-6">
            <h3 className="text-xs font-mono uppercase text-neutral-400 tracking-wider">Search Parameters</h3>
            
            <form onSubmit={handleStartDiscovery} className="space-y-4">
              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Target Keyword
                </label>
                <input
                  type="text"
                  required
                  value={keyword}
                  disabled={loading}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="e.g. HVAC, Dental, Cafe"
                  className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                />
              </div>

              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Search Location
                </label>
                <input
                  type="text"
                  required
                  value={location}
                  disabled={loading}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Chicago, Mumbai"
                  className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                />
              </div>

              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Type of Leads
                </label>
                <select
                  value={websiteFilter}
                  onChange={(e) => setWebsiteFilter(e.target.value)}
                  disabled={loading}
                  className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                >
                  <option value="all">All Leads (With & Without Website)</option>
                  <option value="without_website">Without Website Only</option>
                  <option value="with_website">With Website Only</option>
                </select>
              </div>

              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Max Leads to Extract
                </label>
                <select
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  disabled={loading}
                  className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                >
                  <option value={10}>10 Leads</option>
                  <option value={20}>20 Leads</option>
                  <option value={50}>50 Leads</option>
                  <option value={100}>100 Leads</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest block mb-1">
                  Directory Networks
                </label>
                
                {["google_maps", "justdial", "indiamart", "tradeindia"].map((provider) => (
                  <label key={provider} className="flex items-center gap-2.5 text-xs text-neutral-300 font-mono select-none cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedProviders.includes(provider)}
                      disabled={loading}
                      onChange={() => toggleProvider(provider)}
                      className="rounded bg-black border-glass text-persian-turquoise focus:ring-persian-turquoise"
                    />
                    {getProviderLabel(provider)}
                  </label>
                ))}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-4 py-2.5 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black font-semibold text-xs rounded-lg transition-all active:scale-[0.98] duration-300 flex items-center justify-center gap-2"
              >
                {loading ? "SEARCHING..." : "TRIGGER ENGINE"}
              </button>
            </form>
          </aside>

          {/* Results Workspace Grid */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Live Progress Bar Card */}
            {activeJob && (
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 text-left space-y-4">
                <div className="flex justify-between items-center text-xs font-mono">
                  <div>
                    STATUS: <span className={`font-bold ${
                      activeJob.status === "completed"
                        ? "text-emerald-400"
                        : activeJob.status === "failed"
                        ? "text-red-400"
                        : activeJob.status === "cancelled"
                        ? "text-zinc-500"
                        : "text-persian-turquoise animate-pulse"
                    }`}>{activeJob.status.toUpperCase()}</span>
                  </div>
                  <div>PROGRESS: <span className="font-bold text-white">{activeJob.progress}%</span></div>
                </div>

                {/* Progress bar line */}
                <div className="w-full bg-black/50 border border-glass h-3.5 rounded-full overflow-hidden p-0.5">
                  <div
                    style={{ width: `${activeJob.progress}%` }}
                    className="h-full bg-gradient-to-r from-persian-indigo to-persian-turquoise rounded-full transition-all duration-500 ease-out"
                  />
                </div>

                <div className="flex justify-between items-center pt-2 text-[10px] font-mono text-neutral-400">
                  <div>Job ID: <span className="text-white">{activeJob.id}</span></div>
                  {activeJob.status === "running" && (
                    <button
                      onClick={handleCancelJob}
                      className="px-2.5 py-1 border border-red-500/30 hover:border-red-500/60 hover:bg-red-500/10 text-red-400 rounded transition-all"
                    >
                      CANCEL EXTRACTION
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Results Table Section */}
            {discoveredLeads.length > 0 && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-mono text-neutral-400">
                    DISCOVERED RESULTS ({discoveredLeads.length})
                  </h3>
                  <div className="flex gap-3">
                    <button
                      onClick={handleExportCsv}
                      className="px-3.5 py-1.5 border border-glass bg-glass-hover text-xs font-mono text-neutral-300 hover:text-white rounded-lg transition-all"
                    >
                      📤 EXPORT JOB CSV
                    </button>
                    <button
                      onClick={handleSaveSelected}
                      disabled={selectedLeadIds.length === 0 || savingLeads}
                      className="px-3.5 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-black font-semibold text-xs rounded-lg transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {savingLeads ? "SAVING..." : `SAVE SELECTED (${selectedLeadIds.length})`}
                    </button>
                  </div>
                </div>

                {/* Scrape Table */}
                <div className="w-full overflow-x-auto border border-glass rounded-xl bg-glass backdrop-blur-xl">
                  <table className="w-full text-left border-collapse font-sans text-sm">
                    <thead>
                      <tr className="border-b border-glass bg-glass-hover text-xs font-mono text-neutral-400 uppercase tracking-wider">
                        <th className="py-4 px-6 text-center w-12">
                          <input
                            type="checkbox"
                            checked={selectedLeadIds.length === discoveredLeads.length}
                            onChange={handleSelectAll}
                            className="rounded bg-black border-glass text-persian-turquoise focus:ring-persian-turquoise"
                          />
                        </th>
                        <th className="py-4 px-6">Company Name</th>
                        <th className="py-4 px-6">Email</th>
                        <th className="py-4 px-6">Phone</th>
                        <th className="py-4 px-6">Location</th>
                        <th className="py-4 px-6 text-center">Score</th>
                        <th className="py-4 px-6 text-right">Provider</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-glass/50 font-mono text-xs text-neutral-300">
                      {discoveredLeads.map((lead) => (
                        <tr key={lead.id} className="hover:bg-glass-hover/20 transition-colors">
                          <td className="py-4 px-6 text-center">
                            <input
                              type="checkbox"
                              checked={selectedLeadIds.includes(lead.id)}
                              onChange={() => handleSelectLead(lead.id)}
                              className="rounded bg-black border-glass text-persian-turquoise focus:ring-persian-turquoise"
                            />
                          </td>
                          <td className="py-4 px-6 font-sans font-medium text-white text-sm">
                            {lead.name}
                            {lead.website && (
                              <a
                                href={lead.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block text-xs text-persian-turquoise hover:underline mt-0.5 font-mono"
                              >
                                {lead.website.replace(/(^\w+:|^)\/\//, "")}
                              </a>
                            )}
                          </td>
                          <td className="py-4 px-6">{lead.email || "—"}</td>
                          <td className="py-4 px-6">{lead.phone || "—"}</td>
                          <td className="py-4 px-6 font-sans">{lead.location || "—"}</td>
                          <td className="py-4 px-6 text-center">
                            {lead.score !== undefined ? (
                              <span className="px-2 py-0.5 rounded bg-black/40 border border-glass">
                                {lead.score}
                              </span>
                            ) : "—"}
                          </td>
                          <td className="py-4 px-6 text-right">
                            <span className="px-2 py-0.5 rounded-full border border-glass bg-glass text-[10px] uppercase text-neutral-400">
                              {getProviderLabel(lead.provider)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Empty view before search */}
            {!activeJob && (
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-12 text-center text-neutral-500 font-mono text-xs">
                CHOOSE PARAMETERS AND TRIGGER DISCOVERY ENGINE TO QUERY LEAD NETWORKS
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
export default DiscoveryPage;
