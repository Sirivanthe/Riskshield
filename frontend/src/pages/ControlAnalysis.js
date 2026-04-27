import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const TENANT_ID = 'default';

const effectivenessColor = (eff) => {
  switch ((eff || '').toUpperCase()) {
    case 'EFFECTIVE': return 'bg-green-600';
    case 'PARTIALLY_EFFECTIVE': return 'bg-yellow-600';
    case 'INEFFECTIVE': return 'bg-red-600';
    default: return 'bg-slate-600';
  }
};

const statusColor = (status) => {
  switch ((status || '').toUpperCase()) {
    case 'PASS': return 'bg-green-600';
    case 'PARTIAL': return 'bg-yellow-600';
    case 'FAIL': return 'bg-red-600';
    case 'INSUFFICIENT': return 'bg-slate-600';
    default: return 'bg-slate-600';
  }
};

const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const GenerateDraftButton = ({ requirement, framework, onSaved, showToast, apiUrl, tenantId, authHeaders }) => {
  const [generating, setGenerating] = React.useState(false);
  const [draft, setDraft] = React.useState(null);
  const [saving, setSaving] = React.useState(false);

  const generate = async () => {
    setGenerating(true);
    setDraft(null);
    try {
      const res = await fetch(`${apiUrl}/api/control-analysis/controls/generate-draft?tenant_id=${tenantId}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement_text: requirement.requirement_text,
          requirement_type: requirement.requirement_type,
          framework: framework,
        }),
      });
      if (res.status >= 400) throw new Error('Generation failed');
      const data = await res.json();
      setDraft(data.draft_control);
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setGenerating(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${apiUrl}/api/control-analysis/controls/save-draft?tenant_id=${tenantId}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ control: draft }),
      });
      if (res.status >= 400) throw new Error('Save failed');
      setDraft(null);
      onSaved();
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-shrink-0 space-y-2">
      {!draft ? (
        <button onClick={generate} disabled={generating}
          className="text-xs px-3 py-1.5 rounded border border-blue-500 text-blue-400 hover:bg-blue-900/20 disabled:opacity-50 whitespace-nowrap">
          {generating ? '⏳ Generating...' : '🤖 Generate Control'}
        </button>
      ) : (
        <div className="w-64 p-3 bg-slate-800 border border-blue-600 rounded space-y-2">
          <div className="text-xs text-blue-400 font-medium">Draft Control</div>
          <div className="text-xs text-white font-medium">{draft.name}</div>
          <div className="text-xs text-slate-400">{draft.domain} · {draft.type}</div>
          <div className="text-xs text-slate-300">{(draft.description || '').slice(0, 120)}...</div>
          {draft.estimated_effort && (
            <div className="text-xs text-slate-400">Effort: <span className="text-yellow-400">{draft.estimated_effort}</span></div>
          )}
          <div className="flex gap-1">
            <button onClick={save} disabled={saving}
              className="flex-1 text-xs px-2 py-1 rounded bg-green-700 text-white hover:bg-green-600 disabled:opacity-50">
              {saving ? 'Saving...' : '✅ Add to Register'}
            </button>
            <button onClick={() => setDraft(null)}
              className="text-xs px-2 py-1 rounded border border-slate-600 text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const ControlAnalysis = () => {
  const [tab, setTab] = useState('register');
  const [controls, setControls] = useState([]);
  const [domains, setDomains] = useState([]);
  const [obligationsList, setObligationsList] = useState([]);
  const [filterDomain, setFilterDomain] = useState('');
  const [filterEffectiveness, setFilterEffectiveness] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [quality, setQuality] = useState(null);
  const [coverage, setCoverage] = useState(null);
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Modal state
  const [selectedControl, setSelectedControl] = useState(null);
  const [modalTab, setModalTab] = useState('details'); // 'details' | 'improve' | 'evidence'
  const [detailExtras, setDetailExtras] = useState(null);

  // AI Improve state
  const [uplift, setUplift] = useState(null);
  const [uplifting, setUplifting] = useState(false);

  // Evidence - single upload (legacy / fallback)
  const [evaluation, setEvaluation] = useState(null);
  const [evaluating, setEvaluating] = useState(false);

  // Evidence - structured checklist
  const [evidenceChecklist, setEvidenceChecklist] = useState(null);
  const [loadingChecklist, setLoadingChecklist] = useState(false);
  const [itemEvaluations, setItemEvaluations] = useState({});
  const [evaluatingItem, setEvaluatingItem] = useState(null);
  const [checklistCache, setChecklistCache] = useState({});

  // Regulation mapping


  const [toast, setToast] = useState(null);
  const csvInputRef = useRef(null);
  const excelInputRef = useRef(null);
  const pdfInputRef = useRef(null);
  const evidenceInputRef = useRef(null);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadAll = async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ tenant_id: TENANT_ID, limit: '500' });
      if (filterDomain) qs.set('domain', filterDomain);
      if (filterEffectiveness) qs.set('effectiveness', filterEffectiveness);
      const [cRes, qRes, dRes, covRes, obRes] = await Promise.all([
        fetch(`${API_URL}/api/control-analysis/controls?${qs}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/control-analysis/quality?tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/control-analysis/duplicates?tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/control-analysis/coverage?tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/control-analysis/obligations?tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
      ]);
      const cd = await cRes.json();
      const qd = await qRes.json();
      const dd = await dRes.json();
      const covd = await covRes.json();
      const obd = await obRes.json();
      setControls(cd.controls || []);
      setDomains(cd.domains || []);
      setObligationsList(obd.obligations || []);
      setQuality(qd);
      setDuplicates(dd.duplicates || []);
      setCoverage(covd);
    } catch (e) {
      console.error(e);
      showToast('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, [filterDomain, filterEffectiveness]);

  const uploadFile = async (file, kind) => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_URL}/api/control-analysis/controls/import/${kind}?tenant_id=${TENANT_ID}`, {
        method: 'POST', body: fd, headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Import failed (${res.status})`);
      const data = await res.json();
      showToast(`Imported ${data.imported}/${data.total_rows} controls`, 'success');
      await loadAll();
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setUploading(false);
    }
  };

  const importServiceNow = async () => {
    setUploading(true);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/controls/import/servicenow?tenant_id=${TENANT_ID}`, {
        method: 'POST', headers: authHeaders(),
      });
      const data = await res.json();
      showToast(`Imported ${data.imported} controls from ServiceNow`, 'success');
      await loadAll();
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setUploading(false);
    }
  };

  const openControl = async (c) => {
    setSelectedControl(c);
    setModalTab('details');
    setEvaluation(null);
    setUplift(null);
    setDetailExtras(null);
    setEvidenceChecklist(checklistCache[c.id] || null);
    setItemEvaluations({});
    try {
      const [detailRes, evalRes] = await Promise.all([
        fetch(`${API_URL}/api/control-analysis/controls/${c.id}?tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/control-analysis/evaluations?control_id=${c.id}&limit=1&tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
      ]);
      const detail = await detailRes.json();
      const evalData = await evalRes.json();
      setDetailExtras({ obligations: detail.obligations || [], similar: detail.similar_controls || [] });
      if (detail.control) setSelectedControl(detail.control);
      if (evalData.evaluations?.length) {
        setEvaluation({
          evaluation_id: evalData.evaluations[0].id,
          control: c,
          evaluation: evalData.evaluations[0].evaluation,
          narrative_5w1h: evalData.evaluations[0].narrative_5w1h,
        });
      }
    } catch (e) { console.error(e); }
  };

  const closeModal = () => {
    setSelectedControl(null);
    setEvaluation(null);
    setUplift(null);
    setEvidenceChecklist(null);
    setItemEvaluations({});
    setModalTab('details');
  };

  // AI Improve
  const runUplift = async () => {
    setUplifting(true);
    setUplift(null);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/controls/${selectedControl.id}/uplift?tenant_id=${TENANT_ID}`, {
        method: 'POST', headers: authHeaders(),
      });
      if (!res.ok) throw new Error('Uplift failed');
      setUplift(await res.json());
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setUplifting(false);
    }
  };

  const applyUplift = async () => {
    if (!uplift || !selectedControl) return;
    try {
      await fetch(`${API_URL}/api/control-analysis/controls/${selectedControl.id}?tenant_id=${TENANT_ID}`, {
        method: 'PUT',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates: {
          name: uplift.improved.name,
          description: uplift.improved.description,
          test_procedure: uplift.improved.test_procedure,
        }}),
      });
      showToast('Improvements applied to control', 'success');
      setUplift(null);
      // Clear checklist cache for this control so it regenerates with new test procedure
      setChecklistCache(prev => { const n = {...prev}; delete n[selectedControl.id]; return n; });
      setEvidenceChecklist(null);
      await loadAll();
      const refreshed = controls.find(c => c.id === selectedControl.id);
      if (refreshed) setSelectedControl(refreshed);
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  // Single evidence upload (used when no checklist / as fallback)
  const evaluateEvidence = async (file) => {
    if (!file || !selectedControl) return;
    setEvaluating(true);
    setEvaluation(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('control_id', selectedControl.id);
      fd.append('uploaded_by', 'current_user');
      const res = await fetch(`${API_URL}/api/control-analysis/evidence/upload?tenant_id=${TENANT_ID}`, {
        method: 'POST', body: fd, headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Evaluation failed (${res.status})`);
      const evalData = await res.json();
      setEvaluation(evalData);
      // Update control effectiveness based on evaluation result
      if (evalData?.evaluation?.effectiveness) {
        await fetch(`${API_URL}/api/control-analysis/controls/${selectedControl.id}?tenant_id=${TENANT_ID}`, {
          method: 'PUT',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ updates: { effectiveness: evalData.evaluation.effectiveness } }),
        });
      }
      showToast('Evidence evaluated via LLM', 'success');
      await loadAll();
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setEvaluating(false);
    }
  };

  // Structured checklist
  const loadEvidenceChecklist = async () => {
    if (!selectedControl) return;
    if (checklistCache[selectedControl.id]) {
      setEvidenceChecklist(checklistCache[selectedControl.id]);
      return;
    }
    setLoadingChecklist(true);
    setEvidenceChecklist(null);
    setItemEvaluations({});
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/evidence/checklist/${selectedControl.id}?tenant_id=${TENANT_ID}`, {
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error('Failed to load checklist');
      const data = await res.json();
      if (!data.evidence_items?.length) {
        showToast('No evidence requirements found — run AI Improve first to generate a test procedure', 'error');
        return;
      }
      setEvidenceChecklist(data);
      setChecklistCache(prev => ({ ...prev, [selectedControl.id]: data }));
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setLoadingChecklist(false);
    }
  };

  const evaluateEvidenceItem = async (file, item) => {
    setEvaluatingItem(item.id);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('control_id', selectedControl.id);
      fd.append('item_id', item.id);
      fd.append('item_description', item.item);
      fd.append('uploaded_by', 'current_user');
      const res = await fetch(`${API_URL}/api/control-analysis/evidence/upload-item?tenant_id=${TENANT_ID}`, {
        method: 'POST', body: fd, headers: authHeaders(),
      });
      if (!res.ok) throw new Error('Item evaluation failed');
      const data = await res.json();
      setItemEvaluations(prev => ({ ...prev, [item.id]: data }));
      showToast(`${item.id}: ${data.status}`, data.status === 'PASS' ? 'success' : 'error');
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setEvaluatingItem(null);
    }
  };



  const downloadWorkpaper = async (format) => {
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/workpaper/${format}?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `control_workpaper.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      a.click();
      URL.revokeObjectURL(url);
      showToast(`Workpaper (${format.toUpperCase()}) downloaded`, 'success');
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  const raiseIssue = async () => {
    try {
      const token = localStorage.getItem('token');
      const failedItems = Object.values(itemEvaluations).filter(e => e.status === 'FAIL' || e.status === 'PARTIAL');
      const gaps = failedItems.flatMap(e => e.gaps || []).join('; ');
      const payload = {
        title: `Control Failure: ${selectedControl.name}`,
        description: `Control ${selectedControl.control_id} evaluated as ${overallVerdict}. Gaps: ${gaps || 'See evidence evaluation'}`,
        issue_type: 'CONTROL_FAILURE',
        severity: overallVerdict === 'FAIL' ? 'HIGH' : 'MEDIUM',
        priority: overallVerdict === 'FAIL' ? 'P1' : 'P2',
        owner: selectedControl.owner || '',
        app_name: selectedControl.control_id,
      };
      const res = await fetch(`${API_URL}/api/issue-management/?creator_id=current_user&creator_name=Auditor`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.status >= 400) throw new Error('Failed to raise issue');
      showToast('Issue raised in Issue Management', 'success');
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  // Derived: overall verdict from item evaluations
  const allItemsEvaluated = evidenceChecklist?.evidence_items?.length > 0 &&
    Object.keys(itemEvaluations).length === evidenceChecklist.evidence_items.length;
  const overallVerdict = allItemsEvaluated
    ? Object.values(itemEvaluations).every(e => e.status === 'PASS') ? 'PASS'
    : Object.values(itemEvaluations).some(e => e.status === 'PASS') ? 'PARTIAL' : 'FAIL'
    : null;

  // Auto-update effectiveness when all items evaluated
  useEffect(() => {
    if (!overallVerdict || !selectedControl) return;
    const effectivenessMap = { PASS: 'EFFECTIVE', PARTIAL: 'PARTIALLY_EFFECTIVE', FAIL: 'INEFFECTIVE' };
    const newEffectiveness = effectivenessMap[overallVerdict];
    if (!newEffectiveness) return;
    fetch(`${API_URL}/api/control-analysis/controls/${selectedControl.id}?tenant_id=${TENANT_ID}`, {
      method: 'PUT',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates: { effectiveness: newEffectiveness } }),
    }).then(() => loadAll());
  }, [overallVerdict]);

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="control-analysis-page">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Control Analysis</h1>
            <p className="text-slate-400">Ingest, analyze and evaluate controls. Upload registers, validate evidence with AI and export audit workpapers.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => downloadWorkpaper('pdf')} className="bg-slate-700 hover:bg-slate-600 text-white">Export PDF</Button>
            <Button onClick={() => downloadWorkpaper('excel')}>Export Excel</Button>
          </div>
        </div>

        {/* Import Card */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader><CardTitle className="text-white text-base">Import Control Register</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap items-center gap-3">
            <input ref={csvInputRef} type="file" accept=".csv" className="hidden" onChange={(e) => uploadFile(e.target.files?.[0], 'csv')} />
            <input ref={excelInputRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => uploadFile(e.target.files?.[0], 'excel')} />
            <input ref={pdfInputRef} type="file" accept=".pdf" className="hidden" onChange={(e) => uploadFile(e.target.files?.[0], 'pdf')} />
            <Button onClick={() => csvInputRef.current?.click()} disabled={uploading}>{uploading ? 'Uploading...' : 'Upload CSV'}</Button>
            <Button variant="outline" onClick={() => excelInputRef.current?.click()} disabled={uploading}>Upload Excel</Button>
            <Button variant="outline" onClick={() => pdfInputRef.current?.click()} disabled={uploading}>Upload PDF (LLM-extract)</Button>
            <Button variant="outline" onClick={importServiceNow} disabled={uploading}>Import from ServiceNow (Mock)</Button>
            <span className="text-xs text-slate-500">CSV/Excel: control_id, name, description, domain, owner, type, category, test_procedure, frameworks · PDF: free-form, extracted by Claude.</span>
          </CardContent>
        </Card>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-700">
          {[
            { id: 'register', label: 'Register' },
            { id: 'quality', label: 'Quality' },
            { id: 'coverage', label: 'Coverage' },
            { id: 'duplicates', label: `Duplicates${duplicates.length ? ` (${duplicates.length})` : ''}` },

          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm ${tab === t.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Quality tab */}
        {tab === 'quality' && quality && (
          <div className="space-y-4">
            {/* Overall Score Banner */}
            <div className={`p-4 rounded-xl border ${
              quality.quality_score >= 80 ? 'bg-green-900/20 border-green-600' :
              quality.quality_score >= 60 ? 'bg-yellow-900/20 border-yellow-600' :
              'bg-red-900/20 border-red-600'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-slate-400 uppercase mb-1">Overall Quality Score</div>
                  <div className="text-4xl font-bold text-white">{(quality.quality_score ?? 0).toFixed(1)} <span className="text-xl text-slate-400">/ 100</span></div>
                  <div className="text-sm text-slate-400 mt-1">
                    {quality.quality_score >= 80 ? '✅ Good — register is well-structured and complete' :
                     quality.quality_score >= 60 ? '⚠️ Fair — some controls need improvement' :
                     '❌ Poor — significant gaps in control quality'}
                  </div>
                </div>
                <div className="text-right text-sm text-slate-400">
                  <div>{quality.total_controls} total controls</div>
                  <div className="text-xs mt-1">Score = (Completeness × 30%) + (Uniqueness × 25%) + (Strength × 20%) + (Effectiveness × 25%)</div>
                </div>
              </div>
            </div>

            {/* Three Score Components */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="text-sm font-medium text-white">Completeness</div>
                    <div className={`text-lg font-bold ${quality.completeness_score >= 80 ? 'text-green-400' : quality.completeness_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {(quality.completeness_score ?? 0).toFixed(1)}%
                    </div>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{width: `${quality.completeness_score ?? 0}%`}} />
                  </div>
                  <div className="text-xs text-slate-400">Each control should have a description, owner, and test procedure. Missing any of these reduces this score.</div>
                  <div className="grid grid-cols-3 gap-1 text-xs">
                    <div className={`text-center p-1 rounded ${quality.missing_descriptions > 0 ? 'bg-red-900/40 text-red-300' : 'bg-green-900/40 text-green-300'}`}>
                      {quality.missing_descriptions} missing desc
                    </div>
                    <div className={`text-center p-1 rounded ${quality.missing_owners > 0 ? 'bg-red-900/40 text-red-300' : 'bg-green-900/40 text-green-300'}`}>
                      {quality.missing_owners} missing owner
                    </div>
                    <div className={`text-center p-1 rounded ${quality.missing_test_procedures > 0 ? 'bg-red-900/40 text-red-300' : 'bg-green-900/40 text-green-300'}`}>
                      {quality.missing_test_procedures} missing test
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="text-sm font-medium text-white">Uniqueness</div>
                    <div className={`text-lg font-bold ${quality.uniqueness_score >= 80 ? 'text-green-400' : quality.uniqueness_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {(quality.uniqueness_score ?? 0).toFixed(1)}%
                    </div>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{width: `${quality.uniqueness_score ?? 0}%`}} />
                  </div>
                  <div className="text-xs text-slate-400">Controls should not overlap or duplicate each other. Duplicate controls waste testing effort and confuse auditors.</div>
                  <div className={`text-center p-1 rounded text-xs ${quality.duplicates_found > 0 ? 'bg-red-900/40 text-red-300' : 'bg-green-900/40 text-green-300'}`}>
                    {quality.duplicates_found === 0 ? '✅ No duplicates found' : `⚠️ ${quality.duplicates_found} duplicate pairs detected`}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="text-sm font-medium text-white">Strength</div>
                    <div className={`text-lg font-bold ${quality.strength_score >= 80 ? 'text-green-400' : quality.strength_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {(quality.strength_score ?? 0).toFixed(1)}%
                    </div>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div className="bg-orange-500 h-2 rounded-full" style={{width: `${quality.strength_score ?? 0}%`}} />
                  </div>
                  <div className="text-xs text-slate-400">Strong controls use mandatory language (automated, enforced, verified). Weak controls use vague language (periodic, should, may).</div>
                  <div className="grid grid-cols-3 gap-1 text-xs">
                    <div className="text-center p-1 rounded bg-green-900/40 text-green-300">
                      {quality.strong_controls} strong
                    </div>
                    <div className="text-center p-1 rounded bg-slate-700 text-slate-300">
                      {quality.total_controls - quality.strong_controls - quality.weak_controls} neutral
                    </div>
                    <div className={`text-center p-1 rounded ${quality.weak_controls > 0 ? 'bg-red-900/40 text-red-300' : 'bg-slate-700 text-slate-400'}`}>
                      {quality.weak_controls} weak
                    </div>
                  </div>
                  {quality.strength_score < 80 && (
                    <div className="text-xs text-yellow-400">💡 Use AI Improve on controls to boost strength score</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Coverage tab */}
        {tab === 'coverage' && coverage && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Domains with Controls', value: coverage.covered_domains, color: 'text-blue-400' },
                { label: 'Total Domains', value: coverage.total_domains, color: 'text-slate-300' },
                { label: 'Effective Controls', value: Object.values(coverage.domains).reduce((a, s) => a + (s.effective || 0), 0), color: 'text-green-400' },
                { label: 'Need Attention', value: Object.values(coverage.domains).reduce((a, s) => a + (s.ineffective || 0) + (s.not_tested || 0), 0), color: 'text-red-400' },
              ].map(m => (
                <Card key={m.label} className="bg-slate-800/50 border-slate-700">
                  <CardContent className="p-3">
                    <div className="text-xs text-slate-400">{m.label}</div>
                    <div className={`text-2xl font-bold ${m.color}`}>{m.value}</div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Domains with controls */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader><CardTitle className="text-white text-base">Domains with Controls</CardTitle></CardHeader>
              <CardContent>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-700">
                      <th className="py-2">Domain</th>
                      <th>Total</th>
                      <th>✅ Effective</th>
                      <th>⚠️ Partial</th>
                      <th>❌ Ineffective</th>
                      <th>🔲 Not Tested</th>
                      <th>Coverage Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(coverage.domains)
                      .filter(([, s]) => s.total_controls > 0)
                      .sort((a, b) => b[1].coverage_score - a[1].coverage_score)
                      .map(([domain, s]) => (
                        <tr key={domain} className="border-b border-slate-800 hover:bg-slate-800/50">
                          <td className="py-2 text-white font-medium">{domain}</td>
                          <td className="text-slate-300">{s.total_controls}</td>
                          <td className="text-green-400">{s.effective || 0}</td>
                          <td className="text-yellow-400">{s.partially_effective || 0}</td>
                          <td className="text-red-400">{s.ineffective || 0}</td>
                          <td className="text-slate-500">{s.not_tested || 0}</td>
                          <td>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-slate-700 rounded-full h-2">
                                <div className={`h-2 rounded-full ${
                                  s.coverage_score >= 80 ? 'bg-green-500' :
                                  s.coverage_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                }`} style={{width: `${s.coverage_score}%`}} />
                              </div>
                              <span className={`text-xs font-medium ${
                                s.coverage_score >= 80 ? 'text-green-400' :
                                s.coverage_score >= 50 ? 'text-yellow-400' : 'text-red-400'
                              }`}>{(s.coverage_score ?? 0).toFixed(1)}%</span>
                            </div>
                          </td>
                        </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            {/* Uncovered domains */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader><CardTitle className="text-white text-base text-red-400">⚠ Domains with No Controls ({Object.values(coverage.domains).filter(s => s.total_controls === 0).length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(coverage.domains)
                    .filter(([, s]) => s.total_controls === 0)
                    .map(([domain]) => (
                      <span key={domain} className="text-xs px-2 py-1 rounded bg-red-900/30 border border-red-700 text-red-300">{domain}</span>
                    ))}
                </div>
                <p className="text-xs text-slate-400 mt-2">These domains have no controls defined. Consider adding controls or importing your RCM to cover these areas.</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Duplicates tab */}
        {tab === 'duplicates' && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader><CardTitle className="text-white text-base">Potential Duplicates</CardTitle></CardHeader>
            <CardContent>
              {duplicates.length === 0 ? <p className="text-slate-400">No duplicates detected.</p> : (
                <div className="space-y-3">
                  {duplicates.map((d, idx) => (
                    <div key={idx} className="p-3 bg-slate-900/50 rounded border border-slate-700">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs text-slate-400">Similarity: {(d.similarity_score * 100).toFixed(1)}%</span>
                        <span className="text-xs px-2 py-1 rounded bg-yellow-700 text-white">{d.recommendation}</span>
                      </div>
                      <div className="text-sm text-white">{d.control_1.name} ({d.control_1.control_id})</div>
                      <div className="text-sm text-slate-300">↔ {d.control_2.name} ({d.control_2.control_id})</div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Regulation mapping — moved to Regulatory Analysis page */}
        {tab === 'regulation' && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-8 text-center space-y-4">
              <div className="text-4xl">📋</div>
              <h3 className="text-white text-lg font-medium">Regulatory Analysis has moved</h3>
              <p className="text-slate-400 text-sm max-w-md mx-auto">
                Full regulatory analysis — PDF upload, AI requirement extraction, control mapping, gap remediation and issue raising — is now available on the dedicated Regulatory Analysis page.
              </p>
              <a href="/regulatory-analysis"
                className="inline-block px-6 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-500">
                Go to Regulatory Analysis →
              </a>
            </CardContent>
          </Card>
        )}
        {tab === 'register' && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="text-white text-base">
                  Controls Register ({controls.length}{(filterDomain || filterEffectiveness || searchQuery) ? ' filtered' : ''})
                </CardTitle>
                <div className="flex flex-wrap gap-2 items-center">
                  <Input placeholder="Search control id, name, description…" value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white" style={{ width: '260px' }} />
                  <select value={filterDomain} onChange={(e) => setFilterDomain(e.target.value)}
                    className="bg-slate-700 border border-slate-600 text-white rounded px-2 py-1 text-sm">
                    <option value="">All domains</option>
                    {domains.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                  <select value={filterEffectiveness} onChange={(e) => setFilterEffectiveness(e.target.value)}
                    className="bg-slate-700 border border-slate-600 text-white rounded px-2 py-1 text-sm">
                    <option value="">All effectiveness</option>
                    <option value="EFFECTIVE">Effective</option>
                    <option value="PARTIALLY_EFFECTIVE">Partially Effective</option>
                    <option value="INEFFECTIVE">Ineffective</option>
                    <option value="NOT_TESTED">Not Tested</option>
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
                {[
                  { label: 'Controls', value: controls.length },
                  { label: 'Avg Strength', value: controls.length ? `${(controls.reduce((a, c) => a + (c.strength_score || 0), 0) / controls.length).toFixed(1)}` : '—' },
                  { label: 'Obligations in scope', value: obligationsList.length },
                  { label: 'Potential Duplicates', value: duplicates.length },
                  { label: 'Mapped to Regs', value: controls.filter((c) => (c.obligations_count || 0) > 0).length },
                ].map((m) => (
                  <div key={m.label} className="bg-slate-900/60 p-2 rounded">
                    <div className="text-xs text-slate-400">{m.label}</div>
                    <div className="text-lg font-bold text-white">{m.value}</div>
                  </div>
                ))}
              </div>
              {loading ? <p className="text-slate-400">Loading...</p> : controls.length === 0 ? (
                <p className="text-slate-400">No controls. Upload a CSV, Excel or PDF register to begin.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-400 border-b border-slate-700">
                        <th className="py-2 pr-3">Control ID</th>
                        <th className="pr-3">Name</th>
                        <th className="pr-3">Domain</th>
                        <th className="pr-3">Owner</th>
                        <th className="pr-3">Strength</th>
                        <th className="pr-3">Effectiveness</th>
                        <th className="pr-3">Regs</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {controls.filter((c) => {
                        if (!searchQuery) return true;
                        const q = searchQuery.toLowerCase();
                        return ((c.control_id || '') + ' ' + (c.name || '') + ' ' + (c.description || '')).toLowerCase().includes(q);
                      }).map((c) => {
                        const s = c.strength_score || 0;
                        const strengthColor = s >= 80 ? '#10b981' : s >= 60 ? '#f59e0b' : '#ef4444';
                        return (
                          <tr key={c.id} onClick={() => openControl(c)}
                            className="border-b border-slate-800 hover:bg-slate-800/70 cursor-pointer">
                            <td className="py-2 pr-3 text-white">{c.control_id}</td>
                            <td className="pr-3 text-slate-200">{c.name}</td>
                            <td className="pr-3 text-slate-300">{c.domain || '—'}</td>
                            <td className="pr-3 text-slate-300">{c.owner || '—'}</td>
                            <td className="pr-3">
                              <div className="flex items-center gap-2">
                                <div style={{ width: '64px', height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                                  <div style={{ width: `${s}%`, height: '100%', background: strengthColor }} />
                                </div>
                                <span style={{ color: strengthColor, fontWeight: 600 }}>{s.toFixed(0)}</span>
                              </div>
                            </td>
                            <td className="pr-3">
                              <span className={`text-xs px-2 py-1 rounded text-white ${effectivenessColor(c.effectiveness)}`}>
                                {c.effectiveness || 'NOT_TESTED'}
                              </span>
                            </td>
                            <td className="pr-3">
                              {c.obligations_count > 0 ? (
                                <span className="text-xs px-2 py-1 rounded bg-emerald-800 text-emerald-100">{c.obligations_count} mapped</span>
                              ) : <span className="text-xs text-slate-500">—</span>}
                            </td>
                            <td>
                              <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); openControl(c); }}>Open</Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* ====== CONTROL DETAIL MODAL ====== */}
      {selectedControl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4"
          onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}>
          <div className="w-full max-w-3xl max-h-[92vh] flex flex-col rounded-xl bg-slate-800 border border-slate-700 shadow-2xl">

            {/* Modal Header */}
            <div className="flex justify-between items-start p-5 border-b border-slate-700 flex-shrink-0">
              <div>
                <h2 className="text-white font-bold text-lg">{selectedControl.control_id} — {selectedControl.name}</h2>
                <div className="text-xs text-slate-400 mt-1">
                  {selectedControl.domain} · {selectedControl.type} · {selectedControl.category} · Owner: {selectedControl.owner}
                </div>
                {selectedControl.strength_score !== undefined && (
                  <div className="mt-2">
                    <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-200 border border-slate-600">
                      Strength: <strong>{selectedControl.strength_score}</strong>/100
                    </span>
                    {evaluation?.evaluation && (
                      <span className={`ml-2 text-xs px-2 py-1 rounded text-white ${statusColor(evaluation.evaluation.status)}`}>
                        Last: {evaluation.evaluation.status}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <button onClick={closeModal} className="text-slate-400 hover:text-white text-xl font-bold px-2">✕</button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-slate-700 flex-shrink-0">
              {[
                { id: 'details', label: '📋 Details' },
                { id: 'improve', label: '🤖 AI Improve' },
                { id: 'evidence', label: '🔍 Evidence Testing' },
              ].map((t) => (
                <button key={t.id} onClick={() => setModalTab(t.id)}
                  className={`px-5 py-3 text-sm font-medium ${modalTab === t.id ? 'text-blue-400 border-b-2 border-blue-400 bg-slate-900/30' : 'text-slate-400 hover:text-slate-200'}`}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Modal Body - scrollable */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">

              {/* ── DETAILS TAB ── */}
              {modalTab === 'details' && (
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-slate-400 uppercase mb-1">Description</div>
                    <p className="text-slate-200">{selectedControl.description || '—'}</p>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 uppercase mb-1">Test Procedure</div>
                    {selectedControl.test_procedure ? (
                      <p className="text-slate-200 whitespace-pre-wrap">{selectedControl.test_procedure}</p>
                    ) : (
                      <p className="text-yellow-400 text-sm">⚠ No test procedure defined. Use AI Improve tab to generate one.</p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(selectedControl.frameworks || []).map((f) => (
                      <span key={f} className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-200">{f}</span>
                    ))}
                  </div>

                  {/* Regulatory Obligations */}
                  {detailExtras?.obligations?.length > 0 && (
                    <div className="pt-3 border-t border-slate-700">
                      <div className="text-xs text-blue-400 uppercase mb-2">Regulatory Obligations Covered ({detailExtras.obligations.length})</div>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {detailExtras.obligations.map((ob) => (
                          <div key={ob.id} className="p-2 bg-slate-900/60 rounded border border-slate-800">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`text-xs px-2 py-1 rounded text-white ${ob.type === 'MANDATORY' ? 'bg-red-700' : ob.type === 'RECOMMENDED' ? 'bg-amber-700' : 'bg-slate-600'}`}>{ob.type}</span>
                              <span className="text-xs text-slate-400">{ob.framework} · {ob.id}</span>
                            </div>
                            <div className="text-sm text-slate-200">{(ob.requirement_text || '').slice(0, 220)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Similar Controls */}
                  {detailExtras?.similar?.length > 0 && (
                    <div className="pt-3 border-t border-slate-700">
                      <div className="text-xs text-blue-400 uppercase mb-2">Similar Controls ({detailExtras.similar.length})</div>
                      <div className="space-y-1 max-h-36 overflow-y-auto">
                        {detailExtras.similar.map((s) => (
                          <div key={s.id} className="flex justify-between items-center p-2 bg-slate-900/60 rounded text-sm">
                            <div className="text-slate-200"><span className="text-slate-500">{s.control_id}</span> · {s.name}</div>
                            <span className="text-xs text-slate-400">similarity {(s.similarity_score * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Last Evaluation Summary */}
                  {evaluation?.evaluation && (
                    <div className="pt-3 border-t border-slate-700">
                      <div className="text-xs text-blue-400 uppercase mb-2">Last Evaluation Result</div>
                      <div className="p-3 bg-slate-900/50 rounded border border-slate-700 space-y-2">
                        <div className="flex items-center gap-3">
                          <span className={`text-xs px-3 py-1 rounded text-white ${statusColor(evaluation.evaluation.status)}`}>{evaluation.evaluation.status}</span>
                          <span className="text-sm text-slate-300">Confidence: {evaluation.evaluation.confidence}%</span>
                          <span className={`text-xs px-2 py-1 rounded text-white ${effectivenessColor(evaluation.evaluation.effectiveness)}`}>{evaluation.evaluation.effectiveness}</span>
                        </div>
                        <div className="text-slate-100 italic text-sm">{evaluation.evaluation.audit_opinion}</div>
                        <Button size="sm" variant="outline" onClick={() => setModalTab('evidence')} className="text-xs">
                          View Full Evidence →
                        </Button>
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-slate-700 flex gap-2 flex-wrap">
                    <Button variant="outline" onClick={() => setModalTab('improve')}>🤖 AI Improve Language</Button>
                    <Button variant="outline" onClick={() => setModalTab('evidence')}>🔍 Test Evidence</Button>
                  </div>
                </div>
              )}

              {/* ── AI IMPROVE TAB ── */}
              {modalTab === 'improve' && (
                <div className="space-y-4">
                  <div className="p-3 bg-slate-900/50 rounded border border-slate-700 text-sm text-slate-300">
                    <p className="font-medium text-white mb-1">How AI Improve works:</p>
                    <ol className="list-decimal list-inside space-y-1 text-slate-400">
                      <li>AI analyzes your control for vague language, missing specifics, and weak test procedures</li>
                      <li>It rewrites the control in mandatory audit language (must/shall)</li>
                      <li>Apply the improvements — this also refreshes the evidence checklist</li>
                    </ol>
                  </div>

                  <Button onClick={runUplift} disabled={uplifting} className="w-full">
                    {uplifting ? '⏳ Analyzing control...' : '🤖 Run AI Language Improvement'}
                  </Button>

                  {uplift && (
                    <div className="space-y-4">
                      <div className="p-4 bg-slate-900/50 rounded border border-blue-700/50 space-y-3">
                        <h4 className="text-white font-medium">AI-Suggested Improvements</h4>
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Improved Name</div>
                          <div className="text-slate-200 font-medium">{uplift.improved?.name || uplift.improved_name}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Improved Description</div>
                          <div className="text-slate-200 text-sm">{uplift.improved?.description || uplift.improved_description}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-400 uppercase mb-1">Improved Test Procedure</div>
                          <div className="text-slate-200 text-sm whitespace-pre-wrap">{uplift.improved?.test_procedure || uplift.improved_test_procedure}</div>
                        </div>
                        {(uplift.changes_summary || uplift.improved?.changes_summary)?.length > 0 && (
                          <div>
                            <div className="text-xs text-slate-400 uppercase mb-1">Changes Made</div>
                            <ul className="list-disc list-inside text-slate-300 text-sm space-y-1">
                              {(uplift.changes_summary || uplift.improved?.changes_summary).map((c, i) => <li key={i}>{c}</li>)}
                            </ul>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={applyUplift} className="flex-1">✅ Apply to Control</Button>
                        <Button variant="outline" onClick={() => setUplift(null)}>Dismiss</Button>
                      </div>
                      <p className="text-xs text-slate-500">After applying, go to Evidence Testing tab to generate a checklist based on the new test procedure.</p>
                    </div>
                  )}
                </div>
              )}

              {/* ── EVIDENCE TESTING TAB ── */}
              {modalTab === 'evidence' && (
                <div className="space-y-4">
                  {!selectedControl.test_procedure && (
                    <div className="p-3 bg-yellow-900/30 border border-yellow-700 rounded text-sm text-yellow-300">
                      ⚠ No test procedure defined. <button onClick={() => setModalTab('improve')} className="underline">Run AI Improve</button> first to get a structured checklist.
                    </div>
                  )}

                  {/* Structured checklist mode */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-white font-medium">Structured Evidence Checklist</h4>
                      <Button size="sm" variant="outline" onClick={() => {
                          setChecklistCache(prev => { const n = {...prev}; delete n[selectedControl.id]; return n; });
                          setEvidenceChecklist(null);
                          setItemEvaluations({});
                          setTimeout(loadEvidenceChecklist, 50);
                        }} disabled={loadingChecklist}>
                        {loadingChecklist ? '⏳ Loading...' : evidenceChecklist ? '🔄 Regenerate' : '📋 Load Checklist'}
                      </Button>
                    </div>
                    <p className="text-xs text-slate-400">AI parses the test procedure and generates specific evidence requirements. Upload evidence per item for granular PASS/FAIL.</p>

                    {evidenceChecklist && evidenceChecklist.evidence_items?.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-300">
                            {Object.keys(itemEvaluations).length}/{evidenceChecklist.evidence_items.length} items evaluated
                          </span>
                          {overallVerdict && (
                            <span className={`text-sm font-bold px-3 py-1 rounded text-white ${
                              overallVerdict === 'PASS' ? 'bg-green-600' : overallVerdict === 'PARTIAL' ? 'bg-yellow-600' : 'bg-red-600'
                            }`}>
                              {overallVerdict === 'PASS' ? '✅' : overallVerdict === 'PARTIAL' ? '⚠️' : '❌'} {overallVerdict}
                            </span>
                          )}
                        </div>

                        {evidenceChecklist.evidence_items.map((item) => {
                          const ev = itemEvaluations[item.id];
                          return (
                            <div key={item.id} className={`p-3 rounded border ${
                              ev ? (ev.status === 'PASS' ? 'border-green-600 bg-green-900/20' :
                                ev.status === 'FAIL' ? 'border-red-600 bg-red-900/20' : 'border-yellow-600 bg-yellow-900/20')
                              : 'border-slate-600 bg-slate-900/30'
                            }`}>
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 space-y-1">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-xs font-mono text-slate-400">{item.id}</span>
                                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                                      item.type === 'screenshot' ? 'bg-blue-800 text-blue-200' :
                                      item.type === 'log' ? 'bg-purple-800 text-purple-200' :
                                      item.type === 'report' ? 'bg-orange-800 text-orange-200' :
                                      item.type === 'config' ? 'bg-cyan-800 text-cyan-200' :
                                      'bg-slate-700 text-slate-300'
                                    }`}>{item.type}</span>
                                    {ev && (
                                      <span className={`text-xs px-2 py-0.5 rounded font-medium text-white ${
                                        ev.status === 'PASS' ? 'bg-green-700' : ev.status === 'FAIL' ? 'bg-red-700' : 'bg-yellow-700'
                                      }`}>{ev.status} · {ev.confidence}%</span>
                                    )}
                                  </div>
                                  <p className="text-sm text-slate-200">{item.item}</p>
                                  <p className="text-xs text-slate-400">{item.why}</p>
                                  {ev?.reasoning && <p className="text-xs text-slate-300 italic mt-1">{ev.reasoning}</p>}
                                  {ev?.gaps?.length > 0 && (
                                    <ul className="text-xs text-red-300 list-disc list-inside">
                                      {ev.gaps.map((g, i) => <li key={i}>{g}</li>)}
                                    </ul>
                                  )}
                                </div>
                                <label className={`flex-shrink-0 cursor-pointer px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
                                  evaluatingItem === item.id ? 'border-slate-600 text-slate-500' :
                                  'border-slate-500 text-slate-300 hover:border-blue-500 hover:text-blue-300'
                                }`}>
                                  {evaluatingItem === item.id ? '⏳...' : ev ? '🔄 Re-upload' : '⬆ Upload'}
                                  <input type="file" className="hidden" disabled={evaluatingItem === item.id}
                                    onChange={(e) => { const f = e.target.files?.[0]; if (f) evaluateEvidenceItem(f, item); e.target.value = ''; }} />
                                </label>
                              </div>
                            </div>
                          );
                        })}

                        {/* Post-completion actions */}
                        {overallVerdict && (
                          <div className={`p-4 rounded border space-y-3 ${
                            overallVerdict === 'PASS' ? 'border-green-500 bg-green-900/20' :
                            overallVerdict === 'PARTIAL' ? 'border-yellow-500 bg-yellow-900/20' : 'border-red-500 bg-red-900/20'
                          }`}>
                            <div className="text-white font-medium">
                              Overall Result: {overallVerdict === 'PASS' ? '✅ PASS' : overallVerdict === 'PARTIAL' ? '⚠️ PARTIAL' : '❌ FAIL'}
                            </div>
                            <div className="text-xs text-slate-300">
                              {Object.values(itemEvaluations).filter(e => e.status === 'PASS').length} passed ·{' '}
                              {Object.values(itemEvaluations).filter(e => e.status === 'FAIL').length} failed ·{' '}
                              {Object.values(itemEvaluations).filter(e => e.status === 'PARTIAL').length} partial
                            </div>
                            <div className="flex gap-2 flex-wrap">
                              {(overallVerdict === 'FAIL' || overallVerdict === 'PARTIAL') && (
                                <Button size="sm" variant="outline" onClick={raiseIssue} className="border-red-500 text-red-400 hover:bg-red-900/20">
                                  🚨 Raise Issue
                                </Button>
                              )}
                              <Button size="sm" variant="outline" onClick={async () => { await loadAll(); showToast('Control record refreshed', 'success'); }} className="border-green-500 text-green-400 hover:bg-green-900/20">
                                💾 Save & Refresh
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Divider */}
                  <div className="border-t border-slate-700 pt-4">
                    <h4 className="text-white font-medium mb-2">Quick Evidence Upload</h4>
                    <p className="text-xs text-slate-400 mb-3">Upload a single file for overall AI evaluation with full audit narrative.</p>
                    <input ref={evidenceInputRef} type="file" accept=".txt,.md,.csv,.json,.log,.pdf" className="hidden"
                      onChange={(e) => evaluateEvidence(e.target.files?.[0])} />
                    <Button variant="outline" onClick={() => evidenceInputRef.current?.click()} disabled={evaluating} className="w-full">
                      {evaluating ? '⏳ Evaluating with LLM...' : '⬆ Upload & Evaluate Evidence (Single File)'}
                    </Button>
                  </div>

                  {/* Single evaluation result */}
                  {evaluation?.evaluation && (
                    <div className="p-4 bg-slate-900/50 rounded border border-slate-700 space-y-3">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className={`text-xs px-3 py-1 rounded text-white ${statusColor(evaluation.evaluation.status)}`}>{evaluation.evaluation.status}</span>
                        <span className="text-sm text-slate-300">Confidence: {evaluation.evaluation.confidence}%</span>
                        <span className={`text-xs px-2 py-1 rounded text-white ${effectivenessColor(evaluation.evaluation.effectiveness)}`}>{evaluation.evaluation.effectiveness}</span>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 uppercase mb-1">Audit Opinion</div>
                        <div className="text-slate-100 italic">{evaluation.evaluation.audit_opinion}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 uppercase mb-1">Reasoning</div>
                        <div className="text-slate-200 text-sm">{evaluation.evaluation.reasoning}</div>
                      </div>
                      {evaluation.evaluation.gaps?.length > 0 && (
                        <div>
                          <div className="text-xs text-red-400 uppercase mb-1">Gaps</div>
                          <ul className="list-disc list-inside text-slate-300 text-sm space-y-1">
                            {evaluation.evaluation.gaps.map((g, i) => <li key={i}>{g}</li>)}
                          </ul>
                        </div>
                      )}
                      {evaluation.evaluation.recommendations?.length > 0 && (
                        <div>
                          <div className="text-xs text-green-400 uppercase mb-1">Recommendations</div>
                          <ul className="list-disc list-inside text-slate-300 text-sm space-y-1">
                            {evaluation.evaluation.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                          </ul>
                        </div>
                      )}
                      {evaluation.narrative_5w1h && (
                        <div className="pt-3 border-t border-slate-700">
                          <h4 className="text-white font-medium mb-2">5W1H Audit Narrative</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                            {['who', 'what', 'when', 'where', 'why', 'how'].map((k) => (
                              <div key={k} className="p-2 bg-slate-800/60 rounded">
                                <div className="text-xs text-blue-400 uppercase">{k}</div>
                                <div className="text-slate-200">{evaluation.narrative_5w1h[k]}</div>
                              </div>
                            ))}
                          </div>
                          {evaluation.narrative_5w1h.summary && (
                            <div className="mt-2 p-2 bg-slate-800/60 rounded">
                              <div className="text-xs text-blue-400 uppercase">Summary</div>
                              <div className="text-slate-200">{evaluation.narrative_5w1h.summary}</div>
                            </div>
                          )}
                          {evaluation.narrative_5w1h.audit_conclusion && (
                            <div className="mt-2 p-2 bg-slate-800/60 rounded">
                              <div className="text-xs text-blue-400 uppercase">Audit Conclusion</div>
                              <div className="text-slate-200 italic">{evaluation.narrative_5w1h.audit_conclusion}</div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 px-4 py-3 rounded shadow-lg text-white z-50 ${
          toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-slate-700'
        }`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
};

export default ControlAnalysis;