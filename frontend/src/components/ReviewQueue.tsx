import { useEffect, useState } from 'react';
import { Check, Pencil, RefreshCw, X } from 'lucide-react';
import { fetchResult, type DocumentResult } from '../lib/api';
import {
  fetchAudit,
  listReviewQueue,
  resolveReview,
  type AuditEntry,
  type ReviewItem,
} from '../lib/review';
import { STRINGS, type Lang } from '../i18n/strings';

/** Human labels for known audit-output keys. Entries with no recognized
 * keys fall back to truncated raw JSON in the same row structure. */
const OUTPUT_LABELS: Record<string, string> = {
  confidence: 'confidence',
  documentType: 'document type',
  escalate: 'escalate',
  rules: 'matched rules',
  version: 'rules version',
  disclaimer: 'disclaimer',
  voiceAvailable: 'voice available',
};

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.length ? value.join(', ') : '—';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (value == null) return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  const s = String(value);
  return s.length > 200 ? `${s.slice(0, 200)}…` : s;
}

function AuditStage({ entry }: { entry: AuditEntry }) {
  const output = (entry.output ?? {}) as Record<string, unknown>;
  const keys = Object.keys(output);
  const recognized = keys.filter((k) => k in OUTPUT_LABELS);
  const rows: Array<[string, string]> =
    recognized.length > 0
      ? recognized.map((k) => [OUTPUT_LABELS[k], formatValue(output[k])])
      : [['output', JSON.stringify(output)?.slice(0, 200) ?? '—']];
  return (
    <li className="p-2 bg-surface rounded-md border border-border">
      <p className="font-mono font-semibold text-text-primary text-sm">{entry.stage}</p>
      {rows.map(([label, value]) => (
        <div key={label} className="flex justify-between gap-2 text-sm">
          <span className="text-text-muted shrink-0">{label}</span>
          <span className="font-mono text-right break-words">{value}</span>
        </div>
      ))}
    </li>
  );
}

type Decision = 'approve' | 'edit' | 'reject';

export default function ReviewQueue({ lang }: { lang: Lang }) {
  const t = STRINGS[lang];
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [docTypes, setDocTypes] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentResult | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [editText, setEditText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const queue = await listReviewQueue();
      setItems(queue);
      setError(null);
      // Triage aid: fetch document types for visible rows (cached per job).
      const missing = queue.map((i) => i.jobId).filter((id) => !(id in docTypes));
      if (missing.length) {
        const settled = await Promise.allSettled(missing.map((id) => fetchResult(id)));
        setDocTypes((prev) => {
          const next = { ...prev };
          settled.forEach((r, idx) => {
            if (r.status === 'fulfilled' && r.value.documentType) next[missing[idx]] = r.value.documentType;
          });
          return next;
        });
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const open = async (jobId: string) => {
    setSelected(jobId);
    setDecision(null);
    setEditText('');
    setResult(await fetchResult(jobId));
    setAudit(await fetchAudit(jobId));
  };

  const close = () => {
    setSelected(null);
    setResult(null);
    setAudit([]);
    setDecision(null);
    setEditText('');
  };

  const decide = async (d: Decision, finalText?: string) => {
    if (!selected || busy) return;
    setBusy(true);
    try {
      await resolveReview(selected, d, finalText);
      close();
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  // Reviewer shortcuts: A approve, E edit, R reject (ignored while typing).
  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) return;
      const k = e.key.toLowerCase();
      if (k === 'a') void decide('approve');
      else if (k === 'e') {
        setDecision('edit');
        setEditText((prev) => prev || result?.explanation || '');
      } else if (k === 'r') void decide('reject');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, busy, editText, result]);

  return (
    <section className="pt-8 space-y-4 max-w-2xl mx-auto">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">
          Review queue <span className="chip-info ml-2">{items.length}</span>
        </h2>
        <button onClick={refresh} className="btn-secondary inline-flex items-center gap-2">
          <RefreshCw size={18} strokeWidth={1.75} aria-hidden /> Refresh
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
              <span className="font-mono text-sm break-all">{i.jobId}</span>
              <span className="ml-2 inline-flex flex-wrap gap-1">
                <span className="chip-warning">{i.routedReason}</span>
                {docTypes[i.jobId] && <span className="chip-info">{docTypes[i.jobId]}</span>}
              </span>
            </button>
          </li>
        ))}
      </ul>
      {result && (
        <div className="card space-y-3">
          <div className="flex justify-between items-start gap-2">
            <p className="text-sm text-text-secondary">
              Status: {result.status} | Type: {result.documentType}
            </p>
            <button onClick={close} className="btn-secondary px-3" aria-label="Close">
              <X size={18} strokeWidth={1.75} aria-hidden />
            </button>
          </div>
          {result.explanation && <p className="text-base leading-7">{result.explanation}</p>}
          <details className="border-t border-border pt-3">
            <summary className="cursor-pointer font-medium min-h-[48px] inline-flex items-center">
              Audit trail ({audit.length} stages)
            </summary>
            <ul className="mt-2 space-y-1">
              {audit.map((a, idx) => (
                <AuditStage key={idx} entry={a} />
              ))}
            </ul>
          </details>
          {decision === 'edit' ? (
            <div className="space-y-2">
              <label htmlFor="review-final-text" className="text-sm font-medium text-text-primary">
                Final explanation text
              </label>
              <textarea
                id="review-final-text"
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full min-h-[160px] rounded-xl border-2 border-border p-3 text-base bg-white"
              />
            <div className="flex flex-col sm:flex-row gap-2">
                <button
                  onClick={() => decide('edit', editText)}
                  disabled={busy || !editText.trim()}
                  className="btn-primary flex-1 inline-flex items-center justify-center gap-2 disabled:opacity-40"
                >
                  <Check size={18} strokeWidth={1.75} aria-hidden /> Save &amp; Approve
                </button>
                <button onClick={() => setDecision(null)} className="btn-secondary flex-1">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={() => decide('approve')}
                disabled={busy}
                className="btn-primary flex-1 inline-flex items-center justify-center gap-2 disabled:opacity-40 min-h-[48px]"
              >
                <Check size={18} strokeWidth={1.75} aria-hidden /> Approve (A)
              </button>
              <button
                onClick={() => {
                  setDecision('edit');
                  setEditText(result.explanation || '');
                }}
                disabled={busy}
                className="btn-secondary flex-1 inline-flex items-center justify-center gap-2 disabled:opacity-40"
              >
                <Pencil size={18} strokeWidth={1.75} aria-hidden /> Edit (E)
              </button>
              <button onClick={() => decide('reject')} disabled={busy} className="btn-danger flex-1 disabled:opacity-40">
                Reject (R)
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
