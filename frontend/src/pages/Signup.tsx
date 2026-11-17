import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authSignup } from '../api';
import { useAuth } from '../AuthContext';
import { ArrowRight } from 'lucide-react';

export default function Signup() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return; }
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    setLoading(true);
    try {
      const res = await authSignup({ email: form.email, password: form.password, full_name: form.full_name });
      login(res.data.access_token, res.data);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center gap-3 mb-8">
          <div className="w-9 h-9 rounded-lg bg-champagne flex items-center justify-center">
            <span className="text-navy font-bold text-lg font-display">H</span>
          </div>
          <span className="text-xl font-display font-semibold text-ivory">Hindsight</span>
        </Link>
        <div className="card p-8">
          <h1 className="text-2xl font-display font-bold text-navy mb-2">Create your account</h1>
          <p className="text-navy-200 text-sm mb-8">Start your virtual investing journey</p>
          {error && <div className="mb-4 p-3 bg-loss/10 border border-loss/20 rounded-xl text-sm text-loss">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-navy mb-1.5">Full Name</label>
              <input value={form.full_name} onChange={(e) => set('full_name', e.target.value)} className="input-field" placeholder="Your name" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1.5">Email</label>
              <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} className="input-field" placeholder="you@example.com" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1.5">Password</label>
              <input type="password" value={form.password} onChange={(e) => set('password', e.target.value)} className="input-field" placeholder="Min. 6 characters" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1.5">Confirm Password</label>
              <input type="password" value={form.confirm} onChange={(e) => set('confirm', e.target.value)} className="input-field" placeholder="Repeat password" required />
            </div>
            <div className="flex items-start gap-2">
              <input type="checkbox" required className="mt-1" />
              <label className="text-xs text-navy-200">
                I understand that Hindsight is an educational simulation with virtual money. It does not provide financial advice.
              </label>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading ? <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-ivory" /> : <>Create Account <ArrowRight size={16} /></>}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-navy-200">
            Already have an account? <Link to="/login" className="text-champagne-500 font-semibold hover:text-champagne-600">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
