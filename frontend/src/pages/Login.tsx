import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authLogin, authDemo } from '../api';
import { useAuth } from '../AuthContext';
import { ArrowRight, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { const res = await authLogin(email, password); login(res.data.access_token, res.data); navigate('/dashboard'); }
    catch (err: any) { setError(err.response?.data?.detail || 'Login failed. Please try again.'); }
    finally { setLoading(false); }
  };
  const handleDemo = async () => {
    setError(''); setDemoLoading(true);
    try { const res = await authDemo(); login(res.data.access_token, res.data); navigate('/dashboard'); }
    catch { setError('Could not start demo. Please try again.'); }
    finally { setDemoLoading(false); }
  };

  return <div className="auth-page flex min-h-screen">
    <div className="auth-intro-panel hidden w-1/2 flex-col justify-between p-12 lg:flex">
      <Link to="/" className="auth-brand flex items-center gap-3"><div className="auth-logo"><span>H</span></div><span className="auth-wordmark">Hindsight</span></Link>
      <div><h2 className="auth-display-heading mb-4">Your portfolio,<br />your rules.</h2><p className="auth-intro-copy max-w-md">Learn how risk profiling, asset allocation, and portfolio rebalancing work — with virtual money and transparent logic.</p></div>
      <p className="auth-muted text-xs">Educational simulation only. Not financial advice.</p>
    </div>
    <div className="flex flex-1 items-center justify-center p-6"><div className="w-full max-w-md">
      <div className="mb-8 lg:hidden"><Link to="/" className="auth-brand flex items-center gap-3"><div className="auth-logo"><span>H</span></div><span className="auth-wordmark">Hindsight</span></Link></div>
      <div className="auth-card p-8">
        <h1 className="auth-heading mb-2">Welcome back</h1><p className="auth-muted mb-8 text-sm">Sign in to your Hindsight account</p>
        {error && <div className="auth-error mb-4">{error}</div>}
        <form onSubmit={handleLogin} className="space-y-5">
          <div><label className="auth-label">Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} className="auth-input" placeholder="you@example.com" required /></div>
          <div><label className="auth-label">Password</label><div className="relative"><input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} className="auth-input pr-12" placeholder="••••••••" required /><button type="button" onClick={() => setShowPw(!showPw)} className="auth-password-toggle absolute right-4 top-1/2 -translate-y-1/2">{showPw ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div></div>
          <button type="submit" disabled={loading} className="auth-button auth-button-emerald flex w-full items-center justify-center gap-2">{loading ? <span className="auth-spinner"/> : <>Sign In <ArrowRight size={16}/></>}</button>
        </form>
        <div className="auth-divider relative my-8"><div className="absolute inset-0 flex items-center"><div className="w-full"/></div><div className="relative flex justify-center text-xs uppercase"><span className="px-3">or</span></div></div>
        <button onClick={handleDemo} disabled={demoLoading} className="auth-button auth-button-champagne flex w-full items-center justify-center gap-2">{demoLoading ? <span className="auth-spinner auth-spinner-dark"/> : <>Try Demo — Instant Access</>}</button>
        <p className="auth-muted mt-6 text-center text-sm">Don't have an account? <Link to="/signup" className="auth-link font-semibold">Sign up</Link></p>
      </div>
    </div></div>
  </div>;
}
