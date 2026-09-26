const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export interface SubmitResult {
  jobId: string;
  status: string;
}

export interface DocumentResult {
  jobId: string;
  status: string;
  errorCode?: string | null;
  targetLanguage?: string | null;
  documentType?: string | null;
  classificationConfidence?: number | null;
  fields: {
    issuingAuthority?: string | null;
    deadlineDate?: string | null;
    amountOwed?: number | null;
    citedSection?: string | null;
    requiredAction?: string | null;
  };
  explanation?: string | null;
  disclaimerIncluded: boolean;
  escalation: { flagged: boolean; matchedRuleIds: string[] };
  voiceAvailable: boolean;
}

export async function submitDocument(
  image: File,
  targetLanguage: string,
): Promise<SubmitResult> {
  const form = new FormData();
  form.append('image', image);
  form.append('targetLanguage', targetLanguage);
  form.append('sessionId', 'web-anon');
  const res = await fetch(`${API_BASE}/api/v1/documents`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message ?? `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function fetchResult(jobId: string): Promise<DocumentResult> {
  const res = await fetch(`${API_BASE}/api/v1/documents/${jobId}`);
  if (!res.ok) throw new Error(`Status fetch failed (${res.status})`);
  return res.json();
}
