import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function Login() {
  const { session, signIn, resetPassword } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  if (session) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await signIn(email, password);
      nav("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const forgot = async () => {
    if (!email) {
      setError("Enter your email above first, then click reset.");
      return;
    }
    setError(null);
    try {
      await resetPassword(email);
      setNotice(`Password reset link sent to ${email}.`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <AuthShell title="Log in" subtitle="Welcome back to Building Energy Lens.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div className="panel border-waste/50 bg-waste/10 p-3 text-sm text-waste">
            {error}
          </div>
        )}
        {notice && (
          <div className="panel border-save/50 bg-save/10 p-3 text-sm text-save">
            {notice}
          </div>
        )}
        <Field
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          autoComplete="email"
        />
        <div>
          <Field
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="current-password"
          />
          <button
            type="button"
            onClick={forgot}
            className="mt-1 text-xs text-muted hover:text-amber"
          >
            Forgot password?
          </button>
        </div>
        <button className="btn btn-primary w-full" disabled={busy}>
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        No account?{" "}
        <Link to="/signup" className="text-amber hover:underline">
          Sign up
        </Link>
      </p>
    </AuthShell>
  );
}

// --- shared bits (kept local to the two auth pages) -------------------------

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto mt-12 max-w-sm">
      <div className="mb-6 flex items-center gap-3">
        <span className="h-2.5 w-2.5 rounded-full bg-amber shadow-[0_0_12px_#f4b740]" />
        <span className="font-display text-lg font-semibold tracking-tight">
          Building Energy Lens
        </span>
      </div>
      <div className="panel p-6">
        <h1 className="font-display text-xl font-semibold">{title}</h1>
        <p className="mt-1 text-sm text-muted">{subtitle}</p>
        <div className="mt-5">{children}</div>
      </div>
    </div>
  );
}

export function Field({
  label,
  type,
  value,
  onChange,
  autoComplete,
}: {
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      <input
        type={type}
        value={value}
        required
        autoComplete={autoComplete}
        onChange={(e) => onChange(e.target.value)}
        className="input mt-1 w-full px-3 py-2"
      />
    </label>
  );
}
