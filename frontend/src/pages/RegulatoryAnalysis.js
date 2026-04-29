import React, { useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const TENANT_ID = 'default';

const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const typeColor = (t) => {
  switch (t) {
    case 'MANDATORY': return 'bg-red-700';
    case 'RECOMMENDED': return 'bg-amber-700';
    case 'GOOD_TO_HAVE': return 'bg-slate-600';
    default: return 'bg-slate-600';
  }
};

const coverageColor = (s) => {
  switch (s) {
    case 'COVERED': return 'bg-green-700';
    case 'PARTIALLY_COVERED': return 'bg-yellow-700';
    case 'NOT_COVERED': return 'bg-red-700';
    default: return 'bg-slate-600';
  }
};

// AI-powered draft control generator component
const AIDraftButton = ({ gap, framework, onSaved, showToast }) => {
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);

  const generate = async () => {
    setGenerating(true);
    setDraft(null);
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/controls/generate-draft?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement_text: gap.requirement_text,
          requirement_type: gap.requirement_type,
          framework,
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
      const res = await fetch(`${API_URL}/api/control-analysis/controls/save-draft?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ control: draft }),
      });
      if (res.status >= 400) throw new Error('Save failed');
      setDraft(null);
      onSaved(gap.requirement_id);
      showToast(`Draft control added to register`, 'success');
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  if (draft) {
    return (
      <div className="mt-3 p-3 bg-slate-800 border border-blue-600 rounded space-y-2">
        <div className="text-xs text-blue-400 font-medium">AI-Generated Draft Control</div>
        <div className="text-sm text-white font-medium">{draft.name}</div>
        <div className="text-xs text-slate-400">{draft.domain} · {draft.type} · {draft.category}</div>
        <div className="text-xs text-slate-300">{(draft.description || '').slice(0, 150)}...</div>
        {draft.estimated_effort && (
          <div className="text-xs text-slate-400">
            Effort: <span className={`font-medium ${draft.estimated_effort === 'LOW' ? 'text-green-400' : draft.estimated_effort === 'MEDIUM' ? 'text-yellow-400' : 'text-red-400'}`}>{draft.estimated_effort}</span>
            {draft.risk_reduction && <span className="text-slate-400"> · {draft.risk_reduction}</span>}
          </div>
        )}
        {draft.implementation_steps?.length > 0 && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Implementation Steps:</div>
            <ol className="text-xs text-slate-300 list-decimal list-inside space-y-0.5">
              {draft.implementation_steps.slice(0, 3).map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          </div>
        )}
        <div className="flex gap-2 pt-1">
          <button onClick={save} disabled={saving}
            className="flex-1 text-xs px-3 py-1.5 rounded bg-green-700 text-white hover:bg-green-600 disabled:opacity-50">
            {saving ? 'Saving...' : '✅ Add to Control Register'}
          </button>
          <button onClick={() => setDraft(null)}
            className="text-xs px-3 py-1.5 rounded border border-slate-600 text-slate-400 hover:text-white">
            ✕ Dismiss
          </button>
        </div>
      </div>
    );
  }

  return (
    <button onClick={generate} disabled={generating}
      className="text-xs px-3 py-1.5 rounded border border-blue-500 text-blue-400 hover:bg-blue-900/20 disabled:opacity-50 whitespace-nowrap">
      {generating ? '⏳ Generating...' : 'AI Draft Control'}
    </button>
  );
};

const RegulatoryAnalysis = () => {
  const [framework, setFramework] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [toast, setToast] = useState(null);
  const [addingIds, setAddingIds] = useState(new Set());
  const [viewMode, setViewMode] = useState('gaps'); // 'gaps' | 'all'
  const fileInputRef = useRef(null);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const onPickFile = async (file) => {
    if (!file) return;
    const autoName = file.name.replace(/\.(pdf|txt|md|csv)$/i, '').replace(/[-_]+/g, ' ').trim();
    const effectiveFramework = framework.trim() || autoName || 'Uploaded Regulation';
    if (!framework.trim()) setFramework(effectiveFramework);

    const name = file.name.toLowerCase();
    if (name.endsWith('.pdf')) {
      showToast('Parsing PDF — this may take a few seconds...', 'info');
      try {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(`${API_URL}/api/rag/documents/upload`, {
          method: 'POST', body: form, headers: authHeaders(),
        });
        if (!res.ok) {
          const msg = await res.text().catch(() => '');
          throw new Error(`PDF upload failed (${res.status}) ${msg.slice(0, 160)}`);
        }
        const data = await res.json();
        const text = data.text || '';
        if (!text.trim()) throw new Error('PDF parsed but no text was extracted (scanned / image-only PDF?)');
        setContent(text);
        showToast(`PDF parsed (${text.length.toLocaleString()} chars). Click Analyze.`, 'success');
      } catch (e) {
        showToast(`PDF parse failed: ${e.message}`, 'error');
      }
    } else {
      try {
        const text = await file.text();
        setContent(text);
        showToast(`Loaded ${file.name}. Click Analyze.`, 'success');
      } catch (e) {
        showToast(`Could not read file: ${e.message}`, 'error');
      }
    }
  };

  const saveToLibrary = async (fwName, text) => {
    try {
      await fetch(`${API_URL}/api/regulations/upload`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: fwName, framework: fwName, content: text, file_name: `${fwName}.txt` }),
      });
    } catch (e) {
      console.warn('Save to library failed', e);
    }
  };

  const analyze = async () => {
    if (!framework.trim() || !content.trim()) {
      showToast('Framework name and regulation content are required', 'error');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      await saveToLibrary(framework, content);
      const res = await fetch(`${API_URL}/api/control-analysis/regulation/map?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ framework_name: framework, regulation_content: content }),
      });
      if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
      const data = await res.json();
      setResult(data);
      showToast(
        `${data.total_requirements} requirements extracted · ${data.parser_used === 'llm' ? 'LLM parser' : 'Rule-based parser'}`,
        'success'
      );
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const addSimpleDraft = async (gap) => {
    setAddingIds((s) => new Set(s).add(gap.requirement_id));
    try {
      const res = await fetch(`${API_URL}/api/control-analysis/controls?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `Control for ${gap.requirement_id}`,
          description: `Draft control created from regulatory gap: ${gap.requirement_text}`,
          domain: 'Compliance',
          type: 'ADMINISTRATIVE',
          category: 'PREVENTIVE',
          test_procedure: `Verify that "${gap.requirement_text.slice(0, 140)}" is addressed by documented procedure and owner accountability.`,
          frameworks: [gap.framework],
          source: 'REGULATORY_GAP',
          regulatory_references: [`${gap.framework} · ${gap.requirement_id}`],
        }),
      });
      if (!res.ok) throw new Error(`Add failed (${res.status})`);
      const created = await res.json();
      showToast(`Added draft control ${created.control_id}`, 'success');
      markGapResolved(gap.requirement_id);
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setAddingIds((s) => { const c = new Set(s); c.delete(gap.requirement_id); return c; });
    }
  };

  const markGapResolved = (requirementId) => {
    setResult((r) => ({
      ...r,
      gaps: (r.gaps || []).filter((g) => g.requirement_id !== requirementId),
      coverage_summary: {
        ...r.coverage_summary,
        not_covered: Math.max(0, (r.coverage_summary?.not_covered || 0) - 1),
      },
    }));
  };

  const createIssueForGap = async (gap) => {
    try {
      const res = await fetch(
        `${API_URL}/api/issue-management/?creator_id=current_user&creator_name=${encodeURIComponent('Regulatory Analysis')}`,
        {
          method: 'POST',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: `Regulatory gap: ${gap.requirement_id}`,
            description: `${gap.framework} requirement "${gap.requirement_text}" is not covered by any existing control.`,
            issue_type: gap.requirement_type === 'MANDATORY' ? 'COMPLIANCE' : 'RISK',
            severity: gap.requirement_type === 'MANDATORY' ? 'HIGH' : 'MEDIUM',
            priority: gap.requirement_type === 'MANDATORY' ? 'P1' : 'P2',
            source: 'REGULATORY_ANALYSIS',
            business_unit: 'Compliance',
          }),
        }
      );
      if (!res.ok) throw new Error(`Issue creation failed (${res.status})`);
      showToast('Issue raised in Issue Management', 'success');
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  const mandatoryCount = result?.by_requirement_type?.mandatory?.total || 0;
  const mandatoryCovered = result?.by_requirement_type?.mandatory?.covered || 0;
  const score = result?.compliance_score ?? 0;

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="regulatory-analysis-page">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">Regulatory Analysis</h1>
          <p className="text-slate-400">
            Upload a regulation, let the LLM extract and classify its requirements, map them against your control register
            and close gaps by adding AI-drafted controls or raising issues — all in one place.
          </p>
        </div>

        {/* Step 1 — Upload */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-base">1. Upload or Paste Regulation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Input
                placeholder="Framework name (e.g., RBI Cyber Security)"
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
              />
              <input ref={fileInputRef} type="file" accept=".txt,.md,.csv,.pdf" className="hidden"
                onChange={(e) => onPickFile(e.target.files?.[0])} />
              <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                📄 Upload Document (.txt/.md/.pdf)
              </Button>
              <Button onClick={analyze} disabled={loading}>
                {loading ? '⏳ Analyzing via LLM...' : '🔍 Analyze & Map to Controls'}
              </Button>
            </div>
            <textarea rows={8}
              placeholder="Paste regulation text here, or upload a document above."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white p-2 rounded text-sm" />
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <>
            {/* Step 2 — Compliance Overview */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">2. Compliance Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Score Banner */}
                <div className={`p-4 rounded-xl border ${
                  score >= 80 ? 'bg-green-900/20 border-green-600' :
                  score >= 50 ? 'bg-yellow-900/20 border-yellow-600' :
                  'bg-red-900/20 border-red-600'
                }`}>
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <div className="text-xs text-slate-400 uppercase mb-1">Compliance Score</div>
                      <div className="text-4xl font-bold text-white">{score.toFixed(1)}<span className="text-xl text-slate-400">%</span></div>
                      <div className="text-sm text-slate-400 mt-1">
                        {score >= 80 ? '✅ Good compliance coverage' :
                         score >= 50 ? '⚠️ Partial coverage — gaps need attention' :
                         '❌ Significant gaps — controls needed'}
                      </div>
                    </div>
                    <div className="text-xs text-slate-400 text-right space-y-1">
                      <div>Score = (Covered + 0.5 × Partial) / Total requirements</div>
                      <div>Parser: <span className="text-slate-300">{result.parser_used === 'llm' ? 'LLM (Gemini)' : '📐 Rule-based fallback'}</span></div>
                      <div>{result.total_requirements} requirements from <span className="text-slate-300">{result.framework}</span></div>
                    </div>
                  </div>
                </div>

                {/* Score Cards */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="bg-green-900/30 border border-green-700 p-3 rounded">
                    <div className="text-xs text-green-300">✅ Covered</div>
                    <div className="text-2xl font-bold text-white">{result.coverage_summary?.covered ?? 0}</div>
                    <div className="text-xs text-green-400">2+ controls mapped</div>
                  </div>
                  <div className="bg-yellow-900/30 border border-yellow-700 p-3 rounded">
                    <div className="text-xs text-yellow-300">⚠️ Partial</div>
                    <div className="text-2xl font-bold text-white">{result.coverage_summary?.partially_covered ?? 0}</div>
                    <div className="text-xs text-yellow-400">1 control mapped</div>
                  </div>
                  <div className="bg-red-900/30 border border-red-700 p-3 rounded">
                    <div className="text-xs text-red-300">❌ Not Covered</div>
                    <div className="text-2xl font-bold text-white">{result.coverage_summary?.not_covered ?? 0}</div>
                    <div className="text-xs text-red-400">No controls mapped</div>
                  </div>
                  <div className="bg-slate-900/60 border border-slate-600 p-3 rounded">
                    <div className="text-xs text-slate-400">📋 Mandatory</div>
                    <div className="text-2xl font-bold text-white">{mandatoryCovered}/{mandatoryCount}</div>
                    <div className="text-xs text-slate-400">covered</div>
                  </div>
                  <div className="bg-slate-900/60 border border-slate-600 p-3 rounded">
                    <div className="text-xs text-slate-400">📋 Total</div>
                    <div className="text-2xl font-bold text-white">{result.total_requirements}</div>
                    <div className="text-xs text-slate-400">requirements</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 3 — Gaps */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white text-base">
                    3. Gaps ({(result.gaps || []).length}) — Close with AI or raise issues
                  </CardTitle>
                  <div className="flex gap-2">
                    <button onClick={() => setViewMode('gaps')}
                      className={`text-xs px-3 py-1 rounded ${viewMode === 'gaps' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                      Gaps Only
                    </button>
                    <button onClick={() => setViewMode('all')}
                      className={`text-xs px-3 py-1 rounded ${viewMode === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                      All Requirements
                    </button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {viewMode === 'gaps' && (
                  <>
                    {(result.gaps || []).length === 0 ? (
                      <p className="text-slate-400">✅ No uncovered requirements. Your control register addresses this regulation well.</p>
                    ) : (
                      <div className="space-y-4">
                        {result.gaps.map((g) => (
                          <div key={g.requirement_id} className="p-4 bg-slate-900/60 rounded border border-red-800/50">
                            <div className="flex items-start justify-between gap-3 flex-wrap">
                              <div className="flex items-center gap-2">
                                <span className={`text-xs px-2 py-1 rounded text-white ${typeColor(g.requirement_type)}`}>
                                  {g.requirement_type}
                                </span>
                                <span className="text-xs text-slate-400">{g.requirement_id}</span>
                              </div>
                              <div className="flex gap-2 flex-wrap">
                                <AIDraftButton
                                  gap={g}
                                  framework={framework}
                                  onSaved={markGapResolved}
                                  showToast={showToast}
                                />
                                <button onClick={() => addSimpleDraft(g)} disabled={addingIds.has(g.requirement_id)}
                                  className="text-xs px-3 py-1.5 rounded border border-slate-500 text-slate-300 hover:border-green-500 hover:text-green-300 disabled:opacity-50">
                                  {addingIds.has(g.requirement_id) ? 'Adding...' : '📝 Quick Draft'}
                                </button>
                                <button onClick={() => createIssueForGap(g)}
                                  className="text-xs px-3 py-1.5 rounded border border-red-600 text-red-400 hover:bg-red-900/20">
                                  🚨 Raise Issue
                                </button>
                              </div>
                            </div>
                            <div className="text-slate-200 text-sm mt-2">{g.requirement_text}</div>
                            {g.gap_description && (
                              <div className="text-slate-500 text-xs mt-1">{g.gap_description}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {viewMode === 'all' && (
                  <div className="overflow-x-auto max-h-[500px]">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-slate-400 border-b border-slate-700 sticky top-0 bg-slate-800">
                          <th className="py-2 pr-3">Req ID</th>
                          <th className="pr-3">Type</th>
                          <th className="pr-3">Requirement</th>
                          <th className="pr-3">Coverage</th>
                          <th>Mapped Controls</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(result.all_mappings || []).map((m) => (
                          <tr key={m.requirement_id} className="border-b border-slate-800 hover:bg-slate-800/50">
                            <td className="py-2 pr-3 text-slate-400 font-mono text-xs">{m.requirement_id}</td>
                            <td className="pr-3">
                              <span className={`text-xs px-2 py-0.5 rounded text-white ${typeColor(m.requirement_type)}`}>
                                {m.requirement_type}
                              </span>
                            </td>
                            <td className="pr-3 text-slate-200">{(m.requirement_text || '').slice(0, 180)}</td>
                            <td className="pr-3">
                              <span className={`text-xs px-2 py-0.5 rounded text-white ${coverageColor(m.coverage_status)}`}>
                                {m.coverage_status === 'COVERED' ? '✅ COVERED' :
                                 m.coverage_status === 'PARTIALLY_COVERED' ? '⚠️ PARTIAL' : '❌ GAP'}
                              </span>
                            </td>
                            <td className="text-slate-300 text-xs">
                              {(m.mapped_controls || []).join(', ') || '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}

        {toast && (
          <div className={`fixed bottom-6 right-6 px-4 py-3 rounded shadow-lg text-white z-50 ${
            toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-slate-700'
          }`}>
            {toast.msg}
          </div>
        )}
      </div>
    </div>
  );
};

export default RegulatoryAnalysis;