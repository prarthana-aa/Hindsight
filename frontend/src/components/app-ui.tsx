import { ReactNode } from 'react';
import { ArrowDownLeft, ArrowUpRight, Check, CircleAlert, Info, LoaderCircle } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export const appMoney = (value: number, digits = 0) => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: digits })}`;
export const appNumber = (value: number, digits = 3) => Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: digits });
export const appDate = (value?: string) => value ? new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: ReactNode }) {
  return <header className="app-page-header"><div><p className="app-eyebrow">{eyebrow}</p><h1 className="app-page-title">{title}</h1>{description && <p className="app-page-description">{description}</p>}</div>{action}</header>;
}

export function SectionLabel({ children }: { children: ReactNode }) { return <p className="app-eyebrow">{children}</p>; }
export function AppButton({ children, variant = 'primary', className = '', ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'quiet' | 'danger' }) { return <button className={`app-button app-button-${variant} ${className}`} {...props}>{children}</button>; }
export function AppLinkButton({ children, variant = 'secondary', className = '', ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { variant?: 'primary' | 'secondary' | 'quiet' }) { return <a className={`app-button app-button-${variant} ${className}`} {...props}>{children}</a>; }

export function Surface({ children, className = '', as: Tag = 'section' }: { children: ReactNode; className?: string; as?: any }) { return <Tag className={`app-surface ${className}`}>{children}</Tag>; }
export function LoadingSkeleton({ rows = 3 }: { rows?: number }) { return <div className="app-loading" aria-label="Loading"><div className="app-skeleton app-skeleton-title"/>{Array.from({ length: rows }).map((_, i) => <div className="app-skeleton" key={i}/>)}</div>; }
export function EmptyState({ icon = <Info size={18}/>, title, description, action }: { icon?: ReactNode; title: string; description: string; action?: ReactNode }) { return <div className="app-empty"><span className="app-empty-icon">{icon}</span><h3>{title}</h3><p>{description}</p>{action}</div>; }
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) { return <div className="app-error"><CircleAlert size={17}/><span>{message}</span>{onRetry && <AppButton variant="quiet" onClick={onRetry}>Retry</AppButton>}</div>; }

export function MetricDisplay({ label, value, helper, tone = 'default', className = '' }: { label: string; value: string; helper?: string; tone?: 'default' | 'positive' | 'negative' | 'accent'; className?: string }) {
  return <div className={`app-metric ${className}`}><span className="app-metric-label">{label}</span><strong className={`app-metric-value app-tone-${tone}`}>{value}</strong>{helper && <span className="app-metric-helper">{helper}</span>}</div>;
}

const allocationColors = ['#4C9B79', '#C9A66B', '#A5A5A0', '#777770'];
export function AllocationChart({ data }: { data: { name: string; value: number }[] }) {
  if (!data.length) return <EmptyState title="No holdings yet" description="Your allocation will appear here after you place an investment." />;
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return <div className="app-allocation"><div className="app-donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="value" nameKey="name" innerRadius="64%" outerRadius="88%" paddingAngle={3} stroke="none">{data.map((item, index) => <Cell key={item.name} fill={allocationColors[index % allocationColors.length]}/>)}</Pie><Tooltip contentStyle={{ background: '#181818', border: '1px solid rgba(232,229,213,.1)', color: '#E8E5D5' }} formatter={(value: any) => [appMoney(Number(value)), 'Value']}/></PieChart></ResponsiveContainer><div className="app-donut-center"><strong>{appMoney(total)}</strong><span>invested value</span></div></div><div className="app-allocation-legend">{data.map((item, index) => <div className="app-legend-row" key={item.name}><span className="app-legend-name"><i style={{ background: allocationColors[index % allocationColors.length] }}/>{item.name}</span><strong>{total ? `${((item.value / total) * 100).toFixed(1)}%` : '0%'}</strong></div>)}</div></div>;
}

export function MarketChart({ data, period, onPeriodChange }: { data: { date: string; value: number }[]; period: string; onPeriodChange: (period: string) => void }) {
  const periods = ['1W', '1M', '3M', '6M', '1Y', 'ALL'];
  return <div className="app-chart-wrap"><div className="app-chart-filters">{periods.map(item => <button key={item} className={period === item ? 'is-selected' : ''} onClick={() => onPeriodChange(item)}>{item}</button>)}</div>{data.length ? <div className="app-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 10, right: 4, bottom: 0, left: 0 }}><defs><linearGradient id="app-chart-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4C9B79" stopOpacity={0.2}/><stop offset="100%" stopColor="#4C9B79" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(232,229,213,.08)"/><XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={32} tick={{ fill: '#777770', fontSize: 11 }}/><YAxis hide domain={['dataMin - 100', 'dataMax + 100']}/><Tooltip contentStyle={{ background: '#181818', border: '1px solid rgba(232,229,213,.1)', borderRadius: 4, color: '#E8E5D5' }} labelStyle={{ color: '#A5A5A0' }} formatter={(value: any) => [appMoney(Number(value), 2), 'Reference price']}/><Area type="monotone" dataKey="value" stroke="#4C9B79" strokeWidth={2} fill="url(#app-chart-fill)"/></AreaChart></ResponsiveContainer></div> : <EmptyState title="History unavailable" description="The backend has not provided historical data for this period."/>}</div>;
}

export function StatusIndicator({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'positive' | 'negative' | 'neutral' | 'accent' }) { return <span className={`app-status app-status-${tone}`}><i/>{children}</span>; }

export function HoldingTable({ holdings }: { holdings: any[] }) {
  if (!holdings.length) return <EmptyState title="No holdings" description="Complete your risk profile or explore assets to get started." />;
  return <div className="app-table-scroll"><table className="app-table"><thead><tr><th>Asset</th><th>Units</th><th>Current price</th><th>Current value</th><th>Return</th></tr></thead><tbody>{holdings.map(h => { const positive = Number(h.unrealized_pnl) >= 0; return <tr key={h.asset}><td><strong>{h.asset}</strong><span>{h.asset === 'NIFTY50' ? 'Indian equity proxy' : h.asset === 'GILT' ? 'Government bonds proxy' : h.asset === 'GOLD' ? 'Gold proxy' : 'International equity proxy'}</span></td><td>{appNumber(Number(h.quantity))}</td><td>{appMoney(Number(h.current_price), 2)}</td><td>{appMoney(Number(h.market_value))}</td><td className={positive ? 'app-positive' : 'app-negative'}>{positive ? '+' : '−'}{appMoney(Math.abs(Number(h.unrealized_pnl)))}<span>{positive ? '+' : ''}{Number(h.unrealized_pnl_pct).toFixed(2)}%</span></td></tr>; })}</tbody></table></div>;
}

export function TransactionList({ entries, orders = [] }: { entries: any[]; orders?: any[] }) {
  const combined = [...entries.map(item => ({ ...item, kind: 'ledger', date: item.created_at, amount: Number(item.amount) * (item.entry_type === 'DEBIT' ? -1 : 1), title: item.memo, detail: item.entry_type === 'CREDIT' ? 'Wallet credit' : 'Wallet debit' })), ...orders.map(item => ({ ...item, kind: 'order', date: item.created_at, amount: item.side === 'BUY' ? -Number(item.net_amount) : Number(item.net_amount), title: `${item.side} ${item.asset}`, detail: `${appNumber(Number(item.quantity))} units · ${item.status}` }))].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 8);
  if (!combined.length) return <EmptyState title="No recent activity" description="Wallet movements and investment orders will appear here." />;
  return <div className="app-activity-list">{combined.map((item, index) => { const positive = item.amount >= 0; return <div className="app-activity-row" key={`${item.kind}-${item.id || index}`}><span className={`app-activity-icon ${positive ? 'is-positive' : 'is-negative'}`}>{positive ? <ArrowDownLeft size={15}/> : <ArrowUpRight size={15}/>}</span><div className="app-activity-copy"><strong>{item.title}</strong><span>{item.detail} · {appDate(item.date)}</span></div><strong className={positive ? 'app-positive' : 'app-negative'}>{positive ? '+' : '−'}{appMoney(Math.abs(item.amount), 2)}</strong></div>; })}</div>;
}

export function SavingNotice() { return <p className="app-disclaimer"><Check size={14}/> Educational simulation · all money is virtual INR.</p>; }
export function InlineLoader() { return <LoaderCircle size={16} className="app-spin"/>; }
