import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { schedulerApi, ScheduledJob, JobHistory } from "../../api/scheduler";
import { NotificationBell } from "../../components/NotificationBell";

export const SchedulerPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<ScheduledJob | null>(null);
  const [history, setHistory] = useState<JobHistory[]>([]);
  const [runningJobId, setRunningJobId] = useState<string | null>(null);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const data = await schedulerApi.listJobs();
      setJobs(data);
      if (data.length > 0 && !selectedJob) {
        selectJob(data[0]);
      }
    } catch {}
  };

  const selectJob = async (job: ScheduledJob) => {
    setSelectedJob(job);
    try {
      const histData = await schedulerApi.getHistory(job.job_id);
      setHistory(histData);
    } catch {}
  };

  const handleRunNow = async (job: ScheduledJob) => {
    setRunningJobId(job.job_id);
    try {
      await schedulerApi.runJobNow(job.job_id);
      fetchJobs();
      if (selectedJob?.job_id === job.job_id) {
        selectJob(job);
      }
    } catch (err: any) {
      alert(`Error running job: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setRunningJobId(null);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Background Scheduler Workspace</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <NotificationBell />
          <button onClick={() => navigate("/plugins")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>🔌 Plugins</button>
          <button onClick={() => navigate("/chat")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>💬 Chat CRM</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 400px", flex: 1, padding: "2rem", gap: "1.5rem" }}>
        {/* Left Column: Scheduled Jobs List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#e2e8f0" }}>Recurring & Scheduled Background Jobs ({jobs.length})</div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {jobs.map(job => (
              <div key={job.job_id} onClick={() => selectJob(job)} style={{ padding: "1.25rem", borderRadius: "10px", border: `1px solid ${selectedJob?.job_id === job.job_id ? "rgba(99,102,241,0.5)" : "rgba(99,102,241,0.2)"}`, background: selectedJob?.job_id === job.job_id ? "rgba(99,102,241,0.12)" : "rgba(15,23,42,0.8)", display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}>
                <div>
                  <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#e2e8f0" }}>{job.name}</div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.25rem" }}>{job.description}</div>
                  <div style={{ fontSize: "0.72rem", color: "#a5b4fc", marginTop: "0.4rem" }}>Cron: <code style={{ color: "#38bdf8" }}>{job.cron_expression || "Interval"}</code> | Workflow: <code style={{ color: "#34d399" }}>{job.workflow_template_id}</code></div>
                </div>

                <button onClick={(e) => { e.stopPropagation(); handleRunNow(job); }} disabled={runningJobId === job.job_id} style={{ padding: "0.5rem 1rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, fontSize: "0.78rem", cursor: runningJobId === job.job_id ? "not-allowed" : "pointer" }}>
                  {runningJobId === job.job_id ? "Running…" : "Run Now ⚡"}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Job Run History */}
        <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "10px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#a5b4fc" }}>Execution Run History</div>
          {selectedJob && (
            <div style={{ fontSize: "0.75rem", color: "#64748b", borderBottom: "1px solid rgba(99,102,241,0.15)", paddingBottom: "0.5rem" }}>
              Target Job: <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{selectedJob.name}</span>
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {history.length === 0 ? (
              <div style={{ color: "#64748b", fontSize: "0.8rem", textAlign: "center", marginTop: "2rem" }}>No historical runs found for this job.</div>
            ) : (
              history.map(h => (
                <div key={h.history_id} style={{ padding: "0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.15)", background: "rgba(30,41,59,0.5)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", fontWeight: 700 }}>
                    <span style={{ color: h.status === "completed" ? "#34d399" : "#f87171" }}>● {h.status.toUpperCase()}</span>
                    <span style={{ color: "#a5b4fc" }}>{h.duration_ms.toFixed(1)} ms</span>
                  </div>
                  <div style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#94a3b8", marginTop: "0.3rem" }}>Exec ID: {h.workflow_execution_id}</div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.2rem" }}>{new Date(h.started_at).toLocaleString()}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchedulerPage;
