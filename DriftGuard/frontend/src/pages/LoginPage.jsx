import React, { useState } from "react";
import { Activity, ArrowDownRight, ArrowRight, Eye, EyeOff, GitBranch, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";
import { api } from "../api/client";

const CAPABILITIES = [
  { number: "01", icon: Activity, title: "See the signal", copy: "Catch distribution shifts before they move your model off course." },
  { number: "02", icon: GitBranch, title: "Move with control", copy: "Evaluate every candidate, keep the best version in production." },
  { number: "03", icon: ShieldCheck, title: "Know what changed", copy: "One clear view of model health, history, and decisions." },
];

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await api.login(username.trim(), password);
      onLoginSuccess(user);
    } catch (err) {
      setError(err.message || "Could not sign in. Check your username and password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="intro-site">
      <nav className="intro-nav" aria-label="Main navigation">
        <a className="intro-brand" href="#top" aria-label="DriftGuard home">
          <span className="intro-brand-icon"><ShieldCheck size={19} /></span>
          <span>DRIFTGUARD<small>MODEL INTELLIGENCE</small></span>
        </a>
        <div className="intro-nav-links"><a href="#platform">Platform</a><a href="#approach">Approach</a></div>
        <a className="intro-nav-cta" href="#access">Workspace login <ArrowRight size={15} /></a>
      </nav>

      <section className="intro-hero" id="top">
        <div className="intro-copy">
          <p className="intro-kicker"><span /> MLOPS, WITH MOMENTUM <span className="intro-kicker-year">EST. FOR WHAT'S NEXT</span></p>
          <h1>Models move.<br /><em>Stay ahead.</em></h1>
          <p className="intro-lede">Production is always changing. DriftGuard gives your team the signal, context, and control to keep machine learning moving in the right direction.</p>
          <a className="intro-primary-link" href="#access">Enter your workspace <ArrowDownRight size={17} /></a>
          <div className="intro-proof"><span className="intro-proof-dot" /> CONTINUOUS MODEL VISIBILITY <span className="intro-proof-line" /> BUILT FOR REAL DATA</div>
        </div>

        <div className="intro-art" aria-hidden="true">
          <div className="intro-art-caption"><span>LIVE MODEL FIELD</span><span>DG / 001</span></div>
          <div className="intro-grid-floor" />
          <div className="intro-orbit intro-orbit-a" /><div className="intro-orbit intro-orbit-b" /><div className="intro-orbit intro-orbit-c" />
          <div className="intro-planet">
            <div className="intro-planet-shade" />
            <div className="intro-latitude intro-latitude-a" /><div className="intro-latitude intro-latitude-b" />
            <div className="intro-longitude intro-longitude-a" /><div className="intro-longitude intro-longitude-b" />
            <div className="intro-planet-core"><span>DG</span></div>
          </div>
          <div className="intro-satellite intro-satellite-a"><i /></div>
          <div className="intro-satellite intro-satellite-b"><i /></div>
          <div className="intro-art-coordinate">40° 42′ 46.08″ N<br />74° 00′ 21.60″ W</div>
          <div className="intro-signal-card"><span className="intro-signal-label"><i /> MODEL HEALTH</span><strong>STABLE <b>+ 0.8%</b></strong><span className="intro-signal-chart"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></span></div>
        </div>

        <section className="intro-access" id="access" aria-labelledby="access-title">
          <div className="intro-access-top"><span><LockKeyhole size={14} /> SECURE ACCESS</span><span className="intro-online"><i /> ONLINE</span></div>
          <p className="intro-access-kicker">YOUR WORKSPACE IS READY</p>
          <h2 id="access-title">Welcome back.</h2>
          <p className="intro-access-copy">Sign in to continue to DriftGuard.</p>
          {error && <div className="intro-error" role="alert">{error}</div>}
          <form onSubmit={handleSubmit} className="intro-login-form">
            <label><span>USERNAME</span><div className="intro-input"><UserRound size={16} /><input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Your username" required /></div></label>
            <label><span>PASSWORD</span><div className="intro-input"><LockKeyhole size={16} /><input type={showPassword ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" required /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button></div></label>
            <button className="intro-submit" type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}<ArrowRight size={17} /></button>
          </form>
          <p className="intro-access-foot"><ShieldCheck size={14} /> Protected access to your model operations</p>
        </section>
        <a className="intro-scroll-cue" href="#platform"><span>SCROLL TO EXPLORE</span><ArrowDownRight size={16} /></a>
      </section>

      <section className="intro-platform" id="platform">
        <div className="intro-section-heading"><div><p className="intro-section-kicker">THE DRIFTGUARD PLATFORM</p><h2>Confidence at every<br />stage of the model.</h2></div><p>From the first signal to the next release, bring monitoring and model decisions into one focused workflow.</p></div>
        <div className="intro-capabilities" id="approach">{CAPABILITIES.map(({ number, icon: Icon, title, copy }) => <article className="intro-capability" key={number}><div className="intro-capability-top"><span>{number}</span><Icon size={19} /></div><h3>{title}</h3><p>{copy}</p></article>)}</div>
        <footer className="intro-footer"><a className="intro-brand" href="#top"><span className="intro-brand-icon"><ShieldCheck size={18} /></span><span>DRIFTGUARD<small>MODEL INTELLIGENCE</small></span></a><span>MONITOR · EVALUATE · IMPROVE</span><span>© 2026 DRIFTGUARD</span></footer>
      </section>
    </main>
  );
}
