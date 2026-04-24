import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/App';

// Unified "My Work" inbox — aggregates pending approvals, overdue issues,
// near-SLA issues, issues I own, and my running assessments.

const sectionStyle = {
  background: '#0f172a',
  border: '1px solid #1e293b',
  borderRadius: '12px',
  padding: '18px',
  marginBottom: '18px',
};

const headerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: '12px',
};

const countPill = (n, accent) => ({
  display: 'inline-block',
  minWidth: '22px',
  padding: '2px 8px',
  borderRadius: '999px',
  background: `${accent}26`,
  color: accent,
  fontSize: '12px',
  fontWeight: 700,
  textAlign: 'center',
});

const rowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '10px 12px',
  background: '#0b1220',
  border: '1px solid #1e293b',
  borderRadius: '8px',
  marginBottom: '8px',
  fontSize: '13px',
};

const MyWork = ({ user }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = () => api.get('/my-work').then((r) => { if (alive) setData(r.data); })
      .catch((e) => { if (alive) setErr(e?.response?.data?.detail || e.message); })
      .finally(() => { if (alive) setLoading(false); });
    load();
    const t = setInterval(load, 30000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  if (loading) {
    return (
      <div className="p-8" style={{ background: '#0b1220', minHeight: '100vh' }} data-testid="my-work-loading">
        <div style={{ color: '#94a3b8' }}>Loading your inbox…</div>
      </div>
    );
  }
  if (err) {
    return (
      <div className="p-8" style={{ background: '#0b1220', minHeight: '100vh' }} data-testid="my-work-error">
        <div style={{ color: '#f87171' }}>Failed to load: {err}</div>
      </div>
    );
  }

  const c = data?.counts || {};

  return (
    <div className="p-8" style={{ background: '#0b1220', minHeight: '100vh' }} data-testid="my-work-page">
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '12px', color: '#64748b', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            Riskshield · My Work
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, color: '#f8fafc', marginTop: '6px' }}>
            Hi {user?.full_name?.split(' ')[0] || 'there'} — here's what needs you.
          </h1>
          <div style={{ color: '#94a3b8', fontSize: '14px', marginTop: '4px' }}>
            {c.total || 0} open items across your register. Auto-refreshes every 30s.
          </div>
        </div>

        {/* Summary strip */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            marginBottom: '18px',
          }}
          data-testid="my-work-summary"
        >
          {[
            ['Pending Approvals', c.pending_approvals, '#6366f1'],
            ['Overdue Issues', c.overdue_issues, '#ef4444'],
            ['Near SLA', c.sla_breaches, '#f59e0b'],
            ['My Open Issues', c.my_open_issues, '#10b981'],
            ['Running Assessments', c.running_assessments, '#3b82f6'],
          ].map(([label, n, accent]) => (
            <div key={label} style={{ ...sectionStyle, marginBottom: 0, padding: '14px' }}>
              <div style={{ color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {label}
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: accent, marginTop: '4px' }}>{n || 0}</div>
            </div>
          ))}
        </div>

        {/* Pending approvals (LOD2/Admin) */}
        {(user.role === 'LOD2_USER' || user.role === 'ADMIN') && (
          <div style={sectionStyle} data-testid="pending-approvals-section">
            <div style={headerStyle}>
              <div style={{ color: '#e2e8f0', fontWeight: 700 }}>Controls awaiting your approval</div>
              <span style={countPill(data.pending_controls.length, '#6366f1')}>{data.pending_controls.length}</span>
            </div>
            {data.pending_controls.length === 0 ? (
              <div style={{ color: '#64748b', fontSize: '13px' }}>No controls pending review. 🎉</div>
            ) : (
              data.pending_controls.map((ctrl) => (
                <div key={ctrl.id} style={rowStyle}>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{ctrl.name}</div>
                    <div style={{ color: '#64748b', fontSize: '11px' }}>{ctrl.control_id} · {(ctrl.frameworks || []).join(', ') || '—'}</div>
                  </div>
                  <Link to="/controls-library" style={{ color: '#6366f1', fontSize: '12px' }}>Open →</Link>
                </div>
              ))
            )}
          </div>
        )}

        {/* Overdue Issues */}
        <div style={sectionStyle} data-testid="overdue-issues-section">
          <div style={headerStyle}>
            <div style={{ color: '#e2e8f0', fontWeight: 700 }}>Overdue issues</div>
            <span style={countPill(data.overdue_issues.length, '#ef4444')}>{data.overdue_issues.length}</span>
          </div>
          {data.overdue_issues.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: '13px' }}>Nothing overdue.</div>
          ) : (
            data.overdue_issues.slice(0, 10).map((it) => (
              <div key={it.id || it.issue_number} style={rowStyle}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{it.title}</div>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>
                    {it.issue_number} · due {it.due_date?.slice(0, 10) || '—'} · owner {it.owner || '—'}
                  </div>
                </div>
                <Link to="/issue-management" style={{ color: '#ef4444', fontSize: '12px' }}>View →</Link>
              </div>
            ))
          )}
        </div>

        {/* My Open Issues */}
        <div style={sectionStyle} data-testid="my-issues-section">
          <div style={headerStyle}>
            <div style={{ color: '#e2e8f0', fontWeight: 700 }}>Issues I own</div>
            <span style={countPill(data.my_open_issues.length, '#10b981')}>{data.my_open_issues.length}</span>
          </div>
          {data.my_open_issues.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: '13px' }}>No open issues assigned to you.</div>
          ) : (
            data.my_open_issues.slice(0, 10).map((it) => (
              <div key={it.id || it.issue_number} style={rowStyle}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{it.title}</div>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>
                    {it.issue_number} · status {it.status} · priority {it.priority}
                  </div>
                </div>
                <Link to="/issue-management" style={{ color: '#10b981', fontSize: '12px' }}>View →</Link>
              </div>
            ))
          )}
        </div>

        {/* Running Assessments */}
        <div style={sectionStyle} data-testid="running-assessments-section">
          <div style={headerStyle}>
            <div style={{ color: '#e2e8f0', fontWeight: 700 }}>Running assessments</div>
            <span style={countPill(data.running_assessments.length, '#3b82f6')}>{data.running_assessments.length}</span>
          </div>
          {data.running_assessments.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: '13px' }}>No background orchestrations in flight.</div>
          ) : (
            data.running_assessments.map((a) => (
              <div key={a.id} style={rowStyle}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{a.name}</div>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>
                    {a.system_name} · {a.business_unit} · {a.status}
                  </div>
                </div>
                <Link to={`/assessments/${a.id}`} style={{ color: '#3b82f6', fontSize: '12px' }}>Open →</Link>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default MyWork;
