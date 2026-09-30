import { useEffect, useState } from 'react';
import { Phone, Scale } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';
const STORAGE_KEY = 'ym_legal_aid_state';

interface AidEntry {
  name: string;
  phone?: string | null;
  url?: string | null;
  verified?: boolean;
}

function loadSavedState(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? '';
  } catch {
    return '';
  }
}

export default function LegalAidCard({ lang }: { lang: Lang }) {
  const t = STRINGS[lang];
  const [states, setStates] = useState<{ code: string; name: string }[]>([]);
  const [state, setState] = useState<string>(loadSavedState);
  const [entries, setEntries] = useState<AidEntry[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/v1/legal-aid/states`)
      .then((r) => (r.ok ? r.json() : { states: [] }))
      .then((body) => {
        if (!cancelled) setStates(body.states ?? []);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const qs = state ? `?state=${encodeURIComponent(state)}` : '';
    fetch(`${API_BASE}/api/v1/legal-aid${qs}`)
      .then((r) => (r.ok ? r.json() : { national: [], entries: [] }))
      .then((body) => {
        if (!cancelled)
          setEntries([...(body.national ?? []), ...(body.entries ?? [])]);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [state]);

  const pickState = (code: string) => {
    setState(code);
    try {
      if (code) localStorage.setItem(STORAGE_KEY, code);
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* storage unavailable */
    }
  };

  return (
    <section className="card space-y-3" aria-label={t.legalAidTitle}>
      <div className="flex items-center gap-2">
        <Scale size={20} strokeWidth={1.75} aria-hidden />
        <h3 className="text-base font-semibold">{t.legalAidTitle}</h3>
      </div>
      <p className="text-sm text-text-secondary">{t.legalAidCaveat}</p>
      {states.length > 0 && (
        <label className="block">
          <span className="text-sm font-medium text-text-secondary">
            {t.legalAidStateLabel}
          </span>
          <select
            value={state}
            onChange={(e) => pickState(e.target.value)}
            className="mt-1 w-full min-h-[48px] rounded-xl border-2 border-border px-4 text-base bg-white"
          >
            <option value="">—</option>
            {states.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <ul className="space-y-2">
        {entries.map((e) => (
          <li
            key={`${e.name}-${e.phone ?? ''}`}
            className="flex flex-col sm:flex-row sm:items-center gap-2"
          >
            <div className="flex-1 min-w-0">
              <p className="text-base font-medium truncate">{e.name}</p>
              {e.url && (
                <a
                  href={e.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-primary break-all"
                >
                  {e.url}
                </a>
              )}
            </div>
            {e.phone && (
              <a
                href={`tel:${e.phone}`}
                className="btn-secondary inline-flex items-center gap-2 shrink-0"
                aria-label={`${t.legalAidCall} ${e.name} ${e.phone}`}
              >
                <Phone size={20} strokeWidth={1.75} aria-hidden />
                {e.phone}
              </a>
            )}
          </li>
        ))}
      </ul>
      <p className="text-xs text-text-muted">{t.disclaimer}</p>
    </section>
  );
}
