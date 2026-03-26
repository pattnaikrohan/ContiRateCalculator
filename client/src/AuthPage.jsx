import { useState } from 'react';
import logo from './assets/aaw1.svg';

function RequestAccessModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({ name: '', email: '', company: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const apiUrl = import.meta.env.VITE_API_URL || '';
    try {
      const response = await fetch(`${apiUrl}/api/auth/request-access`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Request failed');
      
      onSuccess('Request sent successfully! Matt will review your access soon.');
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="glass-panel modal-content fade-in" style={{maxWidth: '400px', width: '90%'}}>
        <h2 style={{marginBottom: '0.5rem'}}>Request Access</h2>
        <p style={{fontSize: '0.8125rem', marginBottom: '1.5rem', opacity: 0.8}}>Submit your details to request an account.</p>
        
        <form onSubmit={handleSubmit} className="form-section" style={{gap: '1rem'}}>
          <div className="form-group">
            <label>Full Name</label>
            <input type="text" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Work Email</label>
            <input type="email" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Company (Optional)</label>
            <input type="text" value={formData.company} onChange={e => setFormData({...formData, company: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Additional Info (Optional)</label>
            <textarea placeholder="e.g. Industry, Role..." value={formData.message} onChange={e => setFormData({...formData, message: e.target.value})} style={{minHeight: '80px', borderRadius: '8px', padding: '0.75rem'}} />
          </div>

          {error && <div className="auth-error" style={{margin: '0.5rem 0'}}>{error}</div>}

          <div style={{display: 'flex', gap: '1rem', marginTop: '1rem'}}>
            <button type="button" onClick={onClose} className="secondary-btn" style={{flex: 1}}>Cancel</button>
            <button type="submit" className="primary-btn" style={{flex: 2}} disabled={loading}>
              {loading ? 'Sending...' : 'Send Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AuthPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRequestModal, setShowRequestModal] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    const endpoint = '/api/auth/login';
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

      onLogin(data.access_token, data.email);
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
            <h2 style={{fontSize: '1.5rem'}}>Login</h2>
            <p style={{fontSize: '0.8125rem'}}>Access your rate calculator</p>
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
              {loading ? 'Processing...' : 'Login'}
            </button>
          </form>

          <footer className="auth-footer" style={{marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', alignItems: 'center'}}>
            <button onClick={() => setShowRequestModal(true)} style={{fontSize: '0.8125rem', color: '#ff4d4d', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer'}}>
              New User? Request Access
            </button>
          </footer>
        </div>
      </div>

      {showRequestModal && (
        <RequestAccessModal 
          onClose={() => setShowRequestModal(false)} 
          onSuccess={(msg) => setSuccess(msg)} 
        />
      )}
    </div>
  );
}

export default AuthPage;
