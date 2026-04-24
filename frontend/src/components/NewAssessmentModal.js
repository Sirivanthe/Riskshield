import { useState } from 'react';
import { api } from '@/App';

const NewAssessmentModal = ({ onClose, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    system_name: '',
    business_unit: '',
    description: '',
    frameworks: [],
    scenario: ''
  });

  const allFrameworks = [
    'NIST CSF',
    'ISO 27001',
    'SOC2',
    'PCI-DSS',
    'GDPR',
    'Basel III'
  ];

  const scenarios = [
    { id: 'none', name: 'None - Standard Assessment' },
    { id: 'ransomware', name: 'Ransomware Attack Scenario' },
    { id: 'iam_breach', name: 'IAM Breach Scenario' },
    { id: 'data_leak', name: 'Data Leakage Scenario' },
    { id: 'outage', name: 'System Outage Scenario' }
  ];

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const toggleFramework = (framework) => {
    if (formData.frameworks.includes(framework)) {
      handleChange('frameworks', formData.frameworks.filter(f => f !== framework));
    } else {
      handleChange('frameworks', [...formData.frameworks, framework]);
    }
  };

  const handleSubmit = async () => {
    if (formData.frameworks.length === 0) {
      alert('Please select at least one framework');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/assessments', formData);
      onSuccess(response.data);
    } catch (error) {
      console.error('Failed to create assessment:', error);
      alert('Failed to create assessment. Please try again.');
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.name && formData.system_name && formData.business_unit;
      case 2:
        return formData.frameworks.length > 0;
      case 3:
        return true;
      default:
        return false;
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px'
      }}
      onClick={onClose}
      data-testid="new-assessment-modal"
    >
      <div
        style={{
          background: 'white',
          borderRadius: '16px',
          maxWidth: '600px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '24px', borderBottom: '1px solid #e5e7eb' }}>
          <div className="flex justify-between items-center">
            <div>
              <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', marginBottom: '4px' }}>New Assessment</h2>
              <p style={{ fontSize: '14px', color: '#64748b' }}>Step {step} of 3</p>
            </div>
            <button
              onClick={onClose}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                border: 'none',
                background: '#f1f5f9',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s'
              }}
              data-testid="close-modal-button"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          {/* Progress Bar */}
          <div style={{ marginTop: '20px', height: '4px', background: '#e5e7eb', borderRadius: '2px', overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                width: `${(step / 3) * 100}%`,
                transition: 'width 0.3s'
              }}
            ></div>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '24px' }}>
          {step === 1 && (
            <div data-testid="assessment-step-1">
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#0f172a', marginBottom: '20px' }}>Basic Information</h3>
              
              <div className="form-group">
                <label className="form-label">Assessment Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Q1 2024 Cloud Infrastructure Assessment"
                  data-testid="assessment-name-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">System/Application Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.system_name}
                  onChange={(e) => handleChange('system_name', e.target.value)}
                  placeholder="AWS Production Environment"
                  data-testid="system-name-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Business Unit *</label>
                <select
                  className="form-select"
                  value={formData.business_unit}
                  onChange={(e) => handleChange('business_unit', e.target.value)}
                  data-testid="business-unit-select"
                >
                  <option value="">Select business unit</option>
                  <option value="Technology">Technology</option>
                  <option value="Operations">Operations</option>
                  <option value="Compliance">Compliance</option>
                  <option value="Risk Management">Risk Management</option>
                  <option value="Security">Security</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Describe the system, infrastructure, and scope of this assessment..."
                  data-testid="description-textarea"
                ></textarea>
              </div>
            </div>
          )}

          {step === 2 && (
            <div data-testid="assessment-step-2">
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Regulatory Frameworks</h3>
              <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>Select the frameworks to assess against</p>
              
              <div className="grid grid-2 gap-3">
                {allFrameworks.map((framework) => (
                  <div
                    key={framework}
                    onClick={() => toggleFramework(framework)}
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: formData.frameworks.includes(framework) ? '2px solid #3b82f6' : '2px solid #e2e8f0',
                      background: formData.frameworks.includes(framework) ? '#eff6ff' : 'white',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    data-testid={`framework-${framework.replace(/\s+/g, '-').toLowerCase()}`}
                  >
                    <div className="flex items-center justify-between">
                      <span style={{ fontWeight: '600', color: '#0f172a' }}>{framework}</span>
                      {formData.frameworks.includes(framework) && (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div data-testid="assessment-step-3">
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Scenario Selection</h3>
              <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>Optional: Run a what-if scenario analysis</p>
              
              <div className="space-y-2">
                {scenarios.map((scenario) => (
                  <div
                    key={scenario.id}
                    onClick={() => handleChange('scenario', scenario.id === 'none' ? '' : scenario.id)}
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: (formData.scenario === scenario.id || (!formData.scenario && scenario.id === 'none')) ? '2px solid #3b82f6' : '2px solid #e2e8f0',
                      background: (formData.scenario === scenario.id || (!formData.scenario && scenario.id === 'none')) ? '#eff6ff' : 'white',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    data-testid={`scenario-${scenario.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <span style={{ fontWeight: '500', color: '#0f172a' }}>{scenario.name}</span>
                      {(formData.scenario === scenario.id || (!formData.scenario && scenario.id === 'none')) && (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: '24px', padding: '16px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #86efac' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>Review Summary</h4>
                <div style={{ fontSize: '13px', color: '#15803d' }}>
                  <div className="mb-1"><strong>Assessment:</strong> {formData.name}</div>
                  <div className="mb-1"><strong>System:</strong> {formData.system_name}</div>
                  <div className="mb-1"><strong>Business Unit:</strong> {formData.business_unit}</div>
                  <div className="mb-1"><strong>Frameworks:</strong> {formData.frameworks.join(', ')}</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '24px', borderTop: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>
          <button
            className="btn btn-secondary"
            onClick={() => step === 1 ? onClose() : setStep(step - 1)}
            disabled={loading}
            data-testid="modal-back-button"
          >
            {step === 1 ? 'Cancel' : 'Back'}
          </button>
          
          {step < 3 ? (
            <button
              className="btn btn-primary"
              onClick={() => setStep(step + 1)}
              disabled={!canProceed()}
              data-testid="modal-next-button"
            >
              Next
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={loading || !canProceed()}
              data-testid="modal-submit-button"
            >
              {loading ? 'Creating Assessment...' : 'Create Assessment'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewAssessmentModal;
