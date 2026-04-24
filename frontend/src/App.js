import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Assessments from "@/pages/Assessments";
import AssessmentDetail from "@/pages/AssessmentDetail";
import Workflows from "@/pages/Workflows";
import Admin from "@/pages/Admin";
import AgentActivityViewer from "@/pages/AgentActivityViewer";
import KnowledgeGraph from "@/pages/KnowledgeGraph";
import Observability from "@/pages/Observability";
import ControlsLibrary from "@/pages/ControlsLibrary";
import AICompliance from "@/pages/AICompliance";
import AutomatedTesting from "@/pages/AutomatedTesting";
import GapRemediation from "@/pages/GapRemediation";
import TrendAnalytics from "@/pages/TrendAnalytics";
import TechRiskAssessment from "@/pages/TechRiskAssessment";
import IssueManagement from "@/pages/IssueManagement";
import ControlAnalysis from "@/pages/ControlAnalysis";
import RegulatoryAnalysis from "@/pages/RegulatoryAnalysis";
import RCMTesting from "@/pages/RCMTesting";
import MyWork from "@/pages/MyWork";
import Layout from "@/components/Layout";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const handleLogin = (token, userData) => {
    localStorage.setItem('token', token);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={
            user ? <Navigate to="/" /> : <Login onLogin={handleLogin} />
          } />
          
          <Route path="/" element={
            user ? <Layout user={user} onLogout={handleLogout} /> : <Navigate to="/login" />
          }>
            <Route index element={<Dashboard user={user} />} />
            <Route path="my-work" element={<MyWork user={user} />} />
            <Route path="assessments" element={<Assessments user={user} />} />
            <Route path="assessments/:id" element={<AssessmentDetail user={user} />} />
            <Route path="agent-activity/:id" element={<AgentActivityViewer user={user} />} />
            <Route path="knowledge-graph" element={<KnowledgeGraph user={user} />} />
            <Route path="observability" element={<Observability user={user} />} />
            <Route path="controls-library" element={<ControlsLibrary user={user} />} />
            <Route path="ai-compliance" element={<AICompliance user={user} />} />
            <Route path="automated-testing" element={<AutomatedTesting user={user} />} />
            <Route path="gap-remediation" element={<GapRemediation user={user} />} />
            <Route path="trend-analytics" element={<TrendAnalytics user={user} />} />
            <Route path="tech-risk-assessment" element={<TechRiskAssessment user={user} />} />
            <Route path="issue-management" element={<IssueManagement user={user} />} />
            <Route path="control-analysis" element={<ControlAnalysis user={user} />} />
            <Route path="regulatory-analysis" element={<RegulatoryAnalysis user={user} />} />
            <Route path="rcm-testing" element={<RCMTesting user={user} />} />
            <Route path="workflows" element={<Workflows user={user} />} />
            <Route path="admin" element={<Admin user={user} />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
