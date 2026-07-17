import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error in component tree:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#030303] text-white p-12 flex items-center justify-center font-sans">
          <div className="max-w-md w-full border border-red-500/30 rounded-2xl bg-black/80 backdrop-blur-xl p-8 space-y-4 text-center">
            <div className="text-4xl">⚠️</div>
            <h2 className="text-lg font-bold text-red-400 font-display">
              {this.props.fallbackTitle || "Workspace Exception Encountered"}
            </h2>
            <p className="text-xs text-neutral-400 font-mono leading-relaxed">
              {this.state.error?.message || "An unexpected rendering exception occurred."}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-4 py-2 bg-red-500/20 border border-red-500/40 hover:bg-red-500/30 text-red-300 text-xs font-mono rounded-lg transition-all"
            >
              🔄 RELOAD WORKSPACE
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
