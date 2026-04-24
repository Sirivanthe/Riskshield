import React, { useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const TENANT_ID = 'default';

const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const statusColor = (s) => {
  switch ((s || '').toUpperCase()) {
    case 'PASS': return 'bg-green-600';
    case 'PARTIAL': return 'bg-yellow-600';
    case 'FAIL': return 'bg-red-600';
    default: return 'bg-slate-600';
  }
};

const RCMTesting = () => {
  const [step, setStep] = useState(1);
  const [controls, setControls] = useState([]);
  const [procedureAnalysis, setProcedureAnalysis] = useState(null); // {results: [...]}
  const [analyzing, setAnalyzing] = useState(false);
  const [importing, setImporting] = useState(false);
  const [evidenceState, setEvidenceState] = useState({}); // control_id -> {status, evaluation, uploading}
  const [finalizing, setFinalizing] = useState(false);
  const [toast, setToast] = useState(null);
  const rcmInputRef = useRef(null);
  const evidenceInputRefs = useRef({});

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // --------- STEP 1: UPLOAD RCM ---------
  const uploadRCM = async (file) => {
    if (!file) return;
    setImporting(true);
    try {
      const kind = file.name.toLowerCase().endsWith('.csv') ? 'csv' : 'excel';
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_URL}/api/control-analysis/controls/import/${kind}?tenant_id=${TENANT_ID}`, {
        method: 'POST', body: fd, headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Import failed (${res.status})`);
      const data = await res.json();
      showToast(`Imported ${data.imported}/${data.total_rows} controls`, 'success');

      const listRes = await fetch(`${API_URL}/api/control-analysis/controls?tenant_id=${TENANT_ID}&limit=500`, { headers: authHeaders() });
      const listData = await listRes.json();
      setControls(listData.controls || []);
      setStep(2);
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setImporting(false);
    }
  };

  // --------- STEP 2: ANALYZE TEST PROCEDURES ---------
  const runProcedureAnalysis = async () => {
    if (controls.length === 0) return;
    setAnalyzing(true);
    setProcedureAnalysis(null);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/procedures/analyze-batch?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ control_ids: controls.map((c) => c.id) }),
      });
      if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
      const data = await res.json();
      setProcedureAnalysis(data);
      showToast(`Analyzed ${data.total} procedures · ${data.inadequate} with gaps`, 'success');
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const applyImprovement = async (controlId, improvedProcedure) => {
    try {
      await fetch(`${API_URL}/api/control-analysis/controls/${controlId}?tenant_id=${TENANT_ID}`, {
        method: 'PUT',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates: { test_procedure: improvedProcedure } }),
      });
      showToast('Improvement applied', 'success');
      setControls((cs) => cs.map((c) => (c.id === controlId ? { ...c, test_procedure: improvedProcedure } : c)));
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  // --------- STEP 3: UPLOAD EVIDENCE + LLM EVALUATION ---------
  const uploadEvidence = async (control, file) => {
    if (!file) return;
    setEvidenceState((s) => ({ ...s, [control.id]: { ...s[control.id], uploading: true } }));
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('control_id', control.id);
      fd.append('uploaded_by', 'current_user');
      const res = await fetch(`${API_URL}/api/control-analysis/evidence/upload?tenant_id=${TENANT_ID}`, {
        method: 'POST', body: fd, headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const data = await res.json();
      setEvidenceState((s) => ({
        ...s,
        [control.id]: {
          uploading: false,
          evaluation: data.evaluation,
          narrative_5w1h: data.narrative_5w1h,
          filename: file.name,
        },
      }));
      showToast(`Evidence evaluated for ${control.control_id}: ${data.evaluation.status}`, 'success');
    } catch (e) {
      setEvidenceState((s) => ({ ...s, [control.id]: { ...s[control.id], uploading: false } }));
      showToast(e.message, 'error');
    }
  };

  const getEvidenceRequirements = (control) => {
    // Pull from procedure analysis first; fall back to control's own stored evidence_requirements
    const analysis = procedureAnalysis?.results.find((r) => r.control_id === control.id)?.analysis;
    if (analysis?.evidence_requirements?.length) return analysis.evidence_requirements;
    return (control.evidence_requirements || []).map((e) => (typeof e === 'string' ? { item: e, why: '', type: 'other' } : e));
  };

  // --------- STEP 5: DOWNLOAD REPORTS ---------
  const downloadWorkpaper = async (format) => {
    setFinalizing(true);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/workpaper/${format}?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ control_ids: controls.map((c) => c.id) }),
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rcm_testing_workpaper.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      a.click();
      URL.revokeObjectURL(url);
      showToast(`${format.toUpperCase()} downloaded`, 'success');
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setFinalizing(false);
    }
  };

  const evalStatusCounts = () => {
    const vals = Object.values(evidenceState).map((v) => v?.evaluation?.status).filter(Boolean);
    return {
      PASS: vals.filter((s) => s === 'PASS').length,
      PARTIAL: vals.filter((s) => s === 'PARTIAL').length,
      FAIL: vals.filter((s) => s === 'FAIL' || s === 'INSUFFICIENT').length,
      pending: controls.length - vals.length,
    };
  };

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="rcm-testing-page">
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">RCM-Driven Control Testing</h1>
          <p className="text-slate-400">
            Upload an RCM → LLM gap-checks each test procedure → request targeted evidence → get a sufficiency summary → export the final workpaper (PDF + Excel with 5W1H).
          </p>
        </div>

        {/* Stepper */}
        <div className="flex items-center gap-2" data-testid="rcm-stepper">
          {[
            { n: 1, label: 'Upload RCM' },
            { n: 2, label: 'Procedure Gaps' },
            { n: 3, label: 'Evidence' },
            { n: 4, label: 'Summary' },
            { n: 5, label: 'Report' },
          ].map((s, i, arr) => (
            <React.Fragment key={s.n}>
              <button
                onClick={() => step >= s.n && setStep(s.n)}
                disabled={step < s.n}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                  step === s.n
                    ? 'bg-blue-600 text-white'
                    : step > s.n
                    ? 'bg-slate-700 text-slate-200 cursor-pointer'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
                data-testid={`step-${s.n}`}
              >
                <span className="w-5 h-5 rounded-full bg-black/30 flex items-center justify-center text-xs font-bold">
                  {step > s.n ? '✓' : s.n}
                </span>
                {s.label}
              </button>
              {i < arr.length - 1 && <div className="flex-1 h-px bg-slate-700" />}
            </React.Fragment>
          ))}
        </div>

        {/* STEP 1 */}
        {step === 1 && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader><CardTitle className="text-white text-base">1. Upload RCM (CSV or Excel)</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-slate-400 text-sm">
                Expected columns: <code className="text-slate-300">control_id, name, description, domain, owner, type, category, test_procedure, frameworks, evidence_requirements</code>
              </p>
              <input
                ref={rcmInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                className="hidden"
                data-testid="rcm-file-input"
                onChange={(e) => uploadRCM(e.target.files?.[0])}
              />
              <Button onClick={() => rcmInputRef.current?.click()} disabled={importing} data-testid="rcm-upload-btn">
                {importing ? 'Uploading...' : 'Select RCM File'}
              </Button>
              {controls.length > 0 && (
                <Button variant="outline" onClick={() => setStep(2)} data-testid="skip-to-step2">
                  Use existing {controls.length} controls →
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="procedure-analysis-card">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-white text-base">2. Test Procedure Gap Analysis ({controls.length} controls)</CardTitle>
                <div className="flex gap-2">
                  <Button onClick={runProcedureAnalysis} disabled={analyzing} data-testid="run-procedure-analysis">
                    {analyzing ? 'Analyzing with LLM...' : procedureAnalysis ? 'Re-analyze' : 'Run LLM Analysis'}
                  </Button>
                  {procedureAnalysis && (
                    <Button variant="outline" onClick={() => setStep(3)} data-testid="go-step3">Continue →</Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {procedureAnalysis ? (
                <>
                  <div className="grid grid-cols-4 gap-3 mb-4">
                    <div className="bg-slate-900/60 p-3 rounded">
                      <div className="text-xs text-slate-400">Total</div>
                      <div className="text-2xl font-bold text-white">{procedureAnalysis.total}</div>
                    </div>
                    <div className="bg-green-900/40 p-3 rounded">
                      <div className="text-xs text-green-300">Adequate</div>
                      <div className="text-2xl font-bold text-white">{procedureAnalysis.adequate}</div>
                    </div>
                    <div className="bg-red-900/40 p-3 rounded">
                      <div className="text-xs text-red-300">Gaps Found</div>
                      <div className="text-2xl font-bold text-white">{procedureAnalysis.inadequate}</div>
                    </div>
                    <div className="bg-slate-900/60 p-3 rounded">
                      <div className="text-xs text-slate-400">Avg Adequacy</div>
                      <div className="text-2xl font-bold text-white">{procedureAnalysis.avg_adequacy_score}%</div>
                    </div>
                  </div>
                  <div className="space-y-3 max-h-[560px] overflow-y-auto">
                    {procedureAnalysis.results.map((r) => (
                      <div key={r.control_id} className="p-3 bg-slate-900/60 rounded border border-slate-700" data-testid={`proc-${r.control_code}`}>
                        <div className="flex justify-between items-start gap-3 mb-2">
                          <div>
                            <div className="text-white font-medium">{r.control_code} — {r.name}</div>
                            <div className="text-xs text-slate-400">Score: {r.analysis.adequacy_score}% · {r.analysis.adequate ? 'Adequate' : 'Has gaps'}</div>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded text-white ${r.analysis.adequate ? 'bg-green-700' : 'bg-red-700'}`}>
                            {r.analysis.adequate ? 'OK' : 'GAP'}
                          </span>
                        </div>
                        {r.analysis.gaps?.length > 0 && (
                          <ul className="list-disc list-inside text-slate-300 text-sm mb-2">
                            {r.analysis.gaps.map((g, i) => <li key={i}>{g}</li>)}
                          </ul>
                        )}
                        {!r.analysis.adequate && r.analysis.suggested_improvement && (
                          <div className="bg-slate-800/80 rounded p-2 mt-2">
                            <div className="text-xs text-blue-400 mb-1">SUGGESTED IMPROVED PROCEDURE</div>
                            <div className="text-slate-200 text-sm mb-2">{r.analysis.suggested_improvement}</div>
                            <Button size="sm" onClick={() => applyImprovement(r.control_id, r.analysis.suggested_improvement)} data-testid={`apply-${r.control_code}`}>
                              Apply to Control
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-slate-400 text-sm">Click "Run LLM Analysis" to audit every test procedure for gaps. ~4 controls analysed in parallel.</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="evidence-card">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-white text-base">3. Upload Evidence per Control</CardTitle>
                <Button variant="outline" onClick={() => setStep(4)} data-testid="go-step4">Continue to Summary →</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[620px] overflow-y-auto">
                {controls.map((c) => {
                  const reqs = getEvidenceRequirements(c);
                  const ev = evidenceState[c.id];
                  return (
                    <div key={c.id} className="p-3 bg-slate-900/60 rounded border border-slate-700" data-testid={`evidence-row-${c.control_id}`}>
                      <div className="flex justify-between items-start gap-3 mb-2">
                        <div className="flex-1">
                          <div className="text-white font-medium">{c.control_id} — {c.name}</div>
                          <div className="text-xs text-slate-500 mt-1">{c.description}</div>
                        </div>
                        {ev?.evaluation && (
                          <span className={`text-xs px-2 py-1 rounded text-white ${statusColor(ev.evaluation.status)}`}>
                            {ev.evaluation.status} · {ev.evaluation.confidence}%
                          </span>
                        )}
                      </div>
                      {reqs.length > 0 && (
                        <div className="bg-slate-800/70 rounded p-2 mb-2 text-sm">
                          <div className="text-xs text-blue-400 mb-1">EVIDENCE REQUIRED</div>
                          <ul className="list-disc list-inside text-slate-300">
                            {reqs.slice(0, 5).map((r, i) => (
                              <li key={i}>
                                <span className="font-medium">{r.item}</span>
                                {r.why && <span className="text-slate-500"> — {r.why}</span>}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <input
                          ref={(el) => { evidenceInputRefs.current[c.id] = el; }}
                          type="file"
                          accept=".txt,.md,.csv,.json,.log,.pdf"
                          className="hidden"
                          data-testid={`evidence-input-${c.control_id}`}
                          onChange={(e) => uploadEvidence(c, e.target.files?.[0])}
                        />
                        <Button
                          size="sm"
                          onClick={() => evidenceInputRefs.current[c.id]?.click()}
                          disabled={ev?.uploading}
                          data-testid={`upload-evidence-${c.control_id}`}
                        >
                          {ev?.uploading ? 'Evaluating...' : ev?.filename ? 'Replace Evidence' : 'Upload Evidence'}
                        </Button>
                        {ev?.filename && <span className="text-xs text-slate-400">{ev.filename}</span>}
                      </div>
                      {ev?.evaluation && (
                        <div className="mt-2 text-xs text-slate-300">
                          <div><span className="text-slate-500">Why:</span> {ev.evaluation.audit_opinion}</div>
                          {ev.evaluation.gaps?.length > 0 && (
                            <div><span className="text-red-400">Gaps:</span> {ev.evaluation.gaps.join('; ')}</div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* STEP 4 — Summary */}
        {step === 4 && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="summary-card">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-white text-base">4. Evidence Sufficiency Summary</CardTitle>
                <Button variant="outline" onClick={() => setStep(5)} data-testid="go-step5">Generate Reports →</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-3 mb-4">
                {Object.entries(evalStatusCounts()).map(([k, v]) => (
                  <div key={k} className="p-3 bg-slate-900/60 rounded">
                    <div className="text-xs text-slate-400 uppercase">{k}</div>
                    <div className="text-2xl font-bold text-white">{v}</div>
                  </div>
                ))}
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-700">
                    <th className="py-2 pr-3">Control</th>
                    <th className="pr-3">Status</th>
                    <th className="pr-3">Why (Audit Opinion)</th>
                    <th>Gaps</th>
                  </tr>
                </thead>
                <tbody>
                  {controls.map((c) => {
                    const ev = evidenceState[c.id];
                    return (
                      <tr key={c.id} className="border-b border-slate-800" data-testid={`summary-${c.control_id}`}>
                        <td className="py-2 pr-3">
                          <div className="text-white text-xs">{c.control_id}</div>
                          <div className="text-slate-400 text-xs">{c.name}</div>
                        </td>
                        <td className="pr-3">
                          {ev?.evaluation ? (
                            <span className={`text-xs px-2 py-1 rounded text-white ${statusColor(ev.evaluation.status)}`}>
                              {ev.evaluation.status}
                            </span>
                          ) : (
                            <span className="text-xs px-2 py-1 rounded text-slate-400 bg-slate-700">No evidence</span>
                          )}
                        </td>
                        <td className="pr-3 text-slate-300 text-xs">{ev?.evaluation?.audit_opinion || '—'}</td>
                        <td className="text-xs text-slate-300">{(ev?.evaluation?.gaps || []).join('; ') || '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {/* STEP 5 — Final report */}
        {step === 5 && (
          <Card className="bg-slate-800/50 border-slate-700" data-testid="report-card">
            <CardHeader><CardTitle className="text-white text-base">5. Final Control Testing Report</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-slate-300 text-sm">
                The workpaper consolidates the control register, quality scores, every evidence evaluation and the full 5W1H audit narrative per control.
              </p>
              <div className="flex gap-3">
                <Button onClick={() => downloadWorkpaper('pdf')} disabled={finalizing} data-testid="download-pdf">
                  {finalizing ? 'Generating...' : 'Download PDF Report'}
                </Button>
                <Button variant="outline" onClick={() => downloadWorkpaper('excel')} disabled={finalizing} data-testid="download-excel">
                  Download Excel Workpaper
                </Button>
              </div>
              <div className="text-xs text-slate-500">
                Tip: the Excel workbook includes four sheets — Control Register, Quality Summary, Domain Coverage and Evidence Evaluations (with 5W1H columns).
              </div>
            </CardContent>
          </Card>
        )}

        {toast && (
          <div
            className={`fixed bottom-6 right-6 px-4 py-3 rounded shadow-lg text-white ${
              toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-slate-700'
            }`}
            data-testid="rcm-toast"
          >
            {toast.msg}
          </div>
        )}
      </div>
    </div>
  );
};

export default RCMTesting;
