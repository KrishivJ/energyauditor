import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { AuthShell, Field } from "./Login";

export default function Signup() {
  const { session, signUp } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmSent, setConfirmSent] = useState(false);

  if (session) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const signedIn = await signUp(email, password);
      if (signedIn) {
        nav("/"); // email confirmation disabled → straight in
      } else {
        setConfirmSent(true); // confirmation required → check inbox
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (confirmSent) {
    return (
      <AuthShell title="Check your email" subtitle="One more step.">
        <div className="panel border-save/50 bg-save/10 p-4 text-sm text-save">
          We sent a confirmation link to <strong>{email}</strong>. Click it to
          activate your account, then log in.
        </div>
        <p className="mt-6 text-center text-sm text-muted">
          <Link to="/login" className="text-amber hover:underline">
            Back to log in
          </Link>
        </p>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Sign up" subtitle="Create your account.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div className="panel border-waste/50 bg-waste/10 p-3 text-sm text-waste">
            {error}
          </div>
        )}
        <Field
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          autoComplete="email"
        />
        <Field
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
        />
        <button className="btn btn-primary w-full" disabled={busy}>
          {busy ? "Creating account…" : "Sign up"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="text-amber hover:underline">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}
