import { useEffect, useState } from 'react';
import { fetchResult, type DocumentResult } from '../lib/api';
import {
  fetchAudit,
  listReviewQueue,
  resolveReview,
  type AuditEntry,
  type ReviewItem,
} from '../lib/review';
import { STRINGS, type Lang } from '../i18n/strings';

export default function ReviewQueue({ lang }: { lang: Lang }) {
  const t = STRINGS[lang];
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
    <section className="pt-8 space-y-4 max-w-2xl mx-auto">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">
          Review queue <span className="chip-info ml-2">{items.length}</span>
        </h2>
        <button onClick={refresh} className="btn-secondary">
          Refresh
        </button>
      </div>
      {error && (
        <div className="card">
          <p className="text-sm text-error">{error}</p>
          <button onClick={refresh} className="btn-secondary w-full mt-3">
            {t.retry}
          </button>
        </div>
      )}
      {items.length === 0 && !error && (
        <div className="card text-center">
          <p className="text-base text-text-secondary">{t.emptyReview}</p>
        </div>
      )}
      <ul className="space-y-2">
        {items.map((i) => (
          <li key={i.jobId}>
            <button
              onClick={() => open(i.jobId)}
              className={`card w-full text-left min-h-[48px] ${
                selected === i.jobId ? 'border-2 border-primary' : ''
              }`}
            >
              <span className="font-mono text-sm">{i.jobId}</span>
              <span className="chip-warning ml-2">{i.routedReason}</span>
            </button>
          </li>
        ))}
      </ul>
      {result && (
        <div className="card space-y-3">
          <p className="text-sm text-text-secondary">
            Status: {result.status} | Type: {result.documentType}
          </p>
          {result.explanation && <p className="text-base leading-7">{result.explanation}</p>}
          <details className="border-t border-border pt-3">
            <summary className="cursor-pointer font-medium min-h-[48px] inline-flex items-center">
              Audit trail ({audit.length} stages)
            </summary>
            <ul className="mt-2 space-y-1 text-sm font-mono">
              {audit.map((a, idx) => (
                <li key={idx} className="p-2 bg-surface rounded-md border border-border">
                  {a.stage}: {JSON.stringify(a.output)?.slice(0, 200)}
                </li>
              ))}
            </ul>
          </details>
          <div className="flex gap-2">
            <button onClick={() => decide('approve')} className="btn-primary flex-1 capitalize">
              Approve
            </button>
            {(['edit', 'reject'] as const).map((d) => (
              <button
                key={d}
                onClick={() => decide(d)}
                className={`flex-1 capitalize min-h-[48px] px-6 py-3 rounded-xl font-medium ${
                  d === 'reject' ? 'btn-danger' : 'btn-secondary'
                }`}
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
