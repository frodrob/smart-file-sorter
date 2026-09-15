import { useEffect, useMemo, useState } from "react";
import { api, ApplyResult, SortPlan, WorkspaceState } from "./api";

const CATEGORY_ICONS: Record<string, string> = {
  Images: "🖼️",
  Documents: "📄",
  Spreadsheets: "📊",
  Presentations: "📽️",
  Audio: "🎵",
  Video: "🎬",
  Archives: "🗜️",
  Code: "💻",
  Data: "🗄️",
  Other: "❓",
};

function icon(category: string): string {
  return CATEGORY_ICONS[category] ?? "📁";
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function App() {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [plan, setPlan] = useState<SortPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setState(await api.getWorkspace());
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const onReset = () =>
    run(async () => {
      setPlan(null);
      setMessage(null);
      const next = await api.reset();
      setState(next);
      setMessage(`Generated ${next.loose.length} messy demo files.`);
    });

  const onPlan = () =>
    run(async () => {
      const next = await api.plan();
      setPlan(next);
      setMessage(`Planned ${next.total_files} files into ${Object.keys(next.groups).length} folders.`);
    });

  const onApply = () =>
    run(async () => {
      const result: ApplyResult = await api.apply();
      setState(result.state);
      setPlan(null);
      setMessage(`Sorted ${result.moves.length} files into category folders. ✨`);
    });

  const looseCount = state?.loose.length ?? 0;
  const organizedEntries = useMemo(
    () => Object.entries(state?.organized ?? {}).sort(([a], [b]) => a.localeCompare(b)),
    [state]
  );

  return (
    <div className="app">
      <header className="hero">
        <h1>
          <span className="logo">🗂️</span> Smart File Sorter
        </h1>
        <p>Turn a messy folder into a tidy, category-organized library in one click.</p>
      </header>

      <div className="toolbar">
        <button className="btn btn-secondary" onClick={onReset} disabled={busy}>
          Generate demo files
        </button>
        <button className="btn btn-secondary" onClick={onPlan} disabled={busy || looseCount === 0}>
          Preview sort plan
        </button>
        <button className="btn btn-primary" onClick={onApply} disabled={busy || looseCount === 0}>
          Sort files
        </button>
      </div>

      {message && <div className="banner banner-info">{message}</div>}
      {error && <div className="banner banner-error">⚠️ {error}</div>}

      <div className="columns">
        <section className="card">
          <h2>
            Unsorted files <span className="pill">{looseCount}</span>
          </h2>
          {looseCount === 0 ? (
            <p className="empty">No loose files. Generate demo files to get started.</p>
          ) : (
            <ul className="file-list">
              {state!.loose.map((f) => (
                <li key={f.name} className="file-row">
                  <span className="file-icon">{icon(f.category)}</span>
                  <span className="file-name">{f.name}</span>
                  <span className="file-size">{formatSize(f.size_bytes)}</span>
                  <span className={`badge badge-${f.category.toLowerCase()}`}>{f.category}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2>{plan ? "Proposed plan" : "Organized folders"}</h2>
          {plan ? (
            <div className="folder-grid">
              {Object.entries(plan.groups).map(([category, files]) => (
                <div key={category} className="folder">
                  <div className="folder-head">
                    <span className="folder-icon">{icon(category)}</span>
                    <strong>{category}</strong>
                    <span className="pill">{files.length}</span>
                  </div>
                  <ul>
                    {files.map((f) => (
                      <li key={f.name}>{f.name}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : organizedEntries.length === 0 ? (
            <p className="empty">Nothing sorted yet. Preview a plan, then sort.</p>
          ) : (
            <div className="folder-grid">
              {organizedEntries.map(([category, files]) => (
                <div key={category} className="folder folder-done">
                  <div className="folder-head">
                    <span className="folder-icon">{icon(category)}</span>
                    <strong>{category}</strong>
                    <span className="pill">{files.length}</span>
                  </div>
                  <ul>
                    {files.map((name) => (
                      <li key={name}>{name}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <footer className="footer">
        Backend: FastAPI · Frontend: React + Vite · Sorts by file type into category folders.
      </footer>
    </div>
  );
}
