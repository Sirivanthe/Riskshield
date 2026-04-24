import { useState, useEffect } from 'react';
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
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="ai-compliance-title">AI Compliance</h1>
          <p className="page-subtitle">Manage AI systems and compliance with EU AI Act & NIST AI RMF</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowRegisterModal(true)}
          data-testid="register-ai-system-button"
        >
          + Register AI System
        </button>
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
                ? Math.round(aiAssessments.filter(a => a.overall_compliance === 'COMPLIANT').length / aiAssessments.filter(a => a.status === 'COMPLETED').length * 100) || 0
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
                  <button className="btn btn-outline btn-sm">View Details</button>
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
            <table className="table" data-testid="assessments-table">
              <thead>
                <tr>
                  <th>Assessment ID</th>
                  <th>AI System</th>
                  <th>Framework</th>
                  <th>Status</th>
                  <th>Compliance</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {aiAssessments.length > 0 ? aiAssessments.map((assessment) => (
                  <tr key={assessment.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{assessment.assessment_id}</td>
                    <td>{assessment.ai_system_name}</td>
                    <td>
                      <span className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>
                        {assessment.framework === 'EU_AI_ACT' ? 'EU AI Act' : 'NIST AI RMF'}
                      </span>
                    </td>
                    <td>
                      <span className="badge" style={{ 
                        background: assessment.status === 'COMPLETED' ? '#f0fdf4' : '#fef3c7',
                        color: assessment.status === 'COMPLETED' ? '#166534' : '#92400e'
                      }}>
                        {assessment.status}
                      </span>
                    </td>
                    <td>
                      {assessment.overall_compliance ? (
                        <span style={{ 
                          color: getComplianceColor(assessment.overall_compliance),
                          fontWeight: '600'
                        }}>
                          {assessment.overall_compliance.replace('_', ' ')}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b' }}>
                      {new Date(assessment.assessment_date).toLocaleDateString()}
                    </td>
                    <td>
                      <button 
                        className="btn btn-outline btn-sm"
                        onClick={() => setSelectedAssessment(assessment)}
                        disabled={assessment.status !== 'COMPLETED'}
                        title={assessment.status !== 'COMPLETED' ? 'Assessment still in progress' : 'View details'}
                      >
                        View
                      </button>
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
          <div className="grid grid-2 gap-6">
            {frameworks.map((fw) => (
              <div key={fw.id} className="card" style={{ padding: '24px' }}>
                <div className="flex items-start gap-4 mb-4">
                  <div style={{ 
                    width: '48px', 
                    height: '48px', 
                    background: fw.id === 'EU_AI_ACT' ? '#1e40af' : '#0f766e',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: '700',
                    fontSize: '14px'
                  }}>
                    {fw.id === 'EU_AI_ACT' ? 'EU' : 'NIST'}
                  </div>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                      {fw.name}
                    </h3>
                    <p style={{ fontSize: '13px', color: '#64748b' }}>{fw.description}</p>
                  </div>
                </div>

                <div className="mb-4">
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                    {fw.id === 'EU_AI_ACT' ? 'Risk Categories' : 'Core Functions'}
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {(fw.risk_categories || fw.functions || fw.categories)?.map((item, idx) => (
                      <span 
                        key={idx} 
                        style={{ 
                          fontSize: '12px', 
                          padding: '4px 12px', 
                          background: '#f1f5f9', 
                          color: '#475569', 
                          borderRadius: '6px' 
                        }}
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>

                {fw.categories && (
                  <div>
                    <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                      Assessment Categories
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {fw.categories.map((cat, idx) => (
                        <span 
                          key={idx} 
                          style={{ 
                            fontSize: '12px', 
                            padding: '4px 12px', 
                            background: '#eff6ff', 
                            color: '#1e40af', 
                            borderRadius: '6px' 
                          }}
                        >
                          {cat}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

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
                    {selectedAssessment.framework === 'EU_AI_ACT' ? 'EU AI Act' : 'NIST AI RMF'}
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
                      <div style={{ fontSize: '12px', color: '#92400e' }}>
                        <strong>Evidence gaps:</strong> {ctrl.evidence_gaps.join(', ')}
                      </div>
                    )}
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
                <button
                  className="btn btn-outline w-full"
                  style={{ justifyContent: 'flex-start', padding: '16px', height: 'auto' }}
                  onClick={() => handleCreateAssessment('EU_AI_ACT')}
                >
                  <div>
                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>EU AI Act Assessment</div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>10 mandatory controls for high-risk AI systems</div>
                  </div>
                </button>
                <button
                  className="btn btn-outline w-full"
                  style={{ justifyContent: 'flex-start', padding: '16px', height: 'auto' }}
                  onClick={() => handleCreateAssessment('NIST_AI_RMF')}
                >
                  <div>
                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>NIST AI RMF Assessment</div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>12 controls across GOVERN, MAP, MEASURE, MANAGE</div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AICompliance;