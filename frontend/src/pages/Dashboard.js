import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/App';

// Command Center — landing hub shown immediately after login.
// Five large tiles, each linking to a self-contained workflow.

const tiles = [
  {
    id: 'control-analysis',
    title: 'Control Analysis',
    tagline: 'Register intelligence',
    description:
      'Import your control register via CSV, Excel or ServiceNow. Get quality scores, find duplicates, measure domain coverage, and upload evidence for real-time AI evaluation and 5W1H audit narratives.',
    cta: 'Open Control Analysis',
    to: '/control-analysis',
    accent: '#6366f1', // indigo
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    id: 'regulatory-analysis',
    title: 'Regulatory Analysis',
    tagline: 'Obligation to control',
    description:
      'Upload regulation documents, let AI extract mandatory and recommended requirements, map them to your existing controls, surface compliance gaps and update your risk and control register with one click.',
    cta: 'Open Regulatory Analysis',
    to: '/regulatory-analysis',
    accent: '#10b981', // emerald
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
  },
  {
    id: 'risk-assessment',
    title: 'Risk Assessment',
    tagline: 'Application and tech risk',
    description:
      'Run AI-guided application and technology risk assessments. Contextual questionnaires adapt to criticality, data classification and deployment. Generate professional PDF reports with ratings and recommendations.',
    cta: 'Open Risk Assessment',
    to: '/tech-risk-assessment',
    accent: '#f59e0b', // amber
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
  {
    id: 'control-assurance',
    title: 'Control Assurance & Testing',
    tagline: 'Guided RCM testing',
    description:
      'Upload an RCM, let the LLM gap-check every test procedure, collect the exact evidence each control needs, see instant sufficiency ratings and download the final PDF report + Excel workpaper with 5W1H.',
    cta: 'Open RCM Testing',
    to: '/rcm-testing',
    accent: '#3b82f6', // blue
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M9 12l2 2 4-4" />
        <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9c1.77 0 3.42.51 4.81 1.4" />
        <path d="M21 4v4h-4" />
      </svg>
    ),
  },
  {
    id: 'issue-management',
    title: 'Issue Management',
    tagline: 'Findings to closure',
    description:
      'Track, assign and resolve findings end-to-end. Full case history, SLA tracking, ServiceNow sync and seamless linkage back to risks, controls and test results.',
    cta: 'Open Issue Management',
    to: '/issue-management',
    accent: '#f43f5e', // rose
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
  },
];

const Dashboard = ({ user }) => {
  const firstName = (user?.full_name || '').split(' ')[0] || 'there';
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get('/system/health')
      .then((res) => { if (mounted) setHealth(res.data); })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  const statusColor = (s) => {
    if (s === 'healthy') return '#10b981';
    if (s === 'warn') return '#f59e0b';
    return '#ef4444';
  };

  const pillHref = (pill) => {
    const label = (pill.label || '').toLowerCase();
    if (label.startsWith('llm')) return '/admin?tab=llm';
    if (label.startsWith('servicenow')) return '/admin?tab=integrations';
    if (label.startsWith('rag')) return '/regulatory-analysis';
    if (label.startsWith('multi-tenancy')) return '/admin?tab=system';
    return '/admin';
  };

  return (
    <div className="p-8 min-h-screen" style={{ background: '#0f172a' }} data-testid="command-center">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div style={{ fontSize: '12px', color: '#64748b', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            RiskShield · Command Center
          </div>
          <h1 className="text-2xl font-bold text-white" style={{ marginTop: '8px', letterSpacing: '0.02em', textShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            Welcome
          </h1>
        </div>

        {/* Health strip */}
        {health && (
          <div
            className="mb-10"
            data-testid="health-strip"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '12px',
            }}
          >
            {health.pills.map((p, i) => (
              <div
                key={i}
                data-testid={`health-pill-${i}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  background: '#1e293b',
                  border: '2px solid #ffffff',
                  cursor: 'pointer',
                  transition: 'background 0.15s, transform 0.15s',
                  textAlign: 'left',
                  width: '100%',
                }}
                onClick={() => window.location.href = pillHref(p)}
                title={`${p.detail} — click to manage`}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = '#334155';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = '#1e293b';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: statusColor(p.status),
                    boxShadow: `0 0 8px ${statusColor(p.status)}99`,
                    flexShrink: 0,
                  }}
                />
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#e2e8f0' }}>
                    {p.label.replace('· EMERGENT', '').replace('· Mock', '').replace('· Empty', '').replace('· 0 tenants', '')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tiles */}
        <div
          className="grid gap-5"
          style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))' }}
          data-testid="tile-grid"
        >
          {tiles.map((t) => (
            <Link
              key={t.id}
              to={t.to}
              data-testid={`tile-${t.id}`}
              style={{
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                padding: '28px',
                borderRadius: '18px',
                background: '#1e293b',
                border: '1px solid #334155',
                textDecoration: 'none',
                color: 'inherit',
                minHeight: '260px',
                overflow: 'hidden',
                transition: 'transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-3px)';
                e.currentTarget.style.borderColor = t.accent;
                e.currentTarget.style.boxShadow = `0 12px 40px -14px ${t.accent}55`;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = '#334155';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              {/* Accent bar */}
              <div
                style={{
                  position: 'absolute',
                  top: 0, left: 0, right: 0,
                  height: '3px',
                  background: t.accent,
                  opacity: 0.85,
                }}
              />

              {/* Icon + tagline */}
              <div className="flex items-start justify-between" style={{ marginBottom: '18px' }}>
                <div
                  style={{
                    width: '52px',
                    height: '52px',
                    borderRadius: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: `${t.accent}1a`,
                    color: t.accent,
                  }}
                >
                  {t.icon}
                </div>
                <span
                  style={{
                    fontSize: '11px',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: t.accent,
                    fontWeight: 600,
                  }}
                >
                  {t.tagline}
                </span>
              </div>

              {/* Title + description */}
              <h2 style={{ fontSize: '1.35rem', color: '#f8fafc', fontWeight: 700, marginBottom: '10px' }}>
                {t.title}
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: 1.55, flex: 1 }}>
                {t.description}
              </p>

              {/* CTA */}
              <div
                style={{
                  marginTop: '22px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: t.accent,
                  fontWeight: 600,
                  fontSize: '14px',
                }}
              >
                {t.cta}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </div>
            </Link>
          ))}
        </div>

              </div>
    </div>
  );
};

export default Dashboard;
