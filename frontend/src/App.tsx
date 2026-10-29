import { useEffect, useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type DashboardSummary = {
  meals_served: number;
  food_wasted_kg: number;
  waste_percentage: number;
  estimated_waste_cost: number;
  active_users: number;
};

type TrendPoint = { date: string; served: number; waste: number; attendance: number };

type CropData = { id: number; name: string; category: string; unit: string };
type MarketData = { id: number; name: string; location: string; currency: string };

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000/api' : '/api');

const roles = [
  { label: 'Admin', value: 'admin' },
  { label: 'Canteen Manager', value: 'canteen_manager' },
  { label: 'Farmer / Buyer', value: 'farmer_buyer' },
];

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [selectedRole, setSelectedRole] = useState('admin');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [dashboard, setDashboard] = useState<{ summary: DashboardSummary; trend_series: TrendPoint[]; recommendations: string[] } | null>(null);
  const [crops, setCrops] = useState<CropData[]>([]);
  const [markets, setMarkets] = useState<MarketData[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<number>(1);
  const [selectedMarket, setSelectedMarket] = useState<number>(1);
  const [cropForecast, setCropForecast] = useState<any>(null);
  const [wasteRecords, setWasteRecords] = useState<any[]>([]);
  const [procurement, setProcurement] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const metrics = useMemo(() => {
    if (!dashboard) return [] as { label: string; value: string; color: string }[];
    return [
      { label: 'Meals served', value: dashboard.summary.meals_served.toLocaleString(), color: '#2d8cff' },
      { label: 'Food wasted', value: `${dashboard.summary.food_wasted_kg} kg`, color: '#ff7b7b' },
      { label: 'Waste %', value: `${dashboard.summary.waste_percentage}%`, color: '#a78bfa' },
      { label: 'Waste cost', value: `₹${dashboard.summary.estimated_waste_cost.toLocaleString()}`, color: '#22c55e' },
    ];
  }, [dashboard]);

  const fetchDashboard = async () => {
    const response = await fetch(`${API_BASE}/dashboard`);
    const data = await response.json();
    setDashboard(data);
  };

  const fetchReferenceData = async () => {
    const [cropRes, marketRes, planRes, wasteRes] = await Promise.all([
      fetch(`${API_BASE}/crops`),
      fetch(`${API_BASE}/markets`),
      fetch(`${API_BASE}/procurement/planning`),
      fetch(`${API_BASE}/waste/records`),
    ]);
    const cropData = await cropRes.json();
    const marketData = await marketRes.json();
    const procurementData = await planRes.json();
    const wasteData = await wasteRes.json();
    setCrops(cropData);
    setMarkets(marketData);
    setProcurement(procurementData);
    setWasteRecords(wasteData);
    if (cropData[0]) setSelectedCrop(cropData[0].id);
    if (marketData[0]) setSelectedMarket(marketData[0].id);
  };

  const getCropForecast = async () => {
    if (!selectedCrop || !selectedMarket) return;
    const response = await fetch(`${API_BASE}/crops/${selectedCrop}/prices?market_id=${selectedMarket}&horizon_days=7`);
    const data = await response.json();
    setCropForecast(data);
  };

  useEffect(() => {
    if (loggedIn) {
      fetchDashboard();
      fetchReferenceData();
      getCropForecast();
    }
  }, [loggedIn]);

  useEffect(() => {
    if (loggedIn) getCropForecast();
  }, [selectedCrop, selectedMarket]);

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error('Invalid username/password');
      const data = await response.json();
      if (data.user?.role) setSelectedRole(data.user.role);
      setLoggedIn(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEntrySubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      entry_date: form.get('entry_date'),
      meal_type: form.get('meal_type'),
      menu_name: form.get('menu_name'),
      expected_attendance: Number(form.get('expected_attendance')),
      actual_attendance: Number(form.get('actual_attendance')),
      meals_prepared: Number(form.get('meals_prepared')),
      meals_served: Number(form.get('meals_served')),
      leftover_quantity_kg: Number(form.get('leftover_quantity_kg')),
      donated_kg: Number(form.get('donated_kg')),
      reused_kg: Number(form.get('reused_kg')),
      discarded_kg: Number(form.get('discarded_kg')),
      notes: form.get('notes') || '',
    };
    await fetch(`${API_BASE}/waste/records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    event.currentTarget.reset();
    fetchDashboard();
    fetchReferenceData();
  };

  if (!loggedIn) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <div className="brand-box">
            <div className="brand-mark">AI</div>
            <div>
              <h1>AgriWaste Intelligence</h1>
              <p>Campus food waste meets crop market intelligence</p>
            </div>
          </div>
          <div className="role-grid">
            {roles.map((role) => (
              <button key={role.value} className={selectedRole === role.value ? 'role-btn active' : 'role-btn'} onClick={() => setSelectedRole(role.value)}>
                {role.label}
              </button>
            ))}
          </div>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p className="error-text">{error}</p>}
          <button className="primary-btn" onClick={handleLogin} disabled={loading}>
            {loading ? 'Logging in...' : 'Access demo app'}
          </button>
          <div className="demo-box">
            <strong>Demo credentials</strong>
            <div>admin / admin123</div>
            <div>canteen / canteen123</div>
            <div>farmer / farmer123</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <h2>AgriWaste Intelligence</h2>
          <small>Shared agri-to-canteen demand and pricing view</small>
        </div>
        <button className="secondary-btn" onClick={() => setLoggedIn(false)}>Logout</button>
      </header>

      <main className="main-grid">
        <section className="panel hero-panel">
          <div className="section-header">
            <h3>Mission summary</h3>
          </div>
          <div className="stat-grid">
            {metrics.map((item) => (
              <div key={item.label} className="stat-card" style={{ borderTop: `4px solid ${item.color}` }}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-header">
            <h3>Food waste trends</h3>
          </div>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={dashboard?.trend_series || []}>
                <defs>
                  <linearGradient id="servedStroke" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#2d8cff" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#2d8cff" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="served" stroke="#2d8cff" fill="url(#servedStroke)" />
                <Area type="monotone" dataKey="waste" stroke="#ff7b7b" fill="rgba(255,123,123,0.3)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel">
          <div className="section-header">
            <h3>Predicted demand and waste</h3>
          </div>
          <div className="recommendation-list">
            {dashboard?.recommendations.map((item) => <div key={item} className="recommendation-item">{item}</div>)}
          </div>
        </section>

        <section className="panel">
          <div className="section-header">
            <h3>Meal entry</h3>
          </div>
          <form className="entry-form" onSubmit={handleEntrySubmit}>
            <div className="form-grid">
              <input type="date" name="entry_date" defaultValue={new Date().toISOString().slice(0,10)} required />
              <input name="meal_type" placeholder="Meal type" defaultValue="Lunch" required />
              <input name="menu_name" placeholder="Menu item" defaultValue="Rice + Curry" required />
              <input name="expected_attendance" type="number" placeholder="Expected attendance" defaultValue={390} required />
              <input name="actual_attendance" type="number" placeholder="Actual attendance" defaultValue={400} required />
              <input name="meals_prepared" type="number" placeholder="Prepared" defaultValue={500} required />
              <input name="meals_served" type="number" placeholder="Served" defaultValue={420} required />
              <input name="leftover_quantity_kg" type="number" step="0.1" placeholder="Leftover kg" defaultValue={23.5} required />
              <input name="donated_kg" type="number" step="0.1" placeholder="Donated kg" defaultValue={5.8} />
              <input name="reused_kg" type="number" step="0.1" placeholder="Reused kg" defaultValue={9.5} />
              <input name="discarded_kg" type="number" step="0.1" placeholder="Discarded kg" defaultValue={8.2} />
              <textarea name="notes" placeholder="Notes" defaultValue="Demand slightly above forecast" />
            </div>
            <button type="submit" className="primary-btn">Save meal record</button>
          </form>
        </section>

        <section className="panel">
          <div className="section-header">
            <h3>Crop market prediction</h3>
          </div>
          <div className="selector-row">
            <select value={selectedCrop} onChange={(e) => setSelectedCrop(Number(e.target.value))}>
              {crops.map((crop) => <option key={crop.id} value={crop.id}>{crop.name}</option>)}
            </select>
            <select value={selectedMarket} onChange={(e) => setSelectedMarket(Number(e.target.value))}>
              {markets.map((market) => <option key={market.id} value={market.id}>{market.name}</option>)}
            </select>
          </div>
          {cropForecast ? (
            <>
              <div className="forecast-strip">
                <div>
                  <span>Current price</span>
                  <strong>₹{cropForecast.current_price}</strong>
                </div>
                <div>
                  <span>Forecast</span>
                  <strong>₹{cropForecast.forecast.predicted_price}</strong>
                </div>
                <div>
                  <span>Trend</span>
                  <strong>{cropForecast.forecast.direction}</strong>
                </div>
              </div>
              <p className="small-note">{cropForecast.demo_notice}</p>
              <div className="chart-box">
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={cropForecast.history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="price" stroke="#16a34a" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : <p>Loading crop prediction...</p>}
        </section>

        <section className="panel">
          <div className="section-header">
            <h3>Procurement planning</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ingredient</th>
                  <th>Market</th>
                  <th>Target</th>
                  <th>Req. kg</th>
                  <th>Est. cost</th>
                </tr>
              </thead>
              <tbody>
                {procurement.map((plan) => (
                  <tr key={plan.id}>
                    <td>{plan.ingredient_name}</td>
                    <td>{plan.market_name}</td>
                    <td>{plan.target_date}</td>
                    <td>{plan.required_kg}</td>
                    <td>₹{plan.estimated_cost.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel">
          <div className="section-header">
            <h3>Waste record log</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Menu</th>
                  <th>Served</th>
                  <th>Waste</th>
                  <th>Donated</th>
                </tr>
              </thead>
              <tbody>
                {wasteRecords.slice(0, 7).map((item) => (
                  <tr key={item.id}>
                    <td>{item.entry_date}</td>
                    <td>{item.menu_name}</td>
                    <td>{item.meals_served}</td>
                    <td>{item.leftover_quantity_kg} kg</td>
                    <td>{item.donated_kg} kg</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
