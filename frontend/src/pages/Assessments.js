import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/App';
import NewAssessmentModal from '@/components/NewAssessmentModal';

const Assessments = ({ user }) => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadAssessments();
  }, []);

  // Poll every 5s while any assessment is still being orchestrated so the
  // status badge flips from IN_PROGRESS to COMPLETED/FAILED without a refresh.
  useEffect(() => {
    const anyRunning = assessments.some(
      (a) => a.status === 'IN_PROGRESS' || a.status === 'PENDING'
    );
    if (!anyRunning) return;
    const t = setInterval(loadAssessments, 5000);
    return () => clearInterval(t);
  }, [assessments]);

  const loadAssessments = async () => {
    try {
      const response = await api.get('/assessments');
      setAssessments(response.data);
    } catch (error) {
      console.error('Failed to load assessments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssessmentCreated = (newAssessment) => {
    setAssessments([newAssessment, ...assessments]);
    setShowModal(false);
  };

  const filteredAssessments = assessments.filter((assessment) => {
    if (filter === 'all') return true;
    return assessment.status === filter.toUpperCase();
  });

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="assessments-page">
      <div className="page-header">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="page-title" data-testid="assessments-title">Assessments</h1>
            <p className="page-subtitle">Manage technology risk assessments</p>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => setShowModal(true)}
            data-testid="new-assessment-button"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            New Assessment
          </button>
        </div>
      </div>

      <div className="page-content">
        {/* Filters */}
        <div className="card mb-6">
          <div className="flex gap-2">
            <button
              className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('all')}
              style={{ fontSize: '13px', padding: '8px 16px' }}
              data-testid="filter-all"
            >
              All ({assessments.length})
            </button>
            <button
              className={`btn ${filter === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('completed')}
              style={{ fontSize: '13px', padding: '8px 16px' }}
              data-testid="filter-completed"
            >
              Completed
            </button>
            <button
              className={`btn ${filter === 'in_progress' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('in_progress')}
              style={{ fontSize: '13px', padding: '8px 16px' }}
              data-testid="filter-in-progress"
            >
              In Progress
            </button>
            <button
              className={`btn ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('pending')}
              style={{ fontSize: '13px', padding: '8px 16px' }}
              data-testid="filter-pending"
            >
              Pending
            </button>
          </div>
        </div>

        {/* Assessment List */}
        {filteredAssessments.length > 0 ? (
          <div className="card">
            <table className="data-table" data-testid="assessments-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>System</th>
                  <th>Business Unit</th>
                  <th>Frameworks</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAssessments.map((assessment) => (
                  <tr key={assessment.id} data-testid={`assessment-row-${assessment.id}`}>
                    <td>
                      <div style={{ fontWeight: '600', color: '#0f172a' }}>{assessment.name}</div>
                    </td>
                    <td>{assessment.system_name}</td>
                    <td>{assessment.business_unit}</td>
                    <td>
                      <div style={{ fontSize: '12px' }}>
                        {assessment.frameworks.slice(0, 2).join(', ')}
                        {assessment.frameworks.length > 2 && (
                          <span style={{ color: '#64748b' }}> +{assessment.frameworks.length - 2}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${assessment.status.toLowerCase()}`}>
                        {assessment.status}
                      </span>
                    </td>
                    <td>
                      {assessment.summary?.overall_score !== undefined ? (
                        <span
                          style={{
                            fontWeight: '600',
                            color: assessment.summary.overall_score >= 80 ? '#059669' : assessment.summary.overall_score >= 60 ? '#f59e0b' : '#dc2626'
                          }}
                        >
                          {assessment.summary.overall_score}
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>-</span>
                      )}
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b' }}>
                      {new Date(assessment.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <Link
                        to={`/assessments/${assessment.id}`}
                        className="btn btn-outline"
                        style={{ fontSize: '13px', padding: '6px 12px' }}
                        data-testid={`view-assessment-${assessment.id}`}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card">
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3 className="empty-title">No assessments found</h3>
              <p className="empty-description">
                {filter === 'all'
                  ? 'Create your first assessment to get started'
                  : `No ${filter} assessments`}
              </p>
              {filter === 'all' && (
                <button
                  className="btn btn-primary"
                  onClick={() => setShowModal(true)}
                  data-testid="create-first-assessment-button"
                >
                  Create Assessment
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <NewAssessmentModal
          onClose={() => setShowModal(false)}
          onSuccess={handleAssessmentCreated}
        />
      )}
    </div>
  );
};

export default Assessments;
