import { Link, Route, Routes } from "react-router-dom";
import NewAnalysis from "./pages/NewAnalysis";
import SavedAnalyses from "./pages/SavedAnalyses";
import AnalysisView from "./pages/AnalysisView";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./lib/auth";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function AppLayout() {
  const { user, signOut } = useAuth();
  return (
    <div className="min-h-screen bg-ink text-[#e6edf3]">
      <header className="border-b border-hairline">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-amber shadow-[0_0_12px_#f4b740]" />
            <span className="font-display text-lg font-semibold tracking-tight">
              Building Energy Lens
            </span>
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            <Link to="/" className="btn">
              Saved
            </Link>
            <Link to="/new" className="btn btn-primary">
              New analysis
            </Link>
            <span className="ml-2 hidden text-xs text-muted sm:inline">
              {user?.email}
            </span>
            <button onClick={() => signOut()} className="btn">
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<SavedAnalyses />} />
          <Route path="/new" element={<NewAnalysis />} />
          <Route path="/analysis/:id" element={<AnalysisView />} />
        </Routes>
      </main>
      <footer className="mx-auto max-w-6xl px-6 py-8 text-xs text-muted">
        Estimates carry ranges and surface their assumptions. Annual figures are
        extrapolations from the measured window — confirm tariffs against an
        actual bill.
      </footer>
    </div>
  );
}
