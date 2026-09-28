import { useState } from 'react';
import { CalendarClock, CalendarPlus } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export default function ReminderCard({
  jobId,
  daysRemaining,
  overdue,
  checklist,
  lang,
}: {
  jobId: string;
  daysRemaining: number | null;
  overdue: boolean;
  checklist: string[];
  lang: Lang;
}) {
  const t = STRINGS[lang];
  const [checked, setChecked] = useState<boolean[]>(() =>
    checklist.map(() => false),
  );

  const chipText = overdue
    ? t.overdueLabel
    : daysRemaining == null
      ? null
      : daysRemaining === 0
        ? t.reminderToday
        : t.daysLeft.replace('{count}', String(daysRemaining));

  return (
    <section className="card space-y-3" aria-label={t.reminderTitle}>
      <div className="flex items-center gap-2">
        <CalendarClock size={20} strokeWidth={1.75} aria-hidden />
        <h3 className="text-base font-semibold">{t.reminderTitle}</h3>
      </div>
      {chipText && (
        <p
          className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${
            overdue
              ? 'bg-error-bg text-error border border-error-border'
              : 'bg-surface text-text-secondary border border-border'
          }`}
        >
          {chipText}
        </p>
      )}
      {checklist.length > 0 && (
        <div>
          <p className="text-sm font-medium text-text-secondary">
            {t.checklistTitle}
          </p>
          <ul className="mt-1">
            {checklist.map((item, i) => (
              <li key={i}>
                <label className="flex items-start gap-3 min-h-[48px] py-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked[i] ?? false}
                    onChange={() =>
                      setChecked((prev) =>
                        prev.map((v, j) => (j === i ? !v : v)),
                      )
                    }
                    className="mt-1 h-5 w-5 shrink-0"
                  />
                  <span className="text-base leading-6">{item}</span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
      {!overdue && daysRemaining != null && daysRemaining >= 0 && (
        <a
          href={`${API_BASE}/api/v1/documents/${jobId}/reminder.ics`}
          className="btn-secondary w-full inline-flex items-center justify-center gap-2"
          download
        >
          <CalendarPlus size={20} strokeWidth={1.75} aria-hidden />
          {t.addToCalendar}
        </a>
      )}
    </section>
  );
}
