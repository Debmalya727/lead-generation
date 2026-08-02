import React, { useState, useEffect } from 'react';
import {
  Search,
  MapPin,
  Layers,
  CheckCircle2,
  TrendingUp,
  Phone,
  Mail,
  Globe,
  Zap,
  ChevronRight,
  RefreshCw,
  Database,
} from 'lucide-react';
import {
  startDiscoveryJob,
  getJobStatus,
  getJobResults,
  getJobDuplicates,
  getDiscoveryAnalytics,
  getLatestJob,
  getAllDiscoveredCompanies,
  saveLeadsToCRM,
  DiscoveredCompany,
  DuplicateMergeLog,
  DiscoveryAnalytics,
  JobStatusResponse,
} from '../../api/discovery';

export const EnterpriseDiscoveryWorkspace: React.FC = () => {
  // Search parameters
  const [keyword, setKeyword] = useState('HVAC Contractors');
  const [location, setLocation] = useState('Mumbai');
  const [selectedProviders, setSelectedProviders] = useState<string[]>([
    'google_maps',
    'justdial',
    'indiamart',
    'tradeindia',
  ]);
  const [websiteFilter, setWebsiteFilter] = useState('all');
  const [limit, setLimit] = useState(25);

  // Active Job State
  const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [discoveredLeads, setDiscoveredLeads] = useState<DiscoveredCompany[]>([]);
  const [duplicateLogs, setDuplicateLogs] = useState<DuplicateMergeLog[]>([]);
  const [analytics, setAnalytics] = useState<DiscoveryAnalytics | null>(null);
  const [selectedLead, setSelectedLead] = useState<DiscoveredCompany | null>(null);
  const [activeTab, setActiveTab] = useState<'leads' | 'dedup' | 'analytics' | 'health'>('leads');
  const [selectedLeadIds, setSelectedLeadIds] = useState<string[]>([]);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
    fetchInitialLeads();
  }, []);

  const fetchInitialLeads = async () => {
    try {
      const latestJob = await getLatestJob();
      if (latestJob && latestJob.id) {
        setActiveJob(latestJob);
        if (latestJob.keyword) setKeyword(latestJob.keyword);
        if (latestJob.location) setLocation(latestJob.location);
        if (latestJob.providers && latestJob.providers.length > 0) setSelectedProviders(latestJob.providers);

        const results = await getJobResults(latestJob.id);
        const duplicates = await getJobDuplicates(latestJob.id);
        setDiscoveredLeads(results);
        setDuplicateLogs(duplicates);
      }
    } catch (e) {
      try {
        const allCompanies = await getAllDiscoveredCompanies();
        if (allCompanies && allCompanies.length > 0) {
          setDiscoveredLeads(allCompanies);
        }
      } catch (err) {
        console.warn('Initial leads fetch error:', err);
      }
    }
  };

  const fetchAnalytics = async () => {
    try {
      const data = await getDiscoveryAnalytics();
      setAnalytics(data);
    } catch (e) {
      console.warn('Analytics fetch error:', e);
    }
  };

  const handleProviderToggle = (provider: string) => {
    if (selectedProviders.includes(provider)) {
      if (selectedProviders.length > 1) {
        setSelectedProviders(selectedProviders.filter((p) => p !== provider));
      }
    } else {
      setSelectedProviders([...selectedProviders, provider]);
    }
  };

  const handleStartDiscovery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword || !location) return;

    setIsSearching(true);
    setSaveSuccessMsg(null);
    try {
      const job = await startDiscoveryJob({
        keyword,
        location,
        providers: selectedProviders,
        website_filter: websiteFilter,
        limit,
      });
      setActiveJob(job);
      pollJobStatus(job.id);
    } catch (err: any) {
      alert(`Discovery start failed: ${err.message}`);
      setIsSearching(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const job = await getJobStatus(jobId);
        setActiveJob(job);

        if (job.status === 'completed') {
          clearInterval(interval);
          setIsSearching(false);
          // Fetch results and merge logs
          const results = await getJobResults(jobId);
          const duplicates = await getJobDuplicates(jobId);
          setDiscoveredLeads(results);
          setDuplicateLogs(duplicates);
          fetchAnalytics();
        } else if (job.status === 'failed' || job.status === 'cancelled') {
          clearInterval(interval);
          setIsSearching(false);
        }
      } catch (e) {
        clearInterval(interval);
        setIsSearching(false);
      }
    }, 2000);
  };

  const handleToggleSelectLead = (id: string) => {
    if (selectedLeadIds.includes(id)) {
      setSelectedLeadIds(selectedLeadIds.filter((item) => item !== id));
    } else {
      setSelectedLeadIds([...selectedLeadIds, id]);
    }
  };

  const handleSaveToCRM = async () => {
    if (!activeJob || selectedLeadIds.length === 0) return;
    try {
      const res = await saveLeadsToCRM(activeJob.id, selectedLeadIds);
      setSaveSuccessMsg(res.message);
      fetchAnalytics();
    } catch (e: any) {
      alert(`Save to CRM failed: ${e.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto', color: '#e2e8f0', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', background: 'linear-gradient(90deg, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: 0 }}>
            Enterprise Lead Discovery Workspace
          </h1>
          <p style={{ color: '#94a3b8', marginTop: '6px', fontSize: '14px' }}>
            Discover, normalize, deduplicate, and enrich business leads across Google Maps, Justdial, IndiaMART, and TradeIndia.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={fetchAnalytics}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer' }}
          >
            <RefreshCw size={16} /> Refresh Metrics
          </button>
        </div>
      </div>

      {/* Analytics KPI Row */}
      {analytics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '24px' }}>
          <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>DISCOVERED LEADS</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {analytics.summary.businesses_discovered_total}
            </div>
            <div style={{ fontSize: '11px', color: '#10b981', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <TrendingUp size={12} /> Live aggregated count
            </div>
          </div>
          <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>DUPLICATES MERGED</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#a855f7', marginTop: '4px' }}>
              {analytics.summary.duplicates_merged_total}
            </div>
            <div style={{ fontSize: '11px', color: '#a855f7', marginTop: '4px' }}>
              {analytics.summary.deduplication_rate_percent}% deduplication efficiency
            </div>
          </div>
          <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>🔥 HOT LEADS</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#ef4444', marginTop: '4px' }}>
              {analytics.quality_distribution.hot}
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>Score &ge; 70</div>
          </div>
          <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>AVG ENRICHMENT</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#3b82f6', marginTop: '4px' }}>
              {analytics.summary.avg_enrichment_time_ms} ms
            </div>
            <div style={{ fontSize: '11px', color: '#3b82f6', marginTop: '4px' }}>AI Summary + Tech Stack</div>
          </div>
          <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>PROVIDER HEALTH</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
              {analytics.provider_health.healthy_count} / {analytics.provider_health.total_providers}
            </div>
            <div style={{ fontSize: '11px', color: '#10b981', marginTop: '4px' }}>Circuit state: CLOSED</div>
          </div>
        </div>
      )}

      {/* Main Search Panel */}
      <div style={{ background: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155', marginBottom: '24px' }}>
        <form onSubmit={handleStartDiscovery}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 2fr 1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', display: 'block' }}>
                TARGET KEYWORD OR CATEGORY
              </label>
              <div style={{ position: 'relative' }}>
                <Search style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} size={18} />
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="e.g. HVAC Contractors, Restaurant, Textile Exporters"
                  style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', padding: '10px 12px 10px 40px', borderRadius: '8px', fontSize: '14px' }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', display: 'block' }}>
                LOCATION / CITY
              </label>
              <div style={{ position: 'relative' }}>
                <MapPin style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} size={18} />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Mumbai, Delhi, Chicago"
                  style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', padding: '10px 12px 10px 40px', borderRadius: '8px', fontSize: '14px' }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', display: 'block' }}>
                WEBSITE FILTER
              </label>
              <select
                value={websiteFilter}
                onChange={(e) => setWebsiteFilter(e.target.value)}
                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', padding: '10px 12px', borderRadius: '8px', fontSize: '14px' }}
              >
                <option value="all">All Businesses</option>
                <option value="with_website">With Website Only</option>
                <option value="without_website">Without Website Only</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', display: 'block' }}>
                TARGET LIMIT ({limit})
              </label>
              <input
                type="range"
                min="5"
                max="100"
                step="5"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#6366f1', marginTop: '8px' }}
              />
            </div>
          </div>

          {/* Provider Selection Multi-Checkboxes */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>PROVIDERS:</span>
              {[
                { id: 'google_maps', label: 'Google Maps', icon: '📍' },
                { id: 'justdial', label: 'Justdial', icon: '📞' },
                { id: 'indiamart', label: 'IndiaMART', icon: '🏭' },
                { id: 'tradeindia', label: 'TradeIndia', icon: '🌐' },
              ].map((p) => (
                <label
                  key={p.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    border: selectedProviders.includes(p.id) ? '1px solid #6366f1' : '1px solid #334155',
                    background: selectedProviders.includes(p.id) ? '#312e81' : '#0f172a',
                    cursor: 'pointer',
                    fontSize: '13px',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedProviders.includes(p.id)}
                    onChange={() => handleProviderToggle(p.id)}
                    style={{ accentColor: '#6366f1' }}
                  />
                  <span>{p.icon}</span>
                  <span>{p.label}</span>
                </label>
              ))}
            </div>

            <button
              type="submit"
              disabled={isSearching}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(90deg, #6366f1, #a855f7)',
                color: '#ffffff',
                fontWeight: 700,
                padding: '12px 28px',
                borderRadius: '10px',
                border: 'none',
                cursor: isSearching ? 'not-allowed' : 'pointer',
                fontSize: '15px',
                boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
              }}
            >
              {isSearching ? <RefreshCw className="animate-spin" size={18} /> : <Zap size={18} />}
              {isSearching ? 'Executing 9-Stage Pipeline...' : 'Start Lead Discovery'}
            </button>
          </div>
        </form>

        {/* Live Progress Bar */}
        {activeJob && (
          <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                Pipeline Progress: {activeJob.progress}% ({activeJob.status.toUpperCase()})
              </span>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                Found: {activeJob.total_results} Leads
              </span>
            </div>
            <div style={{ width: '100%', height: '8px', background: '#0f172a', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${activeJob.progress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #6366f1, #10b981)',
                  transition: 'width 0.5s ease',
                }}
              />
            </div>

            {/* 9-Stage Progress Markers */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px', marginTop: '12px', fontSize: '11px', color: '#64748b' }}>
              <span style={{ color: activeJob.progress >= 10 ? '#10b981' : '#64748b' }}>1. Init</span>
              <span style={{ color: activeJob.progress >= 30 ? '#10b981' : '#64748b' }}>2. Multi-Search</span>
              <span style={{ color: activeJob.progress >= 45 ? '#10b981' : '#64748b' }}>3. Normalize</span>
              <span style={{ color: activeJob.progress >= 60 ? '#10b981' : '#64748b' }}>4. AI Dedup</span>
              <span style={{ color: activeJob.progress >= 85 ? '#10b981' : '#64748b' }}>5. AI Enrich & Score</span>
              <span style={{ color: activeJob.progress >= 100 ? '#10b981' : '#64748b' }}>6. Knowledge & CRM</span>
            </div>
          </div>
        )}
      </div>

      {saveSuccessMsg && (
        <div style={{ background: '#064e3b', border: '1px solid #10b981', color: '#a7f3d0', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> {saveSuccessMsg}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('leads')}
          style={{ background: 'none', border: 'none', color: activeTab === 'leads' ? '#6366f1' : '#94a3b8', borderBottom: activeTab === 'leads' ? '2px solid #6366f1' : 'none', paddingBottom: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '15px' }}
        >
          Discovered & Enriched Leads ({discoveredLeads.length})
        </button>
        <button
          onClick={() => setActiveTab('dedup')}
          style={{ background: 'none', border: 'none', color: activeTab === 'dedup' ? '#6366f1' : '#94a3b8', borderBottom: activeTab === 'dedup' ? '2px solid #6366f1' : 'none', paddingBottom: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '15px' }}
        >
          AI Deduplication Merge Viewer ({duplicateLogs.length})
        </button>
        <button
          onClick={() => setActiveTab('health')}
          style={{ background: 'none', border: 'none', color: activeTab === 'health' ? '#6366f1' : '#94a3b8', borderBottom: activeTab === 'health' ? '2px solid #6366f1' : 'none', paddingBottom: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '15px' }}
        >
          Provider Circuit Health Telemetry
        </button>
      </div>

      {/* Tab Content 1: Leads Grid */}
      {activeTab === 'leads' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8' }}>
              Selected {selectedLeadIds.length} leads
            </div>
            <button
              onClick={handleSaveToCRM}
              disabled={selectedLeadIds.length === 0}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: selectedLeadIds.length > 0 ? '#10b981' : '#334155',
                color: '#ffffff',
                padding: '8px 20px',
                borderRadius: '8px',
                border: 'none',
                fontWeight: 600,
                cursor: selectedLeadIds.length > 0 ? 'pointer' : 'not-allowed',
              }}
            >
              <Database size={16} /> Import Selected to CRM
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
            {discoveredLeads.map((lead) => {
              const compName = lead.company_name || lead.name || 'Discovered Business';
              const leadScore = lead.quality_score ?? lead.score ?? 50;
              const isHot = lead.quality_tier === 'Hot' || leadScore >= 70;
              const isWarm = lead.quality_tier === 'Warm' || (leadScore >= 40 && leadScore < 70);
              const sourcesList = lead.source_providers?.length ? lead.source_providers : [lead.provider || 'Scraper'];
              const phoneList = lead.phones?.length ? lead.phones : lead.phone ? [lead.phone] : [];
              const emailList = lead.emails?.length ? lead.emails : lead.email ? [lead.email] : [];
              const locStr = lead.city ? `${lead.city}, ${lead.country || 'IN'}` : lead.location || lead.address || '';

              return (
                <div
                  key={lead.id || lead.fingerprint || Math.random().toString()}
                  style={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '12px',
                    padding: '20px',
                    position: 'relative',
                    transition: 'border-color 0.2s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input
                        type="checkbox"
                        checked={selectedLeadIds.includes(lead.id || lead.fingerprint || '')}
                        onChange={() => handleToggleSelectLead(lead.id || lead.fingerprint || '')}
                        style={{ accentColor: '#6366f1', width: '16px', height: '16px' }}
                      />
                      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>
                        {compName}
                      </h3>
                    </div>

                    <span
                      style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: 700,
                        background: isHot ? '#7f1d1d' : isWarm ? '#7c2d12' : '#1e3a8a',
                        color: isHot ? '#fca5a5' : isWarm ? '#fdba74' : '#93c5fd',
                      }}
                    >
                      {isHot ? '🔥 Hot' : isWarm ? '♨️ Warm' : '❄️ Cold'} ({leadScore})
                    </span>
                  </div>

                  {lead.is_merged && (
                    <div style={{ background: '#312e81', border: '1px solid #4338ca', color: '#c7d2fe', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', marginBottom: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      <Layers size={12} /> Merged from {sourcesList.join(', ')}
                    </div>
                  )}

                  <div style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {phoneList.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Phone size={14} style={{ color: '#6366f1' }} /> {phoneList[0]}
                      </div>
                    )}
                    {lead.website && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Globe size={14} style={{ color: '#10b981' }} />
                        <a href={lead.website} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'none' }}>
                          {lead.website_domain || lead.website}
                        </a>
                      </div>
                    )}
                    {emailList.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Mail size={14} style={{ color: '#a855f7' }} /> {emailList[0]}
                      </div>
                    )}
                    {locStr && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8' }}>
                        <MapPin size={14} /> {locStr}
                      </div>
                    )}
                  </div>

                  {lead.ai_summary && (
                    <div style={{ background: '#0f172a', padding: '10px 12px', borderRadius: '8px', fontSize: '12px', color: '#94a3b8', fontStyle: 'italic', marginBottom: '12px' }}>
                      &ldquo;{lead.ai_summary}&rdquo;
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid #334155' }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {sourcesList.map((sp) => (
                        <span key={sp} style={{ background: '#0f172a', border: '1px solid #334155', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', color: '#94a3b8' }}>
                          {sp}
                        </span>
                      ))}
                    </div>

                    <button
                      onClick={() => setSelectedLead(lead)}
                      style={{ background: 'none', border: 'none', color: '#6366f1', fontSize: '12px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      Full Details <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab Content 2: Deduplication Viewer */}
      {activeTab === 'dedup' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {duplicateLogs.map((log, idx) => (
            <div key={idx} style={{ background: '#1e293b', border: '1px solid #4338ca', padding: '20px', borderRadius: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ margin: 0, fontSize: '16px', color: '#c7d2fe', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={18} style={{ color: '#818cf8' }} /> Unified Company Cluster: {log.merged_company_names[0]}
                </h3>
                <span style={{ background: '#312e81', color: '#a5b4fc', padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
                  Confidence: {Math.round(log.confidence * 100)}% Match
                </span>
              </div>

              <div style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '12px' }}>
                <strong>Merged Records ({log.merged_company_names.length}):</strong> {log.merged_company_names.join(' + ')}
              </div>

              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>
                <strong>Matched Providers:</strong> {log.merged_providers.join(', ')}
              </div>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {log.match_reasons.map((r, rIdx) => (
                  <span key={rIdx} style={{ background: '#0f172a', border: '1px solid #334155', color: '#10b981', padding: '4px 10px', borderRadius: '6px', fontSize: '11px' }}>
                    ✓ {r}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab Content 3: Provider Health Cards */}
      {activeTab === 'health' && analytics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          {Object.entries(analytics.provider_health.providers || {}).map(([pName, pHealth]) => (
            <div key={pName} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#f8fafc', textTransform: 'capitalize' }}>
                  {pName.replace('_', ' ')}
                </h3>
                <span style={{ padding: '4px 12px', borderRadius: '12px', fontSize: '11px', fontWeight: 700, background: pHealth.status === 'healthy' ? '#064e3b' : '#7f1d1d', color: pHealth.status === 'healthy' ? '#a7f3d0' : '#fca5a5' }}>
                  {pHealth.status.toUpperCase()} (Circuit: {pHealth.circuit_state})
                </span>
              </div>
              <div style={{ fontSize: '13px', color: '#cbd5e1', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '12px' }}>
                <div>RPM Quota: <strong>{pHealth.requests_per_minute_quota}</strong></div>
                <div>Total Requests: <strong>{pHealth.total_requests}</strong></div>
                <div>Success Count: <strong style={{ color: '#10b981' }}>{pHealth.success_count}</strong></div>
                <div>Failure Count: <strong style={{ color: '#ef4444' }}>{pHealth.failure_count}</strong></div>
                <div>Avg Latency: <strong>{pHealth.avg_latency_ms} ms</strong></div>
                <div>Last Error: <strong>{pHealth.last_error || 'None'}</strong></div>
              </div>
            </div>
          ))}
        </div>
      )}
      {selectedLead && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.8)', display: 'flex', justifyContent: 'flex-end', zIndex: 100 }}>
          <div style={{ width: '500px', background: '#1e293b', height: '100%', padding: '24px', overflowY: 'auto', borderLeft: '1px solid #334155', boxShadow: '-10px 0 30px rgba(0,0,0,0.5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
                {selectedLead.company_name}
              </h2>
              <button onClick={() => setSelectedLead(null)} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: '#0f172a', padding: '16px', borderRadius: '10px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>AI EXECUTIVE SUMMARY</div>
                <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>
                  {selectedLead.ai_summary || 'AI intelligence summary active.'}
                </div>
              </div>

              <div style={{ background: '#0f172a', padding: '16px', borderRadius: '10px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>BUSINESS METRICS</div>
                <div style={{ fontSize: '13px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>Industry: <strong>{selectedLead.industry || 'B2B'}</strong></div>
                  <div>Maturity: <strong>{selectedLead.business_maturity || 'SME'}</strong></div>
                  <div>Buyer Intent: <strong>{selectedLead.buyer_intent || 'High'}</strong></div>
                  <div>GSTIN: <strong>{selectedLead.gst || 'N/A'}</strong></div>
                </div>
              </div>

              <div style={{ background: '#0f172a', padding: '16px', borderRadius: '10px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>MULTICHANNEL CONTACTS</div>
                <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div>Phones: {(selectedLead.phones || [selectedLead.phone]).filter(Boolean).join(', ') || 'N/A'}</div>
                  <div>Emails: {(selectedLead.emails || [selectedLead.email]).filter(Boolean).join(', ') || 'N/A'}</div>
                  <div>Website: {selectedLead.website || 'N/A'}</div>
                  <div>Address: {selectedLead.address || selectedLead.city}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
