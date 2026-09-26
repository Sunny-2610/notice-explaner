import { STRINGS, type Lang } from '../i18n/strings';

export default function VerdictBanner({ escalated, lang }: { escalated: boolean; lang: Lang }) {
  const t = STRINGS[lang];
  return (
    <div className={`verdict ${escalated ? 'verdict-danger' : 'verdict-safe'}`} role="alert">
      <span className="verdict-emoji" aria-hidden>
        {escalated ? '🚨' : '✅'}
      </span>
      <div>
        <h2 className="verdict-title">{escalated ? t.verdictDanger : t.verdictSafe}</h2>
        <p className="verdict-subtitle">{escalated ? t.verdictDangerSub : t.verdictSafeSub}</p>
      </div>
    </div>
  );
}
