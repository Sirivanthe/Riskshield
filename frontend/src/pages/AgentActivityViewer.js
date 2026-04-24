import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '@/App';

const AgentActivityViewer = ({ user }) => {
  const { id } = useParams();
  const [activities, setActivities] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [explanations, setExplanations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('activities');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 2 seconds if enabled
    const interval = autoRefresh ? setInterval(loadData, 2000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, autoRefresh]);

  const loadData = async () => {
    try {
      const [activitiesRes, metricsRes, explanationsRes] = await Promise.all([
        api.get(`/agent-activities/${id}`),
        api.get(`/model-metrics/${id}`),
        api.get(`/explanations/${id}`)
      ]);
      
      setActivities(activitiesRes.data);
      setMetrics(metricsRes.data);
      setExplanations(explanationsRes.data);
    } catch (error) {
      console.error('Failed to load activity data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'RUNNING': '#3b82f6',
      'COMPLETED': '#10b981',
      'FAILED': '#ef4444',
      'WAITING': '#f59e0b'
    };
    return colors[status] || '#6b7280';
  };

  const getActivityIcon = (activityType) => {
    const icons = {
      'risk_identification': '🔍',
      'control_testing': '✅',
      'evidence_collection': '📄',
      'report_generation': '📊',
      'graph_construction': '🕸️',
      'assessment': '📝'
    };
    return icons[activityType] || '🤖';
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="agent-activity-page">
      <div className="page-header">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="page-title" data-testid="activity-title">Agent Activity Monitor</h1>
            <p className="page-subtitle">Real-time AI agent activity tracking</p>
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
            <button className="btn btn-outline" onClick={loadData}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="page-content">
        {/* Summary Cards */}
        {metrics && metrics.summary && (
          <div className="grid grid-4 mb-6">
            <div className="stat-card">
              <div className="stat-label">Total Requests</div>
              <div className="stat-value">{metrics.summary.total_requests}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total Tokens</div>
              <div className="stat-value">{metrics.summary.total_tokens.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total Cost</div>
              <div className="stat-value" style={{ fontSize: '28px' }}>${metrics.summary.total_cost_usd}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Latency</div>
              <div className="stat-value" style={{ fontSize: '28px' }}>{metrics.summary.avg_latency_ms}ms</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'activities' ? 'active' : ''}`}
              onClick={() => setActiveTab('activities')}
              data-testid="tab-activities"
            >
              Agent Activities ({activities.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'metrics' ? 'active' : ''}`}
              onClick={() => setActiveTab('metrics')}
              data-testid="tab-metrics"
            >
              Model Metrics
            </button>
            <button
              className={`tab-button ${activeTab === 'explanations' ? 'active' : ''}`}
              onClick={() => setActiveTab('explanations')}
              data-testid="tab-explanations"
            >
              AI Explanations ({explanations.length})
            </button>
          </div>
        </div>

        {/* Activities Tab */}
        {activeTab === 'activities' && (
          <div className="card" data-testid="activities-content">
            {activities.length > 0 ? (
              <div className="space-y-3">
                {activities.map((activity, idx) => (
                  <div
                    key={activity.id}
                    style={{
                      padding: '16px',
                      background: '#f8fafc',
                      borderRadius: '8px',
                      borderLeft: `4px solid ${getStatusColor(activity.status)}`
                    }}
                  >
                    <div className="flex items-start gap-3">
                      <div style={{ fontSize: '24px' }}>{getActivityIcon(activity.activity_type)}</div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a' }}>
                              {activity.agent_name}
                            </div>
                            <div style={{ fontSize: '14px', color: '#64748b' }}>
                              {activity.description}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              style={{
                                padding: '4px 12px',
                                borderRadius: '12px',
                                fontSize: '12px',
                                fontWeight: '600',
                                background: activity.status === 'COMPLETED' ? '#d1fae5' : 
                                           activity.status === 'FAILED' ? '#fee2e2' :
                                           activity.status === 'RUNNING' ? '#dbeafe' : '#fef3c7',
                                color: activity.status === 'COMPLETED' ? '#065f46' :
                                       activity.status === 'FAILED' ? '#991b1b' :
                                       activity.status === 'RUNNING' ? '#1e40af' : '#92400e'
                              }}
                            >
                              {activity.status === 'RUNNING' && '🔄 '}
                              {activity.status}
                            </span>
                            {activity.duration_ms && (
                              <span style={{ fontSize: '12px', color: '#64748b' }}>
                                {activity.duration_ms}ms
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Inputs/Outputs */}
                        {(Object.keys(activity.inputs || {}).length > 0 || Object.keys(activity.outputs || {}).length > 0) && (
                          <div className="grid grid-2 gap-2 mt-3">
                            {Object.keys(activity.inputs || {}).length > 0 && (
                              <div style={{ padding: '8px', background: '#e0e7ff', borderRadius: '6px' }}>
                                <div style={{ fontSize: '11px', fontWeight: '600', color: '#3730a3', marginBottom: '4px' }}>INPUTS</div>
                                {Object.entries(activity.inputs).map(([key, value]) => (
                                  <div key={key} style={{ fontSize: '12px', color: '#4338ca' }}>
                                    {key}: {JSON.stringify(value)}
                                  </div>
                                ))}
                              </div>
                            )}
                            {Object.keys(activity.outputs || {}).length > 0 && (
                              <div style={{ padding: '8px', background: '#d1fae5', borderRadius: '6px' }}>
                                <div style={{ fontSize: '11px', fontWeight: '600', color: '#065f46', marginBottom: '4px' }}>OUTPUTS</div>
                                {Object.entries(activity.outputs).map(([key, value]) => (
                                  <div key={key} style={{ fontSize: '12px', color: '#047857' }}>
                                    {key}: {JSON.stringify(value)}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '8px' }}>
                          Started: {new Date(activity.started_at).toLocaleTimeString()}
                          {activity.completed_at && (
                            <> | Completed: {new Date(activity.completed_at).toLocaleTimeString()}</>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p className="text-gray">No activities recorded yet</p>
              </div>
            )}
          </div>
        )}

        {/* Metrics Tab */}
        {activeTab === 'metrics' && metrics && (
          <div className="card" data-testid="metrics-content">
            {metrics.metrics && metrics.metrics.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Endpoint</th>
                    <th>Prompt Tokens</th>
                    <th>Completion Tokens</th>
                    <th>Latency</th>
                    <th>Cost</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.metrics.map((metric) => (
                    <tr key={metric.id}>
                      <td style={{ fontWeight: '600' }}>{metric.model_name}</td>
                      <td style={{ fontSize: '13px' }}>{metric.endpoint}</td>
                      <td>{metric.prompt_tokens.toLocaleString()}</td>
                      <td>{metric.completion_tokens.toLocaleString()}</td>
                      <td>{metric.latency_ms}ms</td>
                      <td>${metric.cost_usd.toFixed(4)}</td>
                      <td>
                        <span className={`badge ${metric.success ? 'effective' : 'ineffective'}`}>
                          {metric.success ? 'Success' : 'Failed'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <p className="text-gray">No model metrics recorded</p>
              </div>
            )}
          </div>
        )}

        {/* Explanations Tab */}
        {activeTab === 'explanations' && (
          <div className="space-y-4" data-testid="explanations-content">
            {explanations.length > 0 ? (
              explanations.map((explanation) => (
                <div key={explanation.id} className="card">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                        {explanation.entity_name}
                      </div>
                      <span className="badge" style={{ background: '#e0e7ff', color: '#3730a3' }}>
                        {explanation.explanation_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div style={{
                      padding: '8px 16px',
                      background: explanation.confidence_score >= 0.8 ? '#d1fae5' : 
                                 explanation.confidence_score >= 0.6 ? '#fef3c7' : '#fee2e2',
                      borderRadius: '8px'
                    }}>
                      <div style={{ fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', color: '#64748b' }}>Confidence</div>
                      <div style={{ fontSize: '20px', fontWeight: '700', color: '#0f172a' }}>
                        {(explanation.confidence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', marginBottom: '16px' }}>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Reasoning</div>
                    <div style={{ fontSize: '14px', color: '#334155', lineHeight: '1.6' }}>
                      {explanation.reasoning}
                    </div>
                  </div>

                  {explanation.supporting_facts && explanation.supporting_facts.length > 0 && (
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Supporting Facts</div>
                      <ul style={{ paddingLeft: '20px', fontSize: '13px', color: '#64748b' }}>
                        {explanation.supporting_facts.map((fact, idx) => (
                          <li key={idx} style={{ marginBottom: '4px' }}>{fact}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {explanation.regulatory_references && explanation.regulatory_references.length > 0 && (
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Regulatory References</div>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {explanation.regulatory_references.map((ref, idx) => (
                          <span
                            key={idx}
                            style={{
                              padding: '4px 12px',
                              background: '#eff6ff',
                              color: '#1e40af',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: '500'
                            }}
                          >
                            {ref}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="card">
                <div className="empty-state">
                  <p className="text-gray">No explanations available</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentActivityViewer;
