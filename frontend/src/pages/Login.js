import { useState } from 'react';
import { api } from '@/App';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/auth/login', { email, password });
      onLogin(response.data.access_token, response.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (role) => {
    if (role === 'lod1') {
      setEmail('lod1@bank.com');
      setPassword('password123');
    } else {
      setEmail('lod2@bank.com');
      setPassword('password123');
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #3b82f6 100%)' }}>
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-md w-full" style={{ background: 'rgba(255, 255, 255, 0.98)', borderRadius: '16px', padding: '48px', boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)' }}>
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' }}>
              <span className="text-2xl font-bold text-white">RS</span>
            </div>
            <h1 className="text-3xl font-bold" style={{ color: '#0f172a', marginBottom: '8px' }}>RiskShield Platform</h1>
            <p style={{ color: '#64748b', fontSize: '14px' }}>Multi-Agent Tech Risk & Control Assurance</p>
          </div>

          <form onSubmit={handleSubmit} data-testid="login-form">
            {error && (
              <div className="mb-4 p-3 rounded-lg" style={{ background: '#fee2e2', color: '#991b1b', fontSize: '14px' }} data-testid="login-error">
                {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@bank.com"
                required
                data-testid="login-email-input"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                data-testid="login-password-input"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full mb-4"
              disabled={loading}
              data-testid="login-submit-button"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            <div className="grid grid-2 gap-2">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => fillDemo('lod1')}
                style={{ fontSize: '13px', padding: '8px 12px', justifyContent: 'center' }}
                data-testid="demo-lod1-button"
              >
                Demo LOD1
              </button>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => fillDemo('lod2')}
                style={{ fontSize: '13px', padding: '8px 12px', justifyContent: 'center' }}
                data-testid="demo-lod2-button"
              >
                Demo LOD2
              </button>
            </div>
          </form>

          <div className="mt-6 pt-6" style={{ borderTop: '1px solid #e5e7eb' }}>
            <p className="text-xs text-gray text-center">
              Demo Credentials:<br />
              LOD1: lod1@bank.com / password123<br />
              LOD2: lod2@bank.com / password123
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 hidden lg:flex items-center justify-center p-8" style={{ background: 'rgba(0, 0, 0, 0.2)' }}>
        <div className="max-w-lg">
          <h2 className="text-4xl font-bold text-white mb-6" style={{ fontFamily: 'IBM Plex Sans' }}>
            Enterprise-Grade<br />Risk Management
          </h2>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'rgba(255, 255, 255, 0.2)' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div>
                <h3 className="text-white font-semibold mb-1">Multi-Agent AI Assessment</h3>
                <p className="text-sm" style={{ color: 'rgba(255, 255, 255, 0.8)' }}>Automated risk identification and control testing</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'rgba(255, 255, 255, 0.2)' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div>
                <h3 className="text-white font-semibold mb-1">Regulatory Compliance</h3>
                <p className="text-sm" style={{ color: 'rgba(255, 255, 255, 0.8)' }}>NIST CSF, ISO 27001, SOC2, PCI-DSS, GDPR, Basel III</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'rgba(255, 255, 255, 0.2)' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div>
                <h3 className="text-white font-semibold mb-1">GRC Integration</h3>
                <p className="text-sm" style={{ color: 'rgba(255, 255, 255, 0.8)' }}>ServiceNow, Archer, MetricStream connectors</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
