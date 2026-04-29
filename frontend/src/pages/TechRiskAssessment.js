import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ratingColor = (r) => {
  switch (r) {
    case 'CRITICAL': return 'bg-red-700 text-white';
    case 'HIGH': return 'bg-orange-600 text-white';
    case 'MEDIUM': return 'bg-yellow-600 text-white';
    case 'LOW': return 'bg-green-700 text-white';
    default: return 'bg-slate-600 text-white';
  }
};

const ratingBorder = (r) => {
  switch (r) {
    case 'CRITICAL': return 'border-red-700 bg-red-900/10';
    case 'HIGH': return 'border-orange-600 bg-orange-900/10';
    case 'MEDIUM': return 'border-yellow-600 bg-yellow-900/10';
    case 'LOW': return 'border-green-700 bg-green-900/10';
    default: return 'border-slate-600';
  }
};

const statusColor = (s) => {
  switch (s) {
    case 'COMPLETED': return 'bg-green-700';
    case 'PENDING_REVIEW': return 'bg-yellow-700';
    case 'DRAFT': return 'bg-slate-600';
    default: return 'bg-slate-600';
  }
};

const QuestionInput = ({ question, value, onChange }) => {
  if (question.type === 'select') {
    return (
      <Select value={value || ''} onValueChange={onChange}>
        <SelectTrigger className="bg-slate-700 border-slate-600">
          <SelectValue placeholder="Select an option" />
        </SelectTrigger>
        <SelectContent>
          {question.options.map(opt => (
            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  }
  if (question.type === 'multiselect') {
    return (
      <div className="flex flex-wrap gap-2">
        {question.options.map(opt => (
          <label key={opt} className="flex items-center gap-2 bg-slate-700 px-3 py-1 rounded cursor-pointer hover:bg-slate-600">
            <input type="checkbox" checked={(value || []).includes(opt)}
              onChange={(e) => {
                const current = value || [];
                onChange(e.target.checked ? [...current, opt] : current.filter(v => v !== opt));
              }} />
            <span className="text-sm text-slate-200">{opt}</span>
          </label>
        ))}
      </div>
    );
  }
  return (
    <Input type={question.type === 'date' ? 'date' : 'text'} value={value || ''}
      onChange={(e) => onChange(e.target.value)} className="bg-slate-700 border-slate-600" />
  );
};

const TechRiskAssessment = ({ user }) => {
  const [assessments, setAssessments] = useState([]);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [detailView, setDetailView] = useState(null); // full assessment detail
  const [questions, setQuestions] = useState(null);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [toast, setToast] = useState(null);
  const [detailTab, setDetailTab] = useState('risks'); // 'risks' | 'controls' | 'summary'
  const [newAssessment, setNewAssessment] = useState({
    app_name: '',
    description: '',
    business_unit: '',
    context: {
      data_classification: 'INTERNAL',
      deployment_type: 'CLOUD',
      internet_facing: false,
      processes_pii: false,
      processes_financial_data: false,
      criticality: 'MEDIUM'
    }
  });

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => { fetchAssessments(); }, []);

  const fetchAssessments = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/tech-risk/assessments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setAssessments(data.assessments || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createAssessment = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `${API_URL}/api/tech-risk/assessments?assessor_id=${user?.id || 'user'}&assessor_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(newAssessment),
        }
      );
      const data = await res.json();
      setAssessments([data, ...assessments]);
      setShowCreateForm(false);
      setSelectedAssessment(data);
      fetchQuestions(data.id);
    } catch (err) {
      showToast('Failed to create assessment', 'error');
    }
  };

  const fetchQuestions = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/tech-risk/assessments/${assessmentId}/questions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuestions(await res.json());
    } catch (err) {
      showToast('Failed to load questions', 'error');
    }
  };

  const submitQuestionnaire = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/tech-risk/assessments/${selectedAssessment.id}/questionnaire`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });
      const result = await res.json();
      showToast(`Assessment complete — ${result.risks_identified} risks · ${result.controls_recommended} controls · ${result.overall_risk_rating}`, 'success');
      await fetchAssessments();
      setSelectedAssessment(null);
      setQuestions(null);
      setResponses({});
    } catch (err) {
      showToast('Submission failed', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const openDetail = (assessment) => {
    setDetailView(assessment);
    setDetailTab('risks');
  };

  const downloadReport = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/tech-risk/assessments/${assessmentId}/report`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `risk_assessment_${assessmentId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      showToast('PDF download failed', 'error');
    }
  };

  const createIssues = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `${API_URL}/api/tech-risk/assessments/${assessmentId}/create-issues?creator_id=${user?.id || 'user'}&creator_name=${encodeURIComponent(user?.full_name || 'User')}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({}) }
      );
      const result = await res.json();
      showToast(`${result.issues_created} issues created in Issue Management`, 'success');
    } catch (err) {
      showToast('Failed to create issues', 'error');
    }
  };

  if (loading) return <div className="p-6 bg-slate-900 min-h-screen text-white">Loading...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="tech-risk-assessment-page">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Tech Risk Assessment</h1>
            <p className="text-slate-400">Application and technology risk assessments with intelligent questionnaire</p>
          </div>
          <Button onClick={() => setShowCreateForm(true)}>New Assessment</Button>
        </div>

        {/* Create Form */}
        {showCreateForm && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader><CardTitle className="text-white">New Tech Risk Assessment</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">Application Name *</label>
                  <Input value={newAssessment.app_name}
                    onChange={(e) => setNewAssessment({...newAssessment, app_name: e.target.value})}
                    className="bg-slate-700 border-slate-600" placeholder="e.g., Payment Gateway" />
                </div>
                <div>
                  <label className="text-sm text-slate-400">Business Unit</label>
                  <Input value={newAssessment.business_unit}
                    onChange={(e) => setNewAssessment({...newAssessment, business_unit: e.target.value})}
                    className="bg-slate-700 border-slate-600" />
                </div>
              </div>
              <div>
                <label className="text-sm text-slate-400">Description</label>
                <Input value={newAssessment.description}
                  onChange={(e) => setNewAssessment({...newAssessment, description: e.target.value})}
                  className="bg-slate-700 border-slate-600" />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-slate-400">Data Classification</label>
                  <Select value={newAssessment.context.data_classification}
                    onValueChange={(v) => setNewAssessment({...newAssessment, context: {...newAssessment.context, data_classification: v}})}>
                    <SelectTrigger className="bg-slate-700 border-slate-600"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PUBLIC">Public</SelectItem>
                      <SelectItem value="INTERNAL">Internal</SelectItem>
                      <SelectItem value="CONFIDENTIAL">Confidential</SelectItem>
                      <SelectItem value="RESTRICTED">Restricted</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Deployment Type</label>
                  <Select value={newAssessment.context.deployment_type}
                    onValueChange={(v) => setNewAssessment({...newAssessment, context: {...newAssessment.context, deployment_type: v}})}>
                    <SelectTrigger className="bg-slate-700 border-slate-600"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ON_PREM">On-Premise</SelectItem>
                      <SelectItem value="CLOUD">Cloud</SelectItem>
                      <SelectItem value="HYBRID">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Criticality</label>
                  <Select value={newAssessment.context.criticality}
                    onValueChange={(v) => setNewAssessment({...newAssessment, context: {...newAssessment.context, criticality: v}})}>
                    <SelectTrigger className="bg-slate-700 border-slate-600"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CRITICAL">Critical</SelectItem>
                      <SelectItem value="HIGH">High</SelectItem>
                      <SelectItem value="MEDIUM">Medium</SelectItem>
                      <SelectItem value="LOW">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex gap-4">
                {[
                  { key: 'internet_facing', label: 'Internet Facing' },
                  { key: 'processes_pii', label: 'Processes PII' },
                  { key: 'processes_financial_data', label: 'Processes Financial Data' },
                ].map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={newAssessment.context[key]}
                      onChange={(e) => setNewAssessment({...newAssessment, context: {...newAssessment.context, [key]: e.target.checked}})} />
                    <span className="text-slate-300">{label}</span>
                  </label>
                ))}
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>Cancel</Button>
                <Button onClick={createAssessment} disabled={!newAssessment.app_name}>Create & Start Assessment</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Questionnaire */}
        {questions && selectedAssessment && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Assessment Questionnaire — {selectedAssessment.app_name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {Object.entries(questions.sections).map(([section, sectionQuestions]) => (
                <div key={section} className="space-y-4">
                  <h3 className="text-lg font-semibold text-blue-400 border-b border-slate-700 pb-2">{section}</h3>
                  {sectionQuestions.map((q) => (
                    <div key={q.id} className="space-y-2">
                      <label className="text-slate-300 text-sm">
                        {q.question} {q.required && <span className="text-red-400">*</span>}
                      </label>
                      <QuestionInput question={q} value={responses[q.id]}
                        onChange={(val) => setResponses({...responses, [q.id]: val})} />
                    </div>
                  ))}
                </div>
              ))}
              <div className="flex gap-2 justify-end pt-4 border-t border-slate-700">
                <Button variant="outline" onClick={() => { setSelectedAssessment(null); setQuestions(null); }}>Cancel</Button>
                <Button onClick={submitQuestionnaire} disabled={submitting}>
                  {submitting ? '⏳ Analyzing risks...' : '🔍 Submit & Analyze Risks'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Assessment List */}
        {!questions && !detailView && (
          <div className="space-y-4">
            {assessments.length === 0 ? (
              <div className="text-center py-12 text-slate-500">No assessments yet. Click "New Assessment" to get started.</div>
            ) : assessments.map((a) => (
              <Card key={a.id} className="bg-slate-800/50 border-slate-700 hover:border-slate-500 transition-colors cursor-pointer"
                onClick={() => openDetail(a)}>
                <CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h3 className="text-lg font-semibold text-white">{a.app_name}</h3>
                        <span className="text-xs bg-slate-700 px-2 py-0.5 rounded font-mono">{a.assessment_id}</span>
                        {a.overall_risk_rating && (
                          <span className={`text-xs px-2 py-0.5 rounded ${ratingColor(a.overall_risk_rating)}`}>
                            {a.overall_risk_rating}
                          </span>
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded text-white ${statusColor(a.status)}`}>
                          {a.status?.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400">{a.context?.description || a.description || 'No description'}</p>
                      <div className="flex gap-4 text-xs text-slate-500 flex-wrap">
                        <span>Risks: <span className="text-white">{a.identified_risks?.length || 0}</span></span>
                        <span>Controls: <span className="text-white">{a.recommended_controls?.length || 0}</span></span>
                        <span>Created: {new Date(a.created_at).toLocaleDateString()}</span>
                        {a.business_unit && <span>BU: {a.business_unit}</span>}
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
                      {a.status === 'DRAFT' && (
                        <Button size="sm" onClick={() => { setSelectedAssessment(a); fetchQuestions(a.id); }}>
                          Continue
                        </Button>
                      )}
                      {(a.status === 'PENDING_REVIEW' || a.status === 'COMPLETED') && (
                        <>
                          <Button size="sm" variant="outline" onClick={() => openDetail(a)}>View Detail</Button>
                          <Button size="sm" variant="outline" onClick={() => downloadReport(a.id)}>PDF</Button>
                          <Button size="sm" onClick={() => createIssues(a.id)}>Create Issues</Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Risk preview chips */}
                  {a.identified_risks?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-700 flex flex-wrap gap-2">
                      {a.identified_risks.slice(0, 4).map((risk, idx) => (
                        <span key={idx} className={`text-xs px-2 py-0.5 rounded ${ratingColor(risk.inherent_rating)}`}>
                          {(risk.title || '').substring(0, 35)}{risk.title?.length > 35 ? '...' : ''}
                        </span>
                      ))}
                      {a.identified_risks.length > 4 && (
                        <span className="text-xs text-slate-500">+{a.identified_risks.length - 4} more</span>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* ====== DETAIL VIEW ====== */}
        {detailView && !questions && (
          <div className="space-y-4">
            {/* Detail Header */}
            <div className="flex items-start justify-between">
              <div>
                <button onClick={() => setDetailView(null)} className="text-xs text-slate-400 hover:text-white mb-2 flex items-center gap-1">
                  ← Back to assessments
                </button>
                <h2 className="text-xl font-bold text-white">{detailView.app_name}</h2>
                <div className="flex items-center gap-3 mt-1 flex-wrap">
                  <span className="text-xs bg-slate-700 px-2 py-0.5 rounded font-mono">{detailView.assessment_id}</span>
                  {detailView.overall_risk_rating && (
                    <span className={`text-sm px-3 py-1 rounded font-bold ${ratingColor(detailView.overall_risk_rating)}`}>
                      {detailView.overall_risk_rating} RISK
                    </span>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded text-white ${statusColor(detailView.status)}`}>
                    {detailView.status?.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => downloadReport(detailView.id)}>📄 Download PDF</Button>
                <Button size="sm" onClick={() => createIssues(detailView.id)}>🚨 Create Issues</Button>
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Overall Rating', value: detailView.overall_risk_rating || '—', color: ratingColor(detailView.overall_risk_rating) },
                { label: 'Risks Identified', value: detailView.identified_risks?.length || 0, color: 'bg-slate-700' },
                { label: 'Controls Recommended', value: detailView.recommended_controls?.length || 0, color: 'bg-slate-700' },
                { label: 'Criticality', value: detailView.context?.criticality || '—', color: 'bg-slate-700' },
              ].map((m) => (
                <Card key={m.label} className="bg-slate-800/50 border-slate-700">
                  <CardContent className="p-3">
                    <div className="text-xs text-slate-400">{m.label}</div>
                    <div className={`text-xl font-bold mt-1 px-2 py-0.5 rounded inline-block ${m.color}`}>{m.value}</div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Context */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 uppercase mb-2">Application Context</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div><span className="text-slate-400">Business Unit: </span><span className="text-white">{detailView.business_unit || '—'}</span></div>
                  <div><span className="text-slate-400">Deployment: </span><span className="text-white">{detailView.context?.deployment_type || '—'}</span></div>
                  <div><span className="text-slate-400">Data Class: </span><span className="text-white">{detailView.context?.data_classification || '—'}</span></div>
                  <div className="flex gap-2 flex-wrap">
                    {detailView.context?.internet_facing && <span className="text-xs bg-orange-800 text-orange-200 px-2 py-0.5 rounded">Internet Facing</span>}
                    {detailView.context?.processes_pii && <span className="text-xs bg-blue-800 text-blue-200 px-2 py-0.5 rounded">PII</span>}
                    {detailView.context?.processes_financial_data && <span className="text-xs bg-purple-800 text-purple-200 px-2 py-0.5 rounded">Financial Data</span>}
                  </div>
                </div>
                {(detailView.context?.description || detailView.description) && (
                  <p className="text-slate-300 text-sm mt-2">{detailView.context?.description || detailView.description}</p>
                )}
              </CardContent>
            </Card>

            {/* Detail Tabs */}
            <div className="flex gap-2 border-b border-slate-700">
              {[
                { id: 'risks', label: `🔴 Risks (${detailView.identified_risks?.length || 0})` },
                { id: 'controls', label: `🛡️ Controls (${detailView.recommended_controls?.length || 0})` },
                { id: 'summary', label: '📋 Summary' },
              ].map((t) => (
                <button key={t.id} onClick={() => setDetailTab(t.id)}
                  className={`px-4 py-2 text-sm ${detailTab === t.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400 hover:text-slate-200'}`}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Risks Tab */}
            {detailTab === 'risks' && (
              <div className="space-y-4">
                {!detailView.identified_risks?.length ? (
                  <p className="text-slate-400">No risks identified.</p>
                ) : detailView.identified_risks.map((risk, idx) => (
                  <Card key={idx} className={`border ${ratingBorder(risk.inherent_rating)}`}>
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className={`text-xs px-2 py-0.5 rounded font-bold ${ratingColor(risk.inherent_rating)}`}>
                              {risk.inherent_rating}
                            </span>
                            {risk.category && (
                              <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">{risk.category}</span>
                            )}
                            {risk.likelihood && (
                              <span className="text-xs text-slate-400">Likelihood: <span className="text-white">{risk.likelihood}</span></span>
                            )}
                            {risk.impact && (
                              <span className="text-xs text-slate-400">Impact: <span className="text-white">{risk.impact}</span></span>
                            )}
                          </div>
                          <h4 className="text-white font-medium">{risk.title}</h4>
                        </div>
                      </div>

                      {risk.description && (
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Description</div>
                          <p className="text-slate-200 text-sm">{risk.description}</p>
                        </div>
                      )}

                      {risk.regulatory_reference && (
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Regulatory Reference</div>
                          <p className="text-slate-300 text-sm">{risk.regulatory_reference}</p>
                        </div>
                      )}

                      {risk.mitigation && (
                        <div className="p-3 bg-green-900/20 border border-green-800 rounded">
                          <div className="text-xs text-green-400 uppercase mb-1">Recommended Mitigation</div>
                          <p className="text-slate-200 text-sm">{risk.mitigation}</p>
                        </div>
                      )}

                      {risk.mapped_controls?.length > 0 && (
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Mapped Controls</div>
                          <div className="flex flex-wrap gap-1">
                            {risk.mapped_controls.map((c, i) => (
                              <span key={i} className="text-xs px-2 py-0.5 rounded bg-blue-900 text-blue-200">{c}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Controls Tab */}
            {detailTab === 'controls' && (
              <div className="space-y-3">
                {!detailView.recommended_controls?.length ? (
                  <p className="text-slate-400">No controls recommended.</p>
                ) : detailView.recommended_controls.map((ctrl, idx) => (
                  <Card key={idx} className="bg-slate-800/50 border-slate-700">
                    <CardContent className="p-4 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            {ctrl.priority && (
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                ctrl.priority === 'HIGH' ? 'bg-red-700 text-white' :
                                ctrl.priority === 'MEDIUM' ? 'bg-yellow-700 text-white' : 'bg-slate-600 text-white'
                              }`}>{ctrl.priority}</span>
                            )}
                            {ctrl.control_type && (
                              <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">{ctrl.control_type}</span>
                            )}
                            {ctrl.framework && (
                              <span className="text-xs text-slate-400">{ctrl.framework}</span>
                            )}
                          </div>
                          <h4 className="text-white font-medium">{ctrl.title || ctrl.name}</h4>
                        </div>
                      </div>
                      {ctrl.description && <p className="text-slate-300 text-sm">{ctrl.description}</p>}
                      {ctrl.implementation_steps?.length > 0 && (
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Implementation Steps</div>
                          <ol className="list-decimal list-inside text-slate-300 text-sm space-y-0.5">
                            {ctrl.implementation_steps.map((s, i) => <li key={i}>{s}</li>)}
                          </ol>
                        </div>
                      )}
                      {ctrl.addresses_risk && (
                        <div className="text-xs text-slate-400">Addresses: <span className="text-slate-300">{ctrl.addresses_risk}</span></div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Summary Tab */}
            {detailTab === 'summary' && (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-5 space-y-4">
                  <div>
                    <div className="text-xs text-slate-400 uppercase mb-2">Executive Summary</div>
                    <p className="text-slate-200">
                      The technology risk assessment for <strong className="text-white">{detailView.app_name}</strong> identified{' '}
                      <strong className="text-white">{detailView.identified_risks?.length || 0} risks</strong> with an overall rating of{' '}
                      <strong className={`px-2 py-0.5 rounded text-sm ${ratingColor(detailView.overall_risk_rating)}`}>
                        {detailView.overall_risk_rating}
                      </strong>.
                      {' '}{detailView.recommended_controls?.length || 0} controls have been recommended to mitigate the identified risks.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-slate-400 uppercase mb-2">Risk Breakdown</div>
                      {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(level => {
                        const count = (detailView.identified_risks || []).filter(r => r.inherent_rating === level).length;
                        if (!count) return null;
                        return (
                          <div key={level} className="flex items-center gap-2 mb-1">
                            <span className={`text-xs px-2 py-0.5 rounded w-20 text-center ${ratingColor(level)}`}>{level}</span>
                            <div className="flex-1 bg-slate-700 rounded-full h-2">
                              <div className={`h-2 rounded-full ${level === 'CRITICAL' ? 'bg-red-600' : level === 'HIGH' ? 'bg-orange-500' : level === 'MEDIUM' ? 'bg-yellow-500' : 'bg-green-500'}`}
                                style={{width: `${(count / (detailView.identified_risks?.length || 1)) * 100}%`}} />
                            </div>
                            <span className="text-xs text-white w-4">{count}</span>
                          </div>
                        );
                      })}
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 uppercase mb-2">Assessment Details</div>
                      <div className="space-y-1 text-sm">
                        <div><span className="text-slate-400">Assessor: </span><span className="text-white">{detailView.assessor_name || '—'}</span></div>
                        <div><span className="text-slate-400">Created: </span><span className="text-white">{new Date(detailView.created_at).toLocaleDateString()}</span></div>
                        <div><span className="text-slate-400">Status: </span><span className="text-white">{detailView.status?.replace(/_/g, ' ')}</span></div>
                        {detailView.completed_at && (
                          <div><span className="text-slate-400">Completed: </span><span className="text-white">{new Date(detailView.completed_at).toLocaleDateString()}</span></div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-700">
                    <div className="text-xs text-slate-400 uppercase mb-2">Recommended Actions</div>
                    <ol className="list-decimal list-inside text-slate-300 text-sm space-y-1">
                      <li>Address all CRITICAL and HIGH risks within 30 days</li>
                      <li>Implement recommended controls in priority order</li>
                      <li>Create issues in Issue Management for tracking</li>
                      <li>Schedule follow-up assessment in 90 days</li>
                    </ol>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>

      {toast && (
        <div className={`fixed bottom-6 right-6 px-4 py-3 rounded shadow-lg text-white z-50 ${
          toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-slate-700'
        }`}>{toast.msg}</div>
      )}
    </div>
  );
};

export default TechRiskAssessment;