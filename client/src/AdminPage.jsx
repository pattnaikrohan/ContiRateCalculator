import { useState, useEffect } from 'react';

/* ── helpers ── */
function fmt(n) { return '$' + Math.round(n).toLocaleString('en-AU'); }

const SURCHARGE_GROUPS = {
  'Fuel Surcharges': ['DEST_FUEL_SURCHARGE', 'ORIGIN_FUEL_SURCHARGE'],
  'Crane & Lifting': ['CRANE_MEL_PER_REEL', 'FREM_CRANE_LIGHT', 'FREM_CRANE_HEAVY'],
  'Fees & Permits': ['PORT_FEE_PER_REEL', 'WP_PERMIT_PER_REEL'],
  'Tax': ['GST_RATE'],
};

// Fallback defaults — shown if the API returns empty constants
const DEFAULT_CONSTANTS = {
  DEST_FUEL_SURCHARGE:   0.43,
  ORIGIN_FUEL_SURCHARGE: 0.18,
  CRANE_MEL_PER_REEL:    1975,
  FREM_CRANE_LIGHT:      500,
  FREM_CRANE_HEAVY:      700,
  PORT_FEE_PER_REEL:     50,
  WP_PERMIT_PER_REEL:    400,
  GST_RATE:              0.10,
};

/* ── component ── */
function AdminPage({ token, onBack }) {
  const [activeTab, setActiveTab] = useState('surcharges');
  const [config, setConfig] = useState(null);
  const [prevTable, setPrevTable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({});
  const [tableData, setTableData] = useState([]);
  const [successMsg, setSuccessMsg] = useState('');


  const apiUrl = import.meta.env.VITE_API_URL || '';

  useEffect(() => { fetchConfig(); }, []);

  const fetchConfig = () => {
    setLoading(true);
    fetch(`${apiUrl}/api/admin/tariff-config`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => { if (!r.ok) throw new Error('Failed to load config'); return r.json(); })
      .then(data => {
        const constants = Object.keys(data.constants || {}).length > 0
          ? data.constants
          : DEFAULT_CONSTANTS;
        setConfig(constants);
        setFormData(constants);
        const copy = JSON.parse(JSON.stringify(
          (data.tariff_table && data.tariff_table.length > 0) ? data.tariff_table : []
        ));
        setTableData(copy);
        setPrevTable(JSON.parse(JSON.stringify(
          (data.tariff_table && data.tariff_table.length > 0) ? data.tariff_table : []
        )));
        setLoading(false);
      })
      .catch(err => { setError(err.message); setLoading(false); });
  };

  const handleSurchargeChange = (key, val) =>
    setFormData(prev => ({ ...prev, [key]: val }));

  const handleTableChange = (rowIndex, field, value) => {
    const newData = [...tableData];
    const val = parseFloat(value) || 0;
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      newData[rowIndex][parent][child] = val;
    } else {
      newData[rowIndex][field] = val;
    }
    setTableData(newData);
  };

  const saveSurcharges = () => {
    const changes = {};
    Object.keys(formData).forEach(k => {
      if (formData[k] !== config[k]) changes[k] = parseFloat(formData[k]);
    });
    if (Object.keys(changes).length === 0) { setEditMode(false); return; }
    fetch(`${apiUrl}/api/admin/save-surcharges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ changes, previous: config }),
    })
      .then(r => r.json())
      .then(() => {
        setSuccessMsg('Values updated. Notification sent.');
        setConfig(formData);
        setEditMode(false);
        setTimeout(() => setSuccessMsg(''), 3500);
      });
  };

  const saveTable = () => {
    fetch(`${apiUrl}/api/admin/save-tariff-table`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ rows: tableData, previous: prevTable }),
    })
      .then(r => r.json())
      .then(() => {
        setSuccessMsg('Tariff table saved. Notification sent.');
        setPrevTable(JSON.parse(JSON.stringify(tableData)));
        setEditMode(false);
        setTimeout(() => setSuccessMsg(''), 3500);
      })
      .catch(err => alert('Save failed: ' + err.message));
  };

  /* ── loading / error ── */
  if (loading) return <div className="state-container"><div className="loader" /></div>;
  if (error) return <div className="state-container"><p style={{ color: '#f87171' }}>{error}</p></div>;

  /* ── render ── */
  return (
    <div className="admin-container fade-in" style={{ padding: '1.5rem 2rem', maxWidth: '1600px', margin: '0 auto', color: 'var(--text-main)' }}>

      {/* ── Top bar ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <button onClick={onBack} className="secondary-btn"
            style={{ padding: '0.45rem 1rem', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            ← Back
          </button>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Tariff Administration</h1>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Manage live rate tables and surcharges</p>
          </div>
        </div>
        {successMsg && (
          <div style={{ padding: '0.6rem 1.25rem', background: 'rgba(52,211,153,0.15)', border: '1px solid #10b981', borderRadius: '8px', fontSize: '0.875rem', color: '#34d399', fontWeight: 600 }}>
            ✓ {successMsg}
          </div>
        )}
      </div>

      {/* ── Tab bar ── */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--glass-border)', marginBottom: '1.75rem' }}>
        {[['surcharges', '⚙️ Surcharges & Fees'], ['table', '📊 Tariff Table']].map(([id, label]) => (
          <button key={id}
            onClick={() => { setActiveTab(id); setEditMode(false); }}
            style={{
              padding: '0.75rem 1.5rem', background: 'none', border: 'none', cursor: 'pointer',
              fontWeight: 600, fontSize: '0.9rem', fontFamily: 'inherit',
              color: activeTab === id ? 'var(--accent)' : 'var(--text-muted)',
              borderBottom: activeTab === id ? '2px solid var(--accent)' : '2px solid transparent',
              transition: 'all 0.2s', marginBottom: '-1px',
            }}>
            {label}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════ SURCHARGES TAB ══════════════════════════════ */}
      {activeTab === 'surcharges' && (
        <div className="glass-panel fade-in" style={{ padding: '1.75rem 2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', gap: '2rem' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Global Rate Constants       </h2>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}></p>
            </div>
            {!editMode ? (
              <button onClick={() => setEditMode(true)} className="secondary-btn"
                style={{ padding: '0.35rem 0.85rem', fontSize: '0.78rem' }}>
                ✏️ Edit Constants
              </button>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => { setEditMode(false); setFormData(config); }} className="secondary-btn"
                  style={{ padding: '0.35rem 0.85rem', fontSize: '0.78rem' }}>
                  Cancel
                </button>
                <button onClick={saveSurcharges} className="primary-btn"
                  style={{ padding: '0.35rem 0.85rem', fontSize: '0.78rem' }}>
                  💾 Save & Notify
                </button>
              </div>
            )}
          </div>

          {/* Grouped surcharge sections */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {Object.entries(SURCHARGE_GROUPS).map(([groupName, keys]) => {
              const groupKeys = keys.filter(k => formData[k] !== undefined);
              if (!groupKeys.length) return null;
              return (
                <div key={groupName}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-muted)', marginBottom: '0.65rem', paddingBottom: '0.4rem', borderBottom: '1px solid var(--glass-border)' }}>
                    {groupName}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
                    {groupKeys.map(key => {
                      const isPct = key.includes('FUEL') || key.includes('GST');
                      const label = key.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
                      const isChanged = formData[key] !== config[key];
                      const displayVal = isPct
                        ? (formData[key] * 100).toFixed(0) + '%'
                        : fmt(formData[key]);

                      return (
                        <div key={key} style={{
                          background: isChanged ? 'rgba(245,158,11,0.12)' : 'rgba(255,255,255,0.03)',
                          border: isChanged ? '1px solid rgba(245,158,11,0.35)' : '1px solid var(--glass-border)',
                          borderRadius: '10px', padding: '0.9rem 1rem', transition: 'all 0.25s',
                        }}>
                          <div style={{ fontSize: '0.72rem', opacity: 0.6, marginBottom: '0.4rem', fontWeight: 500 }}>{label}</div>
                          {!editMode ? (
                            <div style={{ fontSize: '1.45rem', fontWeight: 700 }}>{displayVal}</div>
                          ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <input
                                type="number"
                                step={isPct ? '1' : '5'}
                                value={isPct ? (formData[key] * 100).toFixed(0) : formData[key]}
                                onChange={e => {
                                  const v = parseFloat(e.target.value);
                                  handleSurchargeChange(key, isPct ? v / 100 : v);
                                }}
                                style={{ fontSize: '1.2rem', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', border: '1px solid var(--input-border)', color: 'white', borderRadius: '6px', width: '100%', fontFamily: 'inherit' }}
                              />
                              {isPct && <span style={{ fontSize: '1.1rem', fontWeight: 600, opacity: 0.7 }}>%</span>}
                            </div>
                          )}
                          {isChanged && (
                            <div style={{ fontSize: '0.68rem', color: '#fcd34d', marginTop: '0.4rem' }}>
                              Was: {isPct ? (config[key] * 100).toFixed(0) + '%' : fmt(config[key])}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ══════════════════════════════ TARIFF TABLE TAB ══════════════════════════════ */}
      {activeTab === 'table' && (
        <div className="glass-panel fade-in" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Weight Bracket Table</h2>
            {!editMode ? (
              <button onClick={() => setEditMode(true)} className="secondary-btn">Edit Grid</button>
            ) : (
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button onClick={() => { setEditMode(false); fetchConfig(); }} className="secondary-btn">Cancel</button>
                <button onClick={saveTable} className="secondary-btn" style={{ background: 'var(--accent-main)', color: 'white', border: 'none' }}>Save & Notify</button>
              </div>
            )}
          </div>

          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
            <table className="admin-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.07)', borderBottom: '1px solid var(--glass-border)' }}>
                  <th style={{ padding: '0.85rem' }}>W(T)</th>
                  <th style={{ padding: '0.85rem' }}>Mel Cart</th>
                  <th style={{ padding: '0.85rem' }}>Comb.</th>
                  <th style={{ padding: '0.85rem' }}>Dem.</th>
                  {['Hz', 'Bs', 'Bd', 'Mw', 'Ji', 'Sf', 'Cc', 'Tp', 'Wa', 'Ya', 'Cl', 'El', 'Ac', 'Ap', 'So'].map(h => (
                    <th key={h} style={{ padding: '0.85rem' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableData.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--glass-border)', background: idx % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent' }}>
                    <td style={{ padding: '0.65rem', fontWeight: 600, background: 'rgba(255,255,255,0.03)' }}>{row.w}</td>
                    {['melCart', 'combined', 'demurr'].map(f => {
                      const isChanged = row[f] !== prevTable[idx]?.[f];
                      return (
                        <td key={f} style={{ padding: '0.35rem', background: isChanged ? 'rgba(245,158,11,0.15)' : 'transparent' }}>
                          {!editMode ? (
                            f === 'combined' ? `$${row[f]}` : fmt(row[f])
                          ) : (
                            <input type="number" value={row[f]}
                              onChange={e => handleTableChange(idx, f, e.target.value)}
                              style={{ width: '55px', padding: '0.35rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white', borderRadius: '3px' }} />
                          )}
                        </td>
                      );
                    })}
                    {Object.keys(row.mineRates).sort().map(m => {
                      const isChanged = row.mineRates[m] !== prevTable[idx]?.mineRates?.[m];
                      return (
                        <td key={m} style={{ padding: '0.35rem', background: isChanged ? 'rgba(245,158,11,0.15)' : 'transparent' }}>
                          {!editMode ? (
                            fmt(row.mineRates[m])
                          ) : (
                            <input type="number" value={row.mineRates[m]}
                              onChange={e => handleTableChange(idx, `mineRates.${m}`, e.target.value)}
                              style={{ width: '55px', padding: '0.35rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white', borderRadius: '3px' }} />
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPage;
