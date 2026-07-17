import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        "Authentication failed. Please verify your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#030303] text-white font-sans overflow-hidden">
      {/* Decorative Persian-inspired holographic background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-persian-indigo via-transparent to-persian-turquoise opacity-20 rounded-full blur-[120px] pointer-events-none" />
      
      {/* Grid Backdrop */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

      {/* Floating Holographic Form Container */}
      <div className="relative z-10 w-full max-w-md p-8 md:p-10 rounded-2xl border border-glass bg-glass backdrop-blur-xl shadow-glass animate-hologram-glow">
        <header className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-glass bg-glass-hover text-xs font-mono text-persian-turquoise tracking-wider mb-4">
            <span className="w-2 h-2 rounded-full bg-persian-turquoise animate-pulse" />
            SECURE ACCESS PORTAL
          </div>
          <h1 className="text-3xl font-display font-extrabold tracking-tight">
            LeadForge<span className="text-persian-turquoise">AI</span>
          </h1>
          <p className="text-neutral-400 text-xs mt-2">
            Enter your credentials to manage your lead pipelines
          </p>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-lg border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-mono">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5 text-left">
            <label className="text-xs font-mono text-neutral-400 uppercase tracking-widest">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@leadforge.ai"
              className="w-full px-4 py-3 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
            />
          </div>

          <div className="space-y-1.5 text-left">
            <label className="text-xs font-mono text-neutral-400 uppercase tracking-widest">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-4 py-3 bg-black/40 border border-glass rounded-lg text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-persian-turquoise focus:ring-1 focus:ring-persian-turquoise transition-all font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black font-semibold text-sm rounded-lg hover:shadow-cyan-glow focus:outline-none focus:ring-2 focus:ring-persian-turquoise transition-all active:scale-[0.98] duration-300 flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
            ) : (
              "AUTHENTICATE OPERATOR"
            )}
          </button>
        </form>

        <footer className="mt-8 pt-6 border-t border-glass text-center text-xs text-neutral-400">
          <span>New to LeadForge? </span>
          <Link
            to="/signup"
            className="text-persian-turquoise hover:underline hover:text-white transition-colors"
          >
            Create an Account
          </Link>
        </footer>
      </div>
    </div>
  );
};
export default LoginPage;
