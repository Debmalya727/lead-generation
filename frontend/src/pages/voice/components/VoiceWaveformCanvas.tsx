import React, { useEffect, useRef } from "react";

interface VoiceWaveformCanvasProps {
  isStreaming: boolean;
  vadState: "SILENCE" | "SPEECH" | "INTERRUPTION";
  audioLevelDb: number;
}

export const VoiceWaveformCanvas: React.FC<VoiceWaveformCanvasProps> = ({
  isStreaming,
  vadState,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    let animId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let phase = 0;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "rgba(10, 15, 30, 0.85)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Render User Input Spectrum (Green/Red)
      ctx.beginPath();
      ctx.lineWidth = 2.5;
      ctx.strokeStyle =
        vadState === "SPEECH"
          ? "#34d399"
          : vadState === "INTERRUPTION"
          ? "#f87171"
          : "#6366f1";

      const amp = vadState === "SPEECH" ? 35 : vadState === "INTERRUPTION" ? 50 : 8;
      const freq = isStreaming ? 0.04 : 0.015;

      for (let x = 0; x < canvas.width; x++) {
        const y =
          canvas.height / 2 +
          Math.sin(x * freq + phase) * amp * Math.cos(x * 0.006);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Render Assistant Output Spectrum Overlay (Purple)
      if (isStreaming) {
        ctx.beginPath();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "rgba(139, 92, 246, 0.7)";
        for (let x = 0; x < canvas.width; x++) {
          const y =
            canvas.height / 2 +
            Math.sin(x * 0.06 - phase * 1.5) * (amp * 0.6) * Math.sin(x * 0.008);
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      phase += isStreaming ? 0.12 : 0.03;
      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [isStreaming, vadState]);

  return (
    <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "16px", padding: "1.25rem", position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#fff" }}>🎙️ Dual Audio Stream Waveform (60 FPS)</h3>
          <span style={{ color: "#64748b", fontSize: "0.78rem" }}>Real-time Dual Spectrum (User Mic Energy vs Assistant Speech Output)</span>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", borderRadius: "100px", background: vadState === "SPEECH" ? "rgba(52,211,153,0.15)" : "rgba(100,116,139,0.15)", color: vadState === "SPEECH" ? "#34d399" : "#94a3b8", fontWeight: 700 }}>
            VAD: {vadState}
          </span>
          <span style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", borderRadius: "100px", background: isStreaming ? "rgba(99,102,241,0.15)" : "rgba(100,116,139,0.15)", color: isStreaming ? "#a5b4fc" : "#94a3b8", fontWeight: 700 }}>
            {isStreaming ? "STREAMING ACTIVE" : "IDLE"}
          </span>
        </div>
      </div>
      <canvas ref={canvasRef} width={1200} height={100} style={{ width: "100%", height: "100px", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.15)" }} />
    </div>
  );
};
