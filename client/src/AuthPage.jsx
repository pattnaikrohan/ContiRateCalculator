import { useState } from 'react';
import logo from './assets/aaw1.svg';

function AuthPage({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
    
    const apiUrl = import.meta.env.VITE_API_URL || '';
    try {
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      if (isLogin) {
        onLogin(data.access_token, data.email);
      } else {
        setIsLogin(true);
        setSuccess('Account created! Please sign in.');
        setEmail('');
        setPassword('');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="auth-card-wrapper">
        <header className="top-bar" style={{border: 'none', justifyContent: 'center', marginBottom: '1rem'}}>
          <div className="brand-section" style={{alignItems: 'center', textAlign: 'center'}}>
            <img src={logo} alt="AAW Logo" className="brand-logo" />
            <div className="brand-text">
              <h1>Coastal Conveyor Reel Estimator</h1>
            </div>
          </div>
        </header>

        <div className="glass-panel auth-card">
          <div className="auth-header" style={{marginBottom: '1.5rem'}}>
            <h2 style={{fontSize: '1.5rem'}}>{isLogin ? 'Login' : 'Register'}</h2>
            <p style={{fontSize: '0.8125rem'}}>{isLogin ? 'Access your rate calculator' : 'Create a new operator account'}</p>
          </div>

          <form onSubmit={handleSubmit} className="form-section" style={{gap: '1rem'}}>
            <div className="form-group">
              <label style={{fontSize: '0.8125rem'}}>Email Id</label>
              <input 
                type="email" 
                placeholder="email@company.com" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
                style={{padding: '0.75rem'}}
              />
            </div>
            <div className="form-group">
              <label style={{fontSize: '0.8125rem'}}>Password</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                style={{padding: '0.75rem'}}
              />
            </div>

            {error && <div className="auth-error fade-in" style={{margin: '0.5rem 0', padding: '0.5rem'}}>{error}</div>}
            {success && <div className="auth-success fade-in" style={{margin: '0.5rem 0', padding: '0.5rem'}}>{success}</div>}

            <button type="submit" className="primary-btn auth-btn" disabled={loading} style={{padding: '0.875rem', marginTop: '0.5rem'}}>
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>

          <footer className="auth-footer" style={{marginTop: '1.5rem'}}>
            <button onClick={() => setIsLogin(!isLogin)} style={{fontSize: '0.8125rem'}}>
              {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
