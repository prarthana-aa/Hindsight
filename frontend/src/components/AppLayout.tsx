import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { BarChart3, BookOpen, CircleHelp, LayoutDashboard, LogOut, Menu, RefreshCw, Settings, Shield, TrendingUp, Wallet, X } from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/invest', label: 'Explore Assets', icon: TrendingUp },
  { path: '/investments', label: 'My Investments', icon: BarChart3 },
  { path: '/risk', label: 'Risk Profile', icon: Shield },
  { path: '/wallet', label: 'Wallet', icon: Wallet },
  { path: '/rebalance', label: 'Rebalancing', icon: RefreshCw },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isActive = (path: string) => location.pathname === path || (path === '/invest' && location.pathname === '/investments');
  const links = <>
    <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.2em] text-navy-200">Workspace</div>
    {navItems.map(({ path, label, icon: Icon }) => <Link key={path} to={path} onClick={() => setMobileOpen(false)} className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${isActive(path) ? 'bg-emerald/10 font-semibold text-emerald' : 'text-navy-200 hover:bg-white/[.05] hover:text-ivory-50'}`}><Icon size={17} strokeWidth={isActive(path) ? 2.4 : 1.8}/><span>{label}</span>{isActive(path) && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald"/>}</Link>)}
    <div className="mb-3 mt-8 px-3 text-[10px] font-bold uppercase tracking-[.2em] text-navy-200">Account</div>
    <Link to="/settings" onClick={() => setMobileOpen(false)} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${location.pathname === '/settings' ? 'bg-emerald/10 font-semibold text-emerald' : 'text-navy-200 hover:bg-white/[.05] hover:text-ivory-50'}`}><Settings size={17}/><span>Settings</span></Link>
  </>;

  return <div className="min-h-screen bg-navy text-ivory-50">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-white/[.07] bg-[#0D141F] px-4 py-5 lg:flex lg:flex-col">
      <Link to="/dashboard" className="mb-10 flex items-center gap-3 px-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-champagne text-lg font-bold text-navy-700">H</div><span className="font-display text-xl font-semibold tracking-tight">Hindsight</span></Link>
      <nav className="flex-1">{links}</nav>
      <div className="border-t border-white/[.07] pt-4"><div className="mb-3 flex items-center gap-3 px-3"><div className="avatar !h-8 !w-8 !text-sm">{user?.full_name?.charAt(0) || 'U'}</div><div className="min-w-0"><p className="truncate text-xs font-semibold text-ivory-50">{user?.full_name}</p><p className="truncate text-[10px] text-navy-200">{user?.is_demo ? 'Demo workspace' : user?.email}</p></div></div><button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-navy-200 transition hover:bg-loss/10 hover:text-loss"><LogOut size={17}/> Sign out</button></div>
    </aside>
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-white/[.07] bg-[#0B1019]/90 px-4 backdrop-blur lg:hidden"><Link to="/dashboard" className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-champagne font-bold text-navy-700">H</span><span className="font-display text-lg font-semibold">Hindsight</span></Link><button onClick={() => setMobileOpen(!mobileOpen)} className="text-ivory-50">{mobileOpen ? <X/> : <Menu/>}</button></header>
    {mobileOpen && <div className="fixed inset-0 z-10 bg-[#0D141F] px-5 pb-8 pt-24 lg:hidden"><nav>{links}</nav><button onClick={logout} className="mt-8 flex items-center gap-3 px-3 py-2.5 text-sm text-loss"><LogOut size={17}/> Sign out</button></div>}
    <main className="min-h-screen lg:pl-64"><div className="mx-auto max-w-[1480px] px-4 py-7 sm:px-6 lg:px-10 lg:py-10">{children}</div><footer className="mx-auto flex max-w-[1480px] items-center gap-2 px-4 pb-8 text-[11px] text-navy-200 sm:px-6 lg:px-10"><CircleHelp size={13}/> Educational simulation only · all money is virtual INR · not financial advice.</footer></main>
  </div>;
}
