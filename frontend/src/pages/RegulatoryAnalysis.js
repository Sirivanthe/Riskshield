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

const RegulatoryAnalysis = () => {
  const [framework, setFramework] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [toast, setToast] = useState(null);
  const [addingIds, setAddingIds] = useState(new Set());
  const fileInputRef = useRef(null);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const onPickFile = async (file) => {
    if (!file) return;
    // Auto-derive a framework name from the filename when the user hasn't typed one
    // — removes the "set framework first" friction that was blocking uploads.
    const autoName = file.name.replace(/\.(pdf|txt|md|csv)$/i, '').replace(/[-_]+/g, ' ').trim();
    const effectiveFramework = framework.trim() || autoName || 'Uploaded Regulation';
    if (!framework.trim()) {
      setFramework(effectiveFramework);
    }

    const name = file.name.toLowerCase();
    if (name.endsWith('.pdf')) {
      showToast('Parsing PDF — this may take a few seconds...', 'info');
      try {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(`${API_URL}/api/rag/documents/upload`, {
          method: 'POST',
          body: form,
          headers: authHeaders(),
        });
        if (!res.ok) {
          const msg = await res.text().catch(() => '');
          throw new Error(`PDF upload failed (${res.status}) ${msg.slice(0, 160)}`);
        }
        const data = await res.json();
        const text = data.text || '';
        if (!text.trim()) throw new Error('PDF parsed but no text was extracted (scanned / image-only PDF?)');
        setContent(text);
        showToast(`PDF parsed (${text.length.toLocaleString()} chars). Framework: ${effectiveFramework}. Click Analyze.`, 'success');
      } catch (e) {
        showToast(`PDF parse failed: ${e.message}`, 'error');
      }
    } else {
      try {
        const text = await file.text();
        setContent(text);
        showToast(`Loaded ${file.name}. Framework: ${effectiveFramework}. Click Analyze.`, 'success');
      } catch (e) {
        showToast(`Could not read file: ${e.message}`, 'error');
      }
    }
  };

  const saveToLibrary = async (fwName, text, fileName) => {
    try {
      await fetch(`${API_URL}/api/regulations/upload`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: fwName,
          framework: fwName,
          content: text,
          file_name: fileName || `${fwName}.txt`,
        }),
      });
    } catch (e) {
      // Non-fatal — surface but don't block analysis
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
      // Save the raw regulation into the Regulations library first so it appears in Admin → Regulations
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
        `Saved to Regulations library · Extracted ${data.total_requirements} requirements (${data.parser_used === 'llm' ? 'LLM parser' : 'rule-based parser'}).`,
        'success'
      );
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const addGapAsControl = async (gap) => {
    setAddingIds((s) => new Set(s).add(gap.requirement_id));
    try {
      const name = `Control for ${gap.requirement_id}`;
      const res = await fetch(`${API_URL}/api/control-analysis/controls?tenant_id=${TENANT_ID}`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: `Draft control created from regulatory gap: ${gap.requirement_text}`,
          domain: 'Compliance',
          type: 'ADMINISTRATIVE',
          category: 'PREVENTIVE',
          test_procedure: `Verify that the requirement "${gap.requirement_text.slice(0, 140)}" is addressed by documented procedure, operating evidence and owner accountability.`,
          frameworks: [gap.framework],
          source: 'REGULATORY_GAP',
          source_file: gap.framework,
          regulatory_references: [`${gap.framework} · ${gap.requirement_id}`],
          requirement_id: gap.requirement_id,
          requirement_text: gap.requirement_text,
        }),
      });
      if (!res.ok) throw new Error(`Add failed (${res.status})`);
      const created = await res.json();
      const libTag = created.library_mirror ? ' · mirrored to Controls Library' : '';
      showToast(`Added draft control ${created.control_id} to register${libTag}`, 'success');
      // Optimistically mark gap as resolved
      setResult((r) => ({
        ...r,
        gaps: (r.gaps || []).filter((g) => g.requirement_id !== gap.requirement_id),
      }));
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setAddingIds((s) => {
        const copy = new Set(s);
        copy.delete(gap.requirement_id);
        return copy;
      });
    }
  };

  const createIssueForGap = async (gap) => {
    try {
      const url = `${API_URL}/api/issue-management/?creator_id=current_user&creator_name=${encodeURIComponent('Regulatory Analysis')}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Regulatory gap: ${gap.requirement_id}`,
          description: `Regulation ${gap.framework} requirement "${gap.requirement_text}" is not covered by any existing control.`,
          issue_type: gap.requirement_type === 'MANDATORY' ? 'COMPLIANCE' : 'RISK',
          severity: gap.requirement_type === 'MANDATORY' ? 'HIGH' : 'MEDIUM',
          priority: gap.requirement_type === 'MANDATORY' ? 'HIGH' : 'MEDIUM',
          source: 'REGULATORY_ANALYSIS',
          business_unit: 'Compliance',
        }),
      });
      if (!res.ok) throw new Error(`Issue creation failed (${res.status})`);
      showToast('Issue created', 'success');
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  const mandatoryCount = (result?.by_requirement_type?.mandatory?.total) || 0;
  const mandatoryCovered = (result?.by_requirement_type?.mandatory?.covered) || 0;

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="regulatory-analysis-page">
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Regulatory Analysis</h1>
          <p className="text-slate-400">
            Upload a regulation, let the LLM extract and classify its requirements, map them against your control register
            and close gaps by adding draft controls or raising issues — all in one place.
          </p>
        </div>

        {/* Upload card */}
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
                data-testid="reg-framework-input"
              />
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.csv,.pdf"
                className="hidden"
                data-testid="reg-file-input"
                onChange={(e) => onPickFile(e.target.files?.[0])}
              />
              <Button
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                data-testid="reg-upload-btn"
              >
                Upload Document (.txt/.md/.pdf)
              </Button>
              <Button onClick={analyze} disabled={loading} data-testid="reg-analyze-btn">
                {loading ? 'Analyzing via LLM...' : 'Analyze & Map to Controls'}
              </Button>
            </div>
            <textarea
              rows={8}
              placeholder="Paste regulation text here, or upload a document above."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white p-2 rounded text-sm"
              data-testid="reg-content-input"
            />
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <>
            <Card className="bg-slate-800/50 border-slate-700" data-testid="reg-score-panel">
              <CardHeader>
                <CardTitle className="text-white text-base">2. Compliance Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="bg-slate-900/60 p-3 rounded">
                    <div className="text-xs text-slate-400">Compliance Score</div>
                    <div className="text-2xl font-bold text-white">{result.compliance_score}%</div>
                  </div>
                  <div className="bg-green-900/40 p-3 rounded">
                    <div className="text-xs text-green-300">Covered</div>
                    <div className="text-2xl font-bold text-white">{result.coverage_summary.covered}</div>
                  </div>
                  <div className="bg-yellow-900/40 p-3 rounded">
                    <div className="text-xs text-yellow-300">Partial</div>
                    <div className="text-2xl font-bold text-white">{result.coverage_summary.partially_covered}</div>
                  </div>
                  <div className="bg-red-900/40 p-3 rounded">
                    <div className="text-xs text-red-300">Not Covered</div>
                    <div className="text-2xl font-bold text-white">{result.coverage_summary.not_covered}</div>
                  </div>
                  <div className="bg-slate-900/60 p-3 rounded">
                    <div className="text-xs text-slate-400">Mandatory</div>
                    <div className="text-xl font-semibold text-white">{mandatoryCovered} / {mandatoryCount}</div>
                  </div>
                </div>
                <div className="text-xs text-slate-500 mt-3">
                  Parser: <span className="text-slate-300">{result.parser_used === 'llm' ? 'LLM (Claude)' : 'Rule-based fallback'}</span>
                  {' · '}
                  {result.total_requirements} requirements extracted from {result.framework}
                </div>
              </CardContent>
            </Card>

            {/* Gaps */}
            <Card className="bg-slate-800/50 border-slate-700" data-testid="reg-gaps-panel">
              <CardHeader>
                <CardTitle className="text-white text-base">
                  3. Gaps ({(result.gaps || []).length}) — add to your register
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(result.gaps || []).length === 0 ? (
                  <p className="text-slate-400">No uncovered requirements. Your control register addresses this regulation well.</p>
                ) : (
                  <div className="space-y-3">
                    {result.gaps.map((g) => (
                      <div
                        key={g.requirement_id}
                        className="p-3 bg-slate-900/60 rounded border border-slate-700"
                        data-testid={`gap-${g.requirement_id}`}
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs px-2 py-1 rounded text-white ${typeColor(g.requirement_type)}`}>
                              {g.requirement_type}
                            </span>
                            <span className="text-xs text-slate-400">{g.requirement_id}</span>
                          </div>
                          <div className="flex gap-2 shrink-0">
                            <Button
                              size="sm"
                              onClick={() => addGapAsControl(g)}
                              disabled={addingIds.has(g.requirement_id)}
                              data-testid={`add-control-${g.requirement_id}`}
                            >
                              {addingIds.has(g.requirement_id) ? 'Adding...' : 'Add to Control Register'}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => createIssueForGap(g)}
                              data-testid={`add-issue-${g.requirement_id}`}
                            >
                              Create Issue
                            </Button>
                          </div>
                        </div>
                        <div className="text-slate-200 text-sm">{g.requirement_text}</div>
                        {g.gap_description && (
                          <div className="text-slate-500 text-xs mt-1">{g.gap_description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Full mapping */}
            <Card className="bg-slate-800/50 border-slate-700" data-testid="reg-all-mappings">
              <CardHeader>
                <CardTitle className="text-white text-base">4. All Requirements & Mappings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto max-h-[480px]">
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
                        <tr key={m.requirement_id} className="border-b border-slate-800">
                          <td className="py-2 pr-3 text-slate-400">{m.requirement_id}</td>
                          <td className="pr-3">
                            <span className={`text-xs px-2 py-1 rounded text-white ${typeColor(m.requirement_type)}`}>
                              {m.requirement_type}
                            </span>
                          </td>
                          <td className="pr-3 text-slate-200">{(m.requirement_text || '').slice(0, 200)}</td>
                          <td className="pr-3">
                            <span className={`text-xs px-2 py-1 rounded text-white ${
                              m.coverage_status === 'COVERED'
                                ? 'bg-green-700'
                                : m.coverage_status === 'PARTIALLY_COVERED'
                                ? 'bg-yellow-700'
                                : 'bg-red-700'
                            }`}>
                              {m.coverage_status.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="text-slate-300">
                            {(m.mapped_controls || []).join(', ') || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {toast && (
          <div
            className={`fixed bottom-6 right-6 px-4 py-3 rounded shadow-lg text-white ${
              toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-slate-700'
            }`}
            data-testid="reg-toast"
          >
            {toast.msg}
          </div>
        )}
      </div>
    </div>
  );
};

export default RegulatoryAnalysis;
