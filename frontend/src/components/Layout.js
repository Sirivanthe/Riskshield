import { useEffect, useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { api } from '@/App';

// Helper: tiny SVG icon builder so the nav stays compact.
const Icon = ({ children }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    {children}
  </svg>
);

// Nav groups modelled on the GRC lifecycle (Plan → Assess → Test → Analyse → Remediate → Insights).
// "My Work" sits at the very top since it's the user's starting point every day.
const NAV_GROUPS = (user) => ([
  {
    key: 'core',
    label: null,
    items: [
      { to: '/', label: 'Dashboard', testid: 'nav-dashboard', exact: true, icon: (
        <Icon><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></Icon>
      )},
      { to: '/my-work', label: 'My Work', testid: 'nav-my-work', badgeKey: 'total', icon: (
        <Icon><path d="M4 4h16v4H4zM4 10h16v10H4z"/><path d="M9 14h6"/></Icon>
      )},
    ],
  },
  {
    key: 'assess',
    label: 'Plan & Assess',
    items: [
      { to: '/assessments', label: 'Assessments', testid: 'nav-assessments', icon: (
        <Icon><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></Icon>
      )},
      { to: '/tech-risk-assessment', label: 'Tech Risk Assessment', testid: 'nav-tech-risk-assessment', icon: (
        <Icon><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></Icon>
      )},
      { to: '/ai-compliance', label: 'AI Compliance', testid: 'nav-ai-compliance', icon: (
        <Icon><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></Icon>
      )},
    ],
  },
  {
    key: 'controls',
    label: 'Controls & Testing',
    items: [
      { to: '/controls-library', label: 'Controls Library', testid: 'nav-controls-library', icon: (
        <Icon><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></Icon>
      )},
      { to: '/automated-testing', label: 'Automated Testing', testid: 'nav-automated-testing', icon: (
        <Icon><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 14l2 2 4-4"/></Icon>
      )},
      { to: '/rcm-testing', label: 'RCM Testing', testid: 'nav-rcm-testing', icon: (
        <Icon><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></Icon>
      )},
    ],
  },
  {
    key: 'analysis',
    label: 'Analysis',
    items: [
      { to: '/control-analysis', label: 'Control Analysis', testid: 'nav-control-analysis', icon: (
        <Icon><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></Icon>
      )},
      { to: '/regulatory-analysis', label: 'Regulatory Analysis', testid: 'nav-regulatory-analysis', icon: (
        <Icon><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></Icon>
      )},
      { to: '/gap-remediation', label: 'Gap Remediation', testid: 'nav-gap-remediation', icon: (
        <Icon><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4M12 16h.01"/></Icon>
      )},
    ],
  },
  {
    key: 'remediation',
    label: 'Remediation',
    items: [
      { to: '/issue-management', label: 'Issue Management', testid: 'nav-issue-management', badgeKey: 'overdue_issues', icon: (
        <Icon><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></Icon>
      )},
      { to: '/workflows', label: 'Workflows', testid: 'nav-workflows', icon: (
        <Icon><path d="M13 10V3L4 14h7v7l9-11h-7z"/></Icon>
      )},
    ],
  },
  {
    key: 'insights',
    label: 'Insights',
    items: [
      { to: '/trend-analytics', label: 'Trend Analytics', testid: 'nav-trend-analytics', icon: (
        <Icon><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></Icon>
      )},
      { to: '/knowledge-graph', label: 'Knowledge Graph', testid: 'nav-knowledge-graph', icon: (
        <Icon><circle cx="12" cy="12" r="3"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M9.5 10.5L6.5 7.5M14.5 10.5L17.5 7.5M9.5 13.5L6.5 16.5M14.5 13.5L17.5 16.5"/></Icon>
      )},
      { to: '/observability', label: 'Observability', testid: 'nav-observability', icon: (
        <Icon><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></Icon>
      )},
    ],
  },
  ...(user.role === 'LOD2_USER' || user.role === 'ADMIN' ? [{
    key: 'admin',
    label: 'System',
    items: [
      { to: '/admin', label: 'Admin', testid: 'nav-admin', icon: (
        <Icon><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></Icon>
      )},
    ],
  }] : []),
]);

const Layout = ({ user, onLogout }) => {
  const [counts, setCounts] = useState({ total: 0, overdue_issues: 0 });

  useEffect(() => {
    let alive = true;
    const load = () => api.get('/my-work/count')
      .then((r) => { if (alive) setCounts(r.data); })
      .catch(() => {});
    load();
    const t = setInterval(load, 30000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const badge = (key) => {
    const n = counts?.[key];
    if (!n) return null;
    return (
      <span
        data-testid={`nav-badge-${key}`}
        style={{
          marginLeft: 'auto',
          background: key === 'overdue_issues' ? '#ef4444' : '#6366f1',
          color: 'white',
          fontSize: '10px',
          fontWeight: 700,
          padding: '2px 7px',
          borderRadius: '999px',
          minWidth: '18px',
          textAlign: 'center',
        }}
      >
        {n}
      </span>
    );
  };

  return (
    <div className="layout">
      <aside className="sidebar" data-testid="sidebar">
        <div className="sidebar-header">
          <NavLink to="/" className="sidebar-logo" data-testid="sidebar-logo">
            <div className="logo-icon">RS</div>
            <span>RiskShield</span>
          </NavLink>
          <div className="user-badge" data-testid="user-badge">
            <div className="user-name">{user.full_name}</div>
            <span className="user-role" data-testid="user-role-badge">{user.role}</span>
            {user.business_unit && (
              <div className="text-xs text-gray mt-2">{user.business_unit}</div>
            )}
          </div>
        </div>

        <nav className="sidebar-nav" data-testid="sidebar-nav">
          {NAV_GROUPS(user).map((group) => (
            <div key={group.key} style={{ marginBottom: '10px' }} data-testid={`nav-group-${group.key}`}>
              {group.label && (
                <div
                  style={{
                    fontSize: '10px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.14em',
                    color: '#64748b',
                    padding: '8px 14px 4px',
                    fontWeight: 600,
                  }}
                >
                  {group.label}
                </div>
              )}
              {group.items.map((it) => (
                <NavLink
                  key={it.to}
                  to={it.to}
                  end={it.exact}
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  data-testid={it.testid}
                  style={{ display: 'flex', alignItems: 'center', gap: '10px' }}
                >
                  {it.icon}
                  <span>{it.label}</span>
                  {it.badgeKey && badge(it.badgeKey)}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="logout-button" onClick={onLogout} data-testid="logout-button">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4m7 14l5-5-5-5m5 5H9"/>
            </svg>
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
