import { useEffect, useState } from 'react';
import { fetchResult, type DocumentResult } from '../lib/api';
import {
  fetchAudit,
  listReviewQueue,
  resolveReview,
  type AuditEntry,
  type ReviewItem,
} from '../lib/review';

export default function ReviewQueue() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentResult | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setItems(await listReviewQueue());
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const open = async (jobId: string) => {
    setSelected(jobId);
    setResult(await fetchResult(jobId));
    setAudit(await fetchAudit(jobId));
  };

  const decide = async (decision: 'approve' | 'edit' | 'reject') => {
    if (!selected) return;
    await resolveReview(selected, decision);
    setSelected(null);
    setResult(null);
    await refresh();
  };

  return (
    <section className="mt-6 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Review queue ({items.length})</h2>
        <button onClick={refresh} className="min-h-[48px] px-4 rounded-lg bg-gray-200">
          Refresh
        </button>
      </div>
      {error && <p className="text-red-700">{error}</p>}
      <ul className="space-y-2">
        {items.map((i) => (
          <li key={i.jobId}>
            <button
              onClick={() => open(i.jobId)}
              className={`w-full text-left p-3 rounded-xl border min-h-[48px] ${
                selected === i.jobId ? 'border-black' : ''
              }`}
            >
              <span className="font-mono text-sm">{i.jobId}</span>
              <span className="ml-2 text-sm text-gray-600">{i.routedReason}</span>
            </button>
          </li>
        ))}
      </ul>
      {result && (
        <div className="space-y-3 p-4 rounded-xl bg-gray-50">
          <p className="text-sm">Status: {result.status} | Type: {result.documentType}</p>
          {result.explanation && <p className="text-lg">{result.explanation}</p>}
          <details>
            <summary className="cursor-pointer font-medium">
              Audit trail ({audit.length} stages)
            </summary>
            <ul className="mt-2 space-y-1 text-sm font-mono">
              {audit.map((a, idx) => (
                <li key={idx} className="p-2 bg-white rounded border">
                  {a.stage}: {JSON.stringify(a.output)?.slice(0, 200)}
                </li>
              ))}
            </ul>
          </details>
          <div className="flex gap-2">
            {(['approve', 'edit', 'reject'] as const).map((d) => (
              <button
                key={d}
                onClick={() => decide(d)}
                className="flex-1 min-h-[52px] rounded-xl bg-black text-white capitalize"
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
