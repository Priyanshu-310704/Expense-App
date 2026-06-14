import React from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
  Link,
  Route,
  Routes,
  useNavigate,
  useLocation,
  Navigate,
} from "react-router-dom";
import {
  ArrowRightLeft,
  FileWarning,
  Home,
  LogOut,
  ReceiptText,
  Scale,
  UsersRound,
  WalletCards,
  User,
  Lock,
  Mail,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Upload,
  Eye,
  EyeOff,
} from "lucide-react";
import "./styles.css";

// ─── API helper ────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

type ApiOptions = RequestInit & { auth?: boolean };

async function api(path: string, options: ApiOptions = {}) {
  const token = localStorage.getItem("access");
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (options.auth !== false && token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }
  return response.json();
}

function formatMoney(value: string | number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(Number(value || 0));
}

// ─── Auth guard ────────────────────────────────────────────────────────────
function RequireAuth({ children }: { children: JSX.Element }) {
  const token = localStorage.getItem("access");
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

// ─── Sidebar / Shell ──────────────────────────────────────────────────────
function Shell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();

  const logout = async () => {
    const refresh = localStorage.getItem("refresh");
    try {
      if (refresh) await api("/auth/logout/", { method: "POST", body: JSON.stringify({ refresh }) });
    } catch {}
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/login");
  };

  const navItems = [
    { to: "/", icon: Home, label: "Dashboard" },
    { to: "/imports", icon: FileWarning, label: "Imports" },
    { to: "/members", icon: UsersRound, label: "Members" },
    { to: "/expenses", icon: ReceiptText, label: "Expenses" },
    { to: "/settlements", icon: ArrowRightLeft, label: "Settlements" },
  ];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Scale size={18} />
          </div>
          SplitAudit
        </div>
        <nav>
          {navItems.map(({ to, icon: Icon, label }) => (
            <Link
              key={to}
              to={to}
              className={location.pathname === to ? "active" : ""}
            >
              <Icon size={17} />
              {label}
            </Link>
          ))}
        </nav>
        <button className="ghost" onClick={logout}>
          <LogOut size={16} />
          Sign out
        </button>
      </aside>
      <main>{children}</main>
    </div>
  );
}

// ─── Login Page ────────────────────────────────────────────────────────────
function Login() {
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPw, setShowPw] = React.useState(false);
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api("/auth/token/", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ username, password }),
      });
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);
      navigate("/");
    } catch (err: any) {
      setError("Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon"><Scale size={20} /></div>
          SplitAudit
        </div>
        <h1>Welcome back</h1>
        <p className="subtitle">Sign in to your account to continue</p>

        <form className="auth-form" onSubmit={submit}>
          <label>
            Username
            <div className="input-wrap">
              <span className="input-icon"><User size={16} /></span>
              <input
                id="login-username"
                autoComplete="username"
                placeholder="Enter your username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            </div>
          </label>

          <label>
            Password
            <div className="input-wrap">
              <span className="input-icon"><Lock size={16} /></span>
              <input
                id="login-password"
                type={showPw ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                style={{ paddingRight: "2.75rem" }}
              />
              <button
                type="button"
                onClick={() => setShowPw(v => !v)}
                style={{ position: "absolute", right: "0.8rem", background: "none", padding: 0, color: "var(--text3)" }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </label>

          {error && (
            <div className="error-msg">
              <AlertCircle size={15} />
              {error}
            </div>
          )}

          <button id="login-submit" type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="auth-link">
          Don't have an account?{" "}
          <Link to="/register">Create one for free</Link>
        </p>
      </div>
    </div>
  );
}

// ─── Register Page ─────────────────────────────────────────────────────────
function Register() {
  const [username, setUsername] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [password2, setPassword2] = React.useState("");
  const [showPw, setShowPw] = React.useState(false);
  const [error, setError] = React.useState("");
  const [success, setSuccess] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (password !== password2) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      await api("/auth/register/", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ username, email, password, password2 }),
      });
      setSuccess("Account created! Signing you in…");
      // Auto-login after register
      const data = await api("/auth/token/", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ username, password }),
      });
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);
      setTimeout(() => navigate("/"), 800);
    } catch (err: any) {
      try {
        const parsed = JSON.parse(err.message);
        const msgs = Object.values(parsed).flat() as string[];
        setError(msgs[0] || "Registration failed. Please try again.");
      } catch {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon"><Scale size={20} /></div>
          SplitAudit
        </div>
        <h1>Create account</h1>
        <p className="subtitle">Join SplitAudit and start tracking expenses</p>

        <form className="auth-form" onSubmit={submit}>
          <label>
            Username
            <div className="input-wrap">
              <span className="input-icon"><User size={16} /></span>
              <input
                id="reg-username"
                autoComplete="username"
                placeholder="Choose a username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            </div>
          </label>

          <label>
            Email address
            <div className="input-wrap">
              <span className="input-icon"><Mail size={16} /></span>
              <input
                id="reg-email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
          </label>

          <label>
            Password
            <div className="input-wrap">
              <span className="input-icon"><Lock size={16} /></span>
              <input
                id="reg-password"
                type={showPw ? "text" : "password"}
                autoComplete="new-password"
                placeholder="At least 8 characters"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                style={{ paddingRight: "2.75rem" }}
              />
              <button
                type="button"
                onClick={() => setShowPw(v => !v)}
                style={{ position: "absolute", right: "0.8rem", background: "none", padding: 0, color: "var(--text3)" }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </label>

          <label>
            Confirm password
            <div className="input-wrap">
              <span className="input-icon"><Lock size={16} /></span>
              <input
                id="reg-password2"
                type={showPw ? "text" : "password"}
                autoComplete="new-password"
                placeholder="Re-enter your password"
                value={password2}
                onChange={e => setPassword2(e.target.value)}
                required
              />
            </div>
          </label>

          {error && (
            <div className="error-msg">
              <AlertCircle size={15} />
              {error}
            </div>
          )}
          {success && (
            <div className="success-msg" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <CheckCircle2 size={15} />
              {success}
            </div>
          )}

          <button id="reg-submit" type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="auth-link">
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

// ─── Data hook ─────────────────────────────────────────────────────────────
function useLoad<T>(path: string, fallback: T) {
  const [data, setData] = React.useState<T>(fallback);
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(() => {
    setLoading(true);
    api(path)
      .then(d => { setData(d); setError(""); })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false));
  }, [path]);

  React.useEffect(() => { load(); }, [load]);
  return { data, error, loading, reload: load };
}

// ─── Dashboard ─────────────────────────────────────────────────────────────
function Dashboard() {
  const { data: groups } = useLoad<any[]>("/groups/", []);
  const group = groups[0];
  const { data: balData, loading } = useLoad<any>(
    group ? `/balances/?group=${group.id}` : "/health/",
    { balances: [], suggested_settlements: [] }
  );
  const balances: any[] = balData?.balances ?? [];
  const settlements: any[] = balData?.suggested_settlements ?? [];

  const totalOwed = balances.filter(b => Number(b.balance) < 0).reduce((s, b) => s + Math.abs(Number(b.balance)), 0);
  const totalCredit = balances.filter(b => Number(b.balance) >= 0).reduce((s, b) => s + Number(b.balance), 0);

  return (
    <Shell>
      <header>
        <h1>Dashboard</h1>
        <p>Track balances and settle debts in one place.</p>
      </header>

      <div className="stat-grid">
        <div className="stat-card purple">
          <span className="stat-label">Total Members</span>
          <span className="stat-value">{balances.length}</span>
          <span className="stat-sub">Active in group</span>
        </div>
        <div className="stat-card teal">
          <span className="stat-label">Total Credit</span>
          <span className="stat-value">{formatMoney(totalCredit)}</span>
          <span className="stat-sub"><TrendingUp size={12} style={{display:"inline"}} /> In the green</span>
        </div>
        <div className="stat-card red">
          <span className="stat-label">Total Owed</span>
          <span className="stat-value">{formatMoney(totalOwed)}</span>
          <span className="stat-sub"><TrendingDown size={12} style={{display:"inline"}} /> Needs settling</span>
        </div>
        <div className="stat-card blue">
          <span className="stat-label">Pending Settlements</span>
          <span className="stat-value">{settlements.length}</span>
          <span className="stat-sub">Suggested transactions</span>
        </div>
      </div>

      <div className="grid two">
        <div className="panel">
          <div className="section-title">
            <h2><WalletCards size={18} /> Net Positions</h2>
          </div>
          {loading ? (
            <div style={{ display: "grid", gap: 8 }}>
              {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 42 }} />)}
            </div>
          ) : balances.length === 0 ? (
            <p style={{ color: "var(--text3)", fontSize: "0.88rem", marginTop: 8 }}>No balance data yet.</p>
          ) : (
            <table>
              <thead><tr><th>Person</th><th>Balance</th></tr></thead>
              <tbody>
                {balances.map((b: any) => (
                  <tr key={b.person}>
                    <td>{b.person}</td>
                    <td className={Number(b.balance) >= 0 ? "positive" : "negative"}>
                      {formatMoney(b.balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="panel">
          <div className="section-title">
            <h2><ArrowRightLeft size={18} /> Suggested Settlements</h2>
          </div>
          {loading ? (
            <div style={{ display: "grid", gap: 8 }}>
              {[1,2].map(i => <div key={i} className="skeleton" style={{ height: 42 }} />)}
            </div>
          ) : settlements.length === 0 ? (
            <p style={{ color: "var(--text3)", fontSize: "0.88rem", marginTop: 8 }}>All settled up! 🎉</p>
          ) : (
            <table>
              <thead><tr><th>Transfer</th><th>Amount</th></tr></thead>
              <tbody>
                {settlements.map((s: any, i: number) => (
                  <tr key={i}>
                    <td>
                      <span style={{ color: "var(--red)", fontWeight: 600 }}>{s.from}</span>
                      <span style={{ color: "var(--text3)", margin: "0 6px" }}>→</span>
                      <span style={{ color: "var(--green)", fontWeight: 600 }}>{s.to}</span>
                    </td>
                    <td style={{ fontWeight: 700 }}>{formatMoney(s.amount_in_inr)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <Ledger groupId={group?.id} />
    </Shell>
  );
}

// ─── Ledger ────────────────────────────────────────────────────────────────
function Ledger({ groupId }: { groupId?: number }) {
  const { data, loading } = useLoad<any[]>(
    groupId ? `/balances/ledger/?group=${groupId}` : "/health/",
    []
  );
  return (
    <div className="panel">
      <div className="section-title">
        <h2><ReceiptText size={18} /> Ledger Trace</h2>
      </div>
      {loading ? (
        <div style={{ display: "grid", gap: 8 }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 38 }} />)}
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th><th>Person</th><th>Kind</th><th>Memo</th><th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(data) && data.map((entry: any) => (
              <tr key={entry.id}>
                <td style={{ color: "var(--text3)", fontSize: "0.83rem" }}>{entry.date}</td>
                <td style={{ fontWeight: 600 }}>{entry.person_name}</td>
                <td><span className="badge info">{entry.kind}</span></td>
                <td style={{ color: "var(--text2)" }}>{entry.memo}</td>
                <td style={{ fontWeight: 700 }}>{formatMoney(entry.amount_in_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ─── Imports ───────────────────────────────────────────────────────────────
function Imports() {
  const [file, setFile] = React.useState<File | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const batches = useLoad<any[]>("/imports/", []);

  async function upload() {
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      await api("/imports/", { method: "POST", body: form });
      batches.reload();
      setFile(null);
    } finally {
      setUploading(false);
    }
  }

  async function resolve(batchId: number, anomalyId: number) {
    await api(`/imports/${batchId}/resolve/`, { method: "POST", body: JSON.stringify({ anomaly_id: anomalyId, status: "approved" }) });
    batches.reload();
  }

  async function commit(batchId: number) {
    await api(`/imports/${batchId}/commit/`, { method: "POST" });
    batches.reload();
  }

  return (
    <Shell>
      <header>
        <h1>CSV Import Review</h1>
        <p>Rows are parsed first, anomalies reviewed second — only approved rows affect balances.</p>
      </header>

      <div className="panel">
        <div className="toolbar">
          <div style={{ flex: 1 }}>
            <label style={{ textTransform: "none", fontSize: "0.88rem", fontWeight: 500, color: "var(--text2)" }}>
              <Upload size={14} style={{ display: "inline", marginRight: 6 }} />
              {file ? file.name : "Select a CSV file to upload"}
              <input type="file" accept=".csv" style={{ display: "none" }} onChange={e => setFile(e.target.files?.[0] ?? null)} />
            </label>
          </div>
          <button className="btn-primary" style={{ width: "auto" }} onClick={upload} disabled={!file || uploading}>
            {uploading ? "Uploading…" : "Upload CSV"}
          </button>
        </div>
      </div>

      {batches.data.map((batch: any) => (
        <div className="panel" key={batch.id}>
          <div className="section-title">
            <h2>{batch.source_filename}</h2>
            <button className="btn-success btn-sm" onClick={() => commit(batch.id)}>
              Commit approved rows
            </button>
          </div>
          <p style={{ fontSize: "0.83rem", marginBottom: "1rem" }}>
            {batch.total_rows} rows · {batch.anomaly_count} anomalies · {batch.committed_rows} committed · {batch.skipped_rows} skipped
          </p>
          <table>
            <thead><tr><th>Row</th><th>Category</th><th>Severity</th><th>Description</th><th>Action</th></tr></thead>
            <tbody>
              {batch.rows.flatMap((row: any) => row.anomalies.map((a: any) => (
                <tr key={a.id}>
                  <td>{a.row_number}</td>
                  <td>{a.category}</td>
                  <td><span className={`badge ${a.severity}`}>{a.severity}</span></td>
                  <td>{a.description}</td>
                  <td>
                    {a.approval_required && a.status === "open" ? (
                      <button className="btn-success btn-sm" onClick={() => resolve(batch.id, a.id)}>Approve</button>
                    ) : <span className="badge success">{a.status}</span>}
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      ))}
    </Shell>
  );
}

// ─── Simple list view ──────────────────────────────────────────────────────
function SimpleList({ title, path, icon: Icon }: { title: string; path: string; icon: any }) {
  const { data, loading } = useLoad<any[]>(path, []);
  return (
    <Shell>
      <header>
        <h1><Icon size={22} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />{title}</h1>
      </header>
      <div className="panel">
        {loading ? (
          <div style={{ display: "grid", gap: 8 }}>
            {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 42 }} />)}
          </div>
        ) : (
          <table>
            <tbody>
              {data.map((item: any) => (
                <tr key={item.id}>
                  <td style={{ fontWeight: 600 }}>
                    {item.display_name ?? item.description ?? item.paid_by_name ?? item.person_name ?? item.name}
                  </td>
                  <td style={{ color: "var(--text3)", fontSize: "0.85rem" }}>
                    {item.date ?? item.joined_on ?? item.status ?? item.base_currency}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  );
}

// ─── App ───────────────────────────────────────────────────────────────────
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/imports" element={<RequireAuth><Imports /></RequireAuth>} />
        <Route path="/members" element={<RequireAuth><SimpleList title="Members" path="/memberships/" icon={UsersRound} /></RequireAuth>} />
        <Route path="/expenses" element={<RequireAuth><SimpleList title="Expenses" path="/expenses/" icon={ReceiptText} /></RequireAuth>} />
        <Route path="/settlements" element={<RequireAuth><SimpleList title="Settlements" path="/settlements/" icon={ArrowRightLeft} /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
