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
    <div className="min-h-screen flex" style={{ background: '#0f172a' }}>
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-md w-full" style={{ background: '#1e293b', borderRadius: '16px', padding: '48px', boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)', border: '1px solid #334155' }}>
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold" style={{ color: '#ffffff', marginBottom: '8px' }}>KPMG RISK SHIELD PLATFORM</h1>
            <p style={{ color: '#94a3b8', fontSize: '14px' }}>Multi-Agent Tech Risk & Control Assurance</p>
          </div>

          <form onSubmit={handleSubmit} data-testid="login-form">
            {error && (
              <div className="mb-4 p-3 rounded-lg" style={{ background: '#7f1d1d', color: '#fca5a5', fontSize: '14px', border: '1px solid #991b1b' }} data-testid="login-error">
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

          <div className="mt-6 pt-6" style={{ borderTop: '1px solid #475569' }}>
            <p className="text-xs text-gray text-center" style={{ color: '#94a3b8' }}>
              Demo Credentials:<br />
              LOD1: lod1@bank.com / password123<br />
              LOD2: lod2@bank.com / password123
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
