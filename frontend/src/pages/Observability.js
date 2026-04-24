import { useState, useEffect } from 'react';
import { api } from '@/App';

const Observability = ({ user }) => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadDashboard();
    
    const interval = autoRefresh ? setInterval(loadDashboard, 5000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const loadDashboard = async () => {
    try {
      const response = await api.get('/observability/dashboard');
      setDashboard(response.data);
    } catch (error) {
      console.error('Failed to load observability dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="observability-page">
      <div className="page-header">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="page-title" data-testid="observability-title">Model Observability</h1>
            <p className="page-subtitle">Monitor AI model performance and system health</p>
          </div>
          <div className="flex gap-2 items-center">
            <label className="flex items-center gap-2" style={{ fontSize: '14px' }}>
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              Auto-refresh
            </label>
            <button className="btn btn-outline" onClick={loadDashboard}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="page-content">
        {dashboard && (
          <>
            {/* Model Performance Section */}
            <div className="mb-6">
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#0f172a', marginBottom: '16px' }}>Model Performance</h2>
              <div className="grid grid-4">
                <div className="stat-card" data-testid="total-requests-card">
                  <div className="stat-label">Total Requests</div>
                  <div className="stat-value">{dashboard.model_performance.total_requests}</div>
                  <div className="stat-change positive">Last 24 hours</div>
                </div>
                <div className="stat-card" data-testid="total-tokens-card">
                  <div className="stat-label">Total Tokens</div>
                  <div className="stat-value" style={{ fontSize: '28px' }}>{dashboard.model_performance.total_tokens.toLocaleString()}</div>
                  <div className="stat-change">Prompt + Completion</div>
                </div>
                <div className="stat-card" data-testid="total-cost-card">
                  <div className="stat-label">Total Cost</div>
                  <div className="stat-value" style={{ fontSize: '28px' }}>${dashboard.model_performance.total_cost_usd}</div>
                  <div className="stat-change">USD</div>
                </div>
                <div className="stat-card" data-testid="avg-latency-card">
                  <div className="stat-label">Avg Latency</div>
                  <div className="stat-value" style={{ fontSize: '28px' }}>{dashboard.model_performance.avg_latency_ms}ms</div>
                  <div className="stat-change positive">{dashboard.model_performance.success_rate}% success</div>
                </div>
              </div>
            </div>

            {/* Agent Activity Section */}
            <div className="mb-6">
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#0f172a', marginBottom: '16px' }}>Agent Activity</h2>
              <div className="grid grid-3">
                <div className="stat-card" data-testid="total-activities-card">
                  <div className="stat-label">Total Activities</div>
                  <div className="stat-value">{dashboard.agent_activity.total_activities}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Completed</div>
                  <div className="stat-value" style={{ color: '#10b981' }}>{dashboard.agent_activity.completed}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Failed</div>
                  <div className="stat-value" style={{ color: dashboard.agent_activity.failed > 0 ? '#ef4444' : '#10b981' }}>
                    {dashboard.agent_activity.failed}
                  </div>
                </div>
              </div>
            </div>

            {/* Knowledge Graph Section */}
            <div className="mb-6">
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#0f172a', marginBottom: '16px' }}>Knowledge Graph</h2>
              <div className="grid grid-2">
                <div className="stat-card" data-testid="total-entities-card">
                  <div className="stat-label">Total Entities</div>
                  <div className="stat-value">{dashboard.knowledge_graph.total_entities}</div>
                  <div className="stat-change">Systems, Risks, Controls, etc.</div>
                </div>
                <div className="stat-card" data-testid="total-relations-card">
                  <div className="stat-label">Total Relations</div>
                  <div className="stat-value">{dashboard.knowledge_graph.total_relations}</div>
                  <div className="stat-change">Connections between entities</div>
                </div>
              </div>
            </div>

            {/* Recent Metrics */}
            <div className="grid grid-2 gap-6">
              <div className="card">
                <h3 className="card-title mb-4">Recent Model Metrics</h3>
                {dashboard.recent_metrics && dashboard.recent_metrics.length > 0 ? (
                  <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Model</th>
                          <th>Tokens</th>
                          <th>Latency</th>
                          <th>Cost</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dashboard.recent_metrics.map((metric, idx) => (
                          <tr key={idx}>
                            <td style={{ fontSize: '13px', fontWeight: '600' }}>{metric.model_name}</td>
                            <td>{metric.total_tokens.toLocaleString()}</td>
                            <td>{metric.latency_ms}ms</td>
                            <td>${metric.cost_usd.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <p className="text-gray text-sm">No recent metrics</p>
                  </div>
                )}
              </div>

              <div className="card">
                <h3 className="card-title mb-4">Recent Activities</h3>
                {dashboard.recent_activities && dashboard.recent_activities.length > 0 ? (
                  <div style={{ maxHeight: '400px', overflowY: 'auto' }} className="space-y-2">
                    {dashboard.recent_activities.map((activity, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '12px',
                          background: '#f8fafc',
                          borderRadius: '6px',
                          borderLeft: `4px solid ${
                            activity.status === 'COMPLETED' ? '#10b981' :
                            activity.status === 'FAILED' ? '#ef4444' :
                            activity.status === 'RUNNING' ? '#3b82f6' : '#f59e0b'
                          }`
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a' }}>
                            {activity.agent_name}
                          </span>
                          <span
                            style={{
                              fontSize: '11px',
                              fontWeight: '600',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              background: activity.status === 'COMPLETED' ? '#d1fae5' :
                                         activity.status === 'FAILED' ? '#fee2e2' :
                                         activity.status === 'RUNNING' ? '#dbeafe' : '#fef3c7',
                              color: activity.status === 'COMPLETED' ? '#065f46' :
                                     activity.status === 'FAILED' ? '#991b1b' :
                                     activity.status === 'RUNNING' ? '#1e40af' : '#92400e'
                            }}
                          >
                            {activity.status}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          {activity.description}
                        </div>
                        {activity.duration_ms && (
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                            {activity.duration_ms}ms
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <p className="text-gray text-sm">No recent activities</p>
                  </div>
                )}
              </div>
            </div>

            {/* System Health Indicators */}
            <div className="card mt-6">
              <h3 className="card-title mb-4">System Health</h3>
              <div className="grid grid-3 gap-4">
                <div style={{ padding: '16px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #86efac' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>Model Performance</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#15803d' }}>Healthy</div>
                  <div style={{ fontSize: '12px', color: '#15803d', marginTop: '4px' }}>
                    {dashboard.model_performance.success_rate}% success rate
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #86efac' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>Agent Operations</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#15803d' }}>Healthy</div>
                  <div style={{ fontSize: '12px', color: '#15803d', marginTop: '4px' }}>
                    {dashboard.agent_activity.success_rate}% success rate
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #86efac' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>Knowledge Graph</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#15803d' }}>Growing</div>
                  <div style={{ fontSize: '12px', color: '#15803d', marginTop: '4px' }}>
                    {dashboard.knowledge_graph.total_entities} entities, {dashboard.knowledge_graph.total_relations} relations
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Observability;
