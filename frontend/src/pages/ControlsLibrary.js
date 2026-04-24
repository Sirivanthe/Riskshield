import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/App';
import AuditTimeline from '@/components/AuditTimeline';

const ControlsLibrary = ({ user }) => {
  const [controls, setControls] = useState([]);
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [auditTarget, setAuditTarget] = useState(null);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectedControl, setSelectedControl] = useState(null);
  const [testingControl, setTestingControl] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [testBusy, setTestBusy] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'TECHNICAL',
    frameworks: [],
    regulatory_references: '',
    implementation_guidance: '',
    testing_procedure: '',
    evidence_requirements: '',
    frequency: 'Annual',
    is_ai_control: false,
    ai_risk_category: null
  });

  const categories = [
    { value: 'TECHNICAL', label: 'Technical' },
    { value: 'ADMINISTRATIVE', label: 'Administrative' },
    { value: 'PHYSICAL', label: 'Physical' },
    { value: 'OPERATIONAL', label: 'Operational' },
    { value: 'AI_GOVERNANCE', label: 'AI Governance' },
    { value: 'AI_TECHNICAL', label: 'AI Technical' },
    { value: 'AI_OPERATIONAL', label: 'AI Operational' }
  ];

  const frameworks = ['NIST CSF', 'ISO 27001', 'SOC2', 'PCI-DSS', 'GDPR', 'Basel III', 'EU_AI_ACT', 'NIST_AI_RMF'];
  const frequencies = ['Continuous', 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annual'];
  const aiRiskCategories = ['MINIMAL', 'LIMITED', 'HIGH', 'UNACCEPTABLE'];

  useEffect(() => {
    loadControls();
  }, [activeTab]);

  const loadControls = async () => {
    setLoading(true);
    try {
      let url = '/controls/library';
      if (activeTab === 'ai') {
        url += '?is_ai_control=true';
      } else if (activeTab === 'pending') {
        url += '?status=PENDING_REVIEW';
      }
      const [listRes, qRes] = await Promise.all([
        api.get(url),
        api.get('/controls/library/quality').catch(() => ({ data: null })),
      ]);
      setControls(listRes.data);
      if (qRes.data) setQuality(qRes.data);
    } catch (error) {
      console.error('Failed to load controls:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateControl = async (e) => {
    e.preventDefault();
    try {
      await api.post('/controls/library', {
        ...formData,
        frameworks: formData.frameworks,
        regulatory_references: formData.regulatory_references.split(',').map(r => r.trim()).filter(r => r),
        evidence_requirements: formData.evidence_requirements.split(',').map(r => r.trim()).filter(r => r)
      });
      setShowCreateModal(false);
      setFormData({
        name: '',
        description: '',
        category: 'TECHNICAL',
        frameworks: [],
        regulatory_references: '',
        implementation_guidance: '',
        testing_procedure: '',
        evidence_requirements: '',
        frequency: 'Annual',
        is_ai_control: false,
        ai_risk_category: null
      });
      loadControls();
    } catch (error) {
      console.error('Failed to create control:', error);
      alert('Failed to create control');
    }
  };

  const handleApprove = async (controlId) => {
    try {
      await api.post(`/controls/library/${controlId}/approve`);
      loadControls();
    } catch (error) {
      console.error('Failed to approve control:', error);
    }
  };

  const handleTestControl = async (control) => {
    setTestingControl(control);
    setTestResult(null);
    setTestBusy(true);
    try {
      const res = await api.post(`/automated-tests/run/${control.id}`, null, {
        params: { test_type: 'CONFIGURATION_CHECK' }
      });
      setTestResult(res.data);
    } catch (error) {
      setTestResult({ error: error?.response?.data?.detail || 'Test failed' });
    } finally {
      setTestBusy(false);
      loadControls();
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const clearSelection = () => setSelectedIds(new Set());

  const canReview = user.role === 'LOD2_USER' || user.role === 'ADMIN';

  const bulkApprove = async () => {
    if (!selectedIds.size) return;
    setBulkBusy(true);
    try {
      await api.post('/controls/library/bulk/approve', { control_ids: [...selectedIds] });
      clearSelection();
      await loadControls();
    } catch (e) {
      alert(`Bulk approve failed: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setBulkBusy(false);
    }
  };

  const bulkReject = async () => {
    if (!selectedIds.size) return;
    const reason = window.prompt('Rejection reason (optional) — applied to all selected:') || '';
    setBulkBusy(true);
    try {
      await api.post('/controls/library/bulk/reject', { control_ids: [...selectedIds], reason });
      clearSelection();
      await loadControls();
    } catch (e) {
      alert(`Bulk reject failed: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setBulkBusy(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'DRAFT': '#94a3b8',
      'PENDING_REVIEW': '#f59e0b',
      'APPROVED': '#22c55e',
      'ACTIVE': '#3b82f6',
      'DEPRECATED': '#6b7280',
      'REJECTED': '#ef4444'
    };
    return colors[status] || '#94a3b8';
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

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="controls-library-page">
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="controls-library-title">Controls Library</h1>
          <p className="page-subtitle">Manage custom controls for risk mitigation and compliance</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
          data-testid="create-control-button"
        >
          + New Control
        </button>
      </div>

      <div className="page-content">
        {/* Quality metrics strip */}
        {quality && (
          <div
            className="mb-6"
            data-testid="library-quality-strip"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '12px',
            }}
          >
            {[
              { label: 'Total', value: quality.total, color: '#334155' },
              { label: 'Completeness', value: `${quality.completeness_score.toFixed(1)}%`, color: '#059669' },
              { label: 'Approved', value: quality.approved, color: '#0284c7' },
              { label: 'Pending Review', value: quality.pending_review, color: '#d97706' },
              { label: 'AI Controls', value: quality.ai_controls, color: '#7c3aed' },
              { label: 'Missing Test Proc.', value: quality.missing_testing_procedure, color: '#dc2626' },
              { label: 'Missing Evidence Reqs', value: quality.missing_evidence_requirements, color: '#dc2626' },
              { label: 'Missing Reg. Refs', value: quality.missing_regulatory_references, color: '#b45309' },
            ].map((m) => (
              <div
                key={m.label}
                data-testid={`quality-${m.label.toLowerCase().replace(/[^a-z]+/g, '-')}`}
                style={{
                  padding: '14px',
                  background: '#fff',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  borderLeft: `4px solid ${m.color}`,
                }}
              >
                <div style={{ fontSize: '11px', color: '#64748b', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                  {m.label}
                </div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>{m.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="tabs mb-6">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'all' ? 'active' : ''}`}
              onClick={() => setActiveTab('all')}
            >
              All Controls ({controls.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'ai' ? 'active' : ''}`}
              onClick={() => setActiveTab('ai')}
            >
              AI Controls
            </button>
            {(user.role === 'LOD2_USER' || user.role === 'ADMIN') && (
              <button
                className={`tab-button ${activeTab === 'pending' ? 'active' : ''}`}
                onClick={() => setActiveTab('pending')}
              >
                Pending Review
              </button>
            )}
          </div>
        </div>

        {/* Bulk action bar (visible only to LOD2/Admin when items selected) */}
        {canReview && selectedIds.size > 0 && (
          <div
            data-testid="bulk-action-bar"
            style={{
              position: 'sticky',
              top: '0',
              zIndex: 20,
              marginBottom: '12px',
              background: '#0f172a',
              border: '1px solid #1e293b',
              borderRadius: '10px',
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ color: '#e2e8f0', fontSize: '13px', fontWeight: 600 }}>
              {selectedIds.size} selected
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={bulkApprove}
                disabled={bulkBusy}
                data-testid="bulk-approve-btn"
                style={{ padding: '6px 12px', borderRadius: '6px', background: '#10b981', color: 'white', border: 'none', fontWeight: 600, cursor: 'pointer' }}
              >
                {bulkBusy ? 'Applying…' : 'Approve Selected'}
              </button>
              <button
                onClick={bulkReject}
                disabled={bulkBusy}
                data-testid="bulk-reject-btn"
                style={{ padding: '6px 12px', borderRadius: '6px', background: '#ef4444', color: 'white', border: 'none', fontWeight: 600, cursor: 'pointer' }}
              >
                Reject Selected
              </button>
              <button
                onClick={clearSelection}
                data-testid="bulk-clear-btn"
                style={{ padding: '6px 12px', borderRadius: '6px', background: '#334155', color: '#e2e8f0', border: 'none', cursor: 'pointer' }}
              >
                Clear
              </button>
            </div>
          </div>
        )}

        {/* Controls Grid */}
        {controls.length > 0 ? (
          <div className="grid grid-2 gap-4">
            {controls.map((control) => (
              <div
                key={control.id}
                className="card"
                style={{ padding: '20px', position: 'relative', border: selectedIds.has(control.id) ? '2px solid #6366f1' : undefined }}
                data-testid={`control-card-${control.id}`}
              >
                {canReview && (
                  <input
                    type="checkbox"
                    checked={selectedIds.has(control.id)}
                    onChange={() => toggleSelect(control.id)}
                    data-testid={`control-select-${control.id}`}
                    title="Select for bulk action"
                    style={{ position: 'absolute', top: '12px', right: '12px', width: '16px', height: '16px', cursor: 'pointer' }}
                  />
                )}
                <div className="flex justify-between items-start mb-3" style={{ paddingRight: canReview ? '28px' : 0 }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                      {control.name}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>{control.control_id}</span>
                  </div>
                  <div className="flex gap-2">
                    {control.is_ai_control && (
                      <span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }}>AI</span>
                    )}
                    <span 
                      className="badge" 
                      style={{ 
                        background: `${getStatusColor(control.status)}20`,
                        color: getStatusColor(control.status)
                      }}
                    >
                      {control.status}
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px', lineHeight: '1.5' }}>
                  {control.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="badge" style={{ background: '#f1f5f9', color: '#475569' }}>
                    {control.category}
                  </span>
                  <span className="badge" style={{ background: '#fef3c7', color: '#92400e' }}>
                    {control.frequency}
                  </span>
                  <span 
                    className="badge"
                    style={{
                      background: `${getEffectivenessColor(control.effectiveness)}20`,
                      color: getEffectivenessColor(control.effectiveness)
                    }}
                  >
                    {control.effectiveness}
                  </span>
                </div>

                {control.frameworks && control.frameworks.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {control.frameworks.map((fw, idx) => (
                      <span key={idx} style={{ fontSize: '11px', padding: '2px 8px', background: '#eff6ff', color: '#1e40af', borderRadius: '4px' }}>
                        {fw}
                      </span>
                    ))}
                  </div>
                )}

                {control.regulatory_references && control.regulatory_references.length > 0 && (
                  <div
                    className="flex flex-wrap gap-1 mb-2"
                    data-testid={`control-reg-refs-${control.id}`}
                  >
                    {control.regulatory_references.map((ref, idx) => (
                      <span
                        key={idx}
                        title="Regulatory reference"
                        style={{ fontSize: '11px', padding: '2px 8px', background: '#ecfdf5', color: '#065f46', borderRadius: '4px', border: '1px solid #a7f3d0' }}
                      >
                        § {ref}
                      </span>
                    ))}
                  </div>
                )}

                {(control.source === 'REGULATORY_GAP' || (control.frameworks || []).some(f => f && control.source_file === f)) && (
                  <div
                    className="mb-3 flex items-center gap-2"
                    data-testid={`control-source-${control.id}`}
                  >
                    <span style={{ fontSize: '11px', padding: '2px 8px', background: '#fef2f2', color: '#991b1b', borderRadius: '4px', border: '1px solid #fecaca' }}>
                      From regulatory gap{control.source_file ? ` · ${control.source_file}` : ''}
                    </span>
                    {control.source_file && (
                      <Link
                        to={`/regulatory-analysis?framework=${encodeURIComponent(control.source_file)}`}
                        data-testid={`control-source-link-${control.id}`}
                        style={{ fontSize: '11px', color: '#2563eb', textDecoration: 'underline' }}
                      >
                        View source regulation →
                      </Link>
                    )}
                  </div>
                )}

                {control.ai_risk_category && (
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '12px' }}>
                    AI Risk Category: <strong style={{ color: control.ai_risk_category === 'HIGH' ? '#dc2626' : '#0f172a' }}>{control.ai_risk_category}</strong>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-3 pt-3" style={{ borderTop: '1px solid #e2e8f0' }}>
                  {control.status === 'PENDING_REVIEW' && (user.role === 'LOD2_USER' || user.role === 'ADMIN') && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleApprove(control.id)}
                    >
                      Approve
                    </button>
                  )}
                  <button className="btn btn-outline btn-sm" onClick={() => setSelectedControl(control)}>View Details</button>
                  <button className="btn btn-outline btn-sm" onClick={() => handleTestControl(control)}>Test Control</button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card">
            <div className="empty-state">
              <h3 className="empty-title">No Controls Found</h3>
              <p className="empty-description">Create custom controls to address policy gaps and compliance requirements</p>
              <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                Create First Control
              </button>
            </div>
          </div>
        )}
      </div>

      {/* View Details Modal */}
      {selectedControl && (
        <div className="modal-overlay" onClick={() => setSelectedControl(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <div>
                <h2 className="modal-title">{selectedControl.name}</h2>
                <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#64748b' }}>{selectedControl.control_id}</span>
              </div>
              <button className="modal-close" onClick={() => setSelectedControl(null)}>&times;</button>
            </div>
            <div className="modal-body">
              {/* Status Row */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <span className="badge" style={{ background: `${getStatusColor(selectedControl.status)}20`, color: getStatusColor(selectedControl.status) }}>{selectedControl.status}</span>
                <span className="badge" style={{ background: '#f1f5f9', color: '#475569' }}>{selectedControl.category}</span>
                <span className="badge" style={{ background: '#fef3c7', color: '#92400e' }}>{selectedControl.frequency}</span>
                <span className="badge" style={{ background: `${getEffectivenessColor(selectedControl.effectiveness)}20`, color: getEffectivenessColor(selectedControl.effectiveness) }}>{selectedControl.effectiveness}</span>
                {selectedControl.is_ai_control && <span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }}>AI</span>}
              </div>

              {/* Description */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Description</h4>
                <p style={{ fontSize: '14px', color: '#0f172a', lineHeight: '1.6' }}>{selectedControl.description}</p>
              </div>

              {/* Frameworks */}
              {selectedControl.frameworks?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Applicable Frameworks</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedControl.frameworks.map((fw, i) => (
                      <span key={i} style={{ fontSize: '12px', padding: '3px 10px', background: '#eff6ff', color: '#1e40af', borderRadius: '6px' }}>{fw}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Regulatory References */}
              {selectedControl.regulatory_references?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Regulatory References</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedControl.regulatory_references.map((ref, i) => (
                      <span key={i} style={{ fontSize: '12px', padding: '3px 10px', background: '#ecfdf5', color: '#065f46', borderRadius: '6px', border: '1px solid #a7f3d0' }}>§ {ref}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Implementation Guidance */}
              {selectedControl.implementation_guidance && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Implementation Guidance</h4>
                  <p style={{ fontSize: '13px', color: '#475569', lineHeight: '1.6', background: '#f8fafc', padding: '12px', borderRadius: '8px' }}>{selectedControl.implementation_guidance}</p>
                </div>
              )}

              {/* Testing Procedure */}
              {selectedControl.testing_procedure && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Testing Procedure</h4>
                  <p style={{ fontSize: '13px', color: '#475569', lineHeight: '1.6', background: '#f8fafc', padding: '12px', borderRadius: '8px' }}>{selectedControl.testing_procedure}</p>
                </div>
              )}

              {/* Evidence Requirements */}
              {selectedControl.evidence_requirements?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Evidence Requirements</h4>
                  <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {selectedControl.evidence_requirements.map((req, i) => (
                      <li key={i} style={{ fontSize: '13px', color: '#475569' }}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* AI Info */}
              {selectedControl.is_ai_control && selectedControl.ai_risk_category && (
                <div style={{ padding: '12px', background: '#eff6ff', borderRadius: '8px', marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#1e40af', marginBottom: '4px' }}>EU AI Act Risk Category</h4>
                  <span style={{ fontSize: '14px', fontWeight: '700', color: selectedControl.ai_risk_category === 'HIGH' ? '#dc2626' : '#0f172a' }}>{selectedControl.ai_risk_category}</span>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setSelectedControl(null)}>Close</button>
              <button className="btn btn-primary" onClick={() => { setSelectedControl(null); handleTestControl(selectedControl); }}>Test Control</button>
            </div>
          </div>
        </div>
      )}

      {/* Test Control Modal */}
      {testingControl && (
        <div className="modal-overlay" onClick={() => !testBusy && setTestingControl(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '550px' }}>
            <div className="modal-header">
              <h2 className="modal-title">Test Control</h2>
              <button className="modal-close" onClick={() => !testBusy && setTestingControl(null)}>&times;</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '14px', color: '#475569', marginBottom: '16px' }}>
                Running automated test for: <strong>{testingControl.name}</strong>
              </p>

              {testBusy && (
                <div style={{ textAlign: 'center', padding: '32px' }}>
                  <div className="loading-spinner" style={{ margin: '0 auto 12px' }}></div>
                  <p style={{ fontSize: '13px', color: '#64748b' }}>Running control test...</p>
                </div>
              )}

              {testResult && !testResult.error && (() => {
                const rating = testResult.effectiveness_rating;
                const confidence = testResult.confidence_score;
                const resultLabel = rating === 'EFFECTIVE' ? 'PASS' : rating === 'PARTIALLY_EFFECTIVE' ? 'PARTIAL' : 'FAIL';
                const resultColor = rating === 'EFFECTIVE' ? '#16a34a' : rating === 'PARTIALLY_EFFECTIVE' ? '#d97706' : '#dc2626';
                const resultBg = rating === 'EFFECTIVE' ? '#f0fdf4' : rating === 'PARTIALLY_EFFECTIVE' ? '#fefce8' : '#fef2f2';

                // Normalize findings — backend may send string or array
                const rawFindings = testResult.findings;
                const findingsList = Array.isArray(rawFindings)
                  ? rawFindings.filter(Boolean)
                  : typeof rawFindings === 'string' && rawFindings.trim()
                    ? rawFindings.split('\n').map(l => l.replace(/^[-•*]\s*/, '').trim()).filter(Boolean)
                    : [];

                // Normalize recommendations
                const rawRecs = testResult.recommendations;
                const recsList = Array.isArray(rawRecs)
                  ? rawRecs.filter(Boolean)
                  : typeof rawRecs === 'string' && rawRecs.trim()
                    ? rawRecs.split('\n').map(l => l.replace(/^[-•*]\s*/, '').trim()).filter(Boolean)
                    : [];

                return (
                  <div>
                    {/* Summary row */}
                    <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                      <div style={{ flex: 1, padding: '14px', background: resultBg, borderRadius: '8px', textAlign: 'center', border: `1px solid ${resultColor}40` }}>
                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Result</div>
                        <div style={{ fontWeight: '800', fontSize: '16px', color: resultColor }}>{resultLabel}</div>
                      </div>
                      <div style={{ flex: 1, padding: '14px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidence</div>
                        <div style={{ fontWeight: '700', fontSize: '16px', color: '#0f172a' }}>{confidence != null ? `${(confidence * 100).toFixed(0)}%` : '-'}</div>
                        <div style={{ fontSize: '10px', color: '#94a3b8' }}>certainty in judgment</div>
                      </div>
                      <div style={{ flex: 1, padding: '14px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Effectiveness</div>
                        <div style={{ fontWeight: '700', fontSize: '11px', color: getEffectivenessColor(rating) }}>
                          {rating?.replace(/_/g, ' ') || '-'}
                        </div>
                      </div>
                    </div>

                    {/* Findings */}
                    {findingsList.length > 0 && (
                      <div style={{ marginBottom: '16px' }}>
                        <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Findings ({findingsList.length})
                        </h4>
                        <ul style={{ margin: 0, paddingLeft: '0', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {findingsList.map((f, i) => (
                            <li key={i} style={{ fontSize: '13px', color: '#475569', background: '#fef9f0', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b', lineHeight: '1.5' }}>
                              {f}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recommendations */}
                    {recsList.length > 0 && (
                      <div style={{ marginBottom: '16px' }}>
                        <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Recommendations ({recsList.length})
                        </h4>
                        <ul style={{ margin: 0, paddingLeft: '0', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {recsList.map((r, i) => (
                            <li key={i} style={{ fontSize: '13px', color: '#475569', background: '#f0fdf4', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #22c55e', lineHeight: '1.5' }}>
                              {r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Full Report */}
                    {testResult.report && (
                      <div>
                        <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Full Audit Report
                        </h4>
                        <div style={{ fontSize: '12px', color: '#475569', background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0', whiteSpace: 'pre-wrap', lineHeight: '1.7', maxHeight: '200px', overflowY: 'auto' }}>
                          {testResult.report}
                        </div>
                      </div>
                    )}

                    {/* Human review notice */}
                    {testResult.requires_human_review && (
                      <div style={{ marginTop: '16px', padding: '10px 14px', background: '#fef3c7', borderRadius: '8px', border: '1px solid #fcd34d', fontSize: '12px', color: '#92400e' }}>
                        ⚠️ This result requires human review before being finalized.
                      </div>
                    )}
                  </div>
                );
              })()}

              {testResult?.error && (
                <div style={{ padding: '14px', background: '#fef2f2', borderRadius: '8px', color: '#991b1b', fontSize: '13px' }}>
                  {testResult.error}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setTestingControl(null)} disabled={testBusy}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Create Control Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">Create Custom Control</h2>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreateControl}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Control Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Multi-Factor Authentication Policy"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description *</label>
                  <textarea
                    className="form-textarea"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe the control's purpose and scope"
                    required
                  />
                </div>

                <div className="grid grid-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Category *</label>
                    <select
                      className="form-select"
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    >
                      {categories.map(cat => (
                        <option key={cat.value} value={cat.value}>{cat.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Testing Frequency *</label>
                    <select
                      className="form-select"
                      value={formData.frequency}
                      onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                    >
                      {frequencies.map(freq => (
                        <option key={freq} value={freq}>{freq}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Applicable Frameworks</label>
                  <div className="flex flex-wrap gap-2">
                    {frameworks.map(fw => (
                      <label key={fw} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={formData.frameworks.includes(fw)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({ ...formData, frameworks: [...formData.frameworks, fw] });
                            } else {
                              setFormData({ ...formData, frameworks: formData.frameworks.filter(f => f !== fw) });
                            }
                          }}
                        />
                        {fw}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Regulatory References</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.regulatory_references}
                    onChange={(e) => setFormData({ ...formData, regulatory_references: e.target.value })}
                    placeholder="e.g., NIST PR.AC-1, ISO 27001 A.9.2.1 (comma separated)"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Implementation Guidance</label>
                  <textarea
                    className="form-textarea"
                    value={formData.implementation_guidance}
                    onChange={(e) => setFormData({ ...formData, implementation_guidance: e.target.value })}
                    placeholder="Provide guidance on how to implement this control"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Testing Procedure</label>
                  <textarea
                    className="form-textarea"
                    value={formData.testing_procedure}
                    onChange={(e) => setFormData({ ...formData, testing_procedure: e.target.value })}
                    placeholder="Describe how to test this control's effectiveness"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Evidence Requirements</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.evidence_requirements}
                    onChange={(e) => setFormData({ ...formData, evidence_requirements: e.target.value })}
                    placeholder="e.g., Configuration screenshots, Audit logs (comma separated)"
                  />
                </div>

                {/* AI Control Section */}
                <div style={{ padding: '16px', background: '#f0f9ff', borderRadius: '8px', marginTop: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.is_ai_control}
                      onChange={(e) => setFormData({ ...formData, is_ai_control: e.target.checked })}
                    />
                    <span style={{ fontWeight: '600', color: '#0369a1' }}>This is an AI-specific control</span>
                  </label>
                  
                  {formData.is_ai_control && (
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label">AI Risk Category (EU AI Act)</label>
                      <select
                        className="form-select"
                        value={formData.ai_risk_category || ''}
                        onChange={(e) => setFormData({ ...formData, ai_risk_category: e.target.value || null })}
                      >
                        <option value="">Select risk category</option>
                        {aiRiskCategories.map(cat => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Control
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ControlsLibrary;