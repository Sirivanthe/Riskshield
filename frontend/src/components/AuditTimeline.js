import { useEffect, useState } from 'react';
import { api } from '@/App';

// Generic audit-trail timeline for any entity (control / assessment / issue).
// Usage: <AuditTimeline entityType="custom_control" entityId={id} />

const actionStyle = (action) => {
  const a = (action || '').toLowerCase();
  if (a.includes('approve')) return { color: '#10b981', label: 'Approved' };
  if (a.includes('reject')) return { color: '#ef4444', label: 'Rejected' };
  if (a.includes('bulk')) return { color: '#6366f1', label: 'Bulk action' };
  if (a.includes('update')) return { color: '#3b82f6', label: 'Updated' };
  if (a.includes('delete')) return { color: '#ef4444', label: 'Deleted' };
  return { color: '#94a3b8', label: action || 'Event' };
};

const AuditTimeline = ({ entityType, entityId, onClose }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!entityType || !entityId) return;
    api.get(`/audit/${entityType}/${entityId}`)
      .then((r) => setEvents(r.data.events || []))
      .catch((e) => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, [entityType, entityId]);

  const human = (iso) => {
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <div
      data-testid="audit-timeline"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(2,6,23,0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 'min(640px, 92vw)',
          maxHeight: '80vh',
          background: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '14px',
          padding: '22px',
          overflow: 'auto',
          color: '#e2e8f0',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ fontSize: '14px', fontWeight: 700 }}>Audit trail · {entityType} · {entityId?.slice(0, 8)}…</div>
          <button
            onClick={onClose}
            data-testid="audit-close"
            style={{ background: 'transparent', color: '#64748b', border: 'none', fontSize: '18px', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>

        {loading && <div style={{ color: '#64748b', fontSize: '13px' }}>Loading timeline…</div>}
        {err && <div style={{ color: '#f87171', fontSize: '13px' }}>Failed: {err}</div>}
        {!loading && !err && events.length === 0 && (
          <div style={{ color: '#64748b', fontSize: '13px' }}>No audit events recorded for this entity yet.</div>
        )}

        {events.map((ev, idx) => {
          const a = actionStyle(ev.action);
          const changed = ev.details?.changed_fields || [];
          return (
            <div
              key={idx}
              data-testid={`audit-event-${idx}`}
              style={{
                borderLeft: `3px solid ${a.color}`,
                paddingLeft: '12px',
                marginBottom: '14px',
                paddingBottom: '12px',
                borderBottom: '1px solid #1e293b',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ color: a.color, fontWeight: 700, fontSize: '13px' }}>{a.label}</span>
                <span style={{ color: '#64748b', fontSize: '11px' }}>{human(ev.created_at)}</span>
              </div>
              <div style={{ color: '#cbd5e1', fontSize: '12px', marginTop: '4px' }}>
                {ev.actor_email || 'system'}
                {ev.actor_role ? <span style={{ color: '#64748b' }}> · {ev.actor_role}</span> : null}
              </div>
              {changed.length > 0 && (
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                  Changed: <span style={{ color: '#cbd5e1' }}>{changed.join(', ')}</span>
                </div>
              )}
              {ev.details?.reason && (
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                  Reason: <span style={{ color: '#cbd5e1' }}>{ev.details.reason}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AuditTimeline;
