import { useState, useEffect, useRef } from 'react';
import { api } from '@/App';

const AICompliance = ({ user }) => {
  const [aiSystems, setAiSystems] = useState([]);
  const [aiAssessments, setAiAssessments] = useState([]);
  const [frameworks, setFrameworks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('systems');
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  
  const [showSystemDetailModal, setShowSystemDetailModal] = useState(false);
  const [uploadingControl, setUploadingControl] = useState(null); // control_id being uploaded
  const [showFrameworkAdmin, setShowFrameworkAdmin] = useState(false);
  const [pollingActive, setPollingActive] = useState(false);
  const pollRef = useRef(null);

  const startPolling = () => {
    if (pollRef.current) return;
    setPollingActive(true);
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.get('/ai-assessments');
        const assessments = res.data;
        setAiAssessments(assessments);
        const stillRunning = assessments.some(a => a.status === 'IN_PROGRESS');
        if (!stillRunning) {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setPollingActive(false);
          // Also refresh systems to get updated compliance flags
          const sysRes = await api.get('/ai-systems');
          setAiSystems(sysRes.data);
        }
      } catch (e) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setPollingActive(false);
      }
    }, 4000);
  };

  // Clean up poll on unmount
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const [systemForm, setSystemForm] = useState({
    name: '',
    description: '',
    purpose: '',
    ai_type: 'ML Model',
    deployment_status: 'Development',
    risk_category: 'LIMITED',
    business_unit: '',
    owner: '',
    data_types_processed: [],
    decision_impact: 'Medium',
    human_oversight_level: 'Limited'
  });

  const aiTypes = ['ML Model', 'Deep Learning', 'LLM', 'Computer Vision', 'NLP', 'Recommendation System', 'Predictive Analytics'];
  const deploymentStatuses = ['Development', 'Testing', 'Production', 'Retired'];
  const riskCategories = ['MINIMAL', 'LIMITED', 'HIGH', 'UNACCEPTABLE'];
  const impactLevels = ['Low', 'Medium', 'High', 'Critical'];
  const oversightLevels = ['None', 'Limited', 'Significant', 'Full'];
  const dataTypes = ['Personal data', 'Financial data', 'Health data', 'Biometric data', 'Location data', 'Behavioral data', 'Credit history'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [systemsRes, assessmentsRes, frameworksRes] = await Promise.all([
        api.get('/ai-systems'),
        api.get('/ai-assessments'),
        api.get('/ai-frameworks')
      ]);
      setAiSystems(systemsRes.data);
      setAiAssessments(assessmentsRes.data);
      setFrameworks(frameworksRes.data.frameworks || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSystem = async (e) => {
    e.preventDefault();
    try {
      await api.post('/ai-systems', systemForm);
      setShowRegisterModal(false);
      setSystemForm({
        name: '',
        description: '',
        purpose: '',
        ai_type: 'ML Model',
        deployment_status: 'Development',
        risk_category: 'LIMITED',
        business_unit: '',
        owner: '',
        data_types_processed: [],
        decision_impact: 'Medium',
        human_oversight_level: 'Limited'
      });
      loadData();
    } catch (error) {
      console.error('Failed to register AI system:', error);
      alert('Failed to register AI system');
    }
  };

  const handleCreateAssessment = async (framework) => {
    if (!selectedSystem) return;
    try {
      await api.post('/ai-assessments', {
        ai_system_id: selectedSystem.id,
        framework: framework,
        assessment_type: 'Initial'
      });
      setShowAssessmentModal(false);
      setSelectedSystem(null);
      loadData();
      startPolling();
    } catch (error) {
      console.error('Failed to create assessment:', error);
      alert('Failed to create assessment');
    }
  };

  const getRiskColor = (risk) => {
    const colors = {
      'MINIMAL': '#22c55e',
      'LIMITED': '#3b82f6',
      'HIGH': '#f59e0b',
      'UNACCEPTABLE': '#ef4444'
    };
    return colors[risk] || '#94a3b8';
  };

  const getComplianceColor = (compliance) => {
    const colors = {
      'COMPLIANT': '#22c55e',
      'PARTIALLY_COMPLIANT': '#f59e0b',
      'NON_COMPLIANT': '#ef4444'
    };
    return colors[compliance] || '#94a3b8';
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="ai-compliance-page">
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="ai-compliance-title">AI Compliance</h1>
          <p className="page-subtitle">Manage AI systems and compliance with EU AI Act & NIST AI RMF</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {pollingActive && (
            <span style={{ fontSize: '13px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: '#f59e0b', display: 'inline-block',
                animation: 'pulse 1.2s ease-in-out infinite'
              }}/>
              Assessment running…
            </span>
          )}
          <button
            className="btn btn-primary"
            onClick={() => setShowRegisterModal(true)}
            data-testid="register-ai-system-button"
          >
            + Register AI System
          </button>
        </div>
      </div>

      <div className="page-content">
        {/* Summary Cards */}
        <div className="grid grid-4 gap-4 mb-6">
          <div className="stat-card">
            <div className="stat-label">Total AI Systems</div>
            <div className="stat-value">{aiSystems.length}</div>
            <div className="stat-trend positive">Registered</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">High Risk Systems</div>
            <div className="stat-value" style={{ color: '#f59e0b' }}>
              {aiSystems.filter(s => s.risk_category === 'HIGH').length}
            </div>
            <div className="stat-trend negative">Requires monitoring</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Assessments</div>
            <div className="stat-value">{aiAssessments.length}</div>
            <div className="stat-trend">Completed & in progress</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Compliance Rate</div>
            <div className="stat-value" style={{ color: '#22c55e' }}>
              {aiAssessments.filter(a => a.overall_compliance === 'COMPLIANT').length > 0 
                ? (() => {
                    const completed = aiAssessments.filter(a => a.status === 'COMPLETED');
                    if (completed.length === 0) return 0;
                    return Math.round(completed.filter(a => a.overall_compliance === 'COMPLIANT').length / completed.length * 100);
                  })()
                : 0}%
            </div>
            <div className="stat-trend positive">Compliant systems</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs mb-6">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'systems' ? 'active' : ''}`}
              onClick={() => setActiveTab('systems')}
            >
              AI Systems ({aiSystems.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'assessments' ? 'active' : ''}`}
              onClick={() => setActiveTab('assessments')}
            >
              Assessments ({aiAssessments.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'frameworks' ? 'active' : ''}`}
              onClick={() => setActiveTab('frameworks')}
            >
              Frameworks
            </button>
          </div>
        </div>

        {/* AI Systems Tab */}
        {activeTab === 'systems' && (
          <div className="grid grid-2 gap-4">
            {aiSystems.length > 0 ? aiSystems.map((system) => (
              <div key={system.id} className="card" style={{ padding: '20px' }} data-testid={`ai-system-card-${system.id}`}>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                      {system.name}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>{system.system_id}</span>
                  </div>
                  <span 
                    className="badge"
                    style={{ 
                      background: `${getRiskColor(system.risk_category)}20`,
                      color: getRiskColor(system.risk_category)
                    }}
                  >
                    {system.risk_category} RISK
                  </span>
                </div>

                <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px' }}>
                  {system.description}
                </p>

                <div className="grid grid-2 gap-2 mb-3" style={{ fontSize: '12px' }}>
                  <div><span style={{ color: '#94a3b8' }}>Type:</span> {system.ai_type}</div>
                  <div><span style={{ color: '#94a3b8' }}>Status:</span> {system.deployment_status}</div>
                  <div><span style={{ color: '#94a3b8' }}>Impact:</span> {system.decision_impact}</div>
                  <div><span style={{ color: '#94a3b8' }}>Oversight:</span> {system.human_oversight_level}</div>
                </div>

                <div className="flex flex-wrap gap-1 mb-3">
                  {system.data_types_processed?.slice(0, 3).map((dt, idx) => (
                    <span key={idx} style={{ fontSize: '11px', padding: '2px 8px', background: '#fef3c7', color: '#92400e', borderRadius: '4px' }}>
                      {dt}
                    </span>
                  ))}
                </div>

                {/* Compliance Status */}
                <div className="flex gap-2 mb-3">
                  <div style={{ 
                    padding: '8px 12px', 
                    background: system.eu_ai_act_compliant ? '#f0fdf4' : '#fef2f2',
                    borderRadius: '6px',
                    fontSize: '12px',
                    flex: 1,
                    textAlign: 'center'
                  }}>
                    EU AI Act: <strong style={{ color: system.eu_ai_act_compliant ? '#166534' : '#991b1b' }}>
                      {system.eu_ai_act_compliant === true ? 'Compliant' : system.eu_ai_act_compliant === false ? 'Non-Compliant' : 'Not Assessed'}
                    </strong>
                  </div>
                  <div style={{ 
                    padding: '8px 12px', 
                    background: system.nist_ai_rmf_compliant ? '#f0fdf4' : '#fef2f2',
                    borderRadius: '6px',
                    fontSize: '12px',
                    flex: 1,
                    textAlign: 'center'
                  }}>
                    NIST AI RMF: <strong style={{ color: system.nist_ai_rmf_compliant ? '#166534' : '#991b1b' }}>
                      {system.nist_ai_rmf_compliant === true ? 'Compliant' : system.nist_ai_rmf_compliant === false ? 'Non-Compliant' : 'Not Assessed'}
                    </strong>
                  </div>
                </div>

                <div className="flex gap-2 pt-3" style={{ borderTop: '1px solid #e2e8f0' }}>
                  <button 
                    className="btn btn-primary btn-sm flex-1"
                    onClick={() => { setSelectedSystem(system); setShowAssessmentModal(true); }}
                  >
                    Run Assessment
                  </button>
                  <button className="btn btn-outline btn-sm" onClick={() => { setSelectedSystem(system); setShowSystemDetailModal(true); }}>View Details</button>
                  <button
                    className="btn btn-sm"
                    style={{ background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca' }}
                    onClick={async () => {
                      if (!window.confirm(`Delete "${system.name}" and all its assessments?`)) return;
                      await api.delete(`/ai-systems/${system.id}`);
                      loadData();
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            )) : (
              <div className="card col-span-2">
                <div className="empty-state">
                  <h3 className="empty-title">No AI Systems Registered</h3>
                  <p className="empty-description">Register your AI systems to track compliance with EU AI Act and NIST AI RMF</p>
                  <button className="btn btn-primary" onClick={() => setShowRegisterModal(true)}>
                    Register AI System
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Assessments Tab */}
        {activeTab === 'assessments' && (
          <div className="card">
            <table className="table" data-testid="assessments-table" style={{ borderSpacing: '0 4px' }}>
              <thead>
                <tr>
                  <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>Assessment ID</th>
                  <th style={{ padding: '12px 16px', minWidth: '160px' }}>AI System</th>
                  <th style={{ padding: '12px 16px', minWidth: '140px' }}>Framework</th>
                  <th style={{ padding: '12px 16px' }}>Status</th>
                  <th style={{ padding: '12px 16px', minWidth: '140px' }}>Compliance</th>
                  <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>Date</th>
                  <th style={{ padding: '12px 16px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {aiAssessments.length > 0 ? aiAssessments.map((assessment) => (
                  <tr key={assessment.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px', padding: '14px 16px', whiteSpace: 'nowrap' }}>{assessment.assessment_id}</td>
                    <td style={{ padding: '14px 16px', fontWeight: '500' }}>{assessment.ai_system_name}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>
                        {(() => { const fw = frameworks.find(f => f.id === assessment.framework); return fw ? `${fw.flag} ${fw.name}` : assessment.framework; })()}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span className="badge" style={{ 
                        background: assessment.status === 'COMPLETED' ? '#f0fdf4' : '#fef3c7',
                        color: assessment.status === 'COMPLETED' ? '#166534' : '#92400e'
                      }}>
                        {assessment.status}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {assessment.overall_compliance ? (
                        <span style={{ 
                          color: getComplianceColor(assessment.overall_compliance),
                          fontWeight: '600'
                        }}>
                          {assessment.overall_compliance.replace(/_/g, ' ')}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b', padding: '14px 16px', whiteSpace: 'nowrap' }}>
                      {new Date(assessment.assessment_date).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          className="btn btn-outline btn-sm"
                          onClick={() => setSelectedAssessment(assessment)}
                          disabled={assessment.status !== 'COMPLETED'}
                          title={assessment.status !== 'COMPLETED' ? 'Assessment still in progress' : 'View details'}
                        >
                          View
                        </button>
                        <button
                          className="btn btn-sm"
                          style={{ background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca' }}
                          onClick={async () => {
                            if (!window.confirm('Delete this assessment?')) return;
                            await api.delete(`/ai-assessments/${assessment.id}`);
                            loadData();
                          }}
                          title="Delete assessment"
                        >
                          ✕
                        </button>
                      </div>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                      No assessments yet. Run an assessment on an AI system to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Frameworks Tab */}
        {activeTab === 'frameworks' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <p style={{ color: '#64748b', fontSize: '13px' }}>Frameworks define which controls are evaluated in each assessment. Add or remove frameworks without any code changes.</p>
              <button className="btn btn-outline btn-sm" onClick={() => setShowFrameworkAdmin(true)}>
                ⚙ Manage Frameworks & Controls
              </button>
            </div>
            <div className="grid grid-2 gap-6">
              {frameworks.map(fw => (
                <div key={fw.id} className="card" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '16px' }}>
                    <div style={{ width: '48px', height: '48px', background: fw.color || '#475569', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: '700', fontSize: '18px', flexShrink: 0 }}>
                      {fw.flag || '🌐'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '2px' }}>{fw.name}</h3>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>{fw.jurisdiction} · Effective {fw.effective_date}</div>
                      <p style={{ fontSize: '12px', color: '#64748b' }}>{fw.description}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '12px' }}>
                    {fw.categories?.map((cat, idx) => (
                      <span key={idx} style={{ fontSize: '11px', padding: '3px 10px', background: fw.bg_color || '#f1f5f9', color: fw.color || '#475569', borderRadius: '6px', border: `1px solid ${fw.color || '#475569'}22` }}>{cat}</span>
                    ))}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', padding: '8px 12px', background: '#f8fafc', borderRadius: '6px' }}>
                    To add controls: insert entries with <code style={{ fontSize: '11px' }}>framework: "{fw.id}"</code> via the Manage panel or seed file.
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Framework Controls Admin Modal */}
      {showFrameworkAdmin && (
        <FrameworkAdminModal onClose={() => setShowFrameworkAdmin(false)} api={api} />
      )}


      {/* Register AI System Modal */}
      {showRegisterModal && (
        <div className="modal-overlay" onClick={() => setShowRegisterModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">Register AI System</h2>
              <button className="modal-close" onClick={() => setShowRegisterModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleRegisterSystem}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">System Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={systemForm.name}
                    onChange={(e) => setSystemForm({ ...systemForm, name: e.target.value })}
                    placeholder="e.g., Customer Credit Scoring Model"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description *</label>
                  <textarea
                    className="form-textarea"
                    value={systemForm.description}
                    onChange={(e) => setSystemForm({ ...systemForm, description: e.target.value })}
                    placeholder="Describe the AI system's functionality"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Purpose *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={systemForm.purpose}
                    onChange={(e) => setSystemForm({ ...systemForm, purpose: e.target.value })}
                    placeholder="e.g., Automated credit risk assessment"
                    required
                  />
                </div>

                <div className="grid grid-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">AI Type *</label>
                    <select
                      className="form-select"
                      value={systemForm.ai_type}
                      onChange={(e) => setSystemForm({ ...systemForm, ai_type: e.target.value })}
                    >
                      {aiTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Deployment Status *</label>
                    <select
                      className="form-select"
                      value={systemForm.deployment_status}
                      onChange={(e) => setSystemForm({ ...systemForm, deployment_status: e.target.value })}
                    >
                      {deploymentStatuses.map(status => (
                        <option key={status} value={status}>{status}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Risk Category (EU AI Act) *</label>
                    <select
                      className="form-select"
                      value={systemForm.risk_category}
                      onChange={(e) => setSystemForm({ ...systemForm, risk_category: e.target.value })}
                    >
                      {riskCategories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                    <div className="form-helper">
                      {systemForm.risk_category === 'UNACCEPTABLE' && 'Prohibited AI systems under EU AI Act'}
                      {systemForm.risk_category === 'HIGH' && 'Subject to strict requirements under EU AI Act'}
                      {systemForm.risk_category === 'LIMITED' && 'Transparency obligations apply'}
                      {systemForm.risk_category === 'MINIMAL' && 'Voluntary codes of conduct'}
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Decision Impact *</label>
                    <select
                      className="form-select"
                      value={systemForm.decision_impact}
                      onChange={(e) => setSystemForm({ ...systemForm, decision_impact: e.target.value })}
                    >
                      {impactLevels.map(level => (
                        <option key={level} value={level}>{level}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Business Unit *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={systemForm.business_unit}
                      onChange={(e) => setSystemForm({ ...systemForm, business_unit: e.target.value })}
                      placeholder="e.g., Consumer Banking"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Owner *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={systemForm.owner}
                      onChange={(e) => setSystemForm({ ...systemForm, owner: e.target.value })}
                      placeholder="e.g., risk-team@bank.com"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Human Oversight Level *</label>
                  <select
                    className="form-select"
                    value={systemForm.human_oversight_level}
                    onChange={(e) => setSystemForm({ ...systemForm, human_oversight_level: e.target.value })}
                  >
                    {oversightLevels.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Data Types Processed</label>
                  <div className="flex flex-wrap gap-2">
                    {dataTypes.map(dt => (
                      <label key={dt} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={systemForm.data_types_processed.includes(dt)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSystemForm({ ...systemForm, data_types_processed: [...systemForm.data_types_processed, dt] });
                            } else {
                              setSystemForm({ ...systemForm, data_types_processed: systemForm.data_types_processed.filter(d => d !== dt) });
                            }
                          }}
                        />
                        {dt}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowRegisterModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Register System
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assessment Detail Modal */}
      {selectedAssessment && (
        <div className="modal-overlay" onClick={() => setSelectedAssessment(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <div>
                <h2 className="modal-title">{selectedAssessment.ai_system_name}</h2>
                <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#64748b' }}>{selectedAssessment.assessment_id}</span>
              </div>
              <button className="modal-close" onClick={() => setSelectedAssessment(null)}>&times;</button>
            </div>
            <div className="modal-body">
              {/* Summary Row */}
              <div className="grid grid-3 gap-4 mb-6">
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Framework</div>
                  <div style={{ fontWeight: '600', color: '#1e40af' }}>
                    {(() => { const fw = frameworks.find(f => f.id === selectedAssessment.framework); return fw ? `${fw.flag} ${fw.name}` : selectedAssessment.framework; })()}
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Overall Compliance</div>
                  <div style={{ fontWeight: '600', color: getComplianceColor(selectedAssessment.overall_compliance) }}>
                    {selectedAssessment.overall_compliance?.replace(/_/g, ' ') || 'N/A'}
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Compliance Score</div>
                  <div style={{ fontWeight: '700', fontSize: '20px', color: getComplianceColor(selectedAssessment.overall_compliance) }}>
                    {(() => {
                      const controls = selectedAssessment.control_results || [];
                      const total = controls.length;
                      if (total === 0) return '-';
                      const compliant = controls.filter(c => c.status === 'COMPLIANT').length;
                      const partial = controls.filter(c => c.status === 'PARTIALLY_COMPLIANT').length;
                      const pct = ((compliant + partial * 0.5) / total * 100).toFixed(1);
                      return `${pct}%`;
                    })()}
                  </div>
                </div>
              </div>

              {/* Control Results */}
              <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', marginBottom: '12px' }}>
                Control Assessment Results ({selectedAssessment.control_results?.length || 0} controls)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
                {selectedAssessment.control_results?.map((ctrl, idx) => (
                  <div key={idx} style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '14px',
                    borderLeft: `4px solid ${ctrl.status === 'COMPLIANT' ? '#22c55e' : ctrl.status === 'PARTIALLY_COMPLIANT' ? '#f59e0b' : '#ef4444'}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <div>
                        <span style={{ fontWeight: '600', fontSize: '14px', color: '#0f172a' }}>{ctrl.control_name}</span>
                        <span style={{ marginLeft: '8px', fontSize: '11px', padding: '2px 8px', background: '#f1f5f9', color: '#475569', borderRadius: '4px' }}>
                          {ctrl.category}
                        </span>
                      </div>
                      <span style={{
                        fontSize: '12px', fontWeight: '600', padding: '3px 10px', borderRadius: '12px',
                        background: ctrl.status === 'COMPLIANT' ? '#f0fdf4' : ctrl.status === 'PARTIALLY_COMPLIANT' ? '#fef3c7' : '#fef2f2',
                        color: ctrl.status === 'COMPLIANT' ? '#166534' : ctrl.status === 'PARTIALLY_COMPLIANT' ? '#92400e' : '#991b1b'
                      }}>
                        {ctrl.status?.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>{ctrl.requirement}</div>
                    {ctrl.findings && (
                      <div style={{ fontSize: '12px', color: '#475569', background: '#f8fafc', padding: '8px', borderRadius: '6px', marginBottom: '6px' }}>
                        <strong>Finding:</strong> {ctrl.findings}
                      </div>
                    )}
                    {ctrl.evidence_gaps?.length > 0 && (
                      <div style={{ fontSize: '12px', color: '#92400e', marginBottom: '10px' }}>
                        <strong>Evidence gaps:</strong>
                        <ul style={{ margin: '4px 0 0 0', paddingLeft: '16px' }}>
                          {ctrl.evidence_gaps.map((gap, gi) => <li key={gi}>{gap}</li>)}
                        </ul>
                      </div>
                    )}
                    {/* Evidence documents already uploaded */}
                    {ctrl.evidence_documents?.length > 0 && (
                      <div style={{ fontSize: '12px', color: '#166534', marginBottom: '8px' }}>
                        <strong>Evidence uploaded:</strong>
                        <ul style={{ margin: '4px 0 0 0', paddingLeft: '16px' }}>
                          {ctrl.evidence_documents.map((doc, di) => (
                            <li key={di}>{doc.filename} — <em>{doc.evaluation?.finding}</em></li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {/* Upload evidence button */}
                    <div style={{ marginTop: '8px' }}>
                      <label style={{
                        display: 'inline-block', cursor: 'pointer',
                        fontSize: '12px', padding: '4px 12px',
                        background: '#eff6ff', color: '#1e40af',
                        border: '1px solid #bfdbfe', borderRadius: '6px'
                      }}>
                        {uploadingControl === ctrl.control_id ? 'Uploading…' : '📎 Upload Evidence'}
                        <input type="file" style={{ display: 'none' }} accept=".pdf,.txt,.csv,.xlsx,.docx"
                          onChange={async (e) => {
                            const file = e.target.files[0];
                            if (!file) return;
                            setUploadingControl(ctrl.control_id);
                            const fd = new FormData();
                            fd.append('file', file);
                            try {
                              const res = await api.post(
                                `/ai-assessments/${selectedAssessment.id}/control/${ctrl.control_id}/evidence`,
                                fd, { headers: { 'Content-Type': 'multipart/form-data' } }
                              );
                              // Refresh the assessment
                              const updated = await api.get('/ai-assessments');
                              const fresh = updated.data.find(a => a.id === selectedAssessment.id);
                              if (fresh) setSelectedAssessment(fresh);
                              setAiAssessments(updated.data);
                            } catch (err) {
                              alert('Upload failed: ' + (err.response?.data?.detail || err.message));
                            } finally {
                              setUploadingControl(null);
                              e.target.value = '';
                            }
                          }}
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>

              {/* Findings */}
              {selectedAssessment.findings?.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', marginBottom: '10px' }}>Key Findings</h3>
                  <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedAssessment.findings.map((f, i) => (
                      <li key={i} style={{ fontSize: '13px', color: '#475569' }}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {selectedAssessment.recommendations?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', marginBottom: '10px' }}>Recommendations</h3>
                  <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedAssessment.recommendations.map((r, i) => (
                      <li key={i} style={{ fontSize: '13px', color: '#475569' }}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setSelectedAssessment(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* System Detail Modal */}
      {showSystemDetailModal && selectedSystem && (
        <div className="modal-overlay" onClick={() => setShowSystemDetailModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <div>
                <h2 className="modal-title">{selectedSystem.name}</h2>
                <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#64748b' }}>{selectedSystem.system_id}</span>
              </div>
              <button className="modal-close" onClick={() => setShowSystemDetailModal(false)}>&times;</button>
            </div>
            <div className="modal-body">
              <div className="grid grid-2 gap-4 mb-4">
                {[
                  ['AI Type', selectedSystem.ai_type],
                  ['Deployment', selectedSystem.deployment_status],
                  ['Risk Category', selectedSystem.risk_category],
                  ['Decision Impact', selectedSystem.decision_impact],
                  ['Human Oversight', selectedSystem.human_oversight_level],
                  ['Business Unit', selectedSystem.business_unit],
                  ['Owner', selectedSystem.owner],
                  ['Registered', selectedSystem.created_at ? new Date(selectedSystem.created_at).toLocaleDateString() : '—'],
                ].map(([label, value]) => (
                  <div key={label} style={{ padding: '10px 14px', background: '#f8fafc', borderRadius: '8px' }}>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>{label}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a' }}>{value || '—'}</div>
                  </div>
                ))}
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Description</div>
                <p style={{ fontSize: '13px', color: '#475569' }}>{selectedSystem.description}</p>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Purpose</div>
                <p style={{ fontSize: '13px', color: '#475569' }}>{selectedSystem.purpose}</p>
              </div>

              {selectedSystem.data_types_processed?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Data types processed</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedSystem.data_types_processed.map((dt, i) => (
                      <span key={i} style={{ fontSize: '12px', padding: '3px 10px', background: '#fef3c7', color: '#92400e', borderRadius: '6px' }}>{dt}</span>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px', padding: '14px', background: '#f8fafc', borderRadius: '8px' }}>
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>EU AI Act</div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: selectedSystem.eu_ai_act_compliant ? '#166534' : '#64748b' }}>
                    {selectedSystem.eu_ai_act_compliant === true ? '✓ Compliant' : selectedSystem.eu_ai_act_compliant === false ? '✗ Non-Compliant' : 'Not Assessed'}
                  </div>
                </div>
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>NIST AI RMF</div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: selectedSystem.nist_ai_rmf_compliant ? '#166534' : '#64748b' }}>
                    {selectedSystem.nist_ai_rmf_compliant === true ? '✓ Compliant' : selectedSystem.nist_ai_rmf_compliant === false ? '✗ Non-Compliant' : 'Not Assessed'}
                  </div>
                </div>
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Last Assessed</div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a' }}>
                    {selectedSystem.last_assessment_date ? new Date(selectedSystem.last_assessment_date).toLocaleDateString() : 'Never'}
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setShowSystemDetailModal(false)}>Close</button>
              <button className="btn btn-primary" onClick={() => { setShowSystemDetailModal(false); setShowAssessmentModal(true); }}>
                Run Assessment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assessment Selection Modal */}
      {showAssessmentModal && selectedSystem && (
        <div className="modal-overlay" onClick={() => setShowAssessmentModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h2 className="modal-title">Run Assessment</h2>
              <button className="modal-close" onClick={() => setShowAssessmentModal(false)}>&times;</button>
            </div>
            <div className="modal-body">
              <p style={{ marginBottom: '16px', color: '#64748b' }}>
                Select a framework to assess <strong>{selectedSystem.name}</strong>:
              </p>
              <div className="space-y-3">
                {frameworks.map(fw => (
                  <button
                    key={fw.id}
                    className="btn btn-outline w-full"
                    style={{ justifyContent: 'flex-start', padding: '16px', height: 'auto', textAlign: 'left' }}
                    onClick={() => handleCreateAssessment(fw.id)}
                  >
                    <span style={{ fontSize: '20px', marginRight: '12px' }}>{fw.flag || '🌐'}</span>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '4px' }}>{fw.name}</div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>{fw.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ── Framework Controls Admin Modal ────────────────────────────────────────────
const FrameworkAdminModal = ({ onClose, api }) => {
  const [tab, setTab] = useState('frameworks'); // 'frameworks' | 'controls'
  const [frameworks, setFrameworks] = useState([]);
  const [controls, setControls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterFw, setFilterFw] = useState('');
  const [showAddControlForm, setShowAddControlForm] = useState(false);
  const [showAddFwForm, setShowAddFwForm] = useState(false);
  const [newControl, setNewControl] = useState({ id: '', framework: '', name: '', category: '', article: '', requirement: '', guidance: '', mandatory: true, risk_category_filter: ['ALL'] });
  const [newFw, setNewFw] = useState({ id: '', name: '', flag: '🌐', color: '#1e40af', bg_color: '#eff6ff', description: '', jurisdiction: '', effective_date: '', categories: '' });

  useEffect(() => {
    Promise.all([
      api.get('/ai-frameworks'),
      api.get('/ai-framework-controls')
    ]).then(([fwRes, ctrlRes]) => {
      setFrameworks(fwRes.data.frameworks || []);
      setControls(ctrlRes.data);
      if (fwRes.data.frameworks?.length) setFilterFw(fwRes.data.frameworks[0].id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = filterFw ? controls.filter(c => c.framework === filterFw) : controls;

  const handleAddControl = async () => {
    if (!newControl.id || !newControl.name || !newControl.requirement || !newControl.framework) return alert('ID, Framework, Name and Requirement are required');
    try {
      await api.post('/ai-framework-controls', newControl);
      const r = await api.get('/ai-framework-controls');
      setControls(r.data);
      setShowAddControlForm(false);
      setNewControl({ id: '', framework: filterFw, name: '', category: '', article: '', requirement: '', guidance: '', mandatory: true, risk_category_filter: ['ALL'] });
    } catch (e) { alert(e.response?.data?.detail || 'Failed to add control'); }
  };

  const handleDeleteControl = async (id) => {
    if (!window.confirm(`Delete control ${id}?`)) return;
    await api.delete(`/ai-framework-controls/${id}`);
    setControls(prev => prev.filter(c => c.id !== id));
  };

  const handleAddFramework = async () => {
    if (!newFw.id || !newFw.name) return alert('ID and Name are required');
    try {
      const payload = { ...newFw, categories: newFw.categories.split(',').map(s => s.trim()).filter(Boolean) };
      const res = await api.post('/ai-frameworks', payload);
      setFrameworks(prev => [...prev, res.data]);
      setShowAddFwForm(false);
      setNewFw({ id: '', name: '', flag: '🌐', color: '#1e40af', bg_color: '#eff6ff', description: '', jurisdiction: '', effective_date: '', categories: '' });
    } catch (e) { alert(e.response?.data?.detail || 'Failed to add framework'); }
  };

  const handleDeactivateFramework = async (id) => {
    if (!window.confirm(`Deactivate framework "${id}"? It will no longer appear in assessments. Controls are preserved.`)) return;
    await api.delete(`/ai-frameworks/${id}`);
    setFrameworks(prev => prev.filter(f => f.id !== id));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <h2 className="modal-title">Manage Frameworks & Controls</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '4px', padding: '0 24px', borderBottom: '1px solid #e2e8f0' }}>
          {['frameworks', 'controls'].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: '10px 18px', border: 'none', background: 'none', cursor: 'pointer',
              fontWeight: tab === t ? '600' : '400',
              color: tab === t ? '#1e40af' : '#64748b',
              borderBottom: tab === t ? '2px solid #1e40af' : '2px solid transparent',
              fontSize: '13px', textTransform: 'capitalize'
            }}>{t}</button>
          ))}
        </div>

        <div className="modal-body">
          {loading ? <p>Loading…</p> : tab === 'frameworks' ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
                <button className="btn btn-primary btn-sm" onClick={() => setShowAddFwForm(v => !v)}>
                  {showAddFwForm ? '✕ Cancel' : '+ Add Framework'}
                </button>
              </div>

              {showAddFwForm && (
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', marginBottom: '16px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>New Framework</h4>
                  <div className="grid grid-2 gap-3">
                    {[['ID (no spaces, e.g. MAS_TRM)', 'id', 'MAS_TRM'], ['Name', 'name', 'MAS Technology Risk Management'], ['Flag emoji', 'flag', '🇸🇬'], ['Jurisdiction', 'jurisdiction', 'Singapore'], ['Effective date', 'effective_date', '2021-01-18'], ['Hex colour', 'color', '#1e40af']].map(([label, key, ph]) => (
                      <div key={key}>
                        <label className="form-label">{label}</label>
                        <input className="form-input" placeholder={ph} value={newFw[key]} onChange={e => setNewFw(p => ({ ...p, [key]: e.target.value }))} />
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <label className="form-label">Description</label>
                    <textarea className="form-input" rows={2} value={newFw.description} onChange={e => setNewFw(p => ({ ...p, description: e.target.value }))} placeholder="Brief framework description..." />
                  </div>
                  <div style={{ marginTop: '8px' }}>
                    <label className="form-label">Categories (comma-separated)</label>
                    <input className="form-input" value={newFw.categories} onChange={e => setNewFw(p => ({ ...p, categories: e.target.value }))} placeholder="Governance, Risk Management, Technology Controls" />
                  </div>
                  <div style={{ marginTop: '4px', fontSize: '12px', color: '#64748b' }}>
                    After saving, add controls for this framework via the Controls tab using the same framework ID.
                  </div>
                  <button className="btn btn-primary" style={{ marginTop: '12px' }} onClick={handleAddFramework}>Save Framework</button>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {frameworks.map(fw => (
                  <div key={fw.id} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '14px 16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ width: '40px', height: '40px', background: fw.color, borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', flexShrink: 0 }}>{fw.flag}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: '#0f172a' }}>{fw.name}</div>
                      <div style={{ fontSize: '12px', color: '#94a3b8' }}>{fw.id} · {fw.jurisdiction} · {controls.filter(c => c.framework === fw.id).length} controls</div>
                    </div>
                    <button className="btn btn-sm" style={{ background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca' }} onClick={() => handleDeactivateFramework(fw.id)}>Deactivate</button>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', alignItems: 'center' }}>
                <select className="form-input" style={{ width: '220px' }} value={filterFw} onChange={e => setFilterFw(e.target.value)}>
                  <option value="">All frameworks</option>
                  {frameworks.map(fw => <option key={fw.id} value={fw.id}>{fw.flag} {fw.name}</option>)}
                </select>
                <span style={{ fontSize: '13px', color: '#64748b' }}>{filtered.length} controls</span>
                <button className="btn btn-primary btn-sm" style={{ marginLeft: 'auto' }} onClick={() => setShowAddControlForm(v => !v)}>
                  {showAddControlForm ? '✕ Cancel' : '+ Add Control'}
                </button>
              </div>

              {showAddControlForm && (
                <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', marginBottom: '16px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>New Control</h4>
                  <div className="grid grid-2 gap-3">
                    {[['ID', 'id', 'EU-AI-019'], ['Name', 'name', 'Control name'], ['Article', 'article', 'Article 5'], ['Category', 'category', 'Governance']].map(([label, key, ph]) => (
                      <div key={key}>
                        <label className="form-label">{label}</label>
                        <input className="form-input" placeholder={ph} value={newControl[key]} onChange={e => setNewControl(p => ({ ...p, [key]: e.target.value }))} />
                      </div>
                    ))}
                    <div>
                      <label className="form-label">Framework</label>
                      <select className="form-input" value={newControl.framework} onChange={e => setNewControl(p => ({ ...p, framework: e.target.value }))}>
                        <option value="">Select framework</option>
                        {frameworks.map(fw => <option key={fw.id} value={fw.id}>{fw.flag} {fw.name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="form-label">Applies to</label>
                      <select className="form-input" value={newControl.risk_category_filter[0]} onChange={e => setNewControl(p => ({ ...p, risk_category_filter: e.target.value === 'ALL' ? ['ALL'] : ['HIGH', 'UNACCEPTABLE'] }))}>
                        <option value="ALL">All risk categories</option>
                        <option value="HIGH">High + Unacceptable only</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <label className="form-label">Requirement</label>
                    <textarea className="form-input" rows={2} value={newControl.requirement} onChange={e => setNewControl(p => ({ ...p, requirement: e.target.value }))} placeholder="Full requirement text..." />
                  </div>
                  <div style={{ marginTop: '8px' }}>
                    <label className="form-label">Guidance</label>
                    <textarea className="form-input" rows={2} value={newControl.guidance} onChange={e => setNewControl(p => ({ ...p, guidance: e.target.value }))} placeholder="Guidance for auditors..." />
                  </div>
                  <button className="btn btn-primary" style={{ marginTop: '12px' }} onClick={handleAddControl}>Save Control</button>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {filtered.map(ctrl => (
                  <div key={ctrl.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px', flexWrap: 'wrap' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#64748b' }}>{ctrl.id}</span>
                        <span style={{ fontSize: '11px', padding: '2px 8px', background: '#f1f5f9', color: '#475569', borderRadius: '4px' }}>{ctrl.category}</span>
                        {ctrl.mandatory && <span style={{ fontSize: '11px', padding: '2px 8px', background: '#fef2f2', color: '#991b1b', borderRadius: '4px' }}>Mandatory</span>}
                      </div>
                      <div style={{ fontWeight: '600', fontSize: '13px', color: '#0f172a', marginBottom: '2px' }}>{ctrl.name}</div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>{ctrl.article}</div>
                    </div>
                    <button className="btn btn-sm" style={{ background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca', flexShrink: 0 }} onClick={() => handleDeleteControl(ctrl.id)}>✕</button>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default AICompliance;