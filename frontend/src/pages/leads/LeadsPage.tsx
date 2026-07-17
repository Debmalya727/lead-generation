import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { Lead, LeadCreate, LeadUpdate, leadsApi } from "../../api/leads";
import { LeadTable } from "../../components/leads/LeadTable";
import { LeadModal } from "../../components/leads/LeadModal";
import { ImportModal } from "../../components/leads/ImportModal";

export const LeadsPage: React.FC = () => {
  const { user, logout } = useAuth();
  
  // Data list states
  const [leads, setLeads] = useState<Lead[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [limit] = useState(10); // Standard pagination limit per page
  
  // Queries, filters, and sorting parameters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [minScore, setMinScore] = useState<number | "">("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Modal displays state controller
  const [isLeadModalOpen, setIsLeadModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);

  const fetchLeads = async () => {
    try {
      const data = await leadsApi.getLeads({
        page,
        limit,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        min_score: minScore !== "" ? minScore : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setLeads(data.items);
      setTotalCount(data.total_count);
      setPages(data.pages);
    } catch (error) {
      console.error("Failed to load workspace leads:", error);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [page, statusFilter, minScore, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLeads();
  };

  const handleResetFilters = () => {
    setSearch("");
    setStatusFilter("");
    setMinScore("");
    setSortBy("created_at");
    setSortOrder("desc");
    setPage(1);
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const handleAddClick = () => {
    setEditingLead(null);
    setIsLeadModalOpen(true);
  };

  const handleEditClick = (lead: Lead) => {
    setEditingLead(lead);
    setIsLeadModalOpen(true);
  };

  const handleDeleteClick = async (lead: Lead) => {
    if (window.confirm(`Are you sure you want to permanently delete lead record: "${lead.name}"?`)) {
      try {
        await leadsApi.deleteLead(lead.id);
        fetchLeads();
      } catch (error) {
        alert("Failed to delete lead from workspace database.");
      }
    }
  };

  const handleLeadFormSubmit = async (leadData: LeadCreate) => {
    if (editingLead) {
      await leadsApi.updateLead(editingLead.id, leadData as LeadUpdate);
    } else {
      await leadsApi.createLead(leadData);
    }
    fetchLeads();
  };

  const handleImportSubmit = async (file: File) => {
    const res = await leadsApi.importLeadsCsv(file);
    fetchLeads();
    return res;
  };

  const handleExportCsv = async () => {
    try {
      const blob = await leadsApi.exportLeadsCsv(statusFilter || undefined);
      // Create download trigger
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `leadforge_export_${statusFilter || "all"}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert("Failed to generate and download CSV export.");
    }
  };

  return (
    <div className="relative min-h-screen bg-[#030303] text-white font-sans overflow-x-hidden pb-12">
      {/* Decorative Persian-inspired architectural background glow */}
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

        {user && (
          <div className="flex items-center gap-3">
            <nav className="hidden md:flex items-center gap-2">
              <Link
                to="/discovery"
                className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all"
              >
                🔍 DISCOVERY
              </Link>
              <Link
                to="/intelligence"
                className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all"
              >
                🧠 INTELLIGENCE
              </Link>
              <Link
                to="/scoring"
                className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all"
              >
                🎯 SCORING
              </Link>
              <Link
                to="/outreach"
                className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all"
              >
                ✉️ OUTREACH
              </Link>
            </nav>
            <div className="hidden md:block text-right">
              <p className="text-xs text-neutral-300 font-medium">{user.full_name}</p>
              <p className="text-[10px] text-neutral-500 font-mono">{user.email}</p>
            </div>
            <button
              onClick={logout}
              className="px-3.5 py-1.5 border border-glass hover:border-red-500/40 hover:bg-red-500/10 text-neutral-400 hover:text-red-400 font-mono text-xs rounded transition-all"
            >
              DISCONNECT
            </button>
          </div>
        )}
      </header>

      {/* Main Workspace Grid */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 mt-8">
        
        {/* Actions row */}
        <section className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-display font-extrabold tracking-tight text-white">Lead Management</h2>
            <p className="text-xs text-neutral-400 mt-1">
              Currently indexing <span className="text-persian-turquoise font-mono font-bold">{totalCount}</span> total leads
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              to="/discovery"
              className="px-4 py-2 border border-glass bg-glass-hover hover:border-persian-turquoise/40 text-persian-turquoise hover:text-white text-xs font-mono rounded-lg transition-all flex items-center justify-center"
            >
              🔍 DISCOVERY ENGINE
            </Link>
            <Link
              to="/intelligence"
              className="px-4 py-2 border border-glass bg-glass-hover hover:border-persian-turquoise/40 text-persian-turquoise hover:text-white text-xs font-mono rounded-lg transition-all flex items-center justify-center"
            >
              🧠 INTELLIGENCE
            </Link>
            <button
              onClick={handleExportCsv}
              className="px-4 py-2 border border-glass bg-glass-hover hover:border-persian-turquoise/40 text-neutral-300 hover:text-white text-xs font-mono rounded-lg transition-all"
            >
              📤 EXPORT CSV
            </button>
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="px-4 py-2 border border-glass bg-glass-hover hover:border-persian-turquoise/40 text-neutral-300 hover:text-white text-xs font-mono rounded-lg transition-all"
            >
              📥 IMPORT CSV
            </button>
            <button
              onClick={handleAddClick}
              className="px-4 py-2 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black font-semibold text-xs rounded-lg shadow-glass transition-all duration-300 active:scale-[0.98]"
            >
              + ADD NEW LEAD
            </button>
          </div>
        </section>

        {/* Filter Sidebar & Table layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Filtering Sidebar */}
          <aside className="lg:col-span-1 border border-glass rounded-xl bg-glass backdrop-blur-xl p-5 space-y-6">
            <h3 className="text-xs font-mono uppercase text-neutral-400 tracking-wider">Search & Filters</h3>
            
            <form onSubmit={handleSearchSubmit} className="space-y-4">
              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Keyword Query
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search query..."
                    className="w-full pl-3 pr-8 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                  />
                  <button type="submit" className="absolute right-2.5 top-2.5 text-xs opacity-50 hover:opacity-100">
                    🔍
                  </button>
                </div>
              </div>
            </form>

            <div className="space-y-4">
              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Status Category
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(1);
                  }}
                  className="w-full px-3 py-2 bg-[#0c0c0c] border border-glass rounded-lg text-xs text-white focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                >
                  <option value="">All Categories</option>
                  <option value="discovered">Discovered</option>
                  <option value="contacted">Contacted</option>
                  <option value="converted">Converted</option>
                  <option value="lost">Lost</option>
                </select>
              </div>

              <div className="space-y-1.5 text-left">
                <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  Min Quality Score
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minScore}
                  onChange={(e) => {
                    setMinScore(e.target.value === "" ? "" : Number(e.target.value));
                    setPage(1);
                  }}
                  placeholder="e.g. 50"
                  className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise transition-all font-mono"
                />
              </div>
            </div>

            <button
              onClick={handleResetFilters}
              className="w-full py-2 border border-glass hover:bg-glass text-neutral-400 hover:text-white text-xs font-mono rounded-lg transition-all"
            >
              🔄 RESET ALL FILTERS
            </button>
          </aside>

          {/* Table list view container */}
          <div className="lg:col-span-3 space-y-4">
            <LeadTable
              leads={leads}
              onEdit={handleEditClick}
              onDelete={handleDeleteClick}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSort={handleSort}
            />

            {/* Pagination controller */}
            {pages > 1 && (
              <div className="flex items-center justify-between px-2 font-mono text-xs text-neutral-400 mt-4">
                <span>Page {page} of {pages}</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(p - 1, 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 border border-glass rounded bg-glass hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    PREV
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(p + 1, pages))}
                    disabled={page === pages}
                    className="px-3 py-1.5 border border-glass rounded bg-glass hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    NEXT
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Modal Dialog Portals */}
      <LeadModal
        isOpen={isLeadModalOpen}
        onClose={() => setIsLeadModalOpen(false)}
        onSubmit={handleLeadFormSubmit}
        lead={editingLead}
      />

      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImport={handleImportSubmit}
      />
    </div>
  );
};
export default LeadsPage;
