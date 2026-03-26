import { useState, useEffect } from 'react';
import logo from './assets/aaw1.svg';
import AuthPage from './AuthPage';
import './index.css';

const ORIGIN = "Continental - Bayswater, VIC";
const DESTINATIONS = [
  { value: "", label: "— Select Destination —" },
  { value: "seafreight", label: "Perth" },
  { value: "hazelmere", label: "Perth Metro – Hazelmere / Kenwick / Welshpool" },
  { value: "bullsbrook", label: "Perth Metro – Bullsbrook" },
  { value: "boddington", label: "Perth Metro – Boddington / Huntley" },
  { value: "mtwhaleback", label: "Mt Whaleback (1,230 km)" },
  { value: "jimblebar", label: "Jimblebar (1,270 km)" },
  { value: "southflank", label: "South Flank (1,365 km)" },
  { value: "christmascreek", label: "Christmas Creek (1,374 km)" },
  { value: "tomprice", label: "Tom Price (1,510 km)" },
  { value: "westangeles", label: "West Angeles (1,357 km)" },
  { value: "yandi", label: "Yandi (1,390 km)" },
  { value: "cloudbreak", label: "Cloudbreak (1,400 km)" },
  { value: "eliwana", label: "Eliwana (1,630 km)" },
  { value: "areac", label: "Area C (1,360 km)" },
  { value: "andersonpoint", label: "Anderson Point (1,670 km)" },
  { value: "solomon", label: "Solomon (1,550 km)" },
];

function fmt(n) {
  return '$' + Math.round(n).toLocaleString('en-AU');
}

function TariffModal({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || '';
    fetch(`${apiUrl}/api/tariff`)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="modal-overlay" style={{ zIndex: 2000 }}>
      <div className="glass-panel modal-content fade-in" style={{ maxWidth: '1100px', width: '95%', maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>Full Pricing Schedule (2026)</h2>
          <button onClick={onClose} className="secondary-btn" style={{ padding: '0.5rem 1rem' }}>Close</button>
        </div>

        {loading ? (
          <div className="state-container"><div className="loader"></div></div>
        ) : data ? (
          <div className="tariff-container">
            <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', minWidth: '800px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'left', background: 'var(--glass-bg)' }}>
                    <th style={{ padding: '0.75rem' }}>Weight (T)</th>
                    <th style={{ padding: '0.75rem' }}>Mel Cart</th>
                    <th style={{ padding: '0.75rem' }}>S/F Rate</th>
                    {Object.keys(data.mine_keys).map(k => (
                      <th key={k} style={{ padding: '0.75rem', textTransform: 'capitalize' }}>{k.replace('mtwhaleback','Mt Whlbk').replace('christmascreek','Xmas Crk').replace('andersonpoint','And. Pt')}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.tariff.map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--glass-border)' }}>
                      <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>{row.w}</td>
                      <td style={{ padding: '0.5rem 0.75rem' }}>{fmt(row.melCart)}</td>
                      <td style={{ padding: '0.5rem 0.75rem' }}>${row.combined}</td>
                      {Object.keys(data.mine_keys).map(k => (
                        <td key={k} style={{ padding: '0.5rem 0.75rem' }}>{fmt(row.mineRates[data.mine_keys[k]])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="section-divider"></div>
            <h3 style={{ margin: '1.5rem 0 1rem' }}>TERMS & CONDITIONS</h3>
            <div style={{ fontSize: '0.8125rem', opacity: 0.8, lineHeight: 1.6 }}>
                <p>• Seafreight calculated on FRT basis — weight (T) or CBM whichever is greater.</p>
                <p>• Melbourne crane cost ($1,975) applied for reels &gt; 30T.</p>
                <p>• Fremantle crane ($500-700) applied to all Perth deliveries.</p>
                <p>• 38% Fuel Surcharge applied to all transport rates.</p>
                <p>• Pilot vehicles ($400) and Western Power permits ($400) applied where applicable.</p>
                <p>• All work performed under AAW Global Logistics Pty Ltd standard conditions.</p>
            </div>
          </div>
        ) : (
          <p>Unable to retrieve pricing data at this time.</p>
        )}
      </div>
    </div>
  );
}

function CalculatorApp({ token, userEmail, onLogout }) {
  const [theme, setTheme] = useState('dark');
  const [showTariff, setShowTariff] = useState(false);
  const [formData, setFormData] = useState({
    origin: 'melbourne',
    dest: '',
    weight: '',
    reels: 1,
    dimL: '',
    dimW: '',
    dimH: ''
  });

  const [cbmDisplay, setCbmDisplay] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const { dimL, dimW, dimH, weight } = formData;
    const L = parseFloat(dimL);
    const W = parseFloat(dimW);
    const H = parseFloat(dimH);
    const wRaw = parseFloat(weight);

    if (!isNaN(L) && !isNaN(W) && !isNaN(H) && L > 0 && W > 0 && H > 0) {
      const cbm = (L / 100) * (W / 100) * (H / 100);
      let basisText = '';
      let isCbmGreater = false;
      if (!isNaN(wRaw) && wRaw > 0) {
        if (cbm > wRaw) {
          basisText = 'CBM Basis';
          isCbmGreater = true;
        } else {
          basisText = 'Weight Basis';
        }
      }
      setCbmDisplay({ val: cbm.toFixed(3), isCbmGreater, basisText });
    } else {
      setCbmDisplay(null);
    }
  }, [formData.dimL, formData.dimW, formData.dimH, formData.weight]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    const w = parseFloat(formData.weight);
    const L = parseFloat(formData.dimL);
    const W = parseFloat(formData.dimW);
    const H = parseFloat(formData.dimH);

    if (!formData.dest || isNaN(w) || w <= 0 || isNaN(L) || L <= 0 || isNaN(W) || W <= 0 || isNaN(H) || H <= 0) {
      setResult(null);
      setError(null);
      return;
    }

    const timer = setTimeout(() => {
      setLoading(true);
      setError(null);
      const apiUrl = import.meta.env.VITE_API_URL || '';
      fetch(`${apiUrl}/api/calculate`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })
      .then(res => {
        if (res.status === 401) {
            onLogout();
            throw new Error("Session expired. Please login again.");
        }
        return res.json();
      })
      .then(data => {
        if (data.error) {
          setError(data.error);
          setResult(null);
        } else {
          setResult(data);
        }
      })
      .catch(err => {
        setError(err.message || "Failed to connect to backend server.");
      })
      .finally(() => {
        setLoading(false);
      });
    }, 500);

    return () => clearTimeout(timer);
  }, [formData, token, onLogout]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="brand-section">
          <img src={logo} alt="AAW Logo" className="brand-logo" />
          <div className="brand-text">
            <h1>Coastal Conveyor Reel Estimator</h1>
          </div>
        </div>
        <div className="meta-info">
          <div style={{fontWeight: 500, color: 'var(--text-main)', marginBottom: '0.25rem'}}>{userEmail}</div>
          <div>Valid: 01/01/2026 – 31/12/2026</div>
          <div style={{display: 'flex', gap: '0.75rem', alignItems: 'center', marginTop: '0.5rem'}}>
            <button className="theme-toggle" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} title="Toggle Theme">
                {theme === 'dark' ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                )}
            </button>
            <button className="theme-toggle" onClick={onLogout} title="Logout" style={{color: '#f87171', borderColor: 'rgba(248, 113, 113, 0.2)'}}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <section className="input-side">
          <div className="glass-panel form-section">
            <h2 className="panel-title">Shipment Parameters</h2>
            
            <div className="input-row">
              <div className="form-group">
                <label>Origin Location</label>
                <select name="origin" value={formData.origin} onChange={handleChange} disabled>
                  <option value="melbourne">{ORIGIN}</option>
                </select>
              </div>
              <div className="form-group">
                <label>Destination Location</label>
                <select name="dest" value={formData.dest} onChange={handleChange} required>
                  {DESTINATIONS.map(d => (
                    <option key={d.value} value={d.value}>{d.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="section-divider"></div>

            <h2 className="panel-title">Reel Specifications</h2>
            
            <div className="input-row">
              <div className="form-group">
                <label>Weight (T)</label>
                <input type="number" name="weight" min="1" max="59" step="0.5" placeholder="e.g. 20" value={formData.weight} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Quantity</label>
                <input type="number" name="reels" min="1" max="20" step="1" value={formData.reels} onChange={handleChange} required />
              </div>
            </div>

            <div className="form-group" style={{marginTop: '0.25rem'}}>
              <label>Dimensions in cm (L × W × H)</label>
              <div className="dimensions-container">
                <input type="number" name="dimL" min="1" step="1" placeholder="L" value={formData.dimL} onChange={handleChange} required />
                <span className="dim-sep">×</span>
                <input type="number" name="dimW" min="1" step="1" placeholder="W" value={formData.dimW} onChange={handleChange} required />
                <span className="dim-sep">×</span>
                <input type="number" name="dimH" min="1" step="1" placeholder="H" value={formData.dimH} onChange={handleChange} required />
              </div>
            </div>

            {cbmDisplay && (
              <div className="insight-box fade-in">
                <div>
                  <span className="insight-val">{cbmDisplay.val}</span>
                  <span className="insight-unit"> m³ per reel</span>
                </div>
                {cbmDisplay.basisText && (
                  <span className={`badge ${cbmDisplay.isCbmGreater ? 'cbm' : 'weight'}`}>
                    {cbmDisplay.basisText}
                  </span>
                )}
              </div>
            )}

          </div>
        </section>

        <aside className="results-side">
          <div className="glass-panel results-panel">
            
            {loading && !result && (
              <div className="state-container fade-in">
                <div className="loader"></div>
                <p>Computing rate algorithm...</p>
              </div>
            )}

            {!loading && !result && !error && (
              <div className="state-container fade-in">
                <div className="state-icon">❖</div>
                <p>Provide shipment parameters to instantiate the cost breakdown.</p>
              </div>
            )}

            {error && (
              <div className="state-container fade-in">
                <div className="state-icon" style={{color: '#f87171'}}>⚠</div>
                <p>{error}</p>
              </div>
            )}

            {result && (
              <div className="fade-in">
                <div className="results-header">
                  <h2>Cost Breakdown</h2>
                  <p className="results-meta">
                    {result.reels} Unit{result.reels > 1 ? 's' : ''} • {result.weightRaw}T • Frt Basis: {result.basisLabel}
                  </p>
                </div>

                <div className="pricing-lines">
                  {result.lines.map((line, idx) => (
                    <div key={idx} className={`line ${line.muted ? 'muted' : ''} ${line.crane || line.fuel ? 'highlight' : ''}`}>
                      <span className="line-name">{line.label}</span>
                      <span className="line-cost">{fmt(line.value)}</span>
                    </div>
                  ))}
                </div>

                <div className="total-wrapper">
                  <span className="total-title">Freight Estimate excl GST</span>
                  <span className="total-amount">{fmt(result.total)}</span>
                </div>

                <div className="terms-mini">
                  * Demurrage applicable at ${result.demurr}/hr post free time. 
                  This is an AI estimation interface. Final pricing is strictly as agreed in the MF commercial tender.
                </div>
              </div>
            )}

          </div>
        </aside>

      </main>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '-0.5rem', marginBottom: '0.5rem' }}>
        <button onClick={() => setShowTariff(true)} className="secondary-btn" style={{ padding: '0.625rem 1.25rem', fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '14px', height: '14px' }}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            Full Tariff Schedule
        </button>
      </div>

      {result && (
        <section className="terms-section glass-panel fade-in">
          <h3 className="terms-title">TERMS & CONDITIONS</h3>
          <ul className="terms-list">
            <li>Seafreight calculated on FRT basis — weight (T) or CBM whichever is greater, at a 1:1 ratio per reel.</li>
            <li>Seafreight rates subject to fluctuation in BAF, coastal surcharge & local charges. Offer basis 2 units per Mafi trailer. Subject to available equipment and vessel schedule.</li>
            <li className={result?.crane_applies ? "terms-highlight" : ""}>Melbourne crane cost is an average assumption of $1,975 per reel for reels over 30T. Actual cost determined by terminal operator. Melbourne has fork capacity to approx. 31T subject to reel dimensions.</li>
            <li>Fremantle crane subject to availability. If unavailable, a mobile crane will be required at cost + 10%. Crane rates reviewed by terminal operator 30 June or as required. Basis vessel discharge at Berth 11 & 12.</li>
            <li>Destination transport rates are base rates ex Fremantle Port. A 38% fuel surcharge is applied on top and reviewed monthly.</li>
            <li className={result?.wp_applies ? "terms-highlight" : ""}>Western Power permit ($400 per reel) applicable for reels above 360 cm in height. Applied as a mandatory charge.</li>
            <li>Port booking fee of $50 per reel applies to all Perth metro and mine site deliveries.</li>
            <li className={result?.pilot_applies ? "terms-highlight" : ""}>Pilot vehicles apply at $400 per reel for movements between 0100–0600hrs on reels 34T–52T.</li>
            <li className="terms-highlight">Mine site deliveries allow 5hrs across port & mine site. Time starts from gate entry. Demurrage rate: {result ? fmt(result.demurr) : '$320'}/hr after free time allowance.</li>
            <li>Transport trailers subject to availability. Max loaded height ex Fremantle is 5.8m (incl. 1m for trailer).</li>
            <li>10% GST applicable where applicable. All work performed under AAW Global Logistics Pty Ltd general terms & conditions, available upon request.</li>
            <li className="terms-highlight">This is an estimation only. Final rates applied as per conditions agreed in MF tender.</li>
          </ul>
        </section>
      )}

      {showTariff && <TariffModal onClose={() => setShowTariff(false)} />}
    </div>
  );
}

function App() {
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail'));

    const handleLogin = (newToken, email) => {
        setToken(newToken);
        setUserEmail(email);
        localStorage.setItem('token', newToken);
        localStorage.setItem('userEmail', email);
    };

    const handleLogout = () => {
        setToken(null);
        setUserEmail(null);
        localStorage.removeItem('token');
        localStorage.removeItem('userEmail');
    };

    if (!token) {
        return <AuthPage onLogin={handleLogin} />;
    }

    return <CalculatorApp token={token} userEmail={userEmail} onLogout={handleLogout} />;
}

export default App;

