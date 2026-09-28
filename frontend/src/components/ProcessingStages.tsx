import { BookOpen, CheckCircle2, Circle, FileText, Loader2, MessagesSquare, ShieldCheck, Tag } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

const STAGES = [
  { key: 'extracting', Icon: BookOpen },
  { key: 'classifying', Icon: Tag },
  { key: 'extracting_fields', Icon: FileText },
  { key: 'generating_explanation', Icon: MessagesSquare },
  { key: 'checking_escalation', Icon: ShieldCheck },
] as const;

const LABEL: Record<Lang, Record<string, string>> = {
  hi: {
    extracting: 'नोटिस पढ़ा जा रहा है',
    classifying: 'प्रकार पहचाना जा रहा है',
    extracting_fields: 'जानकारी निकाली जा रही है',
    generating_explanation: 'सरल भाषा में समझाया जा रहा है',
    checking_escalation: 'गंभीरता जाँची जा रही है',
  },
  mr: {
    extracting: 'नोटीस वाचली जात आहे',
    classifying: 'प्रकार ओळखला जात आहे',
    extracting_fields: 'माहिती काढली जात आहे',
    generating_explanation: 'सोप्या भाषेत समजावले जात आहे',
    checking_escalation: 'गांभीर्य तपासले जात आहे',
  },
};

/** Animated stage list driven by the live job status — no bare spinners. */
export default function ProcessingStages({ status, lang }: { status: string; lang: Lang }) {
  const order = ['queued', ...STAGES.map((s) => s.key)];
  const currentIndex = Math.max(order.indexOf(status), 0);
  return (
    <div className="card" aria-live="polite">
      <p className="text-sm font-medium text-text-secondary mb-1">{STRINGS[lang].processing}</p>
      {STAGES.map((stage, i) => {
        const stageIndex = i + 1;
        const done = stageIndex < currentIndex || currentIndex >= order.length;
        const active = !done && stageIndex === currentIndex;
        const cls = done ? 'stage stage-done' : active ? 'stage stage-active' : 'stage';
        const { Icon } = stage;
        return (
          <div key={stage.key} className={cls}>
            <span aria-hidden>
              {done ? (
                <CheckCircle2 size={20} strokeWidth={1.75} />
              ) : active ? (
                <Loader2 size={20} strokeWidth={1.75} className="animate-spin" />
              ) : (
                <Circle size={20} strokeWidth={1.75} />
              )}
            </span>
            <span className="inline-flex items-center gap-2">
              <Icon size={20} strokeWidth={1.75} aria-hidden /> {LABEL[lang][stage.key]}
            </span>
          </div>
        );
      })}
    </div>
  );
}
