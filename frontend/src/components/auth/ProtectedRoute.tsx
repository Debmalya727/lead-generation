import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="relative min-h-screen flex flex-col items-center justify-center bg-[#030303] text-white overflow-hidden">
        {/* Hologram Arch and grid backdrop */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-tr from-persian-indigo via-transparent to-persian-turquoise opacity-20 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:45px_45px] pointer-events-none" />
        
        {/* Spinner */}
        <div className="relative z-10 p-8 rounded-xl border border-glass bg-glass backdrop-blur-xl flex flex-col items-center gap-4 text-center">
          <div className="w-10 h-10 border-4 border-glass border-t-persian-turquoise rounded-full animate-spin" />
          <p className="text-xs font-mono text-neutral-400 tracking-widest">LOADING SESSION...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
