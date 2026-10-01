// Provisional-first status pill, shown above the explanation.
//
// Provisional (default): amber "AI summary ready — expert check pending".
// Warns the user not to act on the AI answer alone; paired with LegalAidCard.
// Verified: green confirmation rendered after the reviewer resolves and the
// second SSE/poll frame flips the job to completed.
import { ShieldCheck, Clock } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function ProvisionalBanner({
  lang,
  verified,
}: {
  lang: Lang;
  verified?: boolean;
}) {
  const t = STRINGS[lang];
  if (verified) {
    return (
      <div className="bg-green-50 border border-green-200 text-green-800 text-sm py-2.5 px-4 rounded-lg flex items-center gap-2">
        <ShieldCheck size={16} className="shrink-0" />
        <span className="font-medium">{t.expertVerified}</span>
      </div>
    );
  }
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex gap-3 text-left">
      <Clock size={20} className="text-amber-600 shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-bold text-amber-900">{t.provisionalTitle}</p>
        <p className="text-xs text-amber-800 mt-0.5">{t.provisionalBody}</p>
        <p className="text-[11px] font-semibold text-amber-600 mt-1.5 uppercase tracking-wide">
          {t.pendingReview}
        </p>
      </div>
    </div>
  );
}
