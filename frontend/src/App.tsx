import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Risk from './pages/Risk';
import Wallet from './pages/Wallet';
import Invest from './pages/Invest';
import Rebalance from './pages/Rebalance';
import Settings from './pages/Settings';
import Portfolio from './pages/Portfolio';
import Recommendations from './pages/Recommendations';
import Transactions from './pages/Transactions';
import AppLayout from './components/AppLayout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy"></div></div>;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/dashboard"
          element={<ProtectedRoute><AppLayout><Dashboard /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/risk"
          element={<ProtectedRoute><AppLayout><Risk /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/wallet"
          element={<ProtectedRoute><AppLayout><Wallet /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/invest"
          element={<ProtectedRoute><AppLayout><Invest /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/investments"
          element={<ProtectedRoute><AppLayout><Invest /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/portfolio"
          element={<ProtectedRoute><AppLayout><Portfolio /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/recommendations"
          element={<ProtectedRoute><AppLayout><Recommendations /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/transactions"
          element={<ProtectedRoute><AppLayout><Transactions /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/rebalance"
          element={<ProtectedRoute><AppLayout><Rebalance /></AppLayout></ProtectedRoute>}
        />
        <Route
          path="/settings"
          element={<ProtectedRoute><AppLayout><Settings /></AppLayout></ProtectedRoute>}
        />
      </Routes>
    </AuthProvider>
  );
}
