import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '@/App';

const AssessmentDetail = ({ user }) => {
  const { id } = useParams();
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [triggeringWorkflows, setTriggeringWorkflows] = useState(false);

  useEffect(() => {
    loadAssessment();
  }, [id]);

  // Auto-poll while orchestration is still running in the background.
  useEffect(() => {
    if (!assessment) return;
    if (assessment.status !== 'IN_PROGRESS' && assessment.status !== 'PENDING') return;
    const t = setInterval(loadAssessment, 5000);
    return () => clearInterval(t);
  }, [assessment]);

  const loadAssessment = async () => {
    try {
      const response = await api.get(`/assessments/${id}`);
      setAssessment(response.data);
    } catch (error) {
      console.error('Failed to load assessment:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerWorkflows = async () => {
    setTriggeringWorkflows(true);
    try {
      const response = await api.post(`/assessments/${id}/trigger-workflows`);
      alert(`Triggered ${response.data.triggered_count} workflow(s)`);
    } catch (error) {
      console.error('Failed to trigger workflows:', error);
      alert('Failed to trigger workflows');
    } finally {
      setTriggeringWorkflows(false);
    }
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="page-content">
        <div className="card">
          <div className="empty-state">
            <h3 className="empty-title">Assessment not found</h3>
            <Link to="/assessments" className="btn btn-primary mt-4">Back to Assessments</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="assessment-detail-page">
      <div className="page-header">
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link to="/assessments" className="text-gray hover:text-blue" data-testid="back-to-assessments">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 12H5M12 19l-7-7 7-7"></path>
                </svg>
              </Link>
              <h1 className="page-title" data-testid="assessment-detail-title">{assessment.name}</h1>
              <span className={`badge ${assessment.status.toLowerCase()}`}>{assessment.status}</span>
              {(assessment.status === 'IN_PROGRESS' || assessment.status === 'PENDING') && (
                <span
                  data-testid="assessment-running-indicator"
                  style={{
                    fontSize: '12px',
                    padding: '4px 10px',
                    background: '#eff6ff',
                    color: '#1d4ed8',
                    borderRadius: '999px',
                    border: '1px solid #bfdbfe',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: '#2563eb',
                      animation: 'pulse 1.2s ease-in-out infinite',
                    }}
                  />
                  AI agents running in background · auto-refreshing
                </span>
              )}
            </div>
            <p className="page-subtitle">{assessment.system_name} • {assessment.business_unit}</p>
          </div>
          
          <div className="flex gap-2">
            <Link
              to={`/agent-activity/${id}`}
              className="btn btn-outline"
              data-testid="view-activity-button"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"></path>
              </svg>
              View Agent Activity
            </Link>
            <button
              className="btn btn-outline"
              onClick={triggerWorkflows}
              disabled={triggeringWorkflows}
              data-testid="trigger-workflows-button"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              {triggeringWorkflows ? 'Triggering...' : 'Trigger Workflows'}
            </button>
          </div>
        </div>
      </div>

      <div className="page-content">
        {/* Summary Cards */}
        {assessment.summary && (
          <div className="grid grid-4 mb-6">
            <div className="stat-card" data-testid="overall-score-card">
              <div className="stat-label">Overall Score</div>
              <div className="stat-value" style={{ color: assessment.summary.overall_score >= 80 ? '#059669' : assessment.summary.overall_score >= 60 ? '#f59e0b' : '#dc2626' }}>
                {assessment.summary.overall_score}
              </div>
              <div className="stat-change">{assessment.summary.compliance_status}</div>
            </div>

            <div className="stat-card" data-testid="total-risks-card">
              <div className="stat-label">Total Risks</div>
              <div className="stat-value">{assessment.summary.risk_summary?.total || 0}</div>
              <div className="text-xs text-gray">
                Critical: {assessment.summary.risk_summary?.critical || 0}, High: {assessment.summary.risk_summary?.high || 0}
              </div>
            </div>

            <div className="stat-card" data-testid="total-controls-card">
              <div className="stat-label">Controls Tested</div>
              <div className="stat-value">{assessment.summary.control_summary?.total || 0}</div>
              <div className="text-xs text-gray">
                Effective: {assessment.summary.control_summary?.effective || 0}, Ineffective: {assessment.summary.control_summary?.ineffective || 0}
              </div>
            </div>

            <div className="stat-card" data-testid="evidence-count-card">
              <div className="stat-label">Evidence Collected</div>
              <div className="stat-value">{assessment.evidence?.length || 0}</div>
              <div className="text-xs text-gray">From multiple sources</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
              data-testid="tab-overview"
            >
              Overview
            </button>
            <button
              className={`tab-button ${activeTab === 'risks' ? 'active' : ''}`}
              onClick={() => setActiveTab('risks')}
              data-testid="tab-risks"
            >
              Risks ({assessment.risks?.length || 0})
            </button>
            <button
              className={`tab-button ${activeTab === 'controls' ? 'active' : ''}`}
              onClick={() => setActiveTab('controls')}
              data-testid="tab-controls"
            >
              Controls ({assessment.controls?.length || 0})
            </button>
            <button
              className={`tab-button ${activeTab === 'evidence' ? 'active' : ''}`}
              onClick={() => setActiveTab('evidence')}
              data-testid="tab-evidence"
            >
              Evidence ({assessment.evidence?.length || 0})
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div data-testid="overview-tab-content">
            <div className="grid grid-2 gap-6">
              <div className="card">
                <h3 className="card-title mb-4">Assessment Details</h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-gray mb-1">System Name</div>
                    <div className="font-semibold">{assessment.system_name}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray mb-1">Business Unit</div>
                    <div className="font-semibold">{assessment.business_unit}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray mb-1">Frameworks</div>
                    <div className="flex gap-2 flex-wrap">
                      {assessment.frameworks.map((fw) => (
                        <span key={fw} className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>{fw}</span>
                      ))}
                    </div>
                  </div>
                  {assessment.description && (
                    <div>
                      <div className="text-xs text-gray mb-1">Description</div>
                      <div className="text-sm">{assessment.description}</div>
                    </div>
                  )}
                  {assessment.scenario && (
                    <div>
                      <div className="text-xs text-gray mb-1">Scenario</div>
                      <div className="text-sm font-semibold">{assessment.scenario}</div>
                    </div>
                  )}
                  <div>
                    <div className="text-xs text-gray mb-1">Created</div>
                    <div className="text-sm">{new Date(assessment.created_at).toLocaleString()}</div>
                  </div>
                  {assessment.completed_at && (
                    <div>
                      <div className="text-xs text-gray mb-1">Completed</div>
                      <div className="text-sm">{new Date(assessment.completed_at).toLocaleString()}</div>
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <h3 className="card-title mb-4">Recommendations</h3>
                {assessment.summary?.recommendations && assessment.summary.recommendations.length > 0 ? (
                  <ul style={{ paddingLeft: '20px' }}>
                    {assessment.summary.recommendations.map((rec, idx) => (
                      <li key={idx} style={{ marginBottom: '12px', fontSize: '14px', color: '#334155' }}>{rec}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray">No recommendations available</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risks' && (
          <div className="card" data-testid="risks-tab-content">
            {assessment.risks && assessment.risks.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Risk</th>
                    <th>Severity</th>
                    <th>Framework</th>
                    <th>Likelihood</th>
                    <th>Impact</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {assessment.risks.map((risk) => (
                    <tr key={risk.id} data-testid={`risk-row-${risk.id}`}>
                      <td>
                        <div style={{ fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>{risk.title}</div>
                        <div style={{ fontSize: '13px', color: '#64748b' }}>{risk.description}</div>
                      </td>
                      <td>
                        <span className={`badge ${risk.severity.toLowerCase()}`}>{risk.severity}</span>
                      </td>
                      <td style={{ fontSize: '13px' }}>{risk.framework}</td>
                      <td style={{ fontSize: '13px' }}>{risk.likelihood}</td>
                      <td style={{ fontSize: '13px' }}>{risk.impact}</td>
                      <td>
                        <details>
                          <summary style={{ cursor: 'pointer', color: '#3b82f6', fontSize: '13px' }}>View</summary>
                          <div style={{ marginTop: '8px', fontSize: '13px', color: '#334155' }}>
                            <div className="mb-2"><strong>Mitigation:</strong> {risk.mitigation}</div>
                            {risk.regulatory_reference && (
                              <div><strong>Reference:</strong> {risk.regulatory_reference}</div>
                            )}
                          </div>
                        </details>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <p className="text-gray">No risks identified</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'controls' && (
          <div className="card" data-testid="controls-tab-content">
            {assessment.controls && assessment.controls.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Control</th>
                    <th>Effectiveness</th>
                    <th>Framework</th>
                    <th>Test Result</th>
                    <th>Last Tested</th>
                  </tr>
                </thead>
                <tbody>
                  {assessment.controls.map((control) => (
                    <tr key={control.id} data-testid={`control-row-${control.id}`}>
                      <td>
                        <div style={{ fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>{control.name}</div>
                        <div style={{ fontSize: '13px', color: '#64748b' }}>{control.description}</div>
                      </td>
                      <td>
                        <span className={`badge ${control.effectiveness.toLowerCase()}`}>
                          {control.effectiveness.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ fontSize: '13px' }}>{control.framework}</td>
                      <td style={{ fontSize: '13px', maxWidth: '300px' }}>{control.test_result || 'N/A'}</td>
                      <td style={{ fontSize: '13px' }}>
                        {control.last_tested ? new Date(control.last_tested).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <p className="text-gray">No controls tested</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="card" data-testid="evidence-tab-content">
            {assessment.evidence && assessment.evidence.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Status</th>
                    <th>Collected</th>
                  </tr>
                </thead>
                <tbody>
                  {assessment.evidence.map((evidence) => (
                    <tr key={evidence.id} data-testid={`evidence-row-${evidence.id}`}>
                      <td style={{ fontWeight: '600', color: '#0f172a' }}>{evidence.source}</td>
                      <td style={{ fontSize: '13px' }}>{evidence.type}</td>
                      <td style={{ fontSize: '13px', maxWidth: '400px' }}>{evidence.description}</td>
                      <td>
                        <span className="badge" style={{ background: '#d1fae5', color: '#065f46' }}>{evidence.status}</span>
                      </td>
                      <td style={{ fontSize: '13px' }}>{new Date(evidence.collected_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <p className="text-gray">No evidence collected</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AssessmentDetail;
