import { Link, useLocation } from 'react-router-dom';
import { BarChart3, BookOpen, ChevronRight, LayoutDashboard, LogOut, Menu, RefreshCw, Settings, ShieldCheck, WalletCards, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../AuthContext';

const groups = [
  { label: 'Overview', links: [{ path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }] },
  { label: 'Invest', links: [{ path: '/investments', label: 'My Investments', icon: BarChart3 }, { path: '/portfolio', label: 'Portfolio', icon: BookOpen }, { path: '/rebalance', label: 'Rebalance', icon: RefreshCw }] },
  { label: 'Plan', links: [{ path: '/risk', label: 'Risk Profile', icon: ShieldCheck }, { path: '/recommendations', label: 'Recommendations', icon: ChevronRight }] },
  { label: 'Manage', links: [{ path: '/wallet', label: 'Wallet', icon: WalletCards }, { path: '/transactions', label: 'Transactions', icon: BookOpen }, { path: '/settings', label: 'Settings', icon: Settings }] },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isActive = (path: string) => location.pathname === path || (path === '/investments' && location.pathname === '/invest');
  const nav = (mobile = false) => <>{groups.map(group => <div className="app-nav-group" key={group.label}><p className="app-nav-label">{group.label}</p>{group.links.map(({ path, label, icon: Icon }) => <Link key={path} to={path} onClick={() => mobile && setMobileOpen(false)} className={`app-nav-link ${isActive(path) ? 'is-active' : ''}`}><Icon size={16} strokeWidth={1.7}/><span>{label}</span></Link>)}</div>)}</>;

  return <div className="app-shell">
    <aside className="app-sidebar"><Link to="/dashboard" className="app-brand"><span className="app-brand-mark">H</span><span className="app-brand-name">Hindsight</span></Link><p className="app-brand-caption">Micro-investing simulation</p><nav className="app-nav">{nav()}</nav><div className="app-account"><div className="app-account-row"><span className="app-avatar">{user?.full_name?.charAt(0) || 'U'}</span><div className="min-w-0"><p className="app-account-name">{user?.full_name || 'Investor'}</p><p className="app-account-meta">{user?.is_demo ? 'Demo account' : user?.email}</p></div></div><button className="app-logout" onClick={logout}><LogOut size={15}/> Sign out</button></div></aside>
    <header className="app-mobile-header"><Link to="/dashboard" className="app-brand"><span className="app-brand-mark">H</span><span className="app-brand-name">Hindsight</span></Link><button className="app-button app-button-quiet" onClick={() => setMobileOpen(value => !value)} aria-label="Toggle navigation">{mobileOpen ? <X size={20}/> : <Menu size={20}/>}</button></header>
    {mobileOpen && <div className="app-mobile-menu"><nav>{nav(true)}</nav><button className="app-logout" onClick={logout}><LogOut size={15}/> Sign out</button></div>}
    <main className="app-main"><div className="app-main-inner">{children}</div><footer className="app-footer"><ShieldCheck size={13}/> Educational simulation · all money is virtual INR · not financial advice.</footer></main>
    <nav className="app-mobile-bottom">{groups.flatMap(group => group.links).filter(item => ['/dashboard', '/investments', '/portfolio', '/wallet'].includes(item.path)).map(({ path, label, icon: Icon }) => <Link key={path} to={path} className={isActive(path) ? 'is-active' : ''}><Icon size={17}/><span>{label === 'My Investments' ? 'Invest' : label}</span></Link>)}</nav>
  </div>;
}
