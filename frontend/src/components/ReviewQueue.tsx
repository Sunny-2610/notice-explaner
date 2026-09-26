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
    <section className="pt-16 space-y-4 max-w-2xl mx-auto">
      <div className="flex justify-between items-center">
        <h2 className="text-[22px] leading-7 font-medium tracking-[0px]">
          Review queue <span className="chip ml-2">{items.length}</span>
        </h2>
        <button onClick={refresh} className="h-[44px] px-5 rounded-full border border-border text-[15px]">
          Refresh
        </button>
      </div>
      {error && <p className="text-sm text-error">{error}</p>}
      <ul className="space-y-2">
        {items.map((i) => (
          <li key={i.jobId}>
            <button
              onClick={() => open(i.jobId)}
              className={`card w-full text-left min-h-[48px] hover:border-text-muted ${
                selected === i.jobId ? 'border-primary' : ''
              }`}
            >
              <span className="font-mono text-sm">{i.jobId}</span>
              <span className="ml-2 text-sm text-text-muted">{i.routedReason}</span>
            </button>
          </li>
        ))}
      </ul>
      {result && (
        <div className="card space-y-3">
          <p className="text-sm text-text-muted">
            Status: {result.status} | Type: {result.documentType}
          </p>
          {result.explanation && <p className="text-[15px] leading-6">{result.explanation}</p>}
          <details className="border-t border-border pt-3">
            <summary className="cursor-pointer font-medium text-[15px]">
              Audit trail ({audit.length} stages)
            </summary>
            <ul className="mt-2 space-y-1 text-sm font-mono">
              {audit.map((a, idx) => (
                <li key={idx} className="p-2 bg-muted-surface rounded-md border border-border">
                  {a.stage}: {JSON.stringify(a.output)?.slice(0, 200)}
                </li>
              ))}
            </ul>
          </details>
          <div className="flex gap-2">
            <button
              onClick={() => decide('approve')}
              className="flex-1 h-[44px] rounded-full bg-secondary text-neutral capitalize text-[15px] font-medium"
            >
              Approve
            </button>
            {(['edit', 'reject'] as const).map((d) => (
              <button
                key={d}
                onClick={() => decide(d)}
                className="flex-1 h-[44px] rounded-full border border-border capitalize text-[15px]"
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
