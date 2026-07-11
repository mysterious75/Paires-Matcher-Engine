import React, { useState, useEffect } from 'react';
import './App.css';

const API = 'http://127.0.0.1:8001';

function App() {
  const [tab, setTab] = useState('overview');
  const [founders, setFounders] = useState([]);
  const [investors, setInvestors] = useState([]);
  const [matches, setMatches] = useState(null);
  const [demo, setDemo] = useState(null);
  const [selected, setSelected] = useState(null);
  const [outreach, setOutreach] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/founders`).then(r => r.json()).then(d => setFounders(d.founders));
    fetch(`${API}/api/investors`).then(r => r.json()).then(d => setInvestors(d.investors));
  }, []);

  const matchFounder = async (id) => {
    setLoading(true); setSelected(id); setOutreach(null);
    try {
      const r = await fetch(`${API}/api/match/founder/${id}?top_k=5`, { method: 'POST' });
      setMatches(await r.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const runDemo = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/demo/run`, { method: 'POST' });
      setDemo(await r.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const genOutreach = async (fId, iId) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/outreach/generate?founder_id=${fId}&investor_id=${iId}`, { method: 'POST' });
      setOutreach(await r.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <span className="nav-logo">Paires</span>
          <div className="nav-tabs">
            {['overview','founders','investors','demo','metrics'].map(t => (
              <button key={t} className={`nav-tab ${tab===t?'active':''}`} onClick={() => setTab(t)}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {tab === 'overview' && <Overview founders={founders} investors={investors} setTab={setTab} />}
      {tab === 'founders' && <Founders founders={founders} selected={selected} matchFounder={matchFounder} matches={matches} genOutreach={genOutreach} outreach={outreach} loading={loading} />}
      {tab === 'investors' && <Investors investors={investors} />}
      {tab === 'demo' && <Demo runDemo={runDemo} demo={demo} loading={loading} />}
      {tab === 'metrics' && <Metrics />}
    </div>
  );
}

/* ===== OVERVIEW ===== */
function Overview({ founders, investors, setTab }) {
  const industries = [...new Set(founders.map(f => f.industry))];
  return (
    <div>
      <div className="hero">
        <h1>Matching Engine v2</h1>
        <p>Real embeddings + SQLite. Semantic similarity as the primary scoring factor.</p>
        <div className="hero-stats">
          <div><div className="hero-stat-num">{founders.length}</div><div className="hero-stat-label">Founders</div></div>
          <div><div className="hero-stat-num">{investors.length}</div><div className="hero-stat-label">Investors</div></div>
          <div><div className="hero-stat-num">{founders.length * investors.length}</div><div className="hero-stat-label">Possible Matches</div></div>
          <div><div className="hero-stat-num">{industries.length}</div><div className="hero-stat-label">Industries</div></div>
        </div>
      </div>

      <div className="main">
        <div className="section">
          <div className="section-title">How it works</div>
          <div className="flow-steps">
            <div className="flow-step"><div className="flow-num">1</div><div className="flow-title">Profile</div><div className="flow-desc">Load founder and investor profiles with structured data</div></div>
            <div className="flow-step"><div className="flow-num">2</div><div className="flow-title">Score</div><div className="flow-desc">Multi-factor weighted scoring across 5 dimensions</div></div>
            <div className="flow-step"><div className="flow-num">3</div><div className="flow-title">Rank</div><div className="flow-desc">Rank and surface the best matches with reasoning</div></div>
            <div className="flow-step"><div className="flow-num">4</div><div className="flow-title">Outreach</div><div className="flow-desc">Generate personalized messages for each match</div></div>
          </div>
        </div>

        <div className="section">
          <div className="section-title">Scoring dimensions</div>
          <div className="weights-grid">
            <div className="weight-item"><div className="weight-pct">40%</div><div className="weight-name">Embeddings</div></div>
            <div className="weight-item"><div className="weight-pct">25%</div><div className="weight-name">Sector</div></div>
            <div className="weight-item"><div className="weight-pct">15%</div><div className="weight-name">Stage</div></div>
            <div className="weight-item"><div className="weight-pct">10%</div><div className="weight-name">Geography</div></div>
            <div className="weight-item"><div className="weight-pct">10%</div><div className="weight-name">Check Size</div></div>
          </div>
        </div>

        <div className="section">
          <div className="section-title">Try it</div>
          <div style={{display:'flex',gap:'12px',flexWrap:'wrap'}}>
            <button className="btn-hero" onClick={() => setTab('founders')}>Match a Founder</button>
            <button className="btn-hero" onClick={() => setTab('demo')} style={{background:'var(--bg3)',color:'var(--text)',border:'1px solid var(--border)'}}>Run Full Demo</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ===== FOUNDERS ===== */
function Founders({ founders, selected, matchFounder, matches, genOutreach, outreach, loading }) {
  const sel = founders.find(f => f.id === selected);
  return (
    <div style={{paddingTop:'80px'}} className="main">
      <div className="section">
        <div className="section-title">Founders</div>
        <div className="section-subtitle">Select a founder to find the best investor matches.</div>
      </div>
      <div className="split">
        <div className="profile-list">
          {founders.map(f => (
            <div key={f.id} className={`profile-item ${selected===f.id?'selected':''}`} onClick={() => matchFounder(f.id)}>
              <div className="profile-name">{f.name}</div>
              <div className="profile-company">{f.company} — {f.headline}</div>
              <div className="profile-tags">
                <span className="tag">{f.industry}</span>
                <span className="tag">{f.funding_stage}</span>
                <span className="tag">${(f.ask_amount/1e6).toFixed(0)}M</span>
              </div>
            </div>
          ))}
        </div>
        <div>
          {!matches && !loading && (
            <div className="empty"><div className="empty-icon">←</div><h3>Select a founder</h3><p>Click any founder to compute matches</p></div>
          )}
          {loading && (
            <div className="empty"><div className="spinner"></div><h3>Computing...</h3></div>
          )}
          {matches && !loading && (
            <div>
              <div className="card-header"><div><div className="card-title">Best investors for {matches.founder}</div><div className="card-subtitle">{matches.company}</div></div></div>
              {matches.matches.map((m, i) => (
                <div key={i} className="match-result">
                  <div className="match-top">
                    <div>
                      <div className="match-name">#{i+1} {m.investor}</div>
                      <div className="match-bars">
                        <div className="match-bar"><div className="match-bar-label"><span>Sector</span><span>{(m.sector_score*100).toFixed(0)}%</span></div><div className="match-bar-track"><div className="match-bar-fill green" style={{width:`${m.sector_score*100}%`}}></div></div></div>
                        <div className="match-bar"><div className="match-bar-label"><span>Stage</span><span>{(m.stage_score*100).toFixed(0)}%</span></div><div className="match-bar-track"><div className="match-bar-fill blue" style={{width:`${m.stage_score*100}%`}}></div></div></div>
                        <div className="match-bar"><div className="match-bar-label"><span>Geo</span><span>{(m.geography_score*100).toFixed(0)}%</span></div><div className="match-bar-track"><div className="match-bar-fill purple" style={{width:`${m.geography_score*100}%`}}></div></div></div>
                        <div className="match-bar"><div className="match-bar-label"><span>Check</span><span>{(m.check_size_score*100).toFixed(0)}%</span></div><div className="match-bar-track"><div className="match-bar-fill amber" style={{width:`${m.check_size_score*100}%`}}></div></div></div>
                        <div className="match-bar"><div className="match-bar-label"><span>Embedding</span><span>{(m.embedding_score*100).toFixed(0)}%</span></div><div className="match-bar-track"><div className="match-bar-fill green" style={{width:`${m.embedding_score*100}%`}}></div></div></div>
                      </div>
                    </div>
                    <div className="match-score">{(m.overall_score*100).toFixed(0)}%</div>
                  </div>
                  {m.match_reasons.map((r, j) => <div key={j} className="match-reason">• {r}</div>)}
                  <div className="match-actions">
                    <button className="btn btn-primary" onClick={() => genOutreach(selected, m.investor_id)}>Generate Outreach</button>
                    <button className="btn btn-success">Meeting Booked</button>
                    <button className="btn btn-ghost">Pass</button>
                  </div>
                </div>
              ))}
              {outreach && (
                <div className="outreach-box">
                  <div className="outreach-label">Generated Outreach</div>
                  <div className="outreach-subject">{outreach.subject}</div>
                  <div className="outreach-body">{outreach.body}</div>
                  <div className="outreach-meta">
                    <span className="tag tag-green">{outreach.tone}</span>
                    <span>Match: {(outreach.match_score*100).toFixed(0)}%</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ===== INVESTORS ===== */
function Investors({ investors }) {
  return (
    <div style={{paddingTop:'80px'}} className="main">
      <div className="section">
        <div className="section-title">Investor Network</div>
        <div className="section-subtitle">Our investor network spans venture capital, impact funds, and sector-specific firms.</div>
      </div>
      <div className="investor-grid">
        {investors.map(inv => (
          <div key={inv.id} className="investor-card">
            <h3>{inv.name}</h3>
            <div className="investor-type">{inv.type} · ${(inv.fund_size/1e9).toFixed(0)}B fund</div>
            <div className="investor-desc">{inv.description}</div>
            <div className="investor-detail"><strong>Focus:</strong> {inv.preferred_sectors.join(', ')}</div>
            <div className="investor-detail"><strong>Stages:</strong> {inv.preferred_stages.join(', ')}</div>
            <div className="investor-detail"><strong>Check Size:</strong> ${(inv.check_size_min/1e6).toFixed(0)}M – ${(inv.check_size_max/1e6).toFixed(0)}M</div>
            <div className="investor-detail"><strong>Geography:</strong> {inv.focus_geographies.join(', ')}</div>
            <div className="investor-portfolio">
              <div className="profile-tags" style={{marginTop:'8px'}}>
                {inv.portfolio_highlights.map(p => <span key={p} className="tag tag-blue">{p}</span>)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===== DEMO ===== */
function Demo({ runDemo, demo, loading }) {
  return (
    <div style={{paddingTop:'80px'}} className="main">
      <div className="section">
        <div className="section-title">Full Matching Demo</div>
        <div className="section-subtitle">Match all 10 founders against all 10 investors in one run.</div>
        <button className="btn-hero" onClick={runDemo} disabled={loading}>{loading ? 'Running...' : 'Run Full Demo'}</button>
      </div>
      {demo && (
        <div className="card" style={{marginTop:'24px'}}>
          <div className="card-header">
            <div className="card-title">{demo.founders_matched} founders matched</div>
            <div className="card-subtitle">Average top score: {(demo.average_top_score*100).toFixed(0)}%</div>
          </div>
          {demo.matches.map((m, i) => (
            <div key={i} className="demo-row">
              <div>
                <div className="demo-founder-name">{m.founder}</div>
                <div className="demo-founder-meta">{m.company} · {m.industry}</div>
              </div>
              <div className="demo-arrow">→</div>
              <div>
                <div className="demo-investor-name">{m.top_match.investor}</div>
                <div className="demo-score">{(m.top_match.score*100).toFixed(0)}%</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ===== METRICS ===== */
function Metrics() {
  const [evals, setEvals] = useState(null);
  useEffect(() => { fetch(`${API}/api/evals`).then(r => r.json()).then(setEvals); }, []);

  return (
    <div style={{paddingTop:'80px'}} className="main">
      <div className="section">
        <div className="section-title">Matching Metrics</div>
        <div className="section-subtitle">Real-time quality metrics for the matching engine.</div>
      </div>
      {evals ? (
        <div>
          <div className="hero-stats" style={{justifyContent:'flex-start',gap:'32px',marginBottom:'32px'}}>
            <div><div className="hero-stat-num">{evals.total_matches_generated}</div><div className="hero-stat-label">Matches Generated</div></div>
            <div><div className="hero-stat-num">{evals.matches_with_feedback}</div><div className="hero-stat-label">Feedback Received</div></div>
            <div><div className="hero-stat-num">{(evals.conversion_rate*100).toFixed(0)}%</div><div className="hero-stat-label">Conversion Rate</div></div>
            <div><div className="hero-stat-num">{(evals.average_predicted_score*100).toFixed(0)}%</div><div className="hero-stat-label">Avg Match Score</div></div>
          </div>
          <div className="card">
            <div className="card-title" style={{marginBottom:'16px'}}>Score Distribution</div>
            <div className="dist-row"><div className="dist-label">High (≥70%)</div><div className="dist-track"><div className="dist-fill high" style={{width:`${(evals.score_distribution.high||0)*10}%`}}></div></div><div className="dist-count">{evals.score_distribution.high||0}</div></div>
            <div className="dist-row"><div className="dist-label">Medium (40-70%)</div><div className="dist-track"><div className="dist-fill med" style={{width:`${(evals.score_distribution.medium||0)*10}%`}}></div></div><div className="dist-count">{evals.score_distribution.medium||0}</div></div>
            <div className="dist-row"><div className="dist-label">Low (&lt;40%)</div><div className="dist-track"><div className="dist-fill low" style={{width:`${(evals.score_distribution.low||0)*10}%`}}></div></div><div className="dist-count">{evals.score_distribution.low||0}</div></div>
          </div>
        </div>
      ) : <div className="empty"><div className="spinner"></div><h3>Loading metrics...</h3></div>}
    </div>
  );
}

export default App;
