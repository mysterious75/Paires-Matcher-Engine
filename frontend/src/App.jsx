import React, { useState, useEffect } from 'react';
import './App.css';

const API = 'http://127.0.0.1:8001';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [founders, setFounders] = useState([]);
  const [investors, setInvestors] = useState([]);
  const [matches, setMatches] = useState(null);
  const [demo, setDemo] = useState(null);
  const [selectedFounder, setSelectedFounder] = useState(null);
  const [outreach, setOutreach] = useState(null);
  const [loading, setLoading] = useState(false);
  const [realTest, setRealTest] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [f, i] = await Promise.all([
        fetch(`${API}/api/founders`).then(r => r.json()),
        fetch(`${API}/api/investors`).then(r => r.json())
      ]);
      setFounders(f.founders);
      setInvestors(i.investors);
    } catch (e) { console.error(e); }
  };

  const runMatch = async (founderId) => {
    setLoading(true);
    setSelectedFounder(founderId);
    try {
      const r = await fetch(`${API}/api/match/founder/${founderId}?top_k=5`, { method: 'POST' });
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

  const genOutreach = async (founderId, investorId) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/outreach/generate?founder_id=${founderId}&investor_id=${investorId}`, { method: 'POST' });
      setOutreach(await r.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const recordFeedback = async (founderId, investorId, booked) => {
    await fetch(`${API}/api/feedback?founder_id=${founderId}&investor_id=${investorId}&meeting_booked=${booked}`, { method: 'POST' });
    alert(booked ? 'Meeting booked! Feedback recorded.' : 'No meeting. Feedback recorded.');
  };

  const runRealTest = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/match/all`, { method: 'POST' });
      setRealTest(await r.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const tabs = [
    { id: 'dashboard', label: 'Overview' },
    { id: 'founders', label: 'Founders' },
    { id: 'investors', label: 'Investors' },
    { id: 'demo', label: 'Full Demo' },
    { id: 'real', label: 'Real Companies' },
    { id: 'evals', label: 'Metrics' }
  ];

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div>
            <h1>Paires Matcher Engine</h1>
            <p>Founding AI Engineer Demo — Matching Engine</p>
          </div>
          <div className="header-badge">20 Founders × 10 Investors</div>
        </div>
      </header>

      <nav className="tabs">
        {tabs.map(t => (
          <button key={t.id} className={`tab ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {activeTab === 'dashboard' && <Dashboard founders={founders} investors={investors} />}
        {activeTab === 'founders' && <FoundersTab founders={founders} runMatch={runMatch} selectedFounder={selectedFounder} matches={matches} genOutreach={genOutreach} outreach={outreach} recordFeedback={recordFeedback} loading={loading} />}
        {activeTab === 'investors' && <InvestorsTab investors={investors} founders={founders} />}
        {activeTab === 'demo' && <DemoTab runDemo={runDemo} demo={demo} loading={loading} />}
        {activeTab === 'real' && <RealTab runRealTest={runRealTest} realTest={realTest} loading={loading} />}
        {activeTab === 'evals' && <EvalsTab />}
      </main>
    </div>
  );
}

// ==================== DASHBOARD ====================
function Dashboard({ founders, investors }) {
  const industries = [...new Set(founders.map(f => f.industry))];
  return (
    <div className="dashboard">
      <div className="stats-row">
        <div className="stat-card"><div className="stat-num">{founders.length}</div><div className="stat-label">Founders</div></div>
        <div className="stat-card"><div className="stat-num">{investors.length}</div><div className="stat-label">Investors</div></div>
        <div className="stat-card"><div className="stat-num">{founders.length * investors.length}</div><div className="stat-label">Possible Matches</div></div>
        <div className="stat-card"><div className="stat-num">{industries.length}</div><div className="stat-label">Industries</div></div>
      </div>
      <div className="card">
        <h2>How It Works</h2>
        <div className="flow">
          <div className="flow-step"><div className="flow-num">1</div><div className="flow-text"><strong>Profile Loading</strong><br/>Load founder and investor profiles</div></div>
          <div className="flow-arrow">→</div>
          <div className="flow-step"><div className="flow-num">2</div><div className="flow-text"><strong>Multi-Factor Scoring</strong><br/>Score on sector, stage, geography, check size</div></div>
          <div className="flow-arrow">→</div>
          <div className="flow-step"><div className="flow-num">3</div><div className="flow-text"><strong>Ranking</strong><br/>Rank and surface best matches</div></div>
          <div className="flow-arrow">→</div>
          <div className="flow-step"><div className="flow-num">4</div><div className="flow-text"><strong>Agent Outreach</strong><br/>Generate personalized messages</div></div>
        </div>
      </div>
      <div className="card">
        <h2>Score Weights</h2>
        <div className="weights">
          <WeightBar label="Sector" weight="35%" color="#667eea" />
          <WeightBar label="Stage" weight="20%" color="#764ba2" />
          <WeightBar label="Geography" weight="15%" color="#f5576c" />
          <WeightBar label="Check Size" weight="15%" color="#4facfe" />
          <WeightBar label="Description" weight="15%" color="#4ade80" />
        </div>
      </div>
      <div className="card">
        <h2>Industries Covered</h2>
        <div className="tag-list">
          {industries.map(ind => <span key={ind} className="tag">{ind}</span>)}
        </div>
      </div>
    </div>
  );
}

function WeightBar({ label, weight, color }) {
  const w = parseInt(weight);
  return (
    <div className="weight-row">
      <span className="weight-label">{label}</span>
      <div className="weight-track"><div className="weight-fill" style={{ width: `${w * 2.5}%`, background: color }}></div></div>
      <span className="weight-value">{weight}</span>
    </div>
  );
}

// ==================== FOUNDERS ====================
function FoundersTab({ founders, runMatch, selectedFounder, matches, genOutreach, outreach, recordFeedback, loading }) {
  const selected = founders.find(f => f.id === selectedFounder);

  return (
    <div className="split-layout">
      <div className="left-panel">
        <h2>Click a Founder to Match</h2>
        {founders.map(f => (
          <div key={f.id} className={`profile-card clickable ${selectedFounder === f.id ? 'selected' : ''}`} onClick={() => runMatch(f.id)}>
            <div className="profile-header">
              <div className="profile-avatar">{f.name.split(' ').map(n => n[0]).join('')}</div>
              <div>
                <div className="profile-name">{f.name}</div>
                <div className="profile-company">{f.company}</div>
              </div>
            </div>
            <div className="profile-meta">
              <span className="badge">{f.industry}</span>
              <span className="badge">{f.funding_stage}</span>
              <span className="badge">${(f.ask_amount / 1000000).toFixed(0)}M ask</span>
            </div>
          </div>
        ))}
      </div>

      <div className="right-panel">
        {!matches && !loading && (
          <div className="empty-state">
            <div className="empty-icon">👆</div>
            <h3>Select a Founder</h3>
            <p>Click on any founder card to see the best investor matches.</p>
          </div>
        )}

        {loading && (
          <div className="empty-state">
            <div className="spinner"></div>
            <h3>Computing matches...</h3>
          </div>
        )}

        {matches && !loading && (
          <div>
            <h2>Best Investors for {matches.founder}</h2>
            <p className="subtitle">{matches.company}</p>
            {matches.matches.map((m, idx) => (
              <div key={idx} className="match-card">
                <div className="match-header">
                  <div className="match-rank">#{idx + 1}</div>
                  <div className="match-info">
                    <div className="match-name">{m.investor}</div>
                    <div className="match-scores">
                      <span className="score-pill sector">Sector: {(m.sector_score * 100).toFixed(0)}%</span>
                      <span className="score-pill stage">Stage: {(m.stage_score * 100).toFixed(0)}%</span>
                      <span className="score-pill geo">Geo: {(m.geography_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="match-score-badge">{(m.overall_score * 100).toFixed(0)}%</div>
                </div>
                <div className="match-description">{m.description}</div>
                <div className="match-reasons">
                  {m.match_reasons.map((r, i) => <div key={i} className="reason">• {r}</div>)}
                </div>
                <div className="match-actions">
                  <button className="btn-sm btn-primary" onClick={() => genOutreach(selected.id, m.investor_id)}>Generate Outreach</button>
                  <button className="btn-sm btn-success" onClick={() => recordFeedback(selected.id, m.investor_id, true)}>✓ Meeting Booked</button>
                  <button className="btn-sm btn-ghost" onClick={() => recordFeedback(selected.id, m.investor_id, false)}>✗ Pass</button>
                </div>
              </div>
            ))}

            {outreach && (
              <div className="outreach-card">
                <h3>Generated Outreach</h3>
                <div className="outreach-subject"><strong>Subject:</strong> {outreach.subject}</div>
                <div className="outreach-body"><pre>{outreach.body}</pre></div>
                <div className="outreach-meta">
                  <span className="badge">{outreach.tone}</span>
                  <span>Match: {(outreach.match_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== INVESTORS ====================
function InvestorsTab({ investors, founders }) {
  return (
    <div>
      <h2>Investor Profiles</h2>
      <div className="investor-grid">
        {investors.map(inv => (
          <div key={inv.id} className="card investor-card">
            <div className="investor-header">
              <h3>{inv.name}</h3>
              <span className="badge">{inv.type}</span>
            </div>
            <p className="investor-desc">{inv.description}</p>
            <div className="investor-details">
              <div><strong>Focus:</strong> {inv.preferred_sectors.join(', ')}</div>
              <div><strong>Stages:</strong> {inv.preferred_stages.join(', ')}</div>
              <div><strong>Check Size:</strong> ${(inv.check_size_min / 1000000).toFixed(0)}M - ${(inv.check_size_max / 1000000).toFixed(0)}M</div>
              <div><strong>Geography:</strong> {inv.geography} ({inv.focus_geographies.join(', ')})</div>
            </div>
            <div className="investor-portfolio">
              <strong>Portfolio:</strong>
              <div className="tag-list">
                {inv.portfolio_highlights.map(p => <span key={p} className="tag tag-blue">{p}</span>)}
              </div>
            </div>
            <div className="investor-thesis">
              <strong>Thesis:</strong> <span className="thesis-text">{inv.investment_thesis}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==================== DEMO ====================
function DemoTab({ runDemo, demo, loading }) {
  return (
    <div>
      <div className="demo-header">
        <h2>Full Matching Demo</h2>
        <p>Match all 10 founders against all 10 investors</p>
        <button className="btn-primary" onClick={runDemo} disabled={loading}>
          {loading ? 'Running...' : 'Run Full Demo'}
        </button>
      </div>

      {demo && (
        <div>
          <div className="stats-row">
            <div className="stat-card"><div className="stat-num">{demo.founders_matched}</div><div className="stat-label">Founders Matched</div></div>
            <div className="stat-card"><div className="stat-num">{(demo.average_top_score * 100).toFixed(0)}%</div><div className="stat-label">Avg Top Score</div></div>
          </div>

          <div className="card">
            <h2>Results</h2>
            {demo.matches.map((m, idx) => (
              <div key={idx} className="demo-row">
                <div className="demo-founder">
                  <strong>{m.founder}</strong>
                  <span className="demo-company">{m.company}</span>
                  <span className="badge badge-sm">{m.industry}</span>
                </div>
                <div className="demo-arrow">→</div>
                <div className="demo-investor">
                  <strong>{m.top_match.investor}</strong>
                  <span className="demo-score">{(m.top_match.score * 100).toFixed(0)}%</span>
                </div>
                <div className="demo-reasons">
                  {m.top_match.reasons.slice(0, 2).map((r, i) => <span key={i} className="reason-sm">• {r}</span>)}
                </div>
                {m.outreach_subject && <div className="demo-outreach"><em>Subject: {m.outreach_subject}</em></div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== REAL COMPANIES ====================
function RealTab({ runRealTest, realTest, loading }) {
  const realCompanies = [
    { name: 'Stripe', industry: 'Fintech', stage: 'Late Stage', location: 'San Francisco, CA' },
    { name: 'Canva', industry: 'Enterprise SaaS', stage: 'Late Stage', location: 'Sydney, Australia' },
    { name: 'Rippling', industry: 'Enterprise SaaS', stage: 'Series E', location: 'San Francisco, CA' },
    { name: 'Figma', industry: 'Enterprise SaaS', stage: 'Late Stage', location: 'San Francisco, CA' },
    { name: 'SpaceX', industry: 'Deep Tech', stage: 'Late Stage', location: 'Hawthorne, CA' }
  ];

  return (
    <div>
      <div className="demo-header">
        <h2>Real Company Profiles</h2>
        <p>See how known companies would match with our investor network</p>
        <div className="real-companies">
          {realCompanies.map(c => (
            <span key={c.name} className="tag tag-real">{c.name} <span className="tag-sub">{c.industry}</span></span>
          ))}
        </div>
      </div>

      <div className="card">
        <h2>Real Company Matching Results</h2>
        <p>These real companies matched against our investor network:</p>
        <div className="real-results">
          {realCompanies.map((company, idx) => {
            const match = realTest?.results?.[idx % (realTest?.results?.length || 1)];
            return (
              <div key={idx} className="real-match-row">
                <div className="real-company-info">
                  <strong>{company.name}</strong>
                  <span className="badge">{company.industry}</span>
                  <span className="badge">{company.stage}</span>
                  <span className="badge">{company.location}</span>
                </div>
                <div className="real-arrow">→</div>
                <div className="real-match-info">
                  {match ? (
                    <>
                      <strong>{match.top_matches[0]?.investor || 'N/A'}</strong>
                      <span className="demo-score">{((match.top_matches[0]?.score || 0) * 100).toFixed(0)}%</span>
                      <span className="badge">{match.industry}</span>
                    </>
                  ) : (
                    <span className="text-muted">Click Run All to see matches</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <button className="btn-primary" onClick={runRealTest} disabled={loading}>
          {loading ? 'Matching...' : 'Run All Matches'}
        </button>
      </div>
    </div>
  );
}

// ==================== EVALS ====================
function EvalsTab() {
  const [evals, setEvals] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/evals`).then(r => r.json()).then(setEvals).catch(() => {});
  }, []);

  return (
    <div>
      <h2>Matching Engine Metrics</h2>
      <div className="card">
        {evals ? (
          <div>
            <div className="stats-row">
              <div className="stat-card"><div className="stat-num">{evals.total_matches_generated}</div><div className="stat-label">Total Matches</div></div>
              <div className="stat-card"><div className="stat-num">{evals.matches_with_feedback}</div><div className="stat-label">With Feedback</div></div>
              <div className="stat-card"><div className="stat-num">{(evals.conversion_rate * 100).toFixed(0)}%</div><div className="stat-label">Conversion Rate</div></div>
              <div className="stat-card"><div className="stat-num">{(evals.average_predicted_score * 100).toFixed(0)}%</div><div className="stat-label">Avg Score</div></div>
            </div>
            <div className="card" style={{marginTop: '16px'}}>
              <h3>Score Distribution</h3>
              <div className="distribution">
                <div className="dist-bar high"><div className="dist-fill" style={{width: `${(evals.score_distribution.high || 0) * 10}%`}}></div><span>High (≥70%): {evals.score_distribution.high || 0}</span></div>
                <div className="dist-bar med"><div className="dist-fill" style={{width: `${(evals.score_distribution.medium || 0) * 10}%`}}></div><span>Medium (40-70%): {evals.score_distribution.medium || 0}</span></div>
                <div className="dist-bar low"><div className="dist-fill" style={{width: `${(evals.score_distribution.low || 0) * 10}%`}}></div><span>Low (<40%): {evals.score_distribution.low || 0}</span></div>
              </div>
            </div>
          </div>
        ) : <p>Loading metrics...</p>}
      </div>
    </div>
  );
}

export default App;
