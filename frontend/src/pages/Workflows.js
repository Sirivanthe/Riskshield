import { useState, useEffect } from 'react';
import { api } from '@/App';

const Workflows = ({ user }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await api.get('/workflows');
      setWorkflows(response.data);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const canManageWorkflows = user.role === 'LOD2_USER' || user.role === 'ADMIN';

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="workflows-page">
      <div className="page-header">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="page-title" data-testid="workflows-title">Workflows</h1>
            <p className="page-subtitle">Automated risk response and GRC integration</p>
          </div>
          {canManageWorkflows && (
            <button
              className="btn btn-primary"
              onClick={() => setShowModal(true)}
              data-testid="new-workflow-button"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              New Workflow
            </button>
          )}
        </div>
      </div>

      <div className="page-content">
        {workflows.length > 0 ? (
          <div className="card">
            <table className="data-table" data-testid="workflows-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Trigger</th>
                  <th>Steps</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((workflow) => (
                  <tr key={workflow.id} data-testid={`workflow-row-${workflow.id}`}>
                    <td>
                      <div style={{ fontWeight: '600', color: '#0f172a' }}>{workflow.name}</div>
                    </td>
                    <td style={{ fontSize: '14px', color: '#64748b', maxWidth: '300px' }}>{workflow.description}</td>
                    <td>
                      <span className="badge" style={{ background: '#fef3c7', color: '#92400e' }}>
                        {workflow.trigger.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ fontSize: '14px' }}>{workflow.steps.length} steps</td>
                    <td>
                      <span className={`badge ${workflow.active ? 'effective' : 'ineffective'}`}>
                        {workflow.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b' }}>
                      {new Date(workflow.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card">
            <div className="empty-state">
              <div className="empty-icon">⚡</div>
              <h3 className="empty-title">No workflows configured</h3>
              <p className="empty-description">Create workflows to automate risk response and GRC integration</p>
              {canManageWorkflows && (
                <button className="btn btn-primary" onClick={() => setShowModal(true)} data-testid="create-first-workflow-button">
                  Create Workflow
                </button>
              )}
            </div>
          </div>
        )}

        {/* Workflow Info */}
        <div className="grid grid-3 gap-4 mt-6">
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '12px' }}>Available Triggers</h3>
            <ul style={{ fontSize: '14px', color: '#64748b', paddingLeft: '20px' }}>
              <li className="mb-2">ON_HIGH_RISK: Triggered when critical/high risks detected</li>
              <li className="mb-2">ON_FAILED_CONTROL: Triggered when controls are ineffective</li>
              <li className="mb-2">ON_TREND_WORSENING: Triggered when risk trends worsen</li>
              <li className="mb-2">MANUAL: Triggered manually by users</li>
            </ul>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '12px' }}>Workflow Actions</h3>
            <ul style={{ fontSize: '14px', color: '#64748b', paddingLeft: '20px' }}>
              <li className="mb-2">CREATE_GRC_TICKET: Create tickets in ServiceNow/Archer</li>
              <li className="mb-2">SEND_EMAIL: Send notification emails</li>
              <li className="mb-2">UPDATE_STATUS: Update assessment status</li>
            </ul>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '12px' }}>GRC Integrations</h3>
            <ul style={{ fontSize: '14px', color: '#64748b', paddingLeft: '20px' }}>
              <li className="mb-2">ServiceNow: Issue tracking</li>
              <li className="mb-2">Archer: Risk management</li>
              <li className="mb-2">MetricStream: GRC platform</li>
            </ul>
          </div>
        </div>
      </div>

      {showModal && (
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
            zIndex: 1000
          }}
          onClick={() => setShowModal(false)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '32px',
              maxWidth: '500px',
              width: '100%'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px' }}>New Workflow</h3>
            <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '24px' }}>
              Workflow creation is available through the API. Contact your administrator for workflow configuration.
            </p>
            <button className="btn btn-primary w-full" onClick={() => setShowModal(false)} style={{ justifyContent: 'center' }}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workflows;
