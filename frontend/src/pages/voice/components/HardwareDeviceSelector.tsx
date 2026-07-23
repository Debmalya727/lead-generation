import React from "react";

interface HardwareDeviceSelectorProps {
  microphone: string;
  setMicrophone: (mic: string) => void;
  codec: string;
  setCodec: (codec: string) => void;
  sampleRate: number;
  setSampleRate: (rate: number) => void;
  bitrate: number;
  setBitrate: (bitrate: number) => void;
}

export const HardwareDeviceSelector: React.FC<HardwareDeviceSelectorProps> = ({
  microphone,
  setMicrophone,
  codec,
  setCodec,
  sampleRate,
  setSampleRate,
  bitrate,
  setBitrate,
}) => {
  return (
    <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>🎛️ Hardware Device & Audio Format Selector</h3>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
        <div>
          <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Microphone Device</label>
          <select value={microphone} onChange={e => setMicrophone(e.target.value)} style={{ width: "100%", padding: "0.55rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", fontSize: "0.85rem" }}>
            <option value="Default Microphone">Default Microphone</option>
            <option value="Studio USB Mic">Studio USB Mic (High Def)</option>
            <option value="Headset Microphone">Headset Microphone</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Audio Codec</label>
          <select value={codec} onChange={e => setCodec(e.target.value)} style={{ width: "100%", padding: "0.55rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", fontSize: "0.85rem" }}>
            <option value="PCM_16BIT">PCM 16-Bit Linear</option>
            <option value="OPUS">Opus Interactive Audio</option>
            <option value="G711_ULAW">G.711 µ-law Telephony</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Sample Rate</label>
          <select value={sampleRate} onChange={e => setSampleRate(Number(e.target.value))} style={{ width: "100%", padding: "0.55rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", fontSize: "0.85rem" }}>
            <option value={16000}>16,000 Hz (Wideband)</option>
            <option value={48000}>48,000 Hz (Fullband Studio)</option>
            <option value={8000}>8,000 Hz (Narrowband Telephony)</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Target Bitrate</label>
          <select value={bitrate} onChange={e => setBitrate(Number(e.target.value))} style={{ width: "100%", padding: "0.55rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", fontSize: "0.85rem" }}>
            <option value={128000}>128 kbps (High Fidelity)</option>
            <option value={64000}>64 kbps (Standard Speech)</option>
            <option value={32000}>32 kbps (Low Bandwidth)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
