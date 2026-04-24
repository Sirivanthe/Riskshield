import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TechRiskAssessment = ({ user }) => {
  const [assessments, setAssessments] = useState([]);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [questions, setQuestions] = useState(null);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
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

  useEffect(() => {
    fetchAssessments();
  }, []);

  const fetchAssessments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/tech-risk/assessments`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setAssessments(data.assessments || []);
    } catch (err) {
      console.error('Error fetching assessments:', err);
    } finally {
      setLoading(false);
    }
  };

  const createAssessment = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/tech-risk/assessments?assessor_id=${user?.id || 'user'}&assessor_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(newAssessment)
        }
      );
      const data = await response.json();
      setAssessments([data, ...assessments]);
      setShowCreateForm(false);
      setSelectedAssessment(data);
      fetchQuestions(data.id);
    } catch (err) {
      console.error('Error creating assessment:', err);
    }
  };

  const fetchQuestions = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/tech-risk/assessments/${assessmentId}/questions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setQuestions(data);
    } catch (err) {
      console.error('Error fetching questions:', err);
    }
  };

  const submitQuestionnaire = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/tech-risk/assessments/${selectedAssessment.id}/questionnaire`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ responses })
      });
      const result = await response.json();
      alert(`Assessment Complete!\nRisks Identified: ${result.risks_identified}\nControls Recommended: ${result.controls_recommended}\nOverall Rating: ${result.overall_risk_rating}`);
      fetchAssessments();
      setSelectedAssessment(null);
      setQuestions(null);
    } catch (err) {
      console.error('Error submitting questionnaire:', err);
    }
  };

  const downloadReport = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/tech-risk/assessments/${assessmentId}/report`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `risk_assessment_${assessmentId}.pdf`;
      a.click();
    } catch (err) {
      console.error('Error downloading report:', err);
    }
  };

  const createIssues = async (assessmentId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/tech-risk/assessments/${assessmentId}/create-issues?creator_id=${user?.id || 'user'}&creator_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({})
        }
      );
      const result = await response.json();
      alert(`Created ${result.issues_created} issues from risks`);
    } catch (err) {
      console.error('Error creating issues:', err);
    }
  };

  const getRatingColor = (rating) => {
    const colors = {
      'CRITICAL': 'bg-red-600',
      'HIGH': 'bg-orange-500',
      'MEDIUM': 'bg-yellow-500',
      'LOW': 'bg-green-500'
    };
    return colors[rating] || 'bg-gray-500';
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
            <label key={opt} className="flex items-center gap-2 bg-slate-700 px-3 py-1 rounded cursor-pointer">
              <input
                type="checkbox"
                checked={(value || []).includes(opt)}
                onChange={(e) => {
                  const current = value || [];
                  if (e.target.checked) {
                    onChange([...current, opt]);
                  } else {
                    onChange(current.filter(v => v !== opt));
                  }
                }}
              />
              <span className="text-sm">{opt}</span>
            </label>
          ))}
        </div>
      );
    }
    return (
      <Input
        type={question.type === 'date' ? 'date' : 'text'}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="bg-slate-700 border-slate-600"
      />
    );
  };

  if (loading) {
    return <div className="p-6 bg-slate-900 min-h-screen text-white">Loading...</div>;
  }

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="tech-risk-assessment-page">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Tech Risk Assessment</h1>
            <p className="text-slate-400">Application and technology risk assessments with intelligent questionnaire</p>
          </div>
          <Button onClick={() => setShowCreateForm(true)} data-testid="new-assessment-btn">
            New Assessment
          </Button>
        </div>

        {/* Create Form */}
        {showCreateForm && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">New Tech Risk Assessment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">Application Name *</label>
                  <Input
                    value={newAssessment.app_name}
                    onChange={(e) => setNewAssessment({...newAssessment, app_name: e.target.value})}
                    className="bg-slate-700 border-slate-600"
                    placeholder="e.g., Payment Gateway"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-400">Business Unit</label>
                  <Input
                    value={newAssessment.business_unit}
                    onChange={(e) => setNewAssessment({...newAssessment, business_unit: e.target.value})}
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm text-slate-400">Description</label>
                <Input
                  value={newAssessment.description}
                  onChange={(e) => setNewAssessment({...newAssessment, description: e.target.value})}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-slate-400">Data Classification</label>
                  <Select 
                    value={newAssessment.context.data_classification}
                    onValueChange={(v) => setNewAssessment({...newAssessment, context: {...newAssessment.context, data_classification: v}})}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
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
                  <Select 
                    value={newAssessment.context.deployment_type}
                    onValueChange={(v) => setNewAssessment({...newAssessment, context: {...newAssessment.context, deployment_type: v}})}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ON_PREM">On-Premise</SelectItem>
                      <SelectItem value="CLOUD">Cloud</SelectItem>
                      <SelectItem value="HYBRID">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Criticality</label>
                  <Select 
                    value={newAssessment.context.criticality}
                    onValueChange={(v) => setNewAssessment({...newAssessment, context: {...newAssessment.context, criticality: v}})}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
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
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newAssessment.context.internet_facing}
                    onChange={(e) => setNewAssessment({...newAssessment, context: {...newAssessment.context, internet_facing: e.target.checked}})}
                  />
                  <span className="text-slate-300">Internet Facing</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newAssessment.context.processes_pii}
                    onChange={(e) => setNewAssessment({...newAssessment, context: {...newAssessment.context, processes_pii: e.target.checked}})}
                  />
                  <span className="text-slate-300">Processes PII</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newAssessment.context.processes_financial_data}
                    onChange={(e) => setNewAssessment({...newAssessment, context: {...newAssessment.context, processes_financial_data: e.target.checked}})}
                  />
                  <span className="text-slate-300">Processes Financial Data</span>
                </label>
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
              <CardTitle className="text-white">
                Assessment Questionnaire - {selectedAssessment.app_name}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {Object.entries(questions.sections).map(([section, sectionQuestions]) => (
                <div key={section} className="space-y-4">
                  <h3 className="text-lg font-semibold text-blue-400 border-b border-slate-700 pb-2">{section}</h3>
                  {sectionQuestions.map((q) => (
                    <div key={q.id} className="space-y-2">
                      <label className="text-slate-300">
                        {q.question} {q.required && <span className="text-red-400">*</span>}
                      </label>
                      <QuestionInput
                        question={q}
                        value={responses[q.id]}
                        onChange={(val) => setResponses({...responses, [q.id]: val})}
                      />
                    </div>
                  ))}
                </div>
              ))}
              <div className="flex gap-2 justify-end pt-4 border-t border-slate-700">
                <Button variant="outline" onClick={() => { setSelectedAssessment(null); setQuestions(null); }}>
                  Cancel
                </Button>
                <Button onClick={submitQuestionnaire}>
                  Submit & Analyze Risks
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Assessments List */}
        {!questions && (
          <div className="grid gap-4">
            {assessments.map((assessment) => (
              <Card key={assessment.id} className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-white">{assessment.app_name}</h3>
                        <span className="text-xs bg-slate-600 px-2 py-1 rounded">{assessment.assessment_id}</span>
                        {assessment.overall_risk_rating && (
                          <span className={`text-xs px-2 py-1 rounded text-white ${getRatingColor(assessment.overall_risk_rating)}`}>
                            {assessment.overall_risk_rating}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-400">{assessment.context?.description || 'No description'}</p>
                      <div className="flex gap-4 text-xs text-slate-500">
                        <span>Status: {assessment.status}</span>
                        <span>Risks: {assessment.identified_risks?.length || 0}</span>
                        <span>Controls: {assessment.recommended_controls?.length || 0}</span>
                        <span>Created: {new Date(assessment.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {assessment.status === 'DRAFT' && (
                        <Button size="sm" onClick={() => { setSelectedAssessment(assessment); fetchQuestions(assessment.id); }}>
                          Continue
                        </Button>
                      )}
                      {assessment.status === 'PENDING_REVIEW' && (
                        <>
                          <Button size="sm" variant="outline" onClick={() => downloadReport(assessment.id)}>
                            Download PDF
                          </Button>
                          <Button size="sm" onClick={() => createIssues(assessment.id)}>
                            Create Issues
                          </Button>
                        </>
                      )}
                      {assessment.status === 'COMPLETED' && (
                        <Button size="sm" variant="outline" onClick={() => downloadReport(assessment.id)}>
                          Download Report
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {assessment.identified_risks?.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-700">
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Identified Risks</h4>
                      <div className="flex flex-wrap gap-2">
                        {assessment.identified_risks.slice(0, 5).map((risk, idx) => (
                          <span key={idx} className={`text-xs px-2 py-1 rounded text-white ${getRatingColor(risk.inherent_rating)}`}>
                            {risk.title.substring(0, 30)}...
                          </span>
                        ))}
                        {assessment.identified_risks.length > 5 && (
                          <span className="text-xs text-slate-500">+{assessment.identified_risks.length - 5} more</span>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
            
            {assessments.length === 0 && (
              <div className="text-center py-12 text-slate-500">
                No assessments yet. Click "New Assessment" to get started.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TechRiskAssessment;
