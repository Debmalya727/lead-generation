import React from "react";

interface AudioVoiceSettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ttsEmotion: string;
  setTtsEmotion: (emotion: string) => void;
  speed: number;
  setSpeed: (s: number) => void;
  pitch: number;
  setPitch: (p: number) => void;
  noiseSuppression: boolean;
  setNoiseSuppression: (ns: boolean) => void;
  echoCancellation: boolean;
  setEchoCancellation: (ec: boolean) => void;
}

export const AudioVoiceSettingsDrawer: React.FC<AudioVoiceSettingsDrawerProps> = ({
  isOpen,
  onClose,
  ttsEmotion,
  setTtsEmotion,
  speed,
  setSpeed,
  pitch,
  setPitch,
  noiseSuppression,
  setNoiseSuppression,
  echoCancellation,
  setEchoCancellation,
}) => {
  if (!isOpen) return null;

  return (
    <div style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: "360px", background: "rgba(15,23,42,0.98)", borderLeft: "1px solid rgba(99,102,241,0.3)", padding: "1.5rem", zIndex: 1000, display: "flex", flexDirection: "column", gap: "1.25rem", backdropFilter: "blur(16px)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "#a5b4fc" }}>⚙️ Voice & Audio Settings</h3>
        <button onClick={onClose} style={{ background: "none", border: "none", color: "#f87171", fontSize: "1.2rem", cursor: "pointer" }}>✕</button>
      </div>

      <div>
        <label style={{ fontSize: "0.8rem", color: "#64748b", display: "block", marginBottom: "0.3rem" }}>Emotion Preset</label>
        <select value={ttsEmotion} onChange={e => setTtsEmotion(e.target.value)} style={{ width: "100%", padding: "0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
          <option value="professional">Professional (1.0x pitch/rate)</option>
          <option value="cheerful">Cheerful (1.15x rate, 1.1x pitch)</option>
          <option value="empathetic">Empathetic (0.9x rate, 0.95x pitch)</option>
          <option value="urgent">Urgent (1.25x rate, 1.05x pitch)</option>
        </select>
      </div>

      <div>
        <label style={{ fontSize: "0.8rem", color: "#64748b", display: "block", marginBottom: "0.3rem" }}>Speech Speed ({speed.toFixed(2)}x)</label>
        <input type="range" min="0.5" max="2.0" step="0.05" value={speed} onChange={e => setSpeed(Number(e.target.value))} style={{ width: "100%" }} />
      </div>

      <div>
        <label style={{ fontSize: "0.8rem", color: "#64748b", display: "block", marginBottom: "0.3rem" }}>Voice Pitch ({pitch.toFixed(2)}x)</label>
        <input type="range" min="0.5" max="1.5" step="0.05" value={pitch} onChange={e => setPitch(Number(e.target.value))} style={{ width: "100%" }} />
      </div>

      <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.85rem", color: "#e2e8f0" }}>Noise Suppression Filter</span>
          <input type="checkbox" checked={noiseSuppression} onChange={e => setNoiseSuppression(e.target.checked)} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.85rem", color: "#e2e8f0" }}>Acoustic Echo Cancellation</span>
          <input type="checkbox" checked={echoCancellation} onChange={e => setEchoCancellation(e.target.checked)} />
        </div>
      </div>
    </div>
  );
};
