import { useState } from "react";
import Head from "next/head";
import axios from "axios";

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

export default function AdminPage() {
  const [password, setPassword] = useState("");
  const [savedPassword, setSavedPassword] = useState("");
  const [data, setData] = useState<AdminData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/customers`,
        { headers: { "x-admin-password": password } }
      );
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
      const res = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/customers`,
        { headers: { "x-admin-password": savedPassword } }
      );
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
              <p className="text-sm text-gray-500">Customer Database</p>
            </div>
            <div className="flex gap-3 items-center">
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="text-sm text-brand underline disabled:opacity-50"
              >
                {loading ? "Refreshing..." : "Refresh"}
              </button>
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

          {/* Search + CSV */}
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

          {/* Table */}
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
                    <td colSpan={6} className="text-center py-10 text-gray-400">
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
                      <td className="px-4 py-3 text-gray-500 text-xs">{c.email ?? <span className="text-gray-300">—</span>}</td>
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

                    {/* Expanded visit history */}
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
        </div>
      </main>
    </>
  );
}
