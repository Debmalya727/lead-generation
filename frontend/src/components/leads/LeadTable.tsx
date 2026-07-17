import React from "react";
import { Lead } from "../../api/leads";

interface LeadTableProps {
  leads: Lead[];
  onEdit: (lead: Lead) => void;
  onDelete: (lead: Lead) => void;
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSort: (column: string) => void;
}

export const LeadTable: React.FC<LeadTableProps> = ({
  leads,
  onEdit,
  onDelete,
  sortBy,
  sortOrder,
  onSort,
}) => {
  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "converted":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "contacted":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "lost":
        return "bg-zinc-800 text-zinc-400 border-zinc-700/50";
      case "discovered":
      default:
        return "bg-persian-indigo/20 text-persian-turquoise border-persian-turquoise/20";
    }
  };

  const renderSortIndicator = (column: string) => {
    if (sortBy !== column) return null;
    return sortOrder === "asc" ? " ▴" : " ▾";
  };

  return (
    <div className="w-full overflow-x-auto border border-glass rounded-xl bg-glass backdrop-blur-xl">
      <table className="w-full text-left border-collapse font-sans text-sm">
        <thead>
          <tr className="border-b border-glass bg-glass-hover text-xs font-mono text-neutral-400 uppercase tracking-wider">
            <th
              onClick={() => onSort("name")}
              className="py-4 px-6 cursor-pointer select-none hover:text-white transition-colors"
            >
              Company Name{renderSortIndicator("name")}
            </th>
            <th className="py-4 px-6">Email</th>
            <th className="py-4 px-6">Phone</th>
            <th className="py-4 px-6">Location</th>
            <th
              onClick={() => onSort("score")}
              className="py-4 px-6 cursor-pointer select-none hover:text-white transition-colors text-center"
            >
              Quality Score{renderSortIndicator("score")}
            </th>
            <th
              onClick={() => onSort("status")}
              className="py-4 px-6 cursor-pointer select-none hover:text-white transition-colors text-center"
            >
              Status{renderSortIndicator("status")}
            </th>
            <th className="py-4 px-6 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-glass/50">
          {leads.length === 0 ? (
            <tr>
              <td colSpan={7} className="py-12 text-center text-neutral-500 font-mono text-xs">
                NO ACTIVE LEADS FOUND IN WORKSPACE
              </td>
            </tr>
          ) : (
            leads.map((lead) => (
              <tr
                key={lead.id}
                className="hover:bg-glass-hover/30 transition-colors group"
              >
                <td className="py-4 px-6 font-medium text-white">
                  <div>
                    {lead.name}
                    {lead.website && (
                      <a
                        href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-xs text-persian-turquoise hover:underline mt-0.5 font-mono"
                      >
                        {lead.website.replace(/(^\w+:|^)\/\//, "")}
                      </a>
                    )}
                  </div>
                </td>
                <td className="py-4 px-6 font-mono text-xs text-neutral-300">
                  {lead.email || <span className="text-neutral-600">—</span>}
                </td>
                <td className="py-4 px-6 font-mono text-xs text-neutral-300">
                  {lead.phone || <span className="text-neutral-600">—</span>}
                </td>
                <td className="py-4 px-6 text-neutral-300">
                  {lead.location || <span className="text-neutral-600">—</span>}
                </td>
                <td className="py-4 px-6 text-center">
                  {lead.score !== undefined && lead.score !== null ? (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-black/40 border border-glass font-mono text-xs text-white">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          lead.score >= 75
                            ? "bg-emerald-400"
                            : lead.score >= 50
                            ? "bg-amber-400"
                            : "bg-red-400"
                        }`}
                      />
                      {lead.score}
                    </div>
                  ) : (
                    <span className="text-neutral-600 font-mono text-xs">—</span>
                  )}
                </td>
                <td className="py-4 px-6 text-center">
                  <span
                    className={`inline-flex px-2.5 py-1 rounded-full border text-xs font-mono uppercase tracking-wider ${getStatusBadgeClass(
                      lead.status
                    )}`}
                  >
                    {lead.status}
                  </span>
                </td>
                <td className="py-4 px-6 text-right">
                  <div className="flex justify-end gap-3 opacity-80 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onEdit(lead)}
                      className="px-2.5 py-1 text-xs font-mono text-neutral-400 hover:text-persian-turquoise hover:bg-glass border border-transparent hover:border-glass rounded transition-all"
                    >
                      EDIT
                    </button>
                    <button
                      onClick={() => onDelete(lead)}
                      className="px-2.5 py-1 text-xs font-mono text-neutral-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 rounded transition-all"
                    >
                      DELETE
                    </button>
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
