import { useState, useEffect } from 'react';
import { api } from '@/App';

const AutomatedTesting = ({ user }) => {
  const [controls, setControls] = useState([]);
  const [testRuns, setTestRuns] = useState([]);
  const [testTypes, setTestTypes] = useState([]);
  const [evidenceSources, setEvidenceSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningTest, setRunningTest] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [activeTab, setActiveTab] = useState('runs');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [controlsRes, runsRes, typesRes, sourcesRes] = await Promise.all([
        api.get('/controls/library?status=APPROVED'),
        api.get('/automated-tests/runs'),
        api.get('/automated-tests/test-types'),
        api.get('/automated-tests/evidence-sources')
      ]);
      setControls(controlsRes.data);
      setTestRuns(runsRes.data);
      setTestTypes(typesRes.data.test_types || []);
      setEvidenceSources(sourcesRes.data.sources || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunTest = async (controlId, testType) => {
    setRunningTest(controlId);
    try {
      const response = await api.post(`/automated-tests/run/${controlId}?test_type=${testType}`);
      alert(`Test completed! Effectiveness: ${response.data.effectiveness_rating}, Confidence: ${(response.data.confidence_score * 100).toFixed(1)}%`);
      loadData();
    } catch (error) {
      console.error('Failed to run test:', error);
      alert('Failed to run automated test');
    } finally {
      setRunningTest(null);
    }
  };

  const handleReviewTest = async (runId, outcome) => {
    try {
      await api.post(`/automated-tests/runs/${runId}/review?outcome=${outcome}`);
      loadData();
      setSelectedRun(null);
    } catch (error) {
      console.error('Failed to review test:', error);
      alert('Failed to submit review');
    }
  };

  const getEffectivenessColor = (effectiveness) => {
    const colors = {
      'EFFECTIVE': '#22c55e',
      'PARTIALLY_EFFECTIVE': '#f59e0b',
      'INEFFECTIVE': '#ef4444',
      'NOT_TESTED': '#94a3b8'
    };
    return colors[effectiveness] || '#94a3b8';
  };

  const getConfidenceLevel = (score) => {
    if (score >= 0.9) return { label: 'High', color: '#22c55e' };
    if (score >= 0.7) return { label: 'Medium', color: '#f59e0b' };
    return { label: 'Low', color: '#ef4444' };
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="automated-testing-page">
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="automated-testing-title">Automated Control Testing</h1>
          <p className="page-subtitle">AI-powered control testing with automated evidence collection</p>
        </div>
      </div>

      <div className="page-content">
        {/* Summary Stats */}
        <div className="grid grid-4 gap-4 mb-6">
          <div className="stat-card">
            <div className="stat-label">Total Test Runs</div>
            <div className="stat-value">{testRuns.length}</div>
            <div className="stat-trend">All time</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Pending Review</div>
            <div className="stat-value" style={{ color: '#f59e0b' }}>
              {testRuns.filter(r => r.requires_human_review && !r.reviewed_by).length}
            </div>
            <div className="stat-trend negative">Needs attention</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Effective Controls</div>
            <div className="stat-value" style={{ color: '#22c55e' }}>
              {testRuns.filter(r => r.effectiveness_rating === 'EFFECTIVE').length}
            </div>
            <div className="stat-trend positive">Passing</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Test Types</div>
            <div className="stat-value">{testTypes.length}</div>
            <div className="stat-trend">Available</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs mb-6">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'runs' ? 'active' : ''}`}
              onClick={() => setActiveTab('runs')}
            >
              Test Runs ({testRuns.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'controls' ? 'active' : ''}`}
              onClick={() => setActiveTab('controls')}
            >
              Run New Test
            </button>
            <button
              className={`tab-button ${activeTab === 'types' ? 'active' : ''}`}
              onClick={() => setActiveTab('types')}
            >
              Test Types & Sources
            </button>
          </div>
        </div>

        {/* Test Runs Tab */}
        {activeTab === 'runs' && (
          <div className="card">
            <table className="table" data-testid="test-runs-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Control</th>
                  <th>Test Type</th>
                  <th>Effectiveness</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {testRuns.length > 0 ? testRuns.map((run) => (
                  <tr key={run.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{run.run_id}</td>
                    <td>{run.control_name}</td>
                    <td>
                      <span className="badge" style={{ background: '#f1f5f9', color: '#475569' }}>
                        {run.test_type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <span style={{ 
                        color: getEffectivenessColor(run.effectiveness_rating),
                        fontWeight: '600'
                      }}>
                        {run.effectiveness_rating?.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ 
                          width: '60px', 
                          height: '6px', 
                          background: '#e2e8f0', 
                          borderRadius: '3px',
                          overflow: 'hidden'
                        }}>
                          <div style={{ 
                            width: `${(run.confidence_score || 0) * 100}%`, 
                            height: '100%', 
                            background: getConfidenceLevel(run.confidence_score).color,
                            transition: 'width 0.3s'
                          }}></div>
                        </div>
                        <span style={{ fontSize: '12px', color: getConfidenceLevel(run.confidence_score).color }}>
                          {((run.confidence_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td>
                      {run.requires_human_review && !run.reviewed_by ? (
                        <span className="badge" style={{ background: '#fef3c7', color: '#92400e' }}>
                          Needs Review
                        </span>
                      ) : run.review_outcome ? (
                        <span className="badge" style={{ 
                          background: run.review_outcome === 'CONFIRMED' ? '#f0fdf4' : '#fef2f2',
                          color: run.review_outcome === 'CONFIRMED' ? '#166534' : '#991b1b'
                        }}>
                          {run.review_outcome}
                        </span>
                      ) : (
                        <span className="badge" style={{ background: '#f0fdf4', color: '#166534' }}>
                          Auto-Accepted
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b' }}>
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button 
                          className="btn btn-outline btn-sm"
                          onClick={() => setSelectedRun(run)}
                        >
                          View
                        </button>
                        {run.requires_human_review && !run.reviewed_by && (user.role === 'LOD2_USER' || user.role === 'ADMIN') && (
                          <button 
                            className="btn btn-primary btn-sm"
                            onClick={() => handleReviewTest(run.id, 'CONFIRMED')}
                          >
                            Approve
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                      No automated tests run yet. Select a control and run a test.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Run New Test Tab */}
        {activeTab === 'controls' && (
          <div className="grid grid-2 gap-4">
            {controls.length > 0 ? controls.map((control) => (
              <div key={control.id} className="card" style={{ padding: '20px' }}>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                      {control.name}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>{control.control_id}</span>
                  </div>
                  {control.is_ai_control && (
                    <span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }}>AI Control</span>
                  )}
                </div>
                
                <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px' }}>
                  {control.description?.substring(0, 100)}...
                </p>

                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Current Effectiveness:</div>
                  <span style={{ color: getEffectivenessColor(control.effectiveness), fontWeight: '600' }}>
                    {control.effectiveness?.replace('_', ' ') || 'Not Tested'}
                  </span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {control.is_ai_control ? (
                    <>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleRunTest(control.id, 'AI_BIAS_CHECK')}
                        disabled={runningTest === control.id}
                      >
                        {runningTest === control.id ? 'Running...' : 'Bias Check'}
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => handleRunTest(control.id, 'AI_FAIRNESS')}
                        disabled={runningTest === control.id}
                      >
                        Fairness Test
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => handleRunTest(control.id, 'AI_EXPLAINABILITY')}
                        disabled={runningTest === control.id}
                      >
                        Explainability
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleRunTest(control.id, 'CONFIGURATION_CHECK')}
                        disabled={runningTest === control.id}
                      >
                        {runningTest === control.id ? 'Running...' : 'Config Check'}
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => handleRunTest(control.id, 'ACCESS_REVIEW')}
                        disabled={runningTest === control.id}
                      >
                        Access Review
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => handleRunTest(control.id, 'VULNERABILITY_SCAN')}
                        disabled={runningTest === control.id}
                      >
                        Vuln Scan
                      </button>
                    </>
                  )}
                </div>
              </div>
            )) : (
              <div className="card col-span-2">
                <div className="empty-state">
                  <h3 className="empty-title">No Approved Controls</h3>
                  <p className="empty-description">Create and approve controls in the Controls Library first</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Test Types Tab */}
        {activeTab === 'types' && (
          <div className="grid grid-2 gap-6">
            <div className="card">
              <h3 className="card-title mb-4">Automated Test Types</h3>
              <div className="space-y-3">
                {testTypes.map((type) => (
                  <div 
                    key={type.id}
                    style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px' }}
                  >
                    <div style={{ fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>{type.name}</div>
                    <div style={{ fontSize: '13px', color: '#64748b' }}>{type.description}</div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="card">
              <h3 className="card-title mb-4">Evidence Sources</h3>
              <div className="space-y-3">
                {evidenceSources.map((source) => (
                  <div 
                    key={source.id}
                    style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px' }}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <div style={{ fontWeight: '600', color: '#0f172a' }}>{source.name}</div>
                      <span className="badge" style={{ background: '#eff6ff', color: '#1e40af', fontSize: '11px' }}>
                        {source.type}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#64748b' }}>{source.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Test Run Detail Modal */}
      {selectedRun && (
        <div className="modal-overlay" onClick={() => setSelectedRun(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">Test Run Details - {selectedRun.run_id}</h2>
              <button className="modal-close" onClick={() => setSelectedRun(null)}>&times;</button>
            </div>
            <div className="modal-body">
              {/* Summary */}
              <div className="grid grid-3 gap-4 mb-6">
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Effectiveness</div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: getEffectivenessColor(selectedRun.effectiveness_rating) }}>
                    {selectedRun.effectiveness_rating?.replace('_', ' ')}
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Confidence</div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: getConfidenceLevel(selectedRun.confidence_score).color }}>
                    {((selectedRun.confidence_score || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Test Type</div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a' }}>
                    {selectedRun.test_type?.replace('_', ' ')}
                  </div>
                </div>
              </div>

              {/* Findings */}
              <div className="mb-4">
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Key Findings</h4>
                {selectedRun.findings?.length > 0 ? (
                  <ul style={{ paddingLeft: '20px', color: '#334155', fontSize: '13px' }}>
                    {selectedRun.findings.map((finding, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{finding}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: '#64748b', fontSize: '13px' }}>No findings recorded</p>
                )}
              </div>

              {/* Recommendations */}
              <div className="mb-4">
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Recommendations</h4>
                {selectedRun.recommendations?.length > 0 ? (
                  <ul style={{ paddingLeft: '20px', color: '#334155', fontSize: '13px' }}>
                    {selectedRun.recommendations.map((rec, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{rec}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: '#64748b', fontSize: '13px' }}>No recommendations</p>
                )}
              </div>

              {/* Evidence */}
              <div className="mb-4">
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Evidence Collected</h4>
                <div className="space-y-2">
                  {selectedRun.evidence_collected?.map((ev, idx) => (
                    <div key={idx} style={{ padding: '12px', background: '#f0fdf4', borderRadius: '8px', fontSize: '13px' }}>
                      <div style={{ fontWeight: '600', color: '#166534' }}>{ev.source} - {ev.type}</div>
                      <div style={{ color: '#64748b', marginTop: '4px' }}>
                        Collected: {new Date(ev.collected_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Review Actions */}
              {selectedRun.requires_human_review && !selectedRun.reviewed_by && (user.role === 'LOD2_USER' || user.role === 'ADMIN') && (
                <div style={{ padding: '16px', background: '#fef3c7', borderRadius: '8px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#92400e', marginBottom: '12px' }}>Review Required</h4>
                  <div className="flex gap-2">
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleReviewTest(selectedRun.id, 'CONFIRMED')}
                    >
                      Confirm Results
                    </button>
                    <button 
                      className="btn btn-outline"
                      onClick={() => handleReviewTest(selectedRun.id, 'OVERRIDDEN')}
                    >
                      Override
                    </button>
                    <button 
                      className="btn btn-outline"
                      onClick={() => handleReviewTest(selectedRun.id, 'ESCALATED')}
                    >
                      Escalate
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomatedTesting;
