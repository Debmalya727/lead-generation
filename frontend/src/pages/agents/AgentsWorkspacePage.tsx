import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  agentsApi,
  AgentJob,
  AgentEvent,
  ExecutiveReport,
  AgentRegistryItem,
  AgentRunParams,
} from '../../api/agents';
import {
  collaborationApi,
  AgentMessageItem,
  AgentArtifactItem,
  ConsensusDecisionItem,
  CollaborationMetrics,
  CollaborationSummary,
} from '../../api/collaboration';

// ──────────────────────────────────────────────────────────────────────────────
// Business pipeline agent configuration
// ──────────────────────────────────────────────────────────────────────────────
const PIPELINE_AGENTS = [
  { id: 'research_agent',       label: 'Research',      icon: '🔬', task: 'task_01_research',  color: '#6366f1' },
  { id: 'memory_agent',         label: 'Memory',        icon: '🧠', task: 'task_02_memory',    color: '#8b5cf6' },
  { id: 'sales_strategy_agent', label: 'Strategy',      icon: '📊', task: 'task_03_strategy',  color: '#06b6d4' },
  { id: 'outreach_agent',       label: 'Outreach',      icon: '✉️',  task: 'task_04_outreach',  color: '#10b981' },
  { id: 'review_agent',         label: 'Review',        icon: '🔍', task: 'task_05_review',    color: '#f59e0b' },
  { id: 'executive_agent',      label: 'Executive',     icon: '🎯', task: 'task_06_executive', color: '#ef4444' },
];

const statusColor = (s: string) => {
  switch (s) {
    case 'completed': return '#10b981';
    case 'running':   return '#6366f1';
    case 'failed':    return '#ef4444';
    case 'pending':   return '#64748b';
    case 'paused_for_approval': return '#f59e0b';
    default:          return '#64748b';
  }
};
const statusBg = (s: string) => {
  switch (s) {
    case 'completed': return 'rgba(16,185,129,0.12)';
    case 'running':   return 'rgba(99,102,241,0.18)';
    case 'failed':    return 'rgba(239,68,68,0.12)';
    case 'pending':   return 'rgba(100,116,139,0.1)';
    case 'paused_for_approval': return 'rgba(245,158,11,0.15)';
    default:          return 'rgba(100,116,139,0.1)';
  }
};
const confidenceColor = (c: number) => c >= 80 ? '#10b981' : c >= 60 ? '#f59e0b' : '#ef4444';
const elapsedSince = (iso: string) => {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  return `${Math.floor(secs / 60)}m ago`;
};

type WorkspaceTab = 'pipeline' | 'messages' | 'artifacts' | 'consensus' | 'metrics' | 'events' | 'report' | 'registry';

export const AgentsWorkspacePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // ── Form state ──
  const [goal, setGoal] = useState('');
  const [leadId, setLeadId] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [executionMode, setExecutionMode] = useState<'auto' | 'business_pipeline'>('business_pipeline');

  // ── Data state ──
  const [jobs, setJobs]                   = useState<AgentJob[]>([]);
  const [selectedJob, setSelectedJob]     = useState<AgentJob | null>(null);
  const [events, setEvents]               = useState<AgentEvent[]>([]);
  const [report, setReport]               = useState<ExecutiveReport | null>(null);
  const [registry, setRegistry]           = useState<AgentRegistryItem[]>([]);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  // ── Collaboration Data ──
  const [messages, setMessages]           = useState<AgentMessageItem[]>([]);
  const [artifacts, setArtifacts]         = useState<AgentArtifactItem[]>([]);
  const [consensus, setConsensus]         = useState<ConsensusDecisionItem[]>([]);
  const [_summary, setSummary]            = useState<CollaborationSummary | null>(null);
  const [metrics, setMetrics]             = useState<CollaborationMetrics | null>(null);

  // ── UI state ──
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab]   = useState<WorkspaceTab>('pipeline');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    agentsApi.listRegisteredAgents().then(setRegistry).catch(() => {});
    fetchJobs();
  }, []);

  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => {
      fetchJobs();
      if (selectedJob && !['completed', 'failed', 'cancelled'].includes(selectedJob.status)) {
        fetchJobDetails(selectedJob.job_id);
      }
    }, 4000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [selectedJob?.job_id, selectedJob?.status]);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await agentsApi.listJobs({ limit: 20 });
      setJobs(data.items);
    } catch { /* silent */ }
  }, []);

  const fetchJobDetails = useCallback(async (jobId: string) => {
    try {
      const [jobData, eventData, msgData, artData, consData, sumData, metData] = await Promise.all([
        agentsApi.getJob(jobId),
        agentsApi.getEvents(jobId),
        collaborationApi.getMessages(jobId).catch(() => []),
        collaborationApi.getArtifacts(jobId).catch(() => []),
        collaborationApi.getConsensus(jobId).catch(() => []),
        collaborationApi.getSummary(jobId).catch(() => null),
        collaborationApi.getMetrics(jobId).catch(() => null),
      ]);
      setSelectedJob(jobData);
      setEvents(eventData);
      setMessages(msgData);
      setArtifacts(artData);
      setConsensus(consData);
      setSummary(sumData);
      setMetrics(metData);

      if (jobData.status === 'completed') {
        agentsApi.getReport(jobId).then(setReport).catch(() => setReport(null));
      }
    } catch { /* silent */ }
  }, []);

  const handleSelectJob = (job: AgentJob) => {
    setSelectedJob(job);
    setReport(null);
    setExpandedAgent(null);
    fetchJobDetails(job.job_id);
  };

  const handleSubmitGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    setSubmitting(true);
    setErrorMessage(null);
    try {
      const params: AgentRunParams = {
        goal: goal.trim(),
        execution_mode: executionMode,
        lead_id: leadId.trim() || undefined,
        company_name: companyName.trim() || undefined,
      };
      const job = await agentsApi.submitJob(params);
      setJobs(prev => [job, ...prev]);
      setSelectedJob(job);
      setReport(null);
      setActiveTab('pipeline');
      setGoal('');
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || 'Failed to submit agent job.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!selectedJob) return;
    try { await agentsApi.cancelJob(selectedJob.job_id); fetchJobDetails(selectedJob.job_id); } catch {}
  };

  const handleRetry = async () => {
    if (!selectedJob) return;
    try { await agentsApi.retryJob(selectedJob.job_id); fetchJobDetails(selectedJob.job_id); } catch {}
  };

  const getTaskForAgent = (agentTaskId: string) => {
    return selectedJob?.plan?.tasks.find(t => t.task_id === agentTaskId);
  };

  const isPipelineJob = selectedJob?.plan?.task_graph_json?.pipeline_type === 'business_pipeline'
    || (selectedJob?.plan?.tasks.some(t => t.agent_name === 'research_agent'));

  return (
    <div style={{ minHeight: '100vh', background: '#0a0f1e', color: '#e2e8f0', fontFamily: "'Inter', sans-serif", display: 'flex', flexDirection: 'column' }}>
      {/* ── Top Nav ── */}
      <nav style={{ background: 'rgba(15,23,42,0.95)', borderBottom: '1px solid rgba(99,102,241,0.2)', padding: '0 2rem', height: '64px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            LeadForgeAI
          </div>
          <div style={{ color: '#64748b', fontSize: '0.85rem' }}>/ Multi-Agent Collaboration Engine</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button onClick={() => navigate('/leads')} style={{ background: 'none', border: '1px solid rgba(99,102,241,0.3)', color: '#94a3b8', padding: '0.4rem 1rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' }}>← Leads</button>
          <span style={{ color: '#64748b', fontSize: '0.85rem' }}>{user?.email}</span>
          <button onClick={logout} style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171', padding: '0.4rem 1rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' }}>Logout</button>
        </div>
      </nav>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', flex: 1, minHeight: 0 }}>
        {/* ── Left Sidebar ── */}
        <aside style={{ background: 'rgba(15,23,42,0.8)', borderRight: '1px solid rgba(99,102,241,0.15)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem', borderBottom: '1px solid rgba(99,102,241,0.15)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>New Agent Job</div>

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              {(['business_pipeline', 'auto'] as const).map(mode => (
                <button key={mode} onClick={() => setExecutionMode(mode)} style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', border: `1px solid ${executionMode === mode ? '#6366f1' : 'rgba(99,102,241,0.2)'}`, background: executionMode === mode ? 'rgba(99,102,241,0.2)' : 'transparent', color: executionMode === mode ? '#a5b4fc' : '#64748b', fontSize: '0.72rem', fontWeight: 600, cursor: 'pointer' }}>
                  {mode === 'business_pipeline' ? '🏢 Business Pipeline' : '🤖 Auto (LLM)'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmitGoal} style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {executionMode === 'business_pipeline' && (
                <>
                  <input value={leadId} onChange={e => setLeadId(e.target.value)} placeholder="Lead ID (optional)" style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(99,102,241,0.25)', background: 'rgba(30,41,59,0.6)', color: '#e2e8f0', fontSize: '0.8rem', outline: 'none' }} />
                  <input value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="Company name (optional)" style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(99,102,241,0.25)', background: 'rgba(30,41,59,0.6)', color: '#e2e8f0', fontSize: '0.8rem', outline: 'none' }} />
                </>
              )}
              <textarea value={goal} onChange={e => setGoal(e.target.value)} placeholder="Describe your sales intelligence goal…" rows={3} style={{ padding: '0.65rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(99,102,241,0.3)', background: 'rgba(30,41,59,0.6)', color: '#e2e8f0', fontSize: '0.82rem', resize: 'none', outline: 'none', lineHeight: 1.5 }} />
              {errorMessage && <div style={{ color: '#f87171', fontSize: '0.75rem', padding: '0.5rem', background: 'rgba(239,68,68,0.1)', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.2)' }}>{errorMessage}</div>}
              <button type="submit" disabled={submitting || !goal.trim()} style={{ padding: '0.6rem', borderRadius: '8px', border: 'none', background: submitting ? 'rgba(99,102,241,0.4)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', fontWeight: 700, fontSize: '0.85rem', cursor: submitting ? 'not-allowed' : 'pointer' }}>
                {submitting ? '⏳ Submitting…' : '🚀 Launch Agent Job'}
              </button>
            </form>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '0.75rem' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>Recent Jobs ({jobs.length})</div>
            {jobs.length === 0 && <div style={{ color: '#475569', fontSize: '0.8rem', textAlign: 'center', padding: '2rem 0' }}>No agent jobs yet. Submit a goal above.</div>}
            {jobs.map(job => (
              <div key={job.job_id} onClick={() => handleSelectJob(job)} style={{ padding: '0.75rem', borderRadius: '8px', marginBottom: '0.4rem', cursor: 'pointer', border: `1px solid ${selectedJob?.job_id === job.job_id ? 'rgba(99,102,241,0.5)' : 'rgba(99,102,241,0.12)'}`, background: selectedJob?.job_id === job.job_id ? 'rgba(99,102,241,0.1)' : 'rgba(30,41,59,0.4)', transition: 'all 0.2s' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>{job.job_id.slice(0, 18)}</span>
                  <span style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: statusBg(job.status), color: statusColor(job.status), fontWeight: 600 }}>{job.status}</span>
                </div>
                <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginBottom: '0.35rem', lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{job.goal}</div>
                <div style={{ height: '3px', background: 'rgba(99,102,241,0.15)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${job.progress}%`, background: statusColor(job.status), transition: 'width 0.5s ease' }} />
                </div>
                <div style={{ fontSize: '0.68rem', color: '#475569', marginTop: '0.25rem' }}>{job.progress.toFixed(0)}% • {elapsedSince(job.created_at)}</div>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Main Panel ── */}
        <main style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
          {!selectedJob ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1.5rem', padding: '4rem' }}>
              <div style={{ fontSize: '3.5rem' }}>🤖</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#e2e8f0' }}>Multi-Agent Collaboration Engine</div>
              <div style={{ color: '#64748b', textAlign: 'center', maxWidth: '540px', lineHeight: 1.7 }}>
                Submit a sales intelligence goal to experience parallel execution, agent-to-agent messaging, shared artifact repositories, conflict resolution, and operational collaboration metrics.
              </div>
              {registry.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', maxWidth: '600px' }}>
                  {registry.map(a => (
                    <span key={a.agent_id} style={{ padding: '0.3rem 0.75rem', borderRadius: '100px', background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)', fontSize: '0.75rem', color: '#a5b4fc' }}>{a.name}</span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Job Header */}
              <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(99,102,241,0.15)', background: 'rgba(15,23,42,0.6)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#6366f1', background: 'rgba(99,102,241,0.12)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>{selectedJob.job_id}</span>
                    <span style={{ fontSize: '0.78rem', padding: '0.2rem 0.65rem', borderRadius: '100px', background: statusBg(selectedJob.status), color: statusColor(selectedJob.status), fontWeight: 700 }}>{selectedJob.status}</span>
                    {isPipelineJob && <span style={{ fontSize: '0.72rem', color: '#8b5cf6', background: 'rgba(139,92,246,0.12)', padding: '0.2rem 0.5rem', borderRadius: '4px', border: '1px solid rgba(139,92,246,0.25)' }}>🏢 Collaborative Pipeline</span>}
                  </div>
                  <div style={{ fontSize: '0.95rem', color: '#e2e8f0', lineHeight: 1.5 }}>{selectedJob.goal}</div>
                  <div style={{ marginTop: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#64748b', marginBottom: '0.3rem' }}>
                      <span>Overall Progress</span><span>{selectedJob.progress.toFixed(0)}%</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(99,102,241,0.15)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${selectedJob.progress}%`, background: 'linear-gradient(90deg, #6366f1, #8b5cf6)', borderRadius: '3px', transition: 'width 0.5s ease' }} />
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                  {['running', 'pending'].includes(selectedJob.status) && (
                    <button onClick={handleCancel} style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.1)', color: '#f87171', fontSize: '0.78rem', cursor: 'pointer' }}>Cancel</button>
                  )}
                  {['failed', 'cancelled'].includes(selectedJob.status) && (
                    <button onClick={handleRetry} style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.1)', color: '#a5b4fc', fontSize: '0.78rem', cursor: 'pointer' }}>Retry</button>
                  )}
                  {selectedJob.status === 'completed' && (
                    <button onClick={() => { setActiveTab('report'); if (selectedJob) agentsApi.getReport(selectedJob.job_id).then(setReport).catch(() => {}); }} style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid rgba(16,185,129,0.3)', background: 'rgba(16,185,129,0.1)', color: '#34d399', fontSize: '0.78rem', cursor: 'pointer' }}>📄 View Report</button>
                  )}
                </div>
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', borderBottom: '1px solid rgba(99,102,241,0.15)', background: 'rgba(15,23,42,0.4)', overflowX: 'auto' }}>
                {[
                  { id: 'pipeline', label: '⚡ Pipeline & Topology' },
                  { id: 'messages', label: `💬 Messages (${messages.length})` },
                  { id: 'artifacts', label: `📦 Artifacts (${artifacts.length})` },
                  { id: 'consensus', label: `⚖️ Consensus (${consensus.length})` },
                  { id: 'metrics', label: '📊 Metrics & Gauges' },
                  { id: 'events', label: `📡 Events (${events.length})` },
                  { id: 'report', label: '📄 Executive Report' },
                  { id: 'registry', label: '🗂 Registry' },
                ].map(tab => (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id as WorkspaceTab)} style={{ padding: '0.75rem 1.1rem', background: 'none', border: 'none', borderBottom: `2px solid ${activeTab === tab.id ? '#6366f1' : 'transparent'}`, color: activeTab === tab.id ? '#a5b4fc' : '#64748b', fontWeight: activeTab === tab.id ? 700 : 400, fontSize: '0.8rem', cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.2s' }}>
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>

                {/* ─── PIPELINE & TOPOLOGY TAB ─── */}
                {activeTab === 'pipeline' && (
                  <div>
                    {isPipelineJob ? (
                      <>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>6-Agent Business Pipeline</div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                          {PIPELINE_AGENTS.map((pa, idx) => {
                            const task = getTaskForAgent(pa.task);
                            const taskStatus = task?.status || 'pending';
                            const conf = (task?.outputs as any)?.confidence;
                            const isExpanded = expandedAgent === pa.id;
                            return (
                              <div key={pa.id} style={{ borderRadius: '10px', border: `1px solid ${isExpanded ? pa.color : 'rgba(99,102,241,0.18)'}`, background: isExpanded ? `rgba(${pa.color.slice(1).match(/../g)?.map(h => parseInt(h,16)).join(',')},0.08)` : 'rgba(15,23,42,0.7)', overflow: 'hidden', transition: 'all 0.25s', cursor: 'pointer' }} onClick={() => setExpandedAgent(isExpanded ? null : pa.id)}>
                                <div style={{ padding: '0.85rem 1rem', display: 'flex', alignItems: 'center', gap: '0.65rem', borderBottom: isExpanded ? `1px solid rgba(99,102,241,0.12)` : 'none' }}>
                                  <span style={{ fontSize: '1.4rem' }}>{pa.icon}</span>
                                  <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0' }}>{idx + 1}. {pa.label}</div>
                                    <div style={{ fontSize: '0.68rem', color: statusColor(taskStatus), fontWeight: 600, marginTop: '0.1rem' }}>● {taskStatus}</div>
                                  </div>
                                  {conf !== undefined && (
                                    <div style={{ textAlign: 'center' }}>
                                      <div style={{ fontSize: '1rem', fontWeight: 800, color: confidenceColor(conf) }}>{conf}%</div>
                                      <div style={{ fontSize: '0.6rem', color: '#64748b' }}>confidence</div>
                                    </div>
                                  )}
                                </div>
                                {taskStatus !== 'pending' && (
                                  <div style={{ height: '3px', background: 'rgba(99,102,241,0.1)' }}>
                                    <div style={{ height: '100%', width: taskStatus === 'completed' ? '100%' : taskStatus === 'running' ? '50%' : '0%', background: pa.color, transition: 'width 0.4s ease' }} />
                                  </div>
                                )}
                                {task?.execution_time_seconds != null && task.execution_time_seconds > 0 && (
                                  <div style={{ padding: '0.25rem 1rem', fontSize: '0.65rem', color: '#475569' }}>⏱ {task.execution_time_seconds.toFixed(1)}s</div>
                                )}
                                {isExpanded && task?.outputs && Object.keys(task.outputs).length > 0 && (
                                  <div style={{ padding: '0.85rem 1rem', borderTop: '1px solid rgba(99,102,241,0.1)' }}>
                                    <AgentOutputPanel outputs={task.outputs} />
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>Task Execution Graph</div>
                        {(selectedJob.plan?.tasks || []).map(task => (
                          <div key={task.task_id} style={{ padding: '0.85rem 1rem', borderRadius: '8px', border: `1px solid ${statusColor(task.status)}30`, background: statusBg(task.status) }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div>
                                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0' }}>{task.name}</div>
                                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.15rem' }}>Agent: {task.agent_name}</div>
                              </div>
                              <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.6rem', borderRadius: '4px', background: statusBg(task.status), color: statusColor(task.status), fontWeight: 700 }}>{task.status}</span>
                            </div>
                            {task.error_message && <div style={{ marginTop: '0.5rem', color: '#f87171', fontSize: '0.75rem' }}>{task.error_message}</div>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ─── MESSAGES TAB ─── */}
                {activeTab === 'messages' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Agent Message Bus History ({messages.length})</div>
                    {messages.length === 0 ? (
                      <div style={{ color: '#475569', textAlign: 'center', padding: '3rem', fontSize: '0.85rem' }}>No inter-agent messages logged yet for this job.</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                        {messages.map(msg => (
                          <div key={msg.message_id} style={{ padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.18)', background: 'rgba(15,23,42,0.7)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#a5b4fc' }}>{msg.from_agent}</span>
                                <span style={{ fontSize: '0.7rem', color: '#64748b' }}>→</span>
                                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8' }}>{msg.to_agent}</span>
                                <span style={{ fontSize: '0.65rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(99,102,241,0.12)', color: '#c7d2fe' }}>{msg.message_type}</span>
                              </div>
                              <span style={{ fontSize: '0.68rem', color: '#64748b', fontFamily: 'monospace' }}>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                            </div>
                            <pre style={{ margin: 0, fontSize: '0.72rem', color: '#cbd5e1', background: 'rgba(10,15,30,0.6)', padding: '0.5rem', borderRadius: '6px', overflowX: 'auto' }}>{JSON.stringify(msg.payload, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ─── ARTIFACTS TAB ─── */}
                {activeTab === 'artifacts' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Shared Versioned Artifact Repository ({artifacts.length})</div>
                    {artifacts.length === 0 ? (
                      <div style={{ color: '#475569', textAlign: 'center', padding: '3rem', fontSize: '0.85rem' }}>No shared artifacts stored for this job yet.</div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                        {artifacts.map(art => (
                          <div key={art.artifact_id} style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.4rem' }}>
                              <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#e2e8f0' }}>{art.title}</div>
                              <span style={{ fontSize: '0.68rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(16,185,129,0.12)', color: '#34d399', fontWeight: 700 }}>v{art.version}</span>
                            </div>
                            <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.5rem' }}>Owner: {art.owner_agent} | Type: {art.artifact_type}</div>
                            <pre style={{ margin: 0, fontSize: '0.68rem', color: '#94a3b8', background: 'rgba(10,15,30,0.6)', padding: '0.5rem', borderRadius: '6px', maxHeight: '140px', overflowY: 'auto' }}>{JSON.stringify(art.content, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ─── CONSENSUS & CONFLICTS TAB ─── */}
                {activeTab === 'consensus' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Consensus Engine & Conflict Resolution Log ({consensus.length})</div>
                    {consensus.length === 0 ? (
                      <div style={{ color: '#475569', textAlign: 'center', padding: '3rem', fontSize: '0.85rem' }}>No conflicts detected or consensus decisions recorded for this job.</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                        {consensus.map(c => (
                          <div key={c.consensus_id} style={{ padding: '1rem', borderRadius: '10px', border: `1px solid ${c.is_conflict ? 'rgba(239,68,68,0.3)' : 'rgba(99,102,241,0.2)'}`, background: c.is_conflict ? 'rgba(239,68,68,0.05)' : 'rgba(15,23,42,0.7)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: c.is_conflict ? '#f87171' : '#e2e8f0' }}>
                                {c.is_conflict ? '⚠️ Conflict Resolved: ' : '⚖️ Consensus: '}{c.topic}
                              </div>
                              <span style={{ fontSize: '0.68rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>Strategy: {c.strategy_used}</span>
                            </div>
                            {c.conflict_details?.reasoning && (
                              <div style={{ fontSize: '0.75rem', color: '#fca5a5', marginBottom: '0.5rem', fontStyle: 'italic' }}>{c.conflict_details.reasoning}</div>
                            )}
                            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginBottom: '0.4rem' }}>Winning Agent: <strong style={{ color: '#34d399' }}>{c.winning_agent || 'N/A'}</strong> (Confidence: {c.confidence}%)</div>
                            <pre style={{ margin: 0, fontSize: '0.7rem', color: '#cbd5e1', background: 'rgba(10,15,30,0.6)', padding: '0.5rem', borderRadius: '6px', overflowX: 'auto' }}>{JSON.stringify(c.resolved_output, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ─── METRICS TAB ─── */}
                {activeTab === 'metrics' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Operational Collaboration Metrics</div>
                    {!metrics ? (
                      <div style={{ color: '#475569', textAlign: 'center', padding: '3rem', fontSize: '0.85rem' }}>Loading metrics summary…</div>
                    ) : (
                      <div>
                        {/* KPI Grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                          <div style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#6366f1' }}>{metrics.message_count}</div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.2rem' }}>Total Messages</div>
                          </div>
                          <div style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#8b5cf6' }}>{metrics.artifact_count}</div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.2rem' }}>Shared Artifacts</div>
                          </div>
                          <div style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981' }}>{metrics.parallel_efficiency.toFixed(2)}x</div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.2rem' }}>Parallel Efficiency</div>
                          </div>
                          <div style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f59e0b' }}>{metrics.actual_job_latency_seconds.toFixed(1)}s</div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.2rem' }}>Job Latency</div>
                          </div>
                        </div>

                        {/* Agent Utilization Gauges */}
                        <div style={{ padding: '1.25rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)' }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#e2e8f0', marginBottom: '1rem' }}>Agent Utilization Breakdown</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {Object.entries(metrics.agent_utilization_percent || {}).map(([agent, pct]) => (
                              <div key={agent}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#cbd5e1', marginBottom: '0.25rem' }}>
                                  <span>{agent}</span>
                                  <span>{pct.toFixed(1)}%</span>
                                </div>
                                <div style={{ height: '6px', background: 'rgba(99,102,241,0.15)', borderRadius: '3px', overflow: 'hidden' }}>
                                  <div style={{ height: '100%', width: `${pct}%`, background: 'linear-gradient(90deg, #6366f1, #10b981)', borderRadius: '3px', transition: 'width 0.4s' }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* ─── EVENTS TAB ─── */}
                {activeTab === 'events' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Event Timeline ({events.length})</div>
                    {events.length === 0 ? (
                      <div style={{ color: '#475569', textAlign: 'center', padding: '3rem', fontSize: '0.85rem' }}>No events recorded yet.</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {[...events].reverse().map(ev => (
                          <div key={ev.event_id} style={{ padding: '0.7rem 1rem', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.12)', background: 'rgba(15,23,42,0.6)', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                            <span style={{ fontSize: '0.72rem', color: '#6366f1', fontFamily: 'monospace', minWidth: '145px', marginTop: '0.1rem' }}>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#a5b4fc' }}>{ev.event_type.replace(/_/g, ' ')}</div>
                              <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Agent: {ev.source_agent} {ev.task_id ? `| Task: ${ev.task_id}` : ''}</div>
                              {Object.keys(ev.payload).length > 0 && <pre style={{ margin: '0.25rem 0 0', fontSize: '0.68rem', color: '#94a3b8', background: 'rgba(99,102,241,0.05)', padding: '0.35rem', borderRadius: '4px', overflowX: 'auto', maxHeight: '80px' }}>{JSON.stringify(ev.payload, null, 2)}</pre>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ─── REPORT TAB ─── */}
                {activeTab === 'report' && (
                  <div>
                    {!report ? (
                      <div style={{ textAlign: 'center', padding: '4rem', color: '#64748b' }}>
                        {selectedJob.status === 'completed' ? (
                          <div>
                            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📄</div>
                            <div style={{ fontSize: '0.9rem' }}>Loading executive report…</div>
                          </div>
                        ) : (
                          <div>
                            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
                            <div style={{ fontSize: '0.9rem' }}>Executive report will be available when the pipeline completes.</div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <ExecutiveReportPanel report={report} />
                    )}
                  </div>
                )}

                {/* ─── REGISTRY TAB ─── */}
                {activeTab === 'registry' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Registered Agents ({registry.length})</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                      {registry.map(a => (
                        <div key={a.agent_id} style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#e2e8f0' }}>{a.name}</div>
                            <span style={{ fontSize: '0.65rem', color: '#6366f1', background: 'rgba(99,102,241,0.12)', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>v{a.version}</span>
                          </div>
                          <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace', marginBottom: '0.5rem' }}>{a.agent_id}</div>
                          <div style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.5, marginBottom: '0.6rem' }}>{a.description}</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                            {a.capabilities.map(cap => (
                              <span key={cap} style={{ fontSize: '0.65rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(99,102,241,0.1)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.2)' }}>{cap}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

const AgentOutputPanel: React.FC<{ outputs: Record<string, any> }> = ({ outputs }) => {
  const entries = Object.entries(outputs).filter(([k]) => k !== 'confidence');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '280px', overflowY: 'auto' }}>
      {entries.map(([key, value]) => (
        <div key={key}>
          <div style={{ fontSize: '0.68rem', color: '#6366f1', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.15rem' }}>{key.replace(/_/g, ' ')}</div>
          {Array.isArray(value) ? (
            <ul style={{ margin: 0, paddingLeft: '1rem' }}>
              {value.slice(0, 4).map((item, i) => (
                <li key={i} style={{ fontSize: '0.72rem', color: '#94a3b8', marginBottom: '0.15rem' }}>
                  {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                </li>
              ))}
              {value.length > 4 && <li style={{ fontSize: '0.68rem', color: '#475569' }}>+{value.length - 4} more</li>}
            </ul>
          ) : typeof value === 'object' ? (
            <pre style={{ fontSize: '0.65rem', color: '#94a3b8', background: 'rgba(15,23,42,0.6)', padding: '0.35rem', borderRadius: '4px', overflow: 'auto', maxHeight: '80px', margin: 0 }}>{JSON.stringify(value, null, 2)}</pre>
          ) : (
            <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: 1.5 }}>{String(value).slice(0, 200)}{String(value).length > 200 ? '…' : ''}</div>
          )}
        </div>
      ))}
    </div>
  );
};

const ExecutiveReportPanel: React.FC<{ report: ExecutiveReport }> = ({ report }) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const Section: React.FC<{ title: string; id: string; children: React.ReactNode }> = ({ title, id, children }) => {
    const open = expandedSection === id;
    return (
      <div style={{ borderRadius: '10px', border: '1px solid rgba(99,102,241,0.18)', marginBottom: '0.75rem', overflow: 'hidden' }}>
        <div onClick={() => setExpandedSection(open ? null : id)} style={{ padding: '0.85rem 1.1rem', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.7)' }}>
          <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#e2e8f0' }}>{title}</span>
          <span style={{ color: '#64748b', transition: 'transform 0.2s', display: 'inline-block', transform: open ? 'rotate(90deg)' : 'none' }}>›</span>
        </div>
        {open && <div style={{ padding: '1rem 1.1rem', background: 'rgba(10,15,30,0.6)', borderTop: '1px solid rgba(99,102,241,0.1)' }}>{children}</div>}
      </div>
    );
  };

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        {[
          { label: 'Opportunity Score', value: `${report.opportunity_score}/100`, color: confidenceColor(report.opportunity_score) },
          { label: 'Confidence', value: `${report.overall_confidence}%`, color: confidenceColor(report.overall_confidence) },
          { label: 'Best Channel', value: report.best_outreach_channel, color: '#8b5cf6' },
          { label: 'Deal Size Est.', value: report.estimated_deal_size, color: '#10b981' },
        ].map(kpi => (
          <div key={kpi.label} style={{ padding: '1rem', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', background: 'rgba(15,23,42,0.7)', textAlign: 'center' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: kpi.color }}>{kpi.value}</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.2rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{kpi.label}</div>
          </div>
        ))}
      </div>

      <div style={{ padding: '1.1rem', borderRadius: '10px', border: '1px solid rgba(16,185,129,0.25)', background: 'rgba(16,185,129,0.05)', marginBottom: '0.75rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>Executive Summary</div>
        <p style={{ fontSize: '0.88rem', color: '#e2e8f0', lineHeight: 1.7, margin: 0 }}>{report.executive_summary}</p>
      </div>

      {report.winning_value_proposition && (
        <div style={{ padding: '0.85rem 1.1rem', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.25)', background: 'rgba(99,102,241,0.06)', marginBottom: '0.75rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.3rem' }}>Winning Value Proposition</div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#c7d2fe', lineHeight: 1.6, fontStyle: 'italic' }}>"{report.winning_value_proposition}"</p>
        </div>
      )}

      <Section title="📋 Recommended Actions" id="actions">
        {report.recommended_actions.map((a, i) => (
          <div key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', marginBottom: '0.6rem', padding: '0.65rem', borderRadius: '6px', background: 'rgba(99,102,241,0.06)' }}>
            <span style={{ fontSize: '0.68rem', padding: '0.15rem 0.4rem', borderRadius: '4px', background: a.priority === 'high' ? 'rgba(239,68,68,0.15)' : a.priority === 'medium' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)', color: a.priority === 'high' ? '#f87171' : a.priority === 'medium' ? '#fbbf24' : '#34d399', fontWeight: 700, flexShrink: 0, marginTop: '0.1rem' }}>{a.priority}</span>
            <div>
              <div style={{ fontSize: '0.82rem', color: '#e2e8f0', fontWeight: 600 }}>{a.action}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{a.timeline} · Owner: {a.owner}</div>
            </div>
          </div>
        ))}
      </Section>

      <Section title="⚠️ Risk Assessment" id="risks">
        {report.risk_assessment.map((r, i) => (
          <div key={i} style={{ marginBottom: '0.6rem', padding: '0.65rem', borderRadius: '6px', background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.1)' }}>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.68rem', color: r.severity === 'high' ? '#ef4444' : r.severity === 'medium' ? '#f59e0b' : '#10b981', fontWeight: 700 }}>{r.severity?.toUpperCase()}</span>
              <span style={{ fontSize: '0.8rem', color: '#e2e8f0', fontWeight: 600 }}>{r.risk}</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>↳ {r.mitigation}</div>
          </div>
        ))}
      </Section>

      <Section title="✅ Execution Checklist" id="checklist">
        {report.execution_checklist.map((item, i) => (
          <div key={i} style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', padding: '0.4rem 0', borderBottom: '1px solid rgba(99,102,241,0.07)' }}>
            <span style={{ fontSize: '0.9rem' }}>☐</span>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>{item.task}</span>
              {item.due && <span style={{ fontSize: '0.68rem', color: '#64748b', marginLeft: '0.5rem' }}>· {item.due}</span>}
            </div>
          </div>
        ))}
      </Section>

      <Section title="🎯 Top Pain Points" id="pains">
        <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
          {report.top_pain_points.map((p, i) => <li key={i} style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>{p}</li>)}
        </ul>
      </Section>

      <Section title="💌 Outreach Package" id="outreach">
        {report.outreach_section?.cold_email && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.72rem', color: '#6366f1', fontWeight: 700, marginBottom: '0.35rem' }}>COLD EMAIL</div>
            <div style={{ fontSize: '0.78rem', color: '#a5b4fc', marginBottom: '0.3rem' }}>Subject: {report.outreach_section.cold_email.subject}</div>
            <pre style={{ fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'pre-wrap', background: 'rgba(99,102,241,0.05)', padding: '0.5rem', borderRadius: '6px', margin: 0 }}>{report.outreach_section.cold_email.body}</pre>
          </div>
        )}
        {report.outreach_section?.linkedin_message && (
          <div>
            <div style={{ fontSize: '0.72rem', color: '#6366f1', fontWeight: 700, marginBottom: '0.35rem' }}>LINKEDIN</div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', background: 'rgba(99,102,241,0.05)', padding: '0.5rem', borderRadius: '6px' }}>{report.outreach_section.linkedin_message}</div>
          </div>
        )}
      </Section>

      <div style={{ marginTop: '1.5rem', textAlign: 'right' }}>
        <button onClick={() => { const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `executive_report_${report.report_id}.json`; a.click(); }} style={{ padding: '0.6rem 1.25rem', borderRadius: '8px', border: '1px solid rgba(16,185,129,0.35)', background: 'rgba(16,185,129,0.1)', color: '#34d399', fontWeight: 700, fontSize: '0.82rem', cursor: 'pointer' }}>
          ⬇ Download JSON Report
        </button>
      </div>
    </div>
  );
};

export default AgentsWorkspacePage;
