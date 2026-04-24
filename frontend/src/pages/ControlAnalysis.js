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
  const [selectedControl, setSelectedControl] = useState(null);
  const [detailExtras, setDetailExtras] = useState(null); // {obligations, similar_controls}
  const [evaluation, setEvaluation] = useState(null);
  const [evaluating, setEvaluating] = useState(false);
  const [uplift, setUplift] = useState(null);
  const [uplifting, setUplifting] = useState(false);
  const [regulation, setRegulation] = useState({ framework_name: '', regulation_content: '' });
  const [regulationResult, setRegulationResult] = useState(null);
  const [mapping, setMapping] = useState(false);
  const [toast, setToast] = useState(null);
  const csvInputRef = useRef(null);
  const excelInputRef = useRef(null);
  const pdfInputRef = useRef(null);
  const evidenceInputRef = useRef(null);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  // (initial load handled by the filter-driven effect below)

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

  useEffect(() => {
    loadAll();
  }, [filterDomain, filterEffectiveness]); // loadAll captures latest state via closure

  const uploadFile = async (file, kind) => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_URL}/api/control-analysis/controls/import/${kind}?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        body: fd,
        headers: authHeaders(),
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
        method: 'POST',
        headers: authHeaders(),
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
        method: 'POST',
        body: fd,
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Evaluation failed (${res.status})`);
      const data = await res.json();
      setEvaluation(data);
      showToast('Evidence evaluated via LLM', 'success');
      await loadAll();
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setEvaluating(false);
    }
  };

  const runUplift = async (control) => {
    setUplifting(true);
    setUplift(null);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/controls/${control.id}/uplift?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error('Uplift failed');
      const data = await res.json();
      setUplift(data);
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
        body: JSON.stringify({
          updates: {
            name: uplift.improved.name,
            description: uplift.improved.description,
            test_procedure: uplift.improved.test_procedure,
          },
        }),
      });
      showToast('Improved language applied to control', 'success');
      setUplift(null);
      await loadAll();
      const refreshed = controls.find(c => c.id === selectedControl.id);
      if (refreshed) setSelectedControl(refreshed);
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  const mapRegulation = async () => {
    if (!regulation.framework_name || !regulation.regulation_content) {
      showToast('Framework name and content required', 'error');
      return;
    }
    setMapping(true);
    setRegulationResult(null);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/regulation/map?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(regulation),
      });
      if (!res.ok) throw new Error('Mapping failed');
      const data = await res.json();
      setRegulationResult(data);
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setMapping(false);
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

  const openControl = async (c) => {
    setSelectedControl(c);
    setEvaluation(null);
    setUplift(null);
    setDetailExtras(null);

    // Fetch enriched detail (obligations + similar_controls) and last evaluation in parallel
    try {
      const [detailRes, evalRes] = await Promise.all([
        fetch(`${API_URL}/api/control-analysis/controls/${c.id}?tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/control-analysis/evaluations?control_id=${c.id}&limit=1&tenant_id=${TENANT_ID}`, { headers: authHeaders() }),
      ]);
      const detail = await detailRes.json();
      const data = await evalRes.json();
      setDetailExtras({
        obligations: detail.obligations || [],
        similar: detail.similar_controls || [],
      });
      if (detail.control) setSelectedControl(detail.control);
      if (data.evaluations?.length) {
        setEvaluation({
          evaluation_id: data.evaluations[0].id,
          control: c,
          evaluation: data.evaluations[0].evaluation,
          narrative_5w1h: data.evaluations[0].narrative_5w1h,
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="control-analysis-page">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Control Analysis</h1>
            <p className="text-slate-400">
              Ingest, analyze and evaluate controls. Upload registers, validate evidence with AI and export audit workpapers.
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => downloadWorkpaper('pdf')} data-testid="download-pdf-workpaper" className="bg-slate-700 hover:bg-slate-600 text-white">
              Export PDF
            </Button>
            <Button onClick={() => downloadWorkpaper('excel')} data-testid="download-excel-workpaper">
              Export Excel
            </Button>
          </div>
        </div>

        {/* Import Card */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-base">Import Control Register</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-3">
            <input
              ref={csvInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              data-testid="import-csv-input"
              onChange={(e) => uploadFile(e.target.files?.[0], 'csv')}
            />
            <input
              ref={excelInputRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              data-testid="import-excel-input"
              onChange={(e) => uploadFile(e.target.files?.[0], 'excel')}
            />
            <input
              ref={pdfInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              data-testid="import-pdf-input"
              onChange={(e) => uploadFile(e.target.files?.[0], 'pdf')}
            />
            <Button
              onClick={() => csvInputRef.current?.click()}
              disabled={uploading}
              data-testid="import-csv-btn"
            >
              {uploading ? 'Uploading...' : 'Upload CSV'}
            </Button>
            <Button
              variant="outline"
              onClick={() => excelInputRef.current?.click()}
              disabled={uploading}
              data-testid="import-excel-btn"
            >
              Upload Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => pdfInputRef.current?.click()}
              disabled={uploading}
              data-testid="import-pdf-btn"
            >
              Upload PDF (LLM-extract)
            </Button>
            <Button
              variant="outline"
              onClick={importServiceNow}
              disabled={uploading}
              data-testid="import-servicenow-btn"
            >
              Import from ServiceNow (Mock)
            </Button>
            <span className="text-xs text-slate-500">
              CSV/Excel: control_id, name, description, domain, owner, type, category, test_procedure, frameworks · PDF: free-form, extracted by Claude.
            </span>
          </CardContent>
        </Card>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-700">
          {[
            { id: 'register', label: 'Register' },
            { id: 'quality', label: 'Quality' },
            { id: 'coverage', label: 'Coverage' },
            { id: 'duplicates', label: `Duplicates${duplicates.length ? ` (${duplicates.length})` : ''}` },
            { id: 'regulation', label: 'Regulation Mapping' },
          ].map((t) => (
            <button
              key={t.id}
              data-testid={`tab-${t.id}`}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm ${tab === t.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Quality tab */}
        {tab === 'quality' && quality && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="quality-panel">
            {[
              { label: 'Total Controls', value: quality.total_controls },
              { label: 'Quality Score', value: `${(quality.quality_score ?? 0).toFixed(1)} / 100` },
              { label: 'Completeness', value: `${(quality.completeness_score ?? 0).toFixed(1)}%` },
              { label: 'Uniqueness', value: `${(quality.uniqueness_score ?? 0).toFixed(1)}%` },
              { label: 'Strength', value: `${(quality.strength_score ?? 0).toFixed(1)}%` },
              { label: 'Duplicates', value: quality.duplicates_found },
              { label: 'Strong / Weak', value: `${quality.strong_controls} / ${quality.weak_controls}` },
              { label: 'Missing Descriptions', value: quality.missing_descriptions },
              { label: 'Missing Owners', value: quality.missing_owners },
              { label: 'Missing Test Procedures', value: quality.missing_test_procedures },
            ].map((m) => (
              <Card key={m.label} className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4">
                  <div className="text-xs text-slate-400">{m.label}</div>
                  <div className="text-2xl font-bold text-white">{m.value}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Coverage tab */}
        {tab === 'coverage' && coverage && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="coverage-panel">
            <CardHeader>
              <CardTitle className="text-white text-base">
                Domain Coverage ({coverage.covered_domains}/{coverage.total_domains})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-700">
                    <th className="py-2">Domain</th>
                    <th>Controls</th>
                    <th>Effective</th>
                    <th>Partial</th>
                    <th>Ineffective</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(coverage.domains).map(([domain, s]) => (
                    <tr key={domain} className="border-b border-slate-800">
                      <td className="py-2 text-white">{domain}</td>
                      <td className="text-slate-300">{s.total_controls}</td>
                      <td className="text-green-400">{s.effective || 0}</td>
                      <td className="text-yellow-400">{s.partially_effective || 0}</td>
                      <td className="text-red-400">{s.ineffective || 0}</td>
                      <td className="text-slate-300">{(s.coverage_score ?? 0).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {/* Duplicates tab */}
        {tab === 'duplicates' && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="duplicates-panel">
            <CardHeader>
              <CardTitle className="text-white text-base">Potential Duplicates</CardTitle>
            </CardHeader>
            <CardContent>
              {duplicates.length === 0 ? (
                <p className="text-slate-400">No duplicates detected.</p>
              ) : (
                <div className="space-y-3">
                  {duplicates.map((d, idx) => (
                    <div key={idx} className="p-3 bg-slate-900/50 rounded border border-slate-700">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs text-slate-400">
                          Similarity: {(d.similarity_score * 100).toFixed(1)}%
                        </span>
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

        {/* Regulation mapping tab */}
        {tab === 'regulation' && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="regulation-panel">
            <CardHeader>
              <CardTitle className="text-white text-base">Regulatory Mapping & Compliance Score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="Framework name (e.g., RBI Cyber Security)"
                value={regulation.framework_name}
                onChange={(e) => setRegulation({ ...regulation, framework_name: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="regulation-framework-input"
              />
              <textarea
                rows={8}
                placeholder="Paste regulation text. Each line is treated as a requirement."
                value={regulation.regulation_content}
                onChange={(e) => setRegulation({ ...regulation, regulation_content: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 text-white p-2 rounded text-sm"
                data-testid="regulation-content-input"
              />
              <Button onClick={mapRegulation} disabled={mapping} data-testid="map-regulation-btn">
                {mapping ? 'Mapping...' : 'Map Controls to Regulation'}
              </Button>

              {regulationResult && (
                <div className="space-y-3 pt-4 border-t border-slate-700">
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-slate-900/50 p-3 rounded">
                      <div className="text-xs text-slate-400">Compliance Score</div>
                      <div className="text-2xl font-bold text-white">{regulationResult.compliance_score}%</div>
                    </div>
                    <div className="bg-green-900/40 p-3 rounded">
                      <div className="text-xs text-green-300">Covered</div>
                      <div className="text-2xl font-bold text-white">{regulationResult.coverage_summary.covered}</div>
                    </div>
                    <div className="bg-yellow-900/40 p-3 rounded">
                      <div className="text-xs text-yellow-300">Partial</div>
                      <div className="text-2xl font-bold text-white">{regulationResult.coverage_summary.partially_covered}</div>
                    </div>
                    <div className="bg-red-900/40 p-3 rounded">
                      <div className="text-xs text-red-300">Not Covered</div>
                      <div className="text-2xl font-bold text-white">{regulationResult.coverage_summary.not_covered}</div>
                    </div>
                  </div>
                  {regulationResult.gaps?.length > 0 && (
                    <div>
                      <h4 className="text-white font-medium mb-2">Gaps ({regulationResult.gaps.length})</h4>
                      <div className="space-y-2 max-h-80 overflow-y-auto">
                        {regulationResult.gaps.slice(0, 20).map((g, i) => (
                          <div key={i} className="p-2 bg-slate-900/50 rounded text-sm text-slate-300">
                            <span className="text-xs text-red-400 mr-2">{g.requirement_type}</span>
                            {g.requirement_text.substring(0, 200)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Register tab */}
        {tab === 'register' && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="register-panel">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="text-white text-base">
                  Controls Register ({controls.length}
                  {(filterDomain || filterEffectiveness || searchQuery) ? ' filtered' : ''})
                </CardTitle>
                <div className="flex flex-wrap gap-2 items-center">
                  <Input
                    placeholder="Search control id, name, description…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white"
                    style={{ width: '260px' }}
                    data-testid="register-search"
                  />
                  <select
                    value={filterDomain}
                    onChange={(e) => setFilterDomain(e.target.value)}
                    className="bg-slate-700 border border-slate-600 text-white rounded px-2 py-1 text-sm"
                    data-testid="filter-domain"
                  >
                    <option value="">All domains</option>
                    {domains.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                  <select
                    value={filterEffectiveness}
                    onChange={(e) => setFilterEffectiveness(e.target.value)}
                    className="bg-slate-700 border border-slate-600 text-white rounded px-2 py-1 text-sm"
                    data-testid="filter-effectiveness"
                  >
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
              {/* Mini-stats */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
                {[
                  { label: 'Controls', value: controls.length },
                  { label: 'Avg Strength', value: controls.length
                      ? `${(controls.reduce((a, c) => a + (c.strength_score || 0), 0) / controls.length).toFixed(1)}`
                      : '—' },
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

              {loading ? (
                <p className="text-slate-400">Loading...</p>
              ) : controls.length === 0 ? (
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
                      {controls
                        .filter((c) => {
                          if (!searchQuery) return true;
                          const q = searchQuery.toLowerCase();
                          return ((c.control_id || '') + ' ' + (c.name || '') + ' ' + (c.description || '')).toLowerCase().includes(q);
                        })
                        .map((c) => {
                          const s = c.strength_score || 0;
                          const strengthColor = s >= 80 ? '#10b981' : s >= 60 ? '#f59e0b' : '#ef4444';
                          return (
                            <tr
                              key={c.id}
                              onClick={() => openControl(c)}
                              className="border-b border-slate-800 hover:bg-slate-800/70 cursor-pointer"
                              data-testid={`control-row-${c.control_id}`}
                            >
                              <td className="py-2 pr-3 text-white">{c.control_id}</td>
                              <td className="pr-3 text-slate-200">{c.name}</td>
                              <td className="pr-3 text-slate-300">{c.domain || '—'}</td>
                              <td className="pr-3 text-slate-300">{c.owner || '—'}</td>
                              <td className="pr-3">
                                <div className="flex items-center gap-2" title={`Strength ${s}`}>
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
                                  <span className="text-xs px-2 py-1 rounded bg-emerald-800 text-emerald-100">
                                    {c.obligations_count} mapped
                                  </span>
                                ) : (
                                  <span className="text-xs text-slate-500">—</span>
                                )}
                              </td>
                              <td>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={(e) => { e.stopPropagation(); openControl(c); }}
                                  data-testid={`open-control-${c.control_id}`}
                                >
                                  Open
                                </Button>
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

        {/* Control detail drawer */}
        {selectedControl && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="control-detail">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-white">
                    {selectedControl.control_id} — {selectedControl.name}
                  </CardTitle>
                  <div className="text-xs text-slate-400 mt-1">
                    {selectedControl.domain} · {selectedControl.type} · {selectedControl.category} · Owner: {selectedControl.owner}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => { setSelectedControl(null); setEvaluation(null); setUplift(null); }}
                  data-testid="close-control-detail"
                >
                  Close
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-xs text-slate-400">Description</div>
                <p className="text-slate-200">{selectedControl.description}</p>
              </div>
              <div>
                <div className="text-xs text-slate-400">Test Procedure</div>
                <p className="text-slate-200">{selectedControl.test_procedure || '—'}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {(selectedControl.frameworks || []).map((f) => (
                  <span key={f} className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-200">{f}</span>
                ))}
                {selectedControl.strength_score !== undefined && (
                  <span className="text-xs px-2 py-1 rounded bg-slate-900/70 text-slate-200 border border-slate-700">
                    Strength: <strong>{selectedControl.strength_score}</strong>/100
                  </span>
                )}
              </div>

              {/* Mapped Obligations */}
              {detailExtras?.obligations?.length > 0 && (
                <div className="pt-3 border-t border-slate-700" data-testid="detail-obligations">
                  <div className="text-xs text-blue-400 uppercase mb-2">Regulatory Obligations Covered ({detailExtras.obligations.length})</div>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {detailExtras.obligations.map((ob) => (
                      <div key={ob.id} className="p-2 bg-slate-900/60 rounded border border-slate-800">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs px-2 py-1 rounded text-white ${
                            ob.type === 'MANDATORY' ? 'bg-red-700' : ob.type === 'RECOMMENDED' ? 'bg-amber-700' : 'bg-slate-600'
                          }`}>{ob.type}</span>
                          <span className="text-xs text-slate-400">{ob.framework} · {ob.id}</span>
                        </div>
                        <div className="text-sm text-slate-200">{(ob.requirement_text || '').slice(0, 220)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Similar controls */}
              {detailExtras?.similar?.length > 0 && (
                <div className="pt-3 border-t border-slate-700" data-testid="detail-similar">
                  <div className="text-xs text-blue-400 uppercase mb-2">Similar Controls ({detailExtras.similar.length})</div>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {detailExtras.similar.map((s) => (
                      <div key={s.id} className="flex justify-between items-center p-2 bg-slate-900/60 rounded text-sm">
                        <div className="text-slate-200">
                          <span className="text-slate-500">{s.control_id}</span> · {s.name}
                        </div>
                        <span className="text-xs text-slate-400">similarity {(s.similarity_score * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-3 border-t border-slate-700">
                <input
                  ref={evidenceInputRef}
                  type="file"
                  accept=".txt,.md,.csv,.json,.log,.pdf"
                  className="hidden"
                  data-testid="evidence-file-input"
                  onChange={(e) => evaluateEvidence(e.target.files?.[0])}
                />
                <Button
                  onClick={() => evidenceInputRef.current?.click()}
                  disabled={evaluating}
                  data-testid="upload-evidence-btn"
                >
                  {evaluating ? 'Evaluating with LLM...' : 'Upload & Evaluate Evidence'}
                </Button>
                <Button variant="outline" onClick={() => runUplift(selectedControl)} disabled={uplifting} data-testid="uplift-btn">
                  {uplifting ? 'Improving...' : 'AI Improve Language'}
                </Button>
              </div>

              {uplift && (
                <div className="p-3 bg-slate-900/50 rounded border border-slate-700 space-y-3" data-testid="uplift-result">
                  <h4 className="text-white font-medium">AI-Suggested Improvements</h4>
                  <div>
                    <div className="text-xs text-slate-400">Improved Name</div>
                    <div className="text-slate-200">{uplift.improved.name}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Improved Description</div>
                    <div className="text-slate-200">{uplift.improved.description}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Improved Test Procedure</div>
                    <div className="text-slate-200">{uplift.improved.test_procedure}</div>
                  </div>
                  {uplift.changes_summary?.length > 0 && (
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Changes</div>
                      <ul className="list-disc list-inside text-slate-300 text-sm">
                        {uplift.changes_summary.map((c, i) => <li key={i}>{c}</li>)}
                      </ul>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Button size="sm" onClick={applyUplift} data-testid="apply-uplift-btn">Apply to Control</Button>
                    <Button size="sm" variant="outline" onClick={() => setUplift(null)}>Dismiss</Button>
                  </div>
                </div>
              )}

              {evaluation && evaluation.evaluation && (
                <div className="p-3 bg-slate-900/50 rounded border border-slate-700 space-y-3" data-testid="evaluation-result">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-3 py-1 rounded text-white ${statusColor(evaluation.evaluation.status)}`}>
                      {evaluation.evaluation.status}
                    </span>
                    <span className="text-sm text-slate-300">Confidence: {evaluation.evaluation.confidence}%</span>
                    <span className={`text-xs px-2 py-1 rounded text-white ${effectivenessColor(evaluation.evaluation.effectiveness)}`}>
                      {evaluation.evaluation.effectiveness}
                    </span>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Audit Opinion</div>
                    <div className="text-slate-100 italic">{evaluation.evaluation.audit_opinion}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Reasoning</div>
                    <div className="text-slate-200">{evaluation.evaluation.reasoning}</div>
                  </div>
                  {evaluation.evaluation.gaps?.length > 0 && (
                    <div>
                      <div className="text-xs text-red-400">Gaps</div>
                      <ul className="list-disc list-inside text-slate-300 text-sm">
                        {evaluation.evaluation.gaps.map((g, i) => <li key={i}>{g}</li>)}
                      </ul>
                    </div>
                  )}
                  {evaluation.evaluation.recommendations?.length > 0 && (
                    <div>
                      <div className="text-xs text-green-400">Recommendations</div>
                      <ul className="list-disc list-inside text-slate-300 text-sm">
                        {evaluation.evaluation.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>
                  )}

                  {evaluation.narrative_5w1h && (
                    <div className="pt-3 border-t border-slate-700" data-testid="narrative-5w1h">
                      <h4 className="text-white font-medium mb-2">5W1H Audit Narrative</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        {['who', 'what', 'when', 'where', 'why', 'how'].map((k) => (
                          <div key={k} className="p-2 bg-slate-800/60 rounded">
                            <div className="text-xs text-blue-400 uppercase">{k}</div>
                            <div className="text-slate-200">{evaluation.narrative_5w1h[k]}</div>
                          </div>
                        ))}
                      </div>
                      {evaluation.narrative_5w1h.summary && (
                        <div className="mt-3 p-2 bg-slate-800/60 rounded">
                          <div className="text-xs text-blue-400 uppercase">Summary</div>
                          <div className="text-slate-200">{evaluation.narrative_5w1h.summary}</div>
                        </div>
                      )}
                      {evaluation.narrative_5w1h.audit_conclusion && (
                        <div className="mt-3 p-2 bg-slate-800/60 rounded">
                          <div className="text-xs text-blue-400 uppercase">Audit Conclusion</div>
                          <div className="text-slate-200 italic">{evaluation.narrative_5w1h.audit_conclusion}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {toast && (
          <div
            className={`fixed bottom-6 right-6 px-4 py-3 rounded shadow-lg text-white ${
              toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-slate-700'
            }`}
            data-testid="toast"
          >
            {toast.msg}
          </div>
        )}
      </div>
    </div>
  );
};

export default ControlAnalysis;
