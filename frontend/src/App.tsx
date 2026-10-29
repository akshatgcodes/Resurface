import { useEffect, useState, type FormEvent } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api } from "./api";
import Library from "./pages/Library";
import DigestPage from "./pages/DigestPage";

export function Logo() {
  return (
    <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="7" fill="var(--accent)" />
      <path d="M9 21c2-6 5-9 7-9s5 3 7 9" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="16" cy="9" r="2.5" fill="#fff" />
    </svg>
  );
}

export default function App() {
  const [user, setUser] = useState<boolean | null>(null);
  const [down, setDown] = useState(false);

  useEffect(() => {
    api.me().then((r) => setUser(r.user)).catch(() => setDown(true));
  }, []);

  if (down) return <div className="center error">Can't reach the Resurface API.</div>;
  if (user === null) return <div className="center muted">Loading…</div>;
  if (!user) return <Login onDone={() => setUser(true)} />;

  return (
    <>
      <header className="topbar">
        <span className="brand">
          <Logo /> Resurface
        </span>
        <nav>
          <NavLink to="/" end>
            Library
          </NavLink>
          <NavLink to="/digest">Digest</NavLink>
        </nav>
        <button className="link-btn" onClick={() => api.logout().then(() => setUser(false))}>
          Log out
        </button>
      </header>
      <Routes>
        <Route path="/" element={<Library />} />
        <Route path="/digest" element={<DigestPage />} />
      </Routes>
    </>
  );
}

function Login({ onDone }: { onDone: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.login(password);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  return (
    <main className="center">
      <form className="card login" onSubmit={submit}>
        <h1 className="brand big">
          <Logo /> Resurface
        </h1>
        <p className="muted">Your highlights, brought back before you forget them.</p>
        <label htmlFor="pw" className="label">
          Password
        </label>
        <input id="pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoFocus required />
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary">Log in</button>
      </form>
    </main>
  );
}
