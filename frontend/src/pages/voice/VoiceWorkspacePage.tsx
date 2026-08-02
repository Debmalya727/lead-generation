import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { NotificationBell } from "../../components/NotificationBell";

// Modular UI Components (Phase 13.5)
import { VoiceWaveformCanvas } from "./components/VoiceWaveformCanvas";
import { LiveTranscriptFeed, TranscriptTurn } from "./components/LiveTranscriptFeed";
import { AIThinkingIndicator } from "./components/AIThinkingIndicator";
import { WorkflowTimeline } from "./components/WorkflowTimeline";
import { SessionMetricsGauges } from "./components/SessionMetricsGauges";
import { HardwareDeviceSelector } from "./components/HardwareDeviceSelector";
import { AudioVoiceSettingsDrawer } from "./components/AudioVoiceSettingsDrawer";
import { DebugConsolePanel, VoiceEvent } from "./components/DebugConsolePanel";
import { StreamingMonitorPanel } from "./components/StreamingMonitorPanel";

interface VoiceSession {
  session_id: string;
  status: string;
  codec: string;
  sample_rate: number;
  connection_quality: string;
  latency_ms: number;
  started_at: string;
}

interface SpeechBenchmark {
  benchmark_id: string;
  provider: string;
  model: string;
  word_error_rate: number;
  avg_latency_ms: number;
  cost_per_min: number;
}

interface TTSBenchmark {
  benchmark_id: string;
  provider: string;
  model: string;
  ttfb_latency_ms: number;
  mos_score: number;
  cost_per_1k_chars: number;
}

interface VoiceCommandLog {
  command_id: string;
  raw_transcript: string;
  intent: string;
  execution_status: string;
  target_workflow_id?: string;
  created_at: string;
}

interface DiarizedSegment {
  segment_id: string;
  speaker_id: string;
  speaker_name: string;
  start_time_sec: number;
  transcript_text: string;
}

interface ActionItem {
  item_id: string;
  action_text: string;
  assignee: string;
  due_date: string;
  status: string;
}

interface MeetingSummary {
  executive_summary: string;
  key_highlights: string[];
  crm_update_status: string;
  followup_email_draft: string;
}

interface AgentDialogueTurn {
  turn_id: string;
  user_transcript: string;
  agent_response: string;
  tool_calls?: any[];
  agent_name?: string;
}

const badge = (label: string, color = "#a5b4fc", bg = "rgba(99,102,241,0.15)") => (
  <span style={{ fontSize: "0.7rem", padding: "0.15rem 0.45rem", borderRadius: "100px", background: bg, color, fontWeight: 700 }}>
    {label}
  </span>
);

export const VoiceWorkspacePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Workspace Mode: "continuous" | "push_to_talk"
  const [audioMode, setAudioMode] = useState<"continuous" | "push_to_talk">("continuous");

  // Navigation tab
  const [activeTab, setActiveTab] = useState<"workspace" | "speech_gateway" | "tts_gateway" | "command_planner" | "meeting_assistant" | "voice_agent" | "telephony">("workspace");

  // Voice Session State
  const [activeSession, setActiveSession] = useState<VoiceSession | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [microphone, setMicrophone] = useState("Default Microphone");
  const [codec, setCodec] = useState("PCM_16BIT");
  const [sampleRate, setSampleRate] = useState(16000);
  const [bitrate, setBitrate] = useState(128000);

  // Telemetry Metrics State
  const [latencyMs] = useState(14.8);
  const [jitterMs] = useState(2.2);
  const [packetLoss] = useState(0.0);
  const [audioLevelDb, setAudioLevelDb] = useState(-55.0);
  const [e2eSpeechToSpeechMs] = useState(485.0);
  const [vadState, setVadState] = useState<"SILENCE" | "SPEECH" | "INTERRUPTION">("SILENCE");

  // Settings Drawer State
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [ttsEmotion, setTtsEmotion] = useState("professional");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [noiseSuppression, setNoiseSuppression] = useState(true);
  const [echoCancellation, setEchoCancellation] = useState(true);

  // AI Thinking & Workflow State
  const [isThinking, setIsThinking] = useState(false);
  const [activeAgent] = useState("Sales Intelligence Agent");
  const [reasoningStep] = useState("Scoring enterprise lead & generating dynamic pitch response");

  // Transcript Feed Turns
  const [transcriptTurns, setTranscriptTurns] = useState<TranscriptTurn[]>([
    {
      id: "turn_1",
      speaker: "user",
      text: "Hi LeadForgeAI, can you give me a summary of my top enterprise leads?",
      confidence: 0.96,
      language: "en-US",
      timestamp: "10:45:12 AM",
    },
    {
      id: "turn_2",
      speaker: "assistant",
      text: "Hello! You have 3 high-intent enterprise leads today: Acme Corp ($120k ARR), TechCorp ($85k ARR), and Global Systems ($150k ARR).",
      timestamp: "10:45:13 AM",
    },
  ]);

  // Event Logs & Benchmarks
  const [eventLogs, setEventLogs] = useState<VoiceEvent[]>([]);
  const [_benchmarks, setBenchmarks] = useState<SpeechBenchmark[]>([]);
  const [_ttsBenchmarks, setTtsBenchmarks] = useState<TTSBenchmark[]>([]);

  // Speech Gateway (13.2) State
  const [sttProvider, setSttProvider] = useState("whisper");
  const [sttModel, setSttModel] = useState("whisper-1");
  const [isTranscribing, setIsTranscribing] = useState(false);

  // TTS Gateway (13.3) State
  const [ttsProvider, setTtsProvider] = useState("elevenlabs");
  const [ttsVoiceId, setTtsVoiceId] = useState("21m00Tcm4TlvDq8ikWAM");
  const [ttsText, _setTtsText] = useState("<speak>Hello! Welcome to LeadForgeAI <break time=\"200ms\"/> Enterprise AI Operating System.</speak>");
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  // Voice Command Planner (13.6) State
  const [commandInput, setCommandInput] = useState("Research Tesla");
  const [isExecutingCommand, setIsExecutingCommand] = useState(false);
  const [_commandLogs, setCommandLogs] = useState<VoiceCommandLog[]>([]);

  // Voice Meeting Assistant (13.7) State
  const [meetingPlatform, setMeetingPlatform] = useState("google_meet");
  const [meetingUrl, setMeetingUrl] = useState("https://meet.google.com/abc-defg-hij");
  const [activeMeetingId, setActiveMeetingId] = useState<string | null>(null);
  const [_isMeetingActive, setIsMeetingActive] = useState(false);
  const [_meetingSegments, setMeetingSegments] = useState<DiarizedSegment[]>([]);
  const [_actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [_meetingSummary, setMeetingSummary] = useState<MeetingSummary | null>(null);
  const [_searchQuery, _setSearchQuery] = useState("");

  // Conversational Voice Agents (13.8) State
  const [selectedPersona, setSelectedPersona] = useState("sdr_persona");
  const [agentSessionId, setAgentSessionId] = useState<string | null>(null);
  const [agentInputText, setAgentInputText] = useState("Can you research Tesla and find CEOs for outreach?");
  const [agentDialogueTurns, setAgentDialogueTurns] = useState<AgentDialogueTurn[]>([]);
  const [handoffStatus, setHandoffStatus] = useState<"none" | "transferred">("none");
  const [isProcessingAgentTurn, setIsProcessingAgentTurn] = useState(false);

  // Enterprise Telephony (13.9) State
  interface TelephonyCall { call_id: string; provider: string; direction: string; status: string; from_number: string; to_number: string; assigned_agent?: string; }
  const [telephonyProvider, setTelephonyProvider] = useState("twilio");
  const [dialToNumber, setDialToNumber] = useState("+14155552671");
  const [dialFromNumber, setDialFromNumber] = useState("+14155550001");
  const [activeCallId, setActiveCallId] = useState<string | null>(null);
  const [activeCallStatus, setActiveCallStatus] = useState("idle");
  const [callLog, setCallLog] = useState<TelephonyCall[]>([]);
  const [queueStats, setQueueStats] = useState<Record<string, { depth: number; avg_wait_seconds: number }>>({});
  const [telephonyProviders, setTelephonyProviders] = useState<Array<{ provider_id: string; display_name: string; available: boolean }>>([]);
  const [sentimentInput, setSentimentInput] = useState("The pricing seems a bit expensive for our budget.");
  const [sentimentResult, setSentimentResult] = useState<any>(null);
  const [isDialing, setIsDialing] = useState(false);
  const [transferTarget, setTransferTarget] = useState("+14155559999");
  const [aiContextResult, setAiContextResult] = useState<any>(null);
  const [objectionType, setObjectionType] = useState("price");
  const [objectionResult, setObjectionResult] = useState<any>(null);

  // Initial Data Fetch
  useEffect(() => {
    fetchEvents();
    fetchBenchmarks();
    fetchTTSBenchmarks();
    fetchCommandHistory();
    fetchTelephonyData();
  }, []);

  const fetchTelephonyData = async () => {
    const token = localStorage.getItem("access_token");
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [callsRes, queueRes, providersRes] = await Promise.all([
        fetch("/api/v1/telephony/calls?limit=20", { headers }),
        fetch("/api/v1/telephony/queue/stats", { headers }),
        fetch("/api/v1/telephony/providers", { headers }),
      ]);
      const calls = await callsRes.json();
      const queue = await queueRes.json();
      const providers = await providersRes.json();
      setCallLog(Array.isArray(calls) ? calls : []);
      setQueueStats(typeof queue === "object" ? queue : {});
      setTelephonyProviders(Array.isArray(providers) ? providers : []);
    } catch {}
  };

  const handleDialOutbound = async () => {
    setIsDialing(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/telephony/call/outbound", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ to_number: dialToNumber, from_number: dialFromNumber, provider_id: telephonyProvider, user_id: user?.id || "user_default", record: true }),
      });
      const data = await res.json();
      setActiveCallId(data.call_id);
      setActiveCallStatus(data.status || "ringing");
      setCallLog(prev => [data, ...prev]);
    } catch (e) { console.error("Dial failed:", e); }
    finally { setIsDialing(false); }
  };

  const handleHangup = async () => {
    if (!activeCallId) return;
    try {
      const token = localStorage.getItem("access_token");
      await fetch("/api/v1/telephony/call/hangup", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ call_id: activeCallId, provider_id: telephonyProvider }),
      });
      setActiveCallStatus("completed");
      setActiveCallId(null);
      fetchTelephonyData();
    } catch {}
  };

  const handleTransfer = async () => {
    if (!activeCallId) return;
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/telephony/call/transfer", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ call_id: activeCallId, target_number: transferTarget, provider_id: telephonyProvider }),
      });
      await res.json();
      setActiveCallStatus("transferred");
    } catch {}
  };

  const handleSentimentAnalysis = async () => {
    if (!activeCallId) return;
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/telephony/call/sentiment", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ call_id: activeCallId, transcript_segment: sentimentInput }),
      });
      const data = await res.json();
      setSentimentResult(data);
    } catch {}
  };

  const handleGetAIContext = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const callId = activeCallId || `ctx_${Date.now()}`;
      const res = await fetch(`/api/v1/telephony/assistant/context?call_id=${callId}&from_number=${dialToNumber}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setAiContextResult(data);
    } catch {}
  };

  const handleGetObjectionHandler = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/telephony/assistant/objection?objection_type=${objectionType}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setObjectionResult(data);
    } catch {}
  };

  const fetchEvents = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/voice/events?limit=30", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setEventLogs(Array.isArray(data) ? data : []);
    } catch {}
  };

  const fetchBenchmarks = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/speech/benchmarks", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setBenchmarks(Array.isArray(data) ? data : []);
    } catch {}
  };

  const fetchTTSBenchmarks = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/tts/benchmarks", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setTtsBenchmarks(Array.isArray(data) ? data : []);
    } catch {}
  };

  const fetchCommandHistory = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/voice/command/history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setCommandLogs(Array.isArray(data) ? data : []);
    } catch {}
  };

  const handleStartSession = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/voice/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          user_id: user?.id || "user_001",
          microphone_name: microphone,
          codec,
          sample_rate: sampleRate,
          bitrate,
        }),
      });
      const data = await res.json();
      setActiveSession(data);
      setIsStreaming(true);
      setVadState("SPEECH");
      setAudioLevelDb(-18.5);
      setIsThinking(true);
      fetchEvents();
    } catch (e) {
      console.error("Failed to start voice session:", e);
    }
  };

  const handleStopSession = async () => {
    if (!activeSession) return;
    try {
      const token = localStorage.getItem("access_token");
      await fetch(`/api/v1/voice/session/stop?session_id=${activeSession.session_id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setActiveSession(null);
      setIsStreaming(false);
      setVadState("SILENCE");
      setAudioLevelDb(-60.0);
      setIsThinking(false);
      fetchEvents();
    } catch (e) {
      console.error("Failed to stop voice session:", e);
    }
  };

  const handleTranscribeSpeech = async () => {
    setIsTranscribing(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/speech/transcribe?provider=${sttProvider}&model=${sttModel}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setTranscriptTurns(prev => [
        ...prev,
        {
          id: `stt_${Date.now()}`,
          speaker: "user",
          text: data.transcript_text,
          confidence: data.confidence_score,
          language: data.detected_language,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (e) {
      console.error("Failed speech transcription:", e);
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleSynthesizeTTS = async () => {
    setIsSynthesizing(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/tts/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          text_prompt: ttsText,
          provider: ttsProvider,
          voice_id: ttsVoiceId,
          emotion: ttsEmotion,
          user_id: user?.id || "user_default",
        }),
      });
      const data = await res.json();
      setTranscriptTurns(prev => [
        ...prev,
        {
          id: `tts_${Date.now()}`,
          speaker: "assistant",
          text: `Synthesized ${data.audio_duration_seconds.toFixed(1)}s audio via ${data.provider_used}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (e) {
      console.error("Failed TTS synthesis:", e);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleExecuteVoiceCommand = async (cmdText?: string) => {
    const textToRun = cmdText || commandInput;
    setIsExecutingCommand(true);
    try {
      const token = localStorage.getItem("access_token");
      await fetch("/api/v1/voice/command/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          transcript: textToRun,
          user_id: user?.id || "user_default",
        }),
      });
      fetchCommandHistory();
    } catch (e) {
      console.error("Failed voice command execution:", e);
    } finally {
      setIsExecutingCommand(false);
    }
  };

  const handleStartMeeting = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/voice/meeting/start", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          meeting_url: meetingUrl,
          title: "Enterprise Discovery & Sales Sync",
          platform: meetingPlatform,
          user_id: user?.id || "user_default",
        }),
      });
      const data = await res.json();
      setActiveMeetingId(data.meeting_id);
      setIsMeetingActive(true);

      const detRes = await fetch(`/api/v1/voice/meeting/${data.meeting_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const detData = await detRes.json();
      setMeetingSegments(detData.segments || []);
    } catch (e) {
      console.error("Failed to start meeting assistant:", e);
    }
  };

  const handleStopMeeting = async () => {
    if (!activeMeetingId) return;
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/voice/meeting/stop?meeting_id=${activeMeetingId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setMeetingSummary(data);
      setIsMeetingActive(false);

      const detRes = await fetch(`/api/v1/voice/meeting/${activeMeetingId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const detData = await detRes.json();
      setActionItems(detData.action_items || []);
    } catch (e) {
      console.error("Failed to stop meeting assistant:", e);
    }
  };

  const handleSendAgentTurn = async (customText?: string) => {
    const textToProcess = customText || agentInputText;
    setIsProcessingAgentTurn(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/voice/agent/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          session_id: agentSessionId,
          persona_id: selectedPersona,
          user_transcript: textToProcess,
          user_id: user?.id || "user_default",
        }),
      });
      const data = await res.json();

      if (data.session_id && !agentSessionId) {
        setAgentSessionId(data.session_id);
      }

      if (data.status === "handed_off") {
        setHandoffStatus("transferred");
      }

      setAgentDialogueTurns(prev => [
        ...prev,
        {
          turn_id: data.turn_id || `turn_${Date.now()}`,
          user_transcript: textToProcess,
          agent_response: data.agent_response,
          tool_calls: data.tool_calls,
          agent_name: data.agent_name,
        },
      ]);
    } catch (e) {
      console.error("Failed voice agent turn:", e);
    } finally {
      setIsProcessingAgentTurn(false);
    }
  };

  const handleTriggerHandoff = async () => {
    if (!agentSessionId) return;
    try {
      const token = localStorage.getItem("access_token");
      await fetch("/api/v1/voice/agent/handoff", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          session_id: agentSessionId,
          reason: "User manually requested human handoff from UI button",
        }),
      });
      setHandoffStatus("transferred");
    } catch (e) {
      console.error("Failed human handoff:", e);
    }
  };

  const workflowSteps = [
    { name: "VAD Ingest", status: (isStreaming ? "completed" : "pending") as any, latency_ms: 12.5 },
    { name: "Streaming STT", status: (isStreaming ? "completed" : "pending") as any, latency_ms: 110.0 },
    { name: "Conversation Manager", status: (isStreaming ? "completed" : "pending") as any, latency_ms: 25.0 },
    { name: "AI Planner", status: (isStreaming ? "active" : "pending") as any, latency_ms: 180.0 },
    { name: "Streaming LLM", status: (isStreaming ? "active" : "pending") as any, latency_ms: 95.0 },
    { name: "Streaming TTS", status: (isStreaming ? "active" : "pending") as any, latency_ms: 65.0 },
    { name: "Audio Stream Out", status: (isStreaming ? "completed" : "pending") as any, latency_ms: 15.0 },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Header Navigation */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Enterprise Voice Workspace</div>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: "flex", gap: "0.4rem" }}>
          <button onClick={() => setActiveTab("workspace")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "workspace" ? "1px solid #6366f1" : "1px solid transparent", background: activeTab === "workspace" ? "rgba(99,102,241,0.2)" : "none", color: activeTab === "workspace" ? "#a5b4fc" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            🎙️ Workspace UI
          </button>
          <button onClick={() => setActiveTab("speech_gateway")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "speech_gateway" ? "1px solid #6366f1" : "1px solid transparent", background: activeTab === "speech_gateway" ? "rgba(99,102,241,0.2)" : "none", color: activeTab === "speech_gateway" ? "#a5b4fc" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            🗣️ Speech (13.2)
          </button>
          <button onClick={() => setActiveTab("tts_gateway")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "tts_gateway" ? "1px solid #6366f1" : "1px solid transparent", background: activeTab === "tts_gateway" ? "rgba(99,102,241,0.2)" : "none", color: activeTab === "tts_gateway" ? "#a5b4fc" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            🔊 TTS (13.3)
          </button>
          <button onClick={() => setActiveTab("command_planner")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "command_planner" ? "1px solid #f59e0b" : "1px solid transparent", background: activeTab === "command_planner" ? "rgba(245,158,11,0.2)" : "none", color: activeTab === "command_planner" ? "#fbbf24" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            🧠 Command (13.6)
          </button>
          <button onClick={() => setActiveTab("meeting_assistant")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "meeting_assistant" ? "1px solid #34d399" : "1px solid transparent", background: activeTab === "meeting_assistant" ? "rgba(52,211,153,0.2)" : "none", color: activeTab === "meeting_assistant" ? "#34d399" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            👥 Meeting (13.7)
          </button>
          <button onClick={() => setActiveTab("voice_agent")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "voice_agent" ? "1px solid #ec4899" : "1px solid transparent", background: activeTab === "voice_agent" ? "rgba(236,72,153,0.2)" : "none", color: activeTab === "voice_agent" ? "#f472b6" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            🤖 Voice Agent (13.8)
          </button>
          <button onClick={() => setActiveTab("telephony")} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: activeTab === "telephony" ? "1px solid #f97316" : "1px solid transparent", background: activeTab === "telephony" ? "rgba(249,115,22,0.2)" : "none", color: activeTab === "telephony" ? "#fb923c" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
            📞 Telephony (13.9)
          </button>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button onClick={() => setIsSettingsOpen(true)} style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 0.85rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>⚙️ Settings</button>
          <button onClick={() => navigate("/voice/analytics")} style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.3)", color: "#34d399", padding: "0.4rem 0.85rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem", fontWeight: 600 }}>📊 Analytics</button>
          <NotificationBell />
          <button onClick={() => navigate("/ai")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>🤖 AI Dashboard</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      {/* Settings Drawer */}
      <AudioVoiceSettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        ttsEmotion={ttsEmotion}
        setTtsEmotion={setTtsEmotion}
        speed={speed}
        setSpeed={setSpeed}
        pitch={pitch}
        setPitch={setPitch}
        noiseSuppression={noiseSuppression}
        setNoiseSuppression={setNoiseSuppression}
        echoCancellation={echoCancellation}
        setEchoCancellation={setEchoCancellation}
      />

      {/* Main Container */}
      <main style={{ flex: 1, padding: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "1400px", margin: "0 auto", width: "100%", boxSizing: "border-box" }}>

        {activeTab === "workspace" ? (
          <>
            {/* Quick Action Toolbar & Audio Mode Switcher */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1rem 1.5rem" }}>
              <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#a5b4fc" }}>Audio Mode:</span>
                <button onClick={() => setAudioMode("continuous")} style={{ padding: "0.4rem 0.85rem", borderRadius: "6px", border: audioMode === "continuous" ? "1px solid #10b981" : "1px solid transparent", background: audioMode === "continuous" ? "rgba(16,185,129,0.2)" : "none", color: audioMode === "continuous" ? "#34d399" : "#94a3b8", fontSize: "0.82rem", fontWeight: 600, cursor: "pointer" }}>⚡ Continuous Duplex</button>
                <button onClick={() => setAudioMode("push_to_talk")} style={{ padding: "0.4rem 0.85rem", borderRadius: "6px", border: audioMode === "push_to_talk" ? "1px solid #6366f1" : "1px solid transparent", background: audioMode === "push_to_talk" ? "rgba(99,102,241,0.2)" : "none", color: audioMode === "push_to_talk" ? "#a5b4fc" : "#94a3b8", fontSize: "0.82rem", fontWeight: 600, cursor: "pointer" }}>🎙️ Push-to-Talk (Spacebar)</button>
              </div>

              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button onClick={() => setIsMuted(!isMuted)} style={{ background: isMuted ? "rgba(239,68,68,0.2)" : "rgba(99,102,241,0.15)", border: isMuted ? "1px solid rgba(239,68,68,0.4)" : "1px solid rgba(99,102,241,0.3)", color: isMuted ? "#f87171" : "#a5b4fc", padding: "0.45rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem", fontWeight: 600 }}>
                  {isMuted ? "🔇 Muted" : "🎙️ Microphone Active"}
                </button>
                {!isStreaming ? (
                  <button onClick={handleStartSession} style={{ padding: "0.45rem 1.25rem", borderRadius: "6px", border: "none", background: "linear-gradient(135deg, #10b981, #059669)", color: "#fff", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}>
                    🚀 Start Voice Session
                  </button>
                ) : (
                  <button onClick={handleStopSession} style={{ padding: "0.45rem 1.25rem", borderRadius: "6px", background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.4)", color: "#f87171", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}>
                    ⏹ Stop Session ({activeSession?.session_id})
                  </button>
                )}
              </div>
            </div>

            {/* 60fps Dual Audio Waveform Canvas */}
            <VoiceWaveformCanvas isStreaming={isStreaming} vadState={vadState} audioLevelDb={audioLevelDb} />

            {/* AI Thinking Visualizer */}
            <AIThinkingIndicator isThinking={isThinking} activeAgent={activeAgent} reasoningStep={reasoningStep} />

            {/* Voice Workflow Execution Timeline */}
            <WorkflowTimeline steps={workflowSteps} />

            {/* Real-time Telemetry Gauges */}
            <SessionMetricsGauges latencyMs={latencyMs} jitterMs={jitterMs} packetLoss={packetLoss} audioLevelDb={audioLevelDb} e2eSpeechToSpeechMs={e2eSpeechToSpeechMs} />

            {/* Controls & Split Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
              <LiveTranscriptFeed turns={transcriptTurns} onClear={() => setTranscriptTurns([])} />
              <DebugConsolePanel logs={eventLogs} />
            </div>

            {/* Hardware Selector & Network Streaming Monitor Split */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
              <HardwareDeviceSelector microphone={microphone} setMicrophone={setMicrophone} codec={codec} setCodec={setCodec} sampleRate={sampleRate} setSampleRate={setSampleRate} bitrate={bitrate} setBitrate={setBitrate} />
              <StreamingMonitorPanel bandwidthKbps={128} frameQueueDepth={2} droppedFrames={0} bufferHealthPct={99} />
            </div>
          </>
        ) : activeTab === "speech_gateway" ? (
          /* SPEECH RECOGNITION GATEWAY TAB (13.2) */
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "16px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>🗣️ Speech Recognition Provider Gateway (13.2)</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
                <div>
                  <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>STT Provider</label>
                  <select value={sttProvider} onChange={e => setSttProvider(e.target.value)} style={{ width: "100%", padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
                    <option value="whisper">OpenAI Whisper</option>
                    <option value="faster_whisper">Faster Whisper (Local)</option>
                    <option value="deepgram">Deepgram (Nova-2)</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>STT Model</label>
                  <select value={sttModel} onChange={e => setSttModel(e.target.value)} style={{ width: "100%", padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
                    <option value="whisper-1">whisper-1 ($0.006/min)</option>
                    <option value="faster-whisper-large-v3">faster-whisper-large-v3 ($0.001/min)</option>
                  </select>
                </div>
                <div style={{ display: "flex", alignItems: "flex-end" }}>
                  <button onClick={handleTranscribeSpeech} disabled={isTranscribing} style={{ width: "100%", padding: "0.65rem", borderRadius: "6px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
                    {isTranscribing ? "⏳ Transcribing..." : "⚡ Transcribe Audio"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === "tts_gateway" ? (
          /* TEXT-TO-SPEECH GATEWAY TAB (13.3) */
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "16px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>🔊 Text-to-Speech (TTS) Gateway (13.3)</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
                <div>
                  <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>TTS Provider</label>
                  <select value={ttsProvider} onChange={e => setTtsProvider(e.target.value)} style={{ width: "100%", padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
                    <option value="elevenlabs">ElevenLabs Multilingual</option>
                    <option value="openai">OpenAI TTS (tts-1)</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Voice Profile</label>
                  <select value={ttsVoiceId} onChange={e => setTtsVoiceId(e.target.value)} style={{ width: "100%", padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
                    <option value="21m00Tcm4TlvDq8ikWAM">Rachel (ElevenLabs - $0.015/1k)</option>
                  </select>
                </div>
                <div style={{ display: "flex", alignItems: "flex-end" }}>
                  <button onClick={handleSynthesizeTTS} disabled={isSynthesizing} style={{ width: "100%", padding: "0.65rem", borderRadius: "6px", border: "none", background: "linear-gradient(135deg, #8b5cf6, #6366f1)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
                    {isSynthesizing ? "⏳ Synthesizing..." : "🔊 Synthesize Speech"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === "command_planner" ? (
          /* VOICE COMMAND PLANNER TAB (13.6) */
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(245,158,11,0.3)", borderRadius: "16px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "#fbbf24" }}>🧠 Voice Command AI Planner Integration (13.6)</h2>
              <div style={{ display: "flex", gap: "1rem" }}>
                <input type="text" value={commandInput} onChange={e => setCommandInput(e.target.value)} style={{ flex: 1, padding: "0.75rem", borderRadius: "8px", background: "#0a0f1e", border: "1px solid rgba(245,158,11,0.3)", color: "#fff" }} />
                <button onClick={() => handleExecuteVoiceCommand()} disabled={isExecutingCommand} style={{ padding: "0.75rem 1.5rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #f59e0b, #d97706)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
                  {isExecutingCommand ? "⏳ Planning..." : "🚀 Execute Command"}
                </button>
              </div>
            </div>
          </div>
        ) : activeTab === "meeting_assistant" ? (
          /* ENTERPRISE VOICE MEETING ASSISTANT TAB (13.7) */
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "16px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "#34d399" }}>👥 Enterprise AI Meeting Assistant (13.7)</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", gap: "1rem" }}>
                <select value={meetingPlatform} onChange={e => setMeetingPlatform(e.target.value)} style={{ padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(52,211,153,0.3)", color: "#fff" }}>
                  <option value="google_meet">Google Meet</option>
                  <option value="teams">Microsoft Teams</option>
                  <option value="zoom">Zoom</option>
                </select>
                <input type="text" value={meetingUrl} onChange={e => setMeetingUrl(e.target.value)} style={{ padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(52,211,153,0.3)", color: "#fff" }} />
                <button onClick={handleStartMeeting} style={{ padding: "0.65rem", borderRadius: "6px", border: "none", background: "linear-gradient(135deg, #10b981, #059669)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>Connect Bot</button>
                <button onClick={handleStopMeeting} style={{ padding: "0.65rem", borderRadius: "6px", background: "rgba(239,68,68,0.2)", color: "#f87171", fontWeight: 700, cursor: "pointer", border: "1px solid rgba(239,68,68,0.4)" }}>Stop Bot</button>
              </div>
            </div>
          </div>
        ) : (
          /* CONVERSATIONAL VOICE AGENTS TAB (13.8) */
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

            {/* Persona Selector & Controller Header */}
            <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(236,72,153,0.3)", borderRadius: "16px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "#f472b6" }}>🤖 Conversational Voice AI Agents</h2>
                  <p style={{ color: "#64748b", fontSize: "0.8rem", margin: "0.2rem 0 0 0" }}>Multi-turn dialogue, voice memory, dynamic tool calling & human handoff</p>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {badge(handoffStatus === "transferred" ? "HUMAN TRANSFERRED" : "AI AGENT ACTIVE", handoffStatus === "transferred" ? "#f87171" : "#f472b6", handoffStatus === "transferred" ? "rgba(239,68,68,0.2)" : "rgba(236,72,153,0.15)")}
                </div>
              </div>

              {/* Persona Palette */}
              <div>
                <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.4rem" }}>Select Agent Voice Persona</label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
                  {[
                    { id: "sdr_persona", name: "Sarah (Sales SDR)", desc: "Proactive lead qualification & demo booking" },
                    { id: "tech_architect_persona", name: "Alex (Solutions Architect)", desc: "Deep technical architecture & latency review" },
                    { id: "support_persona", name: "Maya (Support Specialist)", desc: "Diagnostic support & API troubleshooting" },
                  ].map(p => (
                    <div
                      key={p.id}
                      onClick={() => setSelectedPersona(p.id)}
                      style={{ padding: "0.85rem", borderRadius: "10px", background: selectedPersona === p.id ? "rgba(236,72,153,0.2)" : "#0a0f1e", border: selectedPersona === p.id ? "1px solid #f472b6" : "1px solid rgba(255,255,255,0.05)", cursor: "pointer" }}
                    >
                      <div style={{ fontWeight: 700, color: selectedPersona === p.id ? "#f472b6" : "#fff", fontSize: "0.9rem" }}>{p.name}</div>
                      <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>{p.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Input Box & Action Buttons */}
              <div style={{ display: "flex", gap: "1rem" }}>
                <input
                  type="text"
                  value={agentInputText}
                  onChange={e => setAgentInputText(e.target.value)}
                  placeholder="Type or speak turn... (e.g., 'Can you research Tesla and find CEOs?')"
                  style={{ flex: 1, padding: "0.75rem", borderRadius: "8px", background: "#0a0f1e", border: "1px solid rgba(236,72,153,0.3)", color: "#fff", fontSize: "0.9rem" }}
                />
                <button
                  onClick={() => handleSendAgentTurn()}
                  disabled={isProcessingAgentTurn}
                  style={{ padding: "0.75rem 1.5rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #ec4899, #db2777)", color: "#fff", fontWeight: 700, fontSize: "0.9rem", cursor: "pointer" }}
                >
                  {isProcessingAgentTurn ? "⏳ Thinking..." : "🎙️ Speak Turn"}
                </button>
                <button
                  onClick={handleTriggerHandoff}
                  style={{ padding: "0.75rem 1.25rem", borderRadius: "8px", background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.4)", color: "#f87171", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}
                >
                  🙋‍♂️ Human Handoff
                </button>
              </div>
            </div>

            {/* Handoff Alert Banner */}
            {handoffStatus === "transferred" && (
              <div style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)", borderRadius: "12px", padding: "1rem", color: "#f87171", fontWeight: 600, fontSize: "0.9rem" }}>
                🚨 Session Handed Off: Call context transferred to Human Sales Representative Queue (#tier1_sales_reps).
              </div>
            )}

            {/* Multi-Turn Dialogue Feed & Tool Calling Log */}
            <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
              <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>💬 Multi-Turn Voice Agent Dialogue Feed</h3>

              <div style={{ display: "flex", flexDirection: "column", gap: "1rem", maxHeight: "400px", overflowY: "auto" }}>
                {agentDialogueTurns.length === 0 ? (
                  <div style={{ color: "#64748b", textAlign: "center", padding: "2rem" }}>Select a persona and send a speech turn to begin multi-turn conversation.</div>
                ) : (
                  agentDialogueTurns.map(turn => (
                    <div key={turn.turn_id} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "8px", padding: "1rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#60a5fa" }}>👤 User:</span>
                        <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Turn ID: {turn.turn_id}</span>
                      </div>
                      <div style={{ color: "#fff", fontSize: "0.9rem" }}>"{turn.user_transcript}"</div>

                      <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "0.5rem", marginTop: "0.25rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#f472b6" }}>🤖 {turn.agent_name || "Voice Agent"}:</span>
                          {turn.tool_calls && turn.tool_calls.length > 0 && badge("TOOL EXECUTED", "#34d399", "rgba(52,211,153,0.15)")}
                        </div>
                        <div style={{ color: "#e2e8f0", fontSize: "0.9rem", marginTop: "0.2rem" }}>"{turn.agent_response}"</div>

                        {turn.tool_calls && turn.tool_calls.length > 0 && (
                          <div style={{ background: "rgba(0,0,0,0.4)", borderRadius: "6px", padding: "0.5rem", marginTop: "0.5rem", fontSize: "0.78rem", color: "#34d399", fontFamily: "monospace" }}>
                            🛠️ Tool Called: {turn.tool_calls[0].tool} → {JSON.stringify(turn.tool_calls[0].result)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════ */}
        {/* PHASE 13.9 — ENTERPRISE TELEPHONY INTEGRATION                         */}
        {/* ═══════════════════════════════════════════════════════════════════════ */}
        {activeTab === "telephony" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

            {/* Header */}
            <div style={{ background: "linear-gradient(135deg, rgba(249,115,22,0.15), rgba(234,88,12,0.08))", border: "1px solid rgba(249,115,22,0.3)", borderRadius: "14px", padding: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ margin: 0, fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #fb923c, #f97316)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>📞 Enterprise Telephony Integration</h2>
                <p style={{ margin: "0.3rem 0 0", color: "#94a3b8", fontSize: "0.9rem" }}>Phase 13.9 — Twilio · SIP · Zoom Phone · Microsoft Teams Phone</p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {badge("Inbound", "#34d399", "rgba(52,211,153,0.15)")}
                {badge("Outbound", "#60a5fa", "rgba(96,165,250,0.15)")}
                {badge("Recording", "#f87171", "rgba(248,113,113,0.15)")}
                {badge("AI Assistant", "#a5b4fc", "rgba(99,102,241,0.15)")}
                {badge("Queue Mgmt", "#fbbf24", "rgba(251,191,36,0.15)")}
              </div>
            </div>

            {/* Row 1: Dialer + Active Call Controls */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>

              {/* Outbound Dialer */}
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#fb923c" }}>📲 Outbound Dialer</h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  <label style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>Provider</label>
                  <select value={telephonyProvider} onChange={e => setTelephonyProvider(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(249,115,22,0.25)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.88rem" }}>
                    {telephonyProviders.length > 0 ? telephonyProviders.map(p => (
                      <option key={p.provider_id} value={p.provider_id}>{p.display_name}</option>
                    )) : [
                      <option key="twilio" value="twilio">Twilio Voice</option>,
                      <option key="sip" value="sip">SIP / VoIP (RFC 3261)</option>,
                      <option key="zoom_phone" value="zoom_phone">Zoom Phone</option>,
                      <option key="teams_phone" value="teams_phone">Microsoft Teams Phone</option>,
                    ]}
                  </select>

                  <label style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>To Number (E.164)</label>
                  <input value={dialToNumber} onChange={e => setDialToNumber(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(249,115,22,0.25)", color: "#e2e8f0", padding: "0.5rem 0.75rem", borderRadius: "6px", fontSize: "0.88rem" }} placeholder="+14155552671" />

                  <label style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>From Number (DID)</label>
                  <input value={dialFromNumber} onChange={e => setDialFromNumber(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(249,115,22,0.25)", color: "#e2e8f0", padding: "0.5rem 0.75rem", borderRadius: "6px", fontSize: "0.88rem" }} placeholder="+14155550001" />
                </div>

                <button onClick={handleDialOutbound} disabled={isDialing} style={{ padding: "0.65rem 1.25rem", borderRadius: "8px", border: "none", background: isDialing ? "rgba(100,100,100,0.5)" : "linear-gradient(135deg, #f97316, #ea580c)", color: "#fff", fontWeight: 700, fontSize: "0.9rem", cursor: isDialing ? "default" : "pointer", transition: "all 0.2s" }}>
                  {isDialing ? "⏳ Dialing..." : "📞 Place Call"}
                </button>

                {activeCallId && (
                  <div style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: "8px", padding: "0.75rem", fontSize: "0.82rem" }}>
                    <div style={{ color: "#34d399", fontWeight: 700 }}>✅ Active Call</div>
                    <div style={{ color: "#94a3b8", marginTop: "0.2rem", fontFamily: "monospace" }}>{activeCallId}</div>
                    <div style={{ color: "#fbbf24", fontWeight: 600, marginTop: "0.2rem", textTransform: "uppercase", fontSize: "0.75rem" }}>Status: {activeCallStatus}</div>
                  </div>
                )}
              </div>

              {/* Active Call Controls */}
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#fb923c" }}>🎛️ Call Controls</h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  <label style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>Transfer To (E.164)</label>
                  <input value={transferTarget} onChange={e => setTransferTarget(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(99,102,241,0.25)", color: "#e2e8f0", padding: "0.5rem 0.75rem", borderRadius: "6px", fontSize: "0.88rem" }} placeholder="+14155559999" />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  <button onClick={handleTransfer} disabled={!activeCallId} style={{ padding: "0.6rem", borderRadius: "8px", border: "1px solid rgba(96,165,250,0.4)", background: "rgba(96,165,250,0.1)", color: "#60a5fa", fontWeight: 700, fontSize: "0.85rem", cursor: activeCallId ? "pointer" : "not-allowed", opacity: activeCallId ? 1 : 0.4 }}>🔀 Transfer</button>
                  <button onClick={handleHangup} disabled={!activeCallId} style={{ padding: "0.6rem", borderRadius: "8px", border: "1px solid rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.15)", color: "#f87171", fontWeight: 700, fontSize: "0.85rem", cursor: activeCallId ? "pointer" : "not-allowed", opacity: activeCallId ? 1 : 0.4 }}>📵 Hang Up</button>
                </div>

                {/* Queue Stats */}
                <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(251,191,36,0.2)", borderRadius: "8px", padding: "0.75rem" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#fbbf24", marginBottom: "0.5rem" }}>📊 Live Queue Stats</div>
                  {Object.keys(queueStats).length > 0 ? (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
                      {Object.entries(queueStats).map(([key, stats]) => (
                        <div key={key} style={{ background: "rgba(255,255,255,0.03)", borderRadius: "6px", padding: "0.4rem 0.6rem", fontSize: "0.78rem" }}>
                          <div style={{ color: "#a5b4fc", fontWeight: 700, textTransform: "capitalize" }}>{key}</div>
                          <div style={{ color: "#64748b" }}>Depth: <span style={{ color: "#fbbf24" }}>{stats.depth}</span> | Avg Wait: <span style={{ color: "#34d399" }}>{stats.avg_wait_seconds}s</span></div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
                      {["sales", "enterprise", "support", "general"].map(q => (
                        <div key={q} style={{ background: "rgba(255,255,255,0.03)", borderRadius: "6px", padding: "0.4rem 0.6rem", fontSize: "0.78rem" }}>
                          <div style={{ color: "#a5b4fc", fontWeight: 700, textTransform: "capitalize" }}>{q}</div>
                          <div style={{ color: "#64748b" }}>Depth: <span style={{ color: "#fbbf24" }}>0</span> | Avg Wait: <span style={{ color: "#34d399" }}>0.0s</span></div>
                        </div>
                      ))}
                    </div>
                  )}
                  <button onClick={fetchTelephonyData} style={{ marginTop: "0.5rem", fontSize: "0.78rem", background: "none", border: "none", color: "#64748b", cursor: "pointer" }}>↻ Refresh</button>
                </div>
              </div>
            </div>

            {/* Row 2: AI Call Assistant */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>

              {/* Pre-call Context & Sentiment */}
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>🧠 AI Call Assistant</h3>

                <div style={{ display: "flex", gap: "0.6rem" }}>
                  <button onClick={handleGetAIContext} style={{ flex: 1, padding: "0.6rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.4)", background: "rgba(99,102,241,0.15)", color: "#a5b4fc", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}>📋 Get Call Context</button>
                </div>

                {aiContextResult && (
                  <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(99,102,241,0.15)", borderRadius: "8px", padding: "0.75rem", fontSize: "0.82rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                    <div style={{ color: "#a5b4fc", fontWeight: 700 }}>🏢 {aiContextResult.company} — Score: <span style={{ color: "#34d399" }}>{aiContextResult.lead_score}/100</span></div>
                    <div style={{ color: "#fbbf24", fontWeight: 600 }}>Stage: {aiContextResult.stage} | Prior Calls: {aiContextResult.previous_calls}</div>
                    <div style={{ color: "#94a3b8" }}>📝 {aiContextResult.notes}</div>
                    <div style={{ marginTop: "0.3rem" }}>
                      <div style={{ color: "#60a5fa", fontWeight: 600, marginBottom: "0.3rem" }}>💬 Suggested Talking Points:</div>
                      {(aiContextResult.talking_points || []).map((p: string, i: number) => (
                        <div key={i} style={{ color: "#94a3b8", fontSize: "0.8rem", paddingLeft: "0.5rem", borderLeft: "2px solid rgba(99,102,241,0.4)", marginBottom: "0.2rem" }}>• {p}</div>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "0.75rem" }}>
                  <label style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>🎭 Live Sentiment Analysis</label>
                  <textarea value={sentimentInput} onChange={e => setSentimentInput(e.target.value)} style={{ width: "100%", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(239,68,68,0.2)", color: "#e2e8f0", padding: "0.5rem 0.75rem", borderRadius: "6px", fontSize: "0.85rem", resize: "none", height: "60px", boxSizing: "border-box" }} />
                  <button onClick={handleSentimentAnalysis} disabled={!activeCallId} style={{ marginTop: "0.4rem", padding: "0.5rem 0.85rem", borderRadius: "6px", border: "1px solid rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.1)", color: "#f87171", fontWeight: 700, fontSize: "0.82rem", cursor: activeCallId ? "pointer" : "not-allowed", opacity: activeCallId ? 1 : 0.5 }}>🔬 Analyze Sentiment</button>

                  {sentimentResult && (
                    <div style={{ marginTop: "0.5rem", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "0.6rem", fontSize: "0.82rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ color: sentimentResult.score > 0.7 ? "#34d399" : sentimentResult.score > 0.45 ? "#fbbf24" : "#f87171", fontWeight: 700, textTransform: "uppercase" }}>{sentimentResult.sentiment}</span>
                        <span style={{ color: "#94a3b8" }}>Score: {(sentimentResult.score * 100).toFixed(0)}%</span>
                      </div>
                      {sentimentResult.coaching_tip && (
                        <div style={{ color: "#a5b4fc", marginTop: "0.3rem", fontSize: "0.8rem" }}>💡 {sentimentResult.coaching_tip}</div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Objection Handler */}
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(234,179,8,0.2)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#fbbf24" }}>🛡️ Objection Handler</h3>

                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {["price", "timing", "competition"].map(o => (
                    <button key={o} onClick={() => setObjectionType(o)} style={{ flex: 1, padding: "0.5rem", borderRadius: "6px", border: objectionType === o ? "1px solid #fbbf24" : "1px solid transparent", background: objectionType === o ? "rgba(251,191,36,0.15)" : "rgba(255,255,255,0.04)", color: objectionType === o ? "#fbbf24" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer", textTransform: "capitalize" }}>{o}</button>
                  ))}
                </div>

                <button onClick={handleGetObjectionHandler} style={{ padding: "0.6rem", borderRadius: "8px", border: "1px solid rgba(251,191,36,0.4)", background: "rgba(251,191,36,0.15)", color: "#fbbf24", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}>Get Script →</button>

                {objectionResult && !objectionResult.error && (
                  <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(251,191,36,0.15)", borderRadius: "8px", padding: "0.75rem", fontSize: "0.82rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    <div>
                      <span style={{ color: "#f87171", fontWeight: 700 }}>Objection: </span>
                      <span style={{ color: "#e2e8f0" }}>{objectionResult.objection}</span>
                    </div>
                    <div>
                      <span style={{ color: "#34d399", fontWeight: 700 }}>Response: </span>
                      <span style={{ color: "#94a3b8" }}>{objectionResult.response}</span>
                    </div>
                    <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "0.4rem" }}>
                      <span style={{ color: "#a5b4fc", fontWeight: 700 }}>Next Step: </span>
                      <span style={{ color: "#64748b" }}>{objectionResult.next_step}</span>
                    </div>
                  </div>
                )}

                {/* Provider Status */}
                <div style={{ marginTop: "auto" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#94a3b8", marginBottom: "0.5rem" }}>📡 Provider Status</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                    {(telephonyProviders.length > 0 ? telephonyProviders : [
                      { provider_id: "twilio", display_name: "Twilio Voice", available: true },
                      { provider_id: "sip", display_name: "SIP / VoIP", available: true },
                      { provider_id: "zoom_phone", display_name: "Zoom Phone", available: true },
                      { provider_id: "teams_phone", display_name: "MS Teams Phone", available: true },
                    ]).map(p => (
                      <div key={p.provider_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(255,255,255,0.03)", borderRadius: "6px", padding: "0.4rem 0.6rem" }}>
                        <span style={{ color: "#e2e8f0", fontSize: "0.82rem" }}>{p.display_name}</span>
                        <span style={{ fontSize: "0.72rem", fontWeight: 700, color: p.available ? "#34d399" : "#f87171", background: p.available ? "rgba(52,211,153,0.1)" : "rgba(248,113,113,0.1)", padding: "0.15rem 0.5rem", borderRadius: "100px" }}>{p.available ? "● ONLINE" : "● OFFLINE"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Row 3: Call Log */}
            <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#fb923c" }}>📋 Call History</h3>
                <button onClick={fetchTelephonyData} style={{ fontSize: "0.8rem", background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.3)", color: "#fb923c", padding: "0.35rem 0.75rem", borderRadius: "6px", cursor: "pointer" }}>↻ Refresh</button>
              </div>

              {callLog.length === 0 ? (
                <div style={{ color: "#64748b", textAlign: "center", padding: "2rem", fontSize: "0.9rem" }}>No calls recorded yet. Use the Outbound Dialer or simulate an inbound call.</div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                        {["Call ID", "Provider", "Direction", "Status", "From", "To", "Agent"].map(h => (
                          <th key={h} style={{ padding: "0.5rem 0.75rem", textAlign: "left", color: "#64748b", fontWeight: 700, fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {callLog.map((c, i) => (
                        <tr key={c.call_id || i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", transition: "background 0.15s" }}>
                          <td style={{ padding: "0.5rem 0.75rem", color: "#a5b4fc", fontFamily: "monospace", fontSize: "0.78rem" }}>{(c.call_id || "").substring(0, 16)}...</td>
                          <td style={{ padding: "0.5rem 0.75rem", color: "#e2e8f0", textTransform: "capitalize" }}>{c.provider}</td>
                          <td style={{ padding: "0.5rem 0.75rem" }}>{badge(c.direction, c.direction === "inbound" ? "#34d399" : "#60a5fa", c.direction === "inbound" ? "rgba(52,211,153,0.1)" : "rgba(96,165,250,0.1)")}</td>
                          <td style={{ padding: "0.5rem 0.75rem" }}>{badge(c.status || "unknown", c.status === "completed" ? "#34d399" : c.status === "ringing" ? "#fbbf24" : c.status === "in_progress" ? "#60a5fa" : "#f87171", "rgba(0,0,0,0.2)")}</td>
                          <td style={{ padding: "0.5rem 0.75rem", color: "#94a3b8", fontFamily: "monospace" }}>{c.from_number}</td>
                          <td style={{ padding: "0.5rem 0.75rem", color: "#94a3b8", fontFamily: "monospace" }}>{c.to_number}</td>
                          <td style={{ padding: "0.5rem 0.75rem", color: "#64748b", fontSize: "0.78rem" }}>{c.assigned_agent || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

          </div>
        )}

      </main>
    </div>
  );
};

export default VoiceWorkspacePage;
