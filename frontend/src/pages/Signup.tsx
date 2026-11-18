import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authSignup } from '../api';
import { useAuth } from '../AuthContext';
import { ArrowRight } from 'lucide-react';

export default function Signup() {
  const navigate = useNavigate(); const { login } = useAuth();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' }); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const set = (key: string, value: string) => setForm(current => ({ ...current, [key]: value }));
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return; }
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    setLoading(true);
    try { const res = await authSignup({ email: form.email, password: form.password, full_name: form.full_name }); login(res.data.access_token, res.data); navigate('/dashboard'); }
    catch (err: any) { setError(err.response?.data?.detail || 'Registration failed.'); }
    finally { setLoading(false); }
  };
  return <div className="auth-page flex min-h-screen items-center justify-center p-6"><div className="w-full max-w-md">
    <Link to="/" className="auth-brand mb-8 flex items-center gap-3"><div className="auth-logo"><span>H</span></div><span className="auth-wordmark">Hindsight</span></Link>
    <div className="auth-card p-8"><h1 className="auth-heading mb-2">Create your account</h1><p className="auth-muted mb-8 text-sm">Start your virtual investing journey</p>{error && <div className="auth-error mb-4">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-5">
        <div><label className="auth-label">Full Name</label><input value={form.full_name} onChange={e => set('full_name', e.target.value)} className="auth-input" placeholder="Your name" required /></div>
        <div><label className="auth-label">Email</label><input type="email" value={form.email} onChange={e => set('email', e.target.value)} className="auth-input" placeholder="you@example.com" required /></div>
        <div><label className="auth-label">Password</label><input type="password" value={form.password} onChange={e => set('password', e.target.value)} className="auth-input" placeholder="Min. 6 characters" required /></div>
        <div><label className="auth-label">Confirm Password</label><input type="password" value={form.confirm} onChange={e => set('confirm', e.target.value)} className="auth-input" placeholder="Repeat password" required /></div>
        <div className="flex items-start gap-2"><input type="checkbox" required className="auth-checkbox mt-1"/><label className="auth-muted text-xs">I understand that Hindsight is an educational simulation with virtual money. It does not provide financial advice.</label></div>
        <button type="submit" disabled={loading} className="auth-button auth-button-champagne flex w-full items-center justify-center gap-2">{loading ? <span className="auth-spinner auth-spinner-dark"/> : <>Create Account <ArrowRight size={16}/></>}</button>
      </form>
      <p className="auth-muted mt-6 text-center text-sm">Already have an account? <Link to="/login" className="auth-link font-semibold">Sign in</Link></p>
    </div>
  </div></div>;
}
