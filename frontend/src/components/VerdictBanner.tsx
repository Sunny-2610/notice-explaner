import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function VerdictBanner({ escalated, lang }: { escalated: boolean; lang: Lang }) {
  const t = STRINGS[lang];
  return (
    <div className={`verdict ${escalated ? 'verdict-danger' : 'verdict-safe'}`} role="alert">
      {escalated ? (
        <span className="verdict-icon-danger" aria-hidden>
          <AlertTriangle size={28} strokeWidth={1.75} />
        </span>
      ) : (
        <span className="verdict-icon-safe" aria-hidden>
          <CheckCircle2 size={28} strokeWidth={1.75} />
        </span>
      )}
      <div>
        {escalated && <span className="verdict-lawyer-chip">{t.seeLawyerChip}</span>}
        <h2 className={`verdict-title ${escalated ? 'mt-2' : ''}`}>
          {escalated ? t.verdictDanger : t.verdictSafe}
        </h2>
        <p className="verdict-subtitle">{escalated ? t.verdictDangerSub : t.verdictSafeSub}</p>
      </div>
    </div>
  );
}
