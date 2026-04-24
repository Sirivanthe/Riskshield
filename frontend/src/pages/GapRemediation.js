import { useState, useEffect } from 'react';
import { api } from '@/App';

const GapRemediation = ({ user }) => {
  const [gaps, setGaps] = useState([]);
  const [remediations, setRemediations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('gaps');
  const [selectedGap, setSelectedGap] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [creatingPlan, setCreatingPlan] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [gapsRes, remediationsRes] = await Promise.all([
        api.get('/gap-analysis'),
        api.get('/gap-remediation')
      ]);
      setGaps(gapsRes.data);
      setRemediations(remediationsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGetRecommendations = async (gap) => {
    setSelectedGap(gap);
    setLoadingRecs(true);
    setRecommendations(null);
    try {
      const response = await api.get(`/gap-remediation/recommendations/${gap.id}`);
      setRecommendations(response.data.recommendations);
    } catch (error) {
      console.error('Failed to get recommendations:', error);
      alert('Failed to get AI recommendations');
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleCreateRemediation = async () => {
    if (!selectedGap) return;
    setCreatingPlan(true);
    try {
      const response = await api.post('/gap-remediation', {
        gap_id: selectedGap.id,
        priority: selectedGap.severity === 'CRITICAL' ? 'CRITICAL' : selectedGap.severity
      });
      alert('Remediation plan created successfully!');
      setSelectedGap(null);
      setRecommendations(null);
      loadData();
    } catch (error) {
      console.error('Failed to create remediation:', error);
      alert('Failed to create remediation plan');
    } finally {
      setCreatingPlan(false);
    }
  };

  const handleSelectApproach = async (remediationId, approach) => {
    try {
      await api.put(`/gap-remediation/${remediationId}/select-approach?approach=${approach}`);
      loadData();
    } catch (error) {
      console.error('Failed to select approach:', error);
    }
  };

  const handleApprove = async (remediationId) => {
    try {
      await api.post(`/gap-remediation/${remediationId}/approve`);
      loadData();
    } catch (error) {
      console.error('Failed to approve:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#ef4444',
      'HIGH': '#f59e0b',
      'MEDIUM': '#3b82f6',
      'LOW': '#22c55e'
    };
    return colors[severity] || '#94a3b8';
  };

  const getStatusColor = (status) => {
    const colors = {
      'OPEN': '#ef4444',
      'IN_PROGRESS': '#f59e0b',
      'REMEDIATED': '#22c55e',
      'ACCEPTED': '#3b82f6',
      'DRAFT': '#94a3b8',
      'APPROVED': '#22c55e',
      'COMPLETED': '#22c55e',
      'VERIFIED': '#10b981'
    };
    return colors[status] || '#94a3b8';
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="gap-remediation-page">
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="gap-remediation-title">Gap Remediation</h1>
          <p className="page-subtitle">AI-powered control gap analysis and remediation planning</p>
        </div>
      </div>

      <div className="page-content">
        {/* Summary Stats */}
        <div className="grid grid-4 gap-4 mb-6">
          <div className="stat-card">
            <div className="stat-label">Open Gaps</div>
            <div className="stat-value" style={{ color: '#ef4444' }}>
              {gaps.filter(g => g.status === 'OPEN').length}
            </div>
            <div className="stat-trend negative">Needs remediation</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">In Progress</div>
            <div className="stat-value" style={{ color: '#f59e0b' }}>
              {remediations.filter(r => r.status === 'IN_PROGRESS').length}
            </div>
            <div className="stat-trend">Being remediated</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Remediated</div>
            <div className="stat-value" style={{ color: '#22c55e' }}>
              {gaps.filter(g => g.status === 'REMEDIATED').length}
            </div>
            <div className="stat-trend positive">Closed</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Critical Gaps</div>
            <div className="stat-value" style={{ color: '#ef4444' }}>
              {gaps.filter(g => g.severity === 'CRITICAL' && g.status === 'OPEN').length}
            </div>
            <div className="stat-trend negative">Urgent</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs mb-6">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'gaps' ? 'active' : ''}`}
              onClick={() => setActiveTab('gaps')}
            >
              Control Gaps ({gaps.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'remediations' ? 'active' : ''}`}
              onClick={() => setActiveTab('remediations')}
            >
              Remediation Plans ({remediations.length})
            </button>
          </div>
        </div>

        {/* Gaps Tab */}
        {activeTab === 'gaps' && (
          <div className="card">
            <table className="table" data-testid="gaps-table">
              <thead>
                <tr>
                  <th>Gap ID</th>
                  <th>Framework</th>
                  <th>Requirement</th>
                  <th>Description</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {gaps.length > 0 ? gaps.map((gap) => (
                  <tr key={gap.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{gap.gap_id}</td>
                    <td>
                      <span className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>
                        {gap.framework}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px' }}>{gap.requirement_id}</td>
                    <td style={{ fontSize: '13px', maxWidth: '300px' }}>
                      {gap.gap_description?.substring(0, 100)}...
                    </td>
                    <td>
                      <span style={{ 
                        color: getSeverityColor(gap.severity),
                        fontWeight: '600'
                      }}>
                        {gap.severity}
                      </span>
                    </td>
                    <td>
                      <span 
                        className="badge"
                        style={{ 
                          background: `${getStatusColor(gap.status)}20`,
                          color: getStatusColor(gap.status)
                        }}
                      >
                        {gap.status}
                      </span>
                    </td>
                    <td>
                      {gap.status === 'OPEN' && (
                        <button 
                          className="btn btn-primary btn-sm"
                          onClick={() => handleGetRecommendations(gap)}
                        >
                          Get AI Recommendations
                        </button>
                      )}
                      {gap.status === 'IN_PROGRESS' && (
                        <span style={{ fontSize: '12px', color: '#64748b' }}>Remediation in progress</span>
                      )}
                      {gap.status === 'REMEDIATED' && (
                        <span style={{ fontSize: '12px', color: '#22c55e' }}>Closed</span>
                      )}
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                      No control gaps identified. Run a gap analysis from an assessment.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Remediations Tab */}
        {activeTab === 'remediations' && (
          <div className="space-y-4">
            {remediations.length > 0 ? remediations.map((rem) => (
              <div key={rem.id} className="card" style={{ padding: '20px' }}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                      {rem.remediation_id}
                    </h3>
                    <div className="flex gap-2 items-center">
                      <span className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>
                        {rem.framework}
                      </span>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        {rem.requirement_id}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span 
                      className="badge"
                      style={{ 
                        background: `${getSeverityColor(rem.priority)}20`,
                        color: getSeverityColor(rem.priority)
                      }}
                    >
                      {rem.priority}
                    </span>
                    <span 
                      className="badge"
                      style={{ 
                        background: `${getStatusColor(rem.status)}20`,
                        color: getStatusColor(rem.status)
                      }}
                    >
                      {rem.status}
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
                  {rem.gap_description}
                </p>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span style={{ fontSize: '12px', color: '#64748b' }}>Progress</span>
                    <span style={{ fontSize: '12px', fontWeight: '600', color: '#0f172a' }}>{rem.progress_percentage}%</span>
                  </div>
                  <div style={{ 
                    width: '100%', 
                    height: '8px', 
                    background: '#e2e8f0', 
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{ 
                      width: `${rem.progress_percentage}%`, 
                      height: '100%', 
                      background: rem.progress_percentage === 100 ? '#22c55e' : '#3b82f6',
                      transition: 'width 0.3s'
                    }}></div>
                  </div>
                </div>

                {/* AI Recommendations Summary */}
                {rem.ai_recommended_controls?.length > 0 && (
                  <div style={{ padding: '12px', background: '#f0f9ff', borderRadius: '8px', marginBottom: '16px' }}>
                    <div style={{ fontSize: '12px', fontWeight: '600', color: '#0369a1', marginBottom: '8px' }}>
                      AI Recommended Controls ({rem.ai_recommended_controls.length})
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {rem.ai_recommended_controls.slice(0, 3).map((ctrl, idx) => (
                        <span key={idx} style={{ fontSize: '12px', padding: '4px 8px', background: '#dbeafe', color: '#1e40af', borderRadius: '4px' }}>
                          {ctrl.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Selected Approach */}
                {rem.selected_approach && (
                  <div style={{ fontSize: '13px', color: '#334155', marginBottom: '12px' }}>
                    <strong>Approach:</strong> {rem.selected_approach}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  {rem.status === 'DRAFT' && (
                    <>
                      <button 
                        className="btn btn-primary btn-sm"
                        onClick={() => handleSelectApproach(rem.id, 'IMPLEMENT')}
                      >
                        Implement Controls
                      </button>
                      <button 
                        className="btn btn-outline btn-sm"
                        onClick={() => handleSelectApproach(rem.id, 'COMPENSATING')}
                      >
                        Compensating Controls
                      </button>
                      <button 
                        className="btn btn-outline btn-sm"
                        onClick={() => handleSelectApproach(rem.id, 'ACCEPT_RISK')}
                      >
                        Accept Risk
                      </button>
                    </>
                  )}
                  {rem.status === 'IN_PROGRESS' && (user.role === 'LOD2_USER' || user.role === 'ADMIN') && (
                    <button 
                      className="btn btn-primary btn-sm"
                      onClick={() => handleApprove(rem.id)}
                    >
                      Approve Plan
                    </button>
                  )}
                  <button className="btn btn-outline btn-sm">View Details</button>
                </div>
              </div>
            )) : (
              <div className="card">
                <div className="empty-state">
                  <h3 className="empty-title">No Remediation Plans</h3>
                  <p className="empty-description">Select a gap and get AI recommendations to create a remediation plan</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AI Recommendations Modal */}
      {selectedGap && (
        <div className="modal-overlay" onClick={() => { setSelectedGap(null); setRecommendations(null); }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">AI Recommendations - {selectedGap.gap_id}</h2>
              <button className="modal-close" onClick={() => { setSelectedGap(null); setRecommendations(null); }}>&times;</button>
            </div>
            <div className="modal-body">
              {/* Gap Info */}
              <div style={{ padding: '16px', background: '#fef2f2', borderRadius: '8px', marginBottom: '20px' }}>
                <div className="flex justify-between items-start mb-2">
                  <span className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>{selectedGap.framework}</span>
                  <span style={{ color: getSeverityColor(selectedGap.severity), fontWeight: '600' }}>{selectedGap.severity}</span>
                </div>
                <div style={{ fontSize: '13px', color: '#334155', marginBottom: '8px' }}>
                  <strong>Requirement:</strong> {selectedGap.requirement_id}
                </div>
                <div style={{ fontSize: '13px', color: '#64748b' }}>
                  {selectedGap.gap_description}
                </div>
              </div>

              {loadingRecs ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <div className="loading-spinner"></div>
                  <p style={{ marginTop: '16px', color: '#64748b' }}>Generating AI recommendations...</p>
                </div>
              ) : recommendations ? (
                <>
                  {/* Recommended Controls */}
                  <div className="mb-6">
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '16px' }}>
                      Recommended Controls
                    </h3>
                    <div className="space-y-3">
                      {recommendations.recommended_controls?.map((ctrl, idx) => (
                        <div 
                          key={idx}
                          style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a' }}>{ctrl.name}</h4>
                            <div className="flex gap-2">
                              <span className="badge" style={{ background: '#fef3c7', color: '#92400e' }}>
                                {ctrl.implementation_effort} Effort
                              </span>
                              <span className="badge" style={{ background: '#f0fdf4', color: '#166534' }}>
                                {ctrl.effectiveness_estimate} Effectiveness
                              </span>
                            </div>
                          </div>
                          <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px' }}>
                            {ctrl.description}
                          </p>
                          <div className="flex flex-wrap gap-4" style={{ fontSize: '12px', color: '#94a3b8' }}>
                            <span>Time: {ctrl.time_to_implement}</span>
                            <span>Cost: {ctrl.cost_estimate}</span>
                            {ctrl.ai_confidence && (
                              <span>AI Confidence: {(ctrl.ai_confidence * 100).toFixed(0)}%</span>
                            )}
                          </div>
                          {ctrl.regulatory_coverage?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {ctrl.regulatory_coverage.map((reg, i) => (
                                <span key={i} style={{ fontSize: '11px', padding: '2px 6px', background: '#eff6ff', color: '#1e40af', borderRadius: '4px' }}>
                                  {reg}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Implementation Plan */}
                  {recommendations.implementation_plan && (
                    <div className="mb-6">
                      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '12px' }}>
                        Implementation Plan
                      </h3>
                      <div style={{ 
                        padding: '16px', 
                        background: '#f8fafc', 
                        borderRadius: '8px',
                        whiteSpace: 'pre-wrap',
                        fontSize: '13px',
                        color: '#334155',
                        fontFamily: 'monospace'
                      }}>
                        {recommendations.implementation_plan}
                      </div>
                    </div>
                  )}

                  {/* Risk & Timeline */}
                  <div className="grid grid-2 gap-4 mb-6">
                    <div style={{ padding: '16px', background: '#fef2f2', borderRadius: '8px' }}>
                      <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#991b1b', marginBottom: '8px' }}>
                        Risk if Delayed
                      </h4>
                      <p style={{ fontSize: '13px', color: '#7f1d1d' }}>
                        {recommendations.risk_if_delayed}
                      </p>
                    </div>
                    <div style={{ padding: '16px', background: '#f0fdf4', borderRadius: '8px' }}>
                      <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>
                        Estimated Timeline
                      </h4>
                      <p style={{ fontSize: '13px', color: '#15803d' }}>
                        {recommendations.timeline}
                      </p>
                      <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                        Effort: {recommendations.effort_estimate}
                      </p>
                    </div>
                  </div>

                  {/* Compensating Controls */}
                  {recommendations.compensating_controls?.length > 0 && (
                    <div className="mb-6">
                      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '12px' }}>
                        Alternative Compensating Controls
                      </h3>
                      <ul style={{ paddingLeft: '20px', color: '#334155', fontSize: '13px' }}>
                        {recommendations.compensating_controls.map((ctrl, idx) => (
                          <li key={idx} style={{ marginBottom: '4px' }}>{ctrl}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : null}
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-outline" 
                onClick={() => { setSelectedGap(null); setRecommendations(null); }}
              >
                Cancel
              </button>
              {recommendations && (
                <button 
                  className="btn btn-primary"
                  onClick={handleCreateRemediation}
                  disabled={creatingPlan}
                >
                  {creatingPlan ? 'Creating...' : 'Create Remediation Plan'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GapRemediation;
