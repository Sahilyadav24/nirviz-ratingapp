import { useState, useEffect } from "react";
import Head from "next/head";
import axios from "axios";
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL;

interface Visit {
  prize_name: string;
  visited_at: string;
}

interface CustomerRecord {
  name: string;
  phone: string;
  email: string | null;
  address: string;
  visit_count: number;
  visits: Visit[];
  first_visit: string;
  last_visit: string;
}

interface AdminData {
  total_customers: number;
  today_registrations: number;
  customers: CustomerRecord[];
}

interface Prize {
  id: string;
  name: string;
  description: string;
  probability: number;
  is_active: boolean;
  total_assigned: number;
}

interface Analytics {
  prize_distribution: { name: string; count: number }[];
  daily_registrations: { date: string; count: number }[];
  repeat_visitor_percentage: number;
  peak_hours: { hour: number; count: number }[];
  total_assignments: number;
}

export default function AdminPage() {
  const [password, setPassword] = useState("");
  const [savedPassword, setSavedPassword] = useState("");
  const [data, setData] = useState<AdminData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<"customers" | "analytics" | "prizes">("customers");

  // Analytics state
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Prize state
  const [prizes, setPrizes] = useState<Prize[]>([]);
  const [prizesLoading, setPrizesLoading] = useState(false);
  const [editingPrize, setEditingPrize] = useState<Prize | null>(null);
  const [editForm, setEditForm] = useState({ name: "", description: "", probability: "" });
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({ name: "", description: "", probability: "" });
  const [prizeError, setPrizeError] = useState("");
  const [prizeSuccess, setPrizeSuccess] = useState("");

  const headers = { "x-admin-password": savedPassword };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/v1/admin/customers`, {
        headers: { "x-admin-password": password },
      });
      setData(res.data);
      setSavedPassword(password);
    } catch {
      setError("Invalid password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/v1/admin/customers`, { headers });
      setData(res.data);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setData(null);
    setPassword("");
    setSavedPassword("");
    setSearch("");
    setExpanded(new Set());
    setPrizes([]);
    setActiveTab("customers");
  };

  const toggleExpand = (index: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  const filtered = (data?.customers ?? []).filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.phone.includes(search)
  );

  const downloadCSV = () => {
    if (!data) return;
    const rows = [
      ["Name", "Phone", "Email", "Address", "Total Visits", "Prizes Won", "First Visit (IST)", "Last Visit (IST)"],
      ...data.customers.map((c) => [
        c.name,
        `+91${c.phone}`,
        c.email ?? "—",
        `"${c.address.replace(/"/g, '""')}"`,
        c.visit_count,
        `"${c.visits.map((v) => v.prize_name).join(", ")}"`,
        c.first_visit,
        c.last_visit,
      ]),
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nirviz_customers_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── Prize helpers ─────────────────────────────────────────────────────────

  const loadPrizes = async () => {
    setPrizesLoading(true);
    setPrizeError("");
    try {
      const res = await axios.get(`${API}/api/v1/admin/prizes`, { headers });
      setPrizes(res.data);
    } catch {
      setPrizeError("Failed to load prizes.");
    } finally {
      setPrizesLoading(false);
    }
  };

  const loadAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const res = await axios.get(`${API}/api/v1/admin/analytics`, { headers });
      setAnalytics(res.data);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleTabChange = (tab: "customers" | "analytics" | "prizes") => {
    setActiveTab(tab);
    if (tab === "prizes" && prizes.length === 0) loadPrizes();
    if (tab === "analytics" && !analytics) loadAnalytics();
  };

  const totalProbability = prizes.reduce((sum, p) => sum + (p.is_active ? p.probability : 0), 0);
  const probOk = Math.abs(totalProbability - 1.0) < 0.01;

  const flashSuccess = (msg: string) => {
    setPrizeSuccess(msg);
    setTimeout(() => setPrizeSuccess(""), 3000);
  };

  const startEdit = (prize: Prize) => {
    setEditingPrize(prize);
    setEditForm({
      name: prize.name,
      description: prize.description,
      probability: String(prize.probability),
    });
  };

  const saveEdit = async () => {
    if (!editingPrize) return;
    setPrizeError("");
    try {
      await axios.put(
        `${API}/api/v1/admin/prizes/${editingPrize.id}`,
        {
          name: editForm.name,
          description: editForm.description,
          probability: parseFloat(editForm.probability),
        },
        { headers }
      );
      setEditingPrize(null);
      await loadPrizes();
      flashSuccess("Prize updated successfully.");
    } catch (err: any) {
      setPrizeError(err?.response?.data?.detail ?? "Failed to update prize.");
    }
  };

  const toggleActive = async (prize: Prize) => {
    setPrizeError("");
    try {
      await axios.patch(`${API}/api/v1/admin/prizes/${prize.id}/toggle`, {}, { headers });
      await loadPrizes();
      flashSuccess(`Prize ${prize.is_active ? "deactivated" : "activated"}.`);
    } catch {
      setPrizeError("Failed to toggle prize status.");
    }
  };

  const deletePrize = async (prize: Prize) => {
    if (!confirm(`Delete "${prize.name}"? This cannot be undone.`)) return;
    setPrizeError("");
    try {
      await axios.delete(`${API}/api/v1/admin/prizes/${prize.id}`, { headers });
      await loadPrizes();
      flashSuccess("Prize deleted.");
    } catch (err: any) {
      setPrizeError(err?.response?.data?.detail ?? "Failed to delete prize.");
    }
  };

  const addPrize = async (e: React.FormEvent) => {
    e.preventDefault();
    setPrizeError("");
    try {
      await axios.post(
        `${API}/api/v1/admin/prizes`,
        {
          name: addForm.name,
          description: addForm.description,
          probability: parseFloat(addForm.probability),
        },
        { headers }
      );
      setAddForm({ name: "", description: "", probability: "" });
      setShowAddForm(false);
      await loadPrizes();
      flashSuccess("Prize added successfully.");
    } catch (err: any) {
      setPrizeError(err?.response?.data?.detail ?? "Failed to add prize.");
    }
  };

  // ── Login screen ──────────────────────────────────────────────────────────
  if (!data) {
    return (
      <>
        <Head>
          <title>Admin Login — NIRVIZ Resort</title>
        </Head>
        <main className="min-h-screen flex items-center justify-center px-4">
          <div className="w-full max-w-sm bg-white rounded-2xl shadow-lg p-8">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-brand-dark">Admin Login</h1>
              <p className="text-sm text-gray-500 mt-1">NIRVIZ Resort — Customer Dashboard</p>
            </div>
            <form onSubmit={handleLogin} className="flex flex-col gap-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter admin password"
                required
                className="border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
              />
              {error && <p className="text-red-500 text-sm text-center">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="bg-brand text-white font-semibold py-3 rounded-xl text-base active:scale-95 transition-transform disabled:opacity-60"
              >
                {loading ? "Logging in..." : "Login"}
              </button>
            </form>
          </div>
        </main>
      </>
    );
  }

  // ── Dashboard ─────────────────────────────────────────────────────────────
  return (
    <>
      <Head>
        <title>Admin Dashboard — NIRVIZ Resort</title>
      </Head>
      <main className="min-h-screen px-4 py-8">
        <div className="max-w-6xl mx-auto">

          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-2xl font-bold text-brand-dark">NIRVIZ Resort</h1>
              <p className="text-sm text-gray-500">Admin Dashboard</p>
            </div>
            <div className="flex gap-3 items-center">
              {activeTab === "customers" && (
                <button onClick={handleRefresh} disabled={loading} className="text-sm text-brand underline disabled:opacity-50">
                  {loading ? "Refreshing..." : "Refresh"}
                </button>
              )}
              {activeTab === "analytics" && (
                <button onClick={loadAnalytics} disabled={analyticsLoading} className="text-sm text-brand underline disabled:opacity-50">
                  {analyticsLoading ? "Loading..." : "Refresh"}
                </button>
              )}
              {activeTab === "prizes" && (
                <button onClick={loadPrizes} disabled={prizesLoading} className="text-sm text-brand underline disabled:opacity-50">
                  {prizesLoading ? "Loading..." : "Refresh"}
                </button>
              )}
              <button onClick={handleLogout} className="text-sm text-gray-400 underline">
                Logout
              </button>
            </div>
          </div>

          {/* Stats cards */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-white rounded-xl shadow p-5 text-center">
              <p className="text-4xl font-bold text-brand-dark">{data.total_customers}</p>
              <p className="text-sm text-gray-500 mt-1">Total Customers</p>
            </div>
            <div className="bg-white rounded-xl shadow p-5 text-center">
              <p className="text-4xl font-bold text-brand-dark">{data.today_registrations}</p>
              <p className="text-sm text-gray-500 mt-1">Today&apos;s Registrations</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-5 bg-gray-100 p-1 rounded-xl w-fit">
            <button
              onClick={() => handleTabChange("customers")}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${
                activeTab === "customers"
                  ? "bg-white text-brand-dark shadow"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Customers
            </button>
            <button
              onClick={() => handleTabChange("analytics")}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${
                activeTab === "analytics"
                  ? "bg-white text-brand-dark shadow"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Analytics
            </button>
            <button
              onClick={() => handleTabChange("prizes")}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${
                activeTab === "prizes"
                  ? "bg-white text-brand-dark shadow"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Prize Management
            </button>
          </div>

          {/* ── Customers Tab ─────────────────────────────────────────────── */}
          {activeTab === "customers" && (
            <>
              <div className="flex gap-3 mb-4">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name or phone..."
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
                />
                <button
                  onClick={downloadCSV}
                  className="bg-brand text-white font-semibold px-4 py-2 rounded-lg text-sm whitespace-nowrap active:scale-95 transition-transform"
                >
                  Download CSV
                </button>
              </div>

              <div className="bg-white rounded-xl shadow overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-amber-50">
                      <th className="text-left px-4 py-3 font-semibold text-gray-600">Name</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-600">Phone</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-600">Email</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-600">Address</th>
                      <th className="text-center px-4 py-3 font-semibold text-gray-600">Visits</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-600">Last Prize Won</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-600">Last Visit (IST)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-10 text-gray-400">
                          No customers found
                        </td>
                      </tr>
                    )}
                    {filtered.map((c, i) => (
                      <>
                        <tr
                          key={`row-${i}`}
                          className={`border-b border-gray-50 transition-colors ${
                            c.visit_count > 1
                              ? "cursor-pointer hover:bg-amber-50/60"
                              : "hover:bg-gray-50/50"
                          }`}
                          onClick={() => c.visit_count > 1 && toggleExpand(i)}
                        >
                          <td className="px-4 py-3 font-medium text-gray-800">
                            {c.visit_count > 1 && (
                              <span className="mr-1 text-brand">
                                {expanded.has(i) ? "▾" : "▸"}
                              </span>
                            )}
                            {c.name}
                          </td>
                          <td className="px-4 py-3 text-gray-600">+91{c.phone}</td>
                          <td className="px-4 py-3 text-gray-500 text-xs">
                            {c.email ?? <span className="text-gray-300">—</span>}
                          </td>
                          <td className="px-4 py-3 text-gray-500 max-w-[180px]">
                            <span className="block truncate">{c.address}</span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="bg-brand-light text-brand-dark font-bold px-2.5 py-0.5 rounded-full text-xs">
                              {c.visit_count}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-gray-700 font-medium">
                            {c.visits.at(-1)?.prize_name ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-xs">{c.last_visit}</td>
                        </tr>

                        {expanded.has(i) &&
                          c.visits.map((v, j) => (
                            <tr
                              key={`visit-${i}-${j}`}
                              className="bg-amber-50/30 border-b border-gray-50"
                            >
                              <td className="px-8 py-2 text-xs text-gray-400 italic">
                                Visit {j + 1}
                              </td>
                              <td colSpan={4} className="px-4 py-2 text-xs text-gray-500">
                                {v.visited_at}
                              </td>
                              <td className="px-4 py-2 text-xs text-brand-dark font-semibold">
                                {v.prize_name}
                              </td>
                              <td />
                            </tr>
                          ))}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="text-xs text-gray-400 text-center mt-4">
                All times shown in Indian Standard Time (IST, UTC+5:30)
              </p>
            </>
          )}

          {/* ── Analytics Tab ─────────────────────────────────────────────── */}
          {activeTab === "analytics" && (
            <div>
              {analyticsLoading && (
                <div className="text-center py-16 text-gray-400">Loading analytics...</div>
              )}
              {!analyticsLoading && analytics && (
                <div className="flex flex-col gap-6">

                  {/* Stat cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white rounded-xl shadow p-4 text-center">
                      <p className="text-3xl font-bold text-brand-dark">{data.total_customers}</p>
                      <p className="text-xs text-gray-500 mt-1">Total Customers</p>
                    </div>
                    <div className="bg-white rounded-xl shadow p-4 text-center">
                      <p className="text-3xl font-bold text-brand-dark">{analytics.total_assignments}</p>
                      <p className="text-xs text-gray-500 mt-1">Total Prizes Assigned</p>
                    </div>
                    <div className="bg-white rounded-xl shadow p-4 text-center">
                      <p className="text-3xl font-bold text-brand-dark">{analytics.repeat_visitor_percentage}%</p>
                      <p className="text-xs text-gray-500 mt-1">Repeat Visitors</p>
                    </div>
                    <div className="bg-white rounded-xl shadow p-4 text-center">
                      <p className="text-3xl font-bold text-brand-dark">{data.today_registrations}</p>
                      <p className="text-xs text-gray-500 mt-1">Today&apos;s Registrations</p>
                    </div>
                  </div>

                  {/* Prize Distribution */}
                  <div className="bg-white rounded-xl shadow p-5">
                    <h3 className="font-semibold text-gray-700 mb-4">Prize Distribution</h3>
                    {mounted && (
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={analytics.prize_distribution} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>

                  {/* Daily Registrations */}
                  <div className="bg-white rounded-xl shadow p-5">
                    <h3 className="font-semibold text-gray-700 mb-4">Daily Registrations (Last 30 Days)</h3>
                    {analytics.daily_registrations.length === 0 ? (
                      <p className="text-sm text-gray-400 text-center py-8">No data yet</p>
                    ) : mounted && (
                      <ResponsiveContainer width="100%" height={220}>
                        <LineChart data={analytics.daily_registrations} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                          <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Line type="monotone" dataKey="count" stroke="#f59e0b" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </div>

                  {/* Peak Hours */}
                  <div className="bg-white rounded-xl shadow p-5">
                    <h3 className="font-semibold text-gray-700 mb-1">Peak Hours (IST)</h3>
                    <p className="text-xs text-gray-400 mb-4">When customers register most often</p>
                    {analytics.peak_hours.length === 0 ? (
                      <p className="text-sm text-gray-400 text-center py-8">No data yet</p>
                    ) : mounted && (
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={analytics.peak_hours} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                          <XAxis dataKey="hour" tick={{ fontSize: 11 }} tickFormatter={(h) => `${h}:00`} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip formatter={(v) => [v, "Registrations"]} labelFormatter={(h) => `${h}:00 – ${h}:59`} />
                          <Bar dataKey="count" fill="#92400e" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>

                </div>
              )}
            </div>
          )}

          {/* ── Prizes Tab ────────────────────────────────────────────────── */}
          {activeTab === "prizes" && (
            <div>
              {/* Probability warning */}
              {prizes.length > 0 && !probOk && (
                <div className="mb-4 bg-orange-50 border border-orange-200 rounded-xl px-4 py-3 text-sm text-orange-700">
                  Active prize probabilities sum to <strong>{(totalProbability * 100).toFixed(1)}%</strong> — must equal 100%. Adjust probabilities before prizes can be won correctly.
                </div>
              )}
              {prizes.length > 0 && probOk && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-700">
                  Probabilities are balanced at 100%.
                </div>
              )}

              {prizeError && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600">
                  {prizeError}
                </div>
              )}
              {prizeSuccess && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-700">
                  {prizeSuccess}
                </div>
              )}

              {/* Add Prize button */}
              <div className="flex justify-end mb-4">
                <button
                  onClick={() => { setShowAddForm(!showAddForm); setPrizeError(""); }}
                  className="bg-brand text-white font-semibold px-4 py-2 rounded-lg text-sm active:scale-95 transition-transform"
                >
                  {showAddForm ? "Cancel" : "+ Add Prize"}
                </button>
              </div>

              {/* Add Prize form */}
              {showAddForm && (
                <form onSubmit={addPrize} className="bg-white rounded-xl shadow p-5 mb-5 flex flex-col gap-3">
                  <h3 className="font-semibold text-gray-700">New Prize</h3>
                  <input
                    type="text"
                    placeholder="Prize name"
                    value={addForm.name}
                    onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                    required
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand"
                  />
                  <input
                    type="text"
                    placeholder="Description"
                    value={addForm.description}
                    onChange={(e) => setAddForm({ ...addForm, description: e.target.value })}
                    required
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand"
                  />
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Probability (0.01 – 1.0)"
                      value={addForm.probability}
                      onChange={(e) => setAddForm({ ...addForm, probability: e.target.value })}
                      step="0.01" min="0.01" max="1"
                      required
                      className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand"
                    />
                    <span className="text-xs text-gray-400">e.g. 0.30 = 30%</span>
                  </div>
                  <button
                    type="submit"
                    className="bg-brand text-white font-semibold py-2 rounded-lg text-sm active:scale-95 transition-transform"
                  >
                    Add Prize
                  </button>
                </form>
              )}

              {/* Prizes table */}
              {prizesLoading ? (
                <div className="text-center py-12 text-gray-400">Loading prizes...</div>
              ) : (
                <div className="bg-white rounded-xl shadow overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 bg-amber-50">
                        <th className="text-left px-4 py-3 font-semibold text-gray-600">Prize Name</th>
                        <th className="text-left px-4 py-3 font-semibold text-gray-600">Description</th>
                        <th className="text-center px-4 py-3 font-semibold text-gray-600">Probability</th>
                        <th className="text-center px-4 py-3 font-semibold text-gray-600">Status</th>
                        <th className="text-center px-4 py-3 font-semibold text-gray-600">Times Won</th>
                        <th className="text-center px-4 py-3 font-semibold text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {prizes.length === 0 && (
                        <tr>
                          <td colSpan={6} className="text-center py-10 text-gray-400">
                            No prizes found. Add one above.
                          </td>
                        </tr>
                      )}
                      {prizes.map((prize) =>
                        editingPrize?.id === prize.id ? (
                          <tr key={prize.id} className="border-b border-gray-100 bg-amber-50/30">
                            <td className="px-3 py-2">
                              <input
                                value={editForm.name}
                                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:border-brand"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <input
                                value={editForm.description}
                                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:border-brand"
                              />
                            </td>
                            <td className="px-3 py-2 text-center">
                              <input
                                type="number"
                                step="0.01" min="0.01" max="1"
                                value={editForm.probability}
                                onChange={(e) => setEditForm({ ...editForm, probability: e.target.value })}
                                className="w-24 border border-gray-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:border-brand"
                              />
                            </td>
                            <td colSpan={2} />
                            <td className="px-3 py-2 text-center">
                              <div className="flex gap-2 justify-center">
                                <button
                                  onClick={saveEdit}
                                  className="bg-brand text-white text-xs font-semibold px-3 py-1 rounded-lg active:scale-95"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={() => setEditingPrize(null)}
                                  className="text-gray-400 text-xs underline"
                                >
                                  Cancel
                                </button>
                              </div>
                            </td>
                          </tr>
                        ) : (
                          <tr key={prize.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                            <td className="px-4 py-3 font-medium text-gray-800">{prize.name}</td>
                            <td className="px-4 py-3 text-gray-500 max-w-[220px]">
                              <span className="block truncate">{prize.description}</span>
                            </td>
                            <td className="px-4 py-3 text-center font-semibold text-gray-700">
                              {(prize.probability * 100).toFixed(1)}%
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                                  prize.is_active
                                    ? "bg-green-100 text-green-700"
                                    : "bg-gray-100 text-gray-500"
                                }`}
                              >
                                {prize.is_active ? "Active" : "Inactive"}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center text-gray-600">{prize.total_assigned}</td>
                            <td className="px-4 py-3 text-center">
                              <div className="flex gap-2 justify-center flex-wrap">
                                <button
                                  onClick={() => startEdit(prize)}
                                  className="text-xs text-brand underline"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => toggleActive(prize)}
                                  className={`text-xs underline ${prize.is_active ? "text-orange-500" : "text-green-600"}`}
                                >
                                  {prize.is_active ? "Deactivate" : "Activate"}
                                </button>
                                <button
                                  onClick={() => deletePrize(prize)}
                                  className="text-xs text-red-400 underline"
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              <p className="text-xs text-gray-400 text-center mt-4">
                Active prize probabilities must sum to 1.0 (100%) for correct prize distribution.
              </p>
            </div>
          )}

        </div>
      </main>
    </>
  );
}
