import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "../contexts/AuthContext";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { GuestRoute } from "../components/auth/GuestRoute";
import LoginPage from "../pages/auth/LoginPage";
import SignupPage from "../pages/auth/SignupPage";
import LeadsPage from "../pages/leads/LeadsPage";
import DiscoveryPage from "../pages/discovery/DiscoveryPage";
import IntelligencePage from "../pages/intelligence/IntelligencePage";
import ScoringPage from "../pages/scoring/ScoringPage";
import OutreachPage from "../pages/outreach/OutreachPage";
import SalesIntelligencePage from "../pages/sales_intelligence/SalesIntelligencePage";
import ResearchPage from "../pages/research/ResearchPage";
import KnowledgeCenterPage from "../pages/knowledge/KnowledgeCenterPage";
import KnowledgeAnalyticsDashboardPage from "../pages/knowledge/KnowledgeAnalyticsDashboardPage";
import AgentsWorkspacePage from "../pages/agents/AgentsWorkspacePage";
import WorkflowsPage from "../pages/workflows/WorkflowsPage";
import ChatPage from "../pages/chat/ChatPage";
import AdminDashboardPage from "../pages/admin/AdminDashboardPage";
import SchedulerPage from "../pages/scheduler/SchedulerPage";
import PluginMarketplacePage from "../pages/plugins/PluginMarketplacePage";
import AIDashboardPage from "../pages/ai/AIDashboardPage";
import VoiceWorkspacePage from "../pages/voice/VoiceWorkspacePage";
import VoiceAnalyticsDashboardPage from "../pages/voice/VoiceAnalyticsDashboardPage";
import ErrorBoundary from "../components/ErrorBoundary";

import "../styles/globals.css";

const App = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/signup"
            element={
              <GuestRoute>
                <SignupPage />
              </GuestRoute>
            }
          />
          <Route
            path="/scheduler"
            element={
              <ProtectedRoute>
                <SchedulerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai"
            element={
              <ProtectedRoute>
                <AIDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/voice"
            element={
              <ProtectedRoute>
                <VoiceWorkspacePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/voice/analytics"
            element={
              <ProtectedRoute>
                <VoiceAnalyticsDashboardPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/plugins"
            element={
              <ProtectedRoute>
                <PluginMarketplacePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <LeadsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/discovery"
            element={
              <ProtectedRoute>
                <DiscoveryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/intelligence"
            element={
              <ProtectedRoute>
                <IntelligencePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/scoring"
            element={
              <ProtectedRoute>
                <ScoringPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/outreach"
            element={
              <ProtectedRoute>
                <OutreachPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sales-intelligence"
            element={
              <ProtectedRoute>
                <SalesIntelligencePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/research"
            element={
              <ProtectedRoute>
                <ResearchPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/knowledge"
            element={
              <ProtectedRoute>
                <KnowledgeCenterPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/knowledge/analytics"
            element={
              <ProtectedRoute>
                <KnowledgeAnalyticsDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/agents"
            element={
              <ProtectedRoute>
                <AgentsWorkspacePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/workflows"
            element={
              <ProtectedRoute>
                <WorkflowsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </ErrorBoundary>
);
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
