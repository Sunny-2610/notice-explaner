export interface ReviewItem {
  jobId: string;
  routedReason: string;
  reviewerId?: string | null;
  decision?: string | null;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export interface AuditEntry {
  stage: string;
  input?: unknown;
  output?: unknown;
}

export async function listReviewQueue(): Promise<ReviewItem[]> {
  const res = await fetch(`${API_BASE}/api/v1/review/queue`);
  if (!res.ok) throw new Error(`Review queue failed (${res.status})`);
  return res.json();
}

export async function resolveReview(
  jobId: string,
  decision: 'approve' | 'edit' | 'reject',
  finalText?: string,
): Promise<ReviewItem> {
  const res = await fetch(`${API_BASE}/api/v1/review/${jobId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewerId: 'web-reviewer', decision, finalText }),
  });
  if (!res.ok) throw new Error(`Resolve failed (${res.status})`);
  return res.json();
}

export async function fetchAudit(jobId: string): Promise<AuditEntry[]> {
  const res = await fetch(`${API_BASE}/api/v1/documents/${jobId}/audit`);
  if (!res.ok) throw new Error(`Audit fetch failed (${res.status})`);
  const body = await res.json();
  return body.entries ?? [];
}
