import { CheckCircle2, ShieldCheck } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

// TODO (manual-test finding): heading + body below are hardcoded Hindi
// "safe / e-KYC" copy — they ignore `lang` AND `escalated`. An escalated
// court summons currently reads "no fine or court order", which is
// dangerously wrong reassurance. Must switch to t.verdictDanger/verdictSafe
// (+ escalation notice) per language before any user sees escalated results.
export default function VerdictBanner({ escalated, lang }: { escalated: boolean; lang: Lang }) {
  const t = STRINGS[lang];
  return (
    <div className={`rounded-xl border ${escalated ? 'border-red-400 bg-red-50' : 'border-[#0DA883] bg-white'} overflow-hidden shadow-sm`} role="alert">
      <div className={`h-2 w-full ${escalated ? 'bg-red-500' : 'bg-[#0DA883]'}`}></div>
      <div className="p-4 sm:p-5 flex flex-col sm:flex-row gap-3 sm:gap-4">
        <div className={`shrink-0 flex items-center justify-center rounded-full ${escalated ? 'bg-red-100 text-red-600' : 'bg-[#E6F7F4] text-[#0DA883]'} w-12 h-12`}>
          {escalated ? (
            <ShieldCheck size={28} strokeWidth={1.75} />
          ) : (
            <CheckCircle2 size={28} strokeWidth={1.75} />
          )}
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${escalated ? 'bg-red-200 text-red-800' : 'bg-[#E6F7F4] text-[#0DA883]'}`}>
              {escalated ? t.verdictEscalatedChip : t.featSimple}
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2 break-words">
            {escalated ? t.verdictDanger : t.verdictSafe}
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed break-words">
            {escalated ? t.verdictDangerSub : t.verdictSafeSub}
          </p>
        </div>
      </div>
    </div>
  );
}
