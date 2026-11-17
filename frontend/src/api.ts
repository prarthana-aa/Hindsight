import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hindsight_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('hindsight_token');
      localStorage.removeItem('hindsight_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

// Auth
export const authDemo = () => api.post('/auth/demo');
export const authLogin = (email: string, password: string) =>
  api.post('/auth/login', { email, password });
export const authSignup = (data: {
  email: string;
  password: string;
  full_name: string;
  age?: number;
  income_band?: string;
  employment_type?: string;
}) => api.post('/auth/signup', data);
export const authMe = () => api.get('/auth/me');
export const authDemoReset = () => api.post('/auth/demo/reset');

// Wallet
export const getWalletBalance = () => api.get('/wallet/balance');
export const walletDeposit = (amount: number, memo?: string) =>
  api.post('/wallet/deposit', { amount, memo });
export const getWalletLedger = (limit = 50, offset = 0) =>
  api.get(`/wallet/ledger?limit=${limit}&offset=${offset}`);
export const walletReconcile = () => api.get('/wallet/reconcile');

// Prices
export const getAllPrices = () => api.get('/prices/');
export const getAssetPrice = (asset: string) => api.get(`/prices/${asset}`);
export const getAssetHistory = (asset: string) =>
  api.get(`/prices/${asset}/history`);

// Portfolio
export const getPortfolioDashboard = () => api.get('/portfolio/dashboard');
export const placeOrder = (data: {
  asset: string;
  side: string;
  quantity: number;
  idempotency_key: string;
}) => api.post('/portfolio/order', data);
export const getOrders = () => api.get('/portfolio/orders');
export const rebalancePreview = () => api.post('/portfolio/rebalance/preview');
export const rebalanceExecute = () => api.post('/portfolio/rebalance/execute');

// Advice
export const getQuestions = () => api.get('/advice/questions');
export const scoreRisk = (data: {
  answers: Record<string, number>;
  goal_type?: string;
  horizon_years?: number;
}) => api.post('/advice/score', data);
export const applyAdvice = (data: {
  answers: Record<string, number>;
  goal_type?: string;
  horizon_years?: number;
}) => api.post('/advice/apply', data);

export default api;
