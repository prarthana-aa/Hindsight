import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, PieChart, Pie, Cell } from 'recharts';
import { ArrowUpRight, Info, RefreshCw, ShieldCheck, TrendingDown, TrendingUp, WalletCards } from 'lucide-react';
import { getAssetHistory, getPortfolioDashboard, getWalletBalance } from '../api';

const colors = ['#2D8B6F', '#C9A96E', '#4F6891', '#A8B5C6'];
const money = (value: number) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
const number = (value: number) => value.toLocaleString('en-IN', { maximumFractionDigits: 3 });

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [wallet, setWallet] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [period, setPeriod] = useState(90);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [portfolio, balance, prices] = await Promise.all([getPortfolioDashboard(), getWalletBalance(), getAssetHistory('NIFTY50')]);
      setDashboard(portfolio.data); setWallet(balance.data); setHistory(prices.data.data || []);
    } catch { setError('We could not load your portfolio. Please refresh and try again.'); }
  };
  useEffect(() => { load(); }, []);

  const chartData = useMemo(() => history.slice(-period).map((item) => ({ date: new Date(item.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }), value: Number(item.close) })), [history, period]);
  const allocation = dashboard?.holdings?.map((h: any) => ({ name: h.asset, value: Number(h.market_value) })) || [];
  const total = Number(dashboard?.total_portfolio_value || 0);

  if (error) return <div className="card max-w-xl"><p className="text-loss">{error}</p><button onClick={load} className="btn-primary mt-5">Retry</button></div>;
  if (!dashboard) return <Loading />;

  return <div className="space-y-8">
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div><p className="eyebrow">Portfolio overview</p><h1 className="page-title">Good morning, investor.</h1><p className="muted mt-2">A clear view of your virtual wealth journey.</p></div>
      <button onClick={load} className="btn-secondary self-start sm:self-auto"><RefreshCw size={16} /> Refresh data</button>
    </header>
    <section className="grid gap-4 lg:grid-cols-[1.5fr_1fr_1fr]">
      <div className="hero-stat"><div className="flex items-center justify-between"><span className="eyebrow text-ivory-300">Total portfolio value</span><span className="badge badge-gold">Virtual INR</span></div><p className="mt-5 text-4xl font-semibold tracking-tight text-ivory">{money(total)}</p><p className="mt-3 flex items-center gap-2 text-sm text-emerald-200"><TrendingUp size={16} /> {Number(dashboard.total_pnl_pct).toFixed(2)}% unrealized return</p></div>
      <Stat title="Available balance" value={money(Number(dashboard.cash_balance))} icon={<WalletCards size={19} />} />
      <Stat title="Unrealized P&L" value={money(Number(dashboard.total_unrealized_pnl))} icon={Number(dashboard.total_unrealized_pnl) >= 0 ? <TrendingUp size={19} /> : <TrendingDown size={19} />} positive={Number(dashboard.total_unrealized_pnl) >= 0} />
    </section>
    {dashboard.needs_rebalance && <div className="notice"><RefreshCw size={20} /><div><strong>Portfolio drift detected</strong><p>Your allocation has moved outside the 5% tolerance band.</p></div><Link className="ml-auto btn-secondary !px-4 !py-2" to="/rebalance">Review</Link></div>}
    <section className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
      <div className="card"><div className="section-head"><div><p className="eyebrow">Market context</p><h2 className="section-title">NIFTY50 reference price <span title="A market proxy used for the simulation."><Info size={14} className="ml-1 inline text-navy-200"/></span></h2></div><div className="flex gap-1 rounded-lg bg-[#0F1723] p-1">{[30,90,180].map(days=><button key={days} onClick={()=>setPeriod(days)} className={`rounded-md px-2.5 py-1 text-[11px] ${period===days?'bg-emerald text-navy-700 font-semibold':'text-navy-200'}`}>{days}D</button>)}</div></div><div className="mt-6 h-64">{chartData.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#55C99A" stopOpacity={0.25}/><stop offset="95%" stopColor="#55C99A" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#2A3747" vertical={false}/><XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={35} tick={{fontSize:11, fill:'#95A1B2'}}/><YAxis hide domain={['dataMin - 100','dataMax + 100']}/><Tooltip contentStyle={{background:'#151E2B',border:'1px solid rgba(255,255,255,.1)',borderRadius:12,color:'#F4F0E8'}} formatter={(v: any) => [money(Number(v)), 'Reference price']} /><Area type="monotone" dataKey="value" stroke="#55C99A" strokeWidth={2.5} fill="url(#fill)" /></AreaChart></ResponsiveContainer> : <Empty />}</div></div>
      <div className="card"><div className="section-head"><div><p className="eyebrow">Allocation</p><h2 className="section-title">Where your money sits</h2></div><Link to="/invest" className="icon-link"><ArrowUpRight size={18}/></Link></div><div className="relative mt-3 h-52"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={allocation} dataKey="value" nameKey="name" innerRadius={58} outerRadius={82} paddingAngle={3}>{allocation.map((_: any, i: number) => <Cell key={i} fill={colors[i % colors.length]} />)}</Pie><Tooltip formatter={(v: any) => [money(Number(v)), 'Value']} /></PieChart></ResponsiveContainer><span className="absolute inset-0 flex items-center justify-center text-xl font-semibold text-navy">{money(total)}</span></div><div className="grid grid-cols-2 gap-3">{allocation.map((item: any, i: number) => <div className="flex items-center gap-2 text-xs" key={item.name}><span className="h-2 w-2 rounded-full" style={{backgroundColor: colors[i % colors.length]}}/><span className="text-navy-200">{item.name}</span><strong className="ml-auto">{total ? ((item.value / total) * 100).toFixed(0) : 0}%</strong></div>)}</div></div>
    </section>
    <section className="card"><div className="section-head"><div><p className="eyebrow">Holdings</p><h2 className="section-title">Your investment mix</h2></div><Link to="/invest" className="text-sm font-semibold text-emerald">Manage investments <ArrowUpRight className="inline" size={15}/></Link></div><div className="mt-5 overflow-x-auto"><table><thead><tr><th>Asset</th><th>Units</th><th>Market value</th><th>Return</th><th>Weight</th></tr></thead><tbody>{dashboard.holdings.map((h: any) => <tr key={h.asset}><td><strong>{h.asset}</strong><span className="block text-xs text-navy-200">Avg cost {money(Number(h.avg_cost))}</span></td><td>{number(Number(h.quantity))}</td><td>{money(Number(h.market_value))}</td><td className={Number(h.unrealized_pnl) >= 0 ? 'positive' : 'negative'}>{money(Number(h.unrealized_pnl))}<span className="block text-xs">{Number(h.unrealized_pnl_pct).toFixed(2)}%</span></td><td>{(Number(h.current_weight) * 100).toFixed(1)}%</td></tr>)}</tbody></table></div></section>
    <section className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]"><div className="card"><div className="section-head"><div><p className="eyebrow">Cash activity</p><h2 className="section-title">Recent transactions</h2></div><Link to="/wallet" className="icon-link"><ArrowUpRight size={18}/></Link></div><div className="mt-3">{wallet?.recent_transactions?.slice(0,5).map((item:any)=><div key={item.id} className="flex items-center justify-between border-b border-white/[.07] py-3 last:border-0"><div><p className="text-sm font-medium">{item.memo}</p><p className="text-xs text-navy-200">{new Date(item.created_at).toLocaleDateString('en-IN')}</p></div><span className={item.entry_type==='CREDIT'?'positive':'negative'}>{item.entry_type==='CREDIT'?'+':'−'}{money(Number(item.amount))}</span></div>) || <p className="muted py-5">No transactions yet.</p>}</div></div><div className="card"><div className="section-head"><div><p className="eyebrow">Strategy check</p><h2 className="section-title">Current vs target</h2></div><Link to="/rebalance" className="icon-link"><RefreshCw size={17}/></Link></div><div className="mt-5 space-y-4">{dashboard.target_allocation ? Object.entries(dashboard.target_allocation).map(([asset,target]:any)=>{const holding=dashboard.holdings.find((h:any)=>h.asset===asset);const current=holding?Number(holding.current_weight)*100:0;const goal=Number(target)*100;return <div key={asset}><div className="mb-1.5 flex justify-between text-xs"><span>{asset}</span><span className="text-navy-200">{current.toFixed(1)}% / {goal.toFixed(0)}%</span></div><div className="h-1.5 rounded-full bg-[#0F1723]"><div className="h-full rounded-full bg-emerald" style={{width:`${Math.min(current,100)}%`}}/></div></div>}) : <p className="muted">Complete your risk profile to set a target allocation.</p>}</div>{dashboard.needs_rebalance&&<Link to="/rebalance" className="mt-6 flex items-center justify-between rounded-xl border border-champagne/20 bg-champagne-50 p-3 text-xs text-champagne">Review rebalance suggestion <ArrowUpRight size={15}/></Link>}</div></section>
    <div className="flex items-center gap-2 text-xs text-navy-200"><ShieldCheck size={15} className="text-emerald"/> Prices are sourced from the backend cache/fallback layer. All values are virtual INR.</div>
  </div>;
}
function Stat({ title, value, icon, positive }: any) { return <div className="card"><div className="flex items-center justify-between"><span className="eyebrow">{title}</span><span className={positive === false ? 'stat-icon red' : 'stat-icon'}>{icon}</span></div><p className="mt-6 text-2xl font-semibold">{value}</p></div>; }
function Loading() { return <div className="space-y-5 animate-pulse"><div className="h-10 w-64 rounded bg-white"/><div className="grid gap-4 md:grid-cols-3"><div className="h-36 rounded-2xl bg-navy/10 md:col-span-1"/><div className="h-36 rounded-2xl bg-white"/><div className="h-36 rounded-2xl bg-white"/></div></div>; }
function Empty() { return <div className="flex h-full items-center justify-center text-sm text-navy-200">No price history available.</div>; }
