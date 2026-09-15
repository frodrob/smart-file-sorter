export interface LooseFile {
  name: string;
  category: string;
  size_bytes: number;
}

export interface WorkspaceState {
  loose: LooseFile[];
  organized: Record<string, string[]>;
}

export interface SortPlan {
  total_files: number;
  groups: Record<string, LooseFile[]>;
}

export interface ApplyResult {
  moves: { from: string; to: string; category: string }[];
  state: WorkspaceState;
}

async function request<T>(path: string, method: "GET" | "POST", body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getWorkspace: () => request<WorkspaceState>("/api/workspace", "GET"),
  reset: () => request<WorkspaceState>("/api/workspace/reset", "POST"),
  plan: () => request<SortPlan>("/api/plan", "POST"),
  apply: () => request<ApplyResult>("/api/apply", "POST", { dry_run: false }),
};
