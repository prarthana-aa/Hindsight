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
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authLogin(email, password);
      login(res.data.access_token, res.data);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setError('');
    setDemoLoading(true);
    try {
      const res = await authDemo();
      login(res.data.access_token, res.data);
      navigate('/dashboard');
    } catch {
      setError('Could not start demo. Please try again.');
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy flex">
      {/* Left decorative panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-champagne flex items-center justify-center">
            <span className="text-navy font-bold text-lg font-display">H</span>
          </div>
          <span className="text-xl font-display font-semibold text-ivory">Hindsight</span>
        </Link>
        <div>
          <h2 className="text-4xl font-display font-bold text-ivory leading-tight mb-4">
            Your portfolio,<br />your rules.
          </h2>
          <p className="text-ivory-300 text-lg max-w-md">
            Learn how risk profiling, asset allocation, and portfolio rebalancing
            work — with virtual money and transparent logic.
          </p>
        </div>
        <p className="text-xs text-navy-200">
          Educational simulation only. Not financial advice.
        </p>
      </div>

      {/* Right login panel */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8">
            <Link to="/" className="flex items-center gap-3 mb-8">
              <div className="w-9 h-9 rounded-lg bg-champagne flex items-center justify-center">
                <span className="text-navy font-bold text-lg font-display">H</span>
              </div>
              <span className="text-xl font-display font-semibold text-ivory">Hindsight</span>
            </Link>
          </div>

          <div className="card p-8">
            <h1 className="text-2xl font-display font-bold text-navy mb-2">Welcome back</h1>
            <p className="text-navy-200 text-sm mb-8">Sign in to your Hindsight account</p>

            {error && (
              <div className="mb-4 p-3 bg-loss/10 border border-loss/20 rounded-xl text-sm text-loss">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-navy mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pr-12"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-200 hover:text-navy"
                  >
                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {loading ? (
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-ivory" />
                ) : (
                  <>
                    Sign In <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>

            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-ivory-300" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 text-navy-200">or</span>
              </div>
            </div>

            <button
              onClick={handleDemo}
              disabled={demoLoading}
              className="btn-champagne w-full flex items-center justify-center gap-2"
            >
              {demoLoading ? (
                <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-navy" />
              ) : (
                <>Try Demo — Instant Access</>
              )}
            </button>

            <p className="mt-6 text-center text-sm text-navy-200">
              Don't have an account?{' '}
              <Link to="/signup" className="text-champagne-500 font-semibold hover:text-champagne-600">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
