import { STRINGS, type Lang } from '../i18n/strings';

const STAGES = [
  { key: 'extracting', icon: '📖' },
  { key: 'classifying', icon: '🏷️' },
  { key: 'extracting_fields', icon: '📝' },
  { key: 'generating_explanation', icon: '💬' },
  { key: 'checking_escalation', icon: '🛡️' },
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
        const cls =
          stageIndex < currentIndex || currentIndex >= order.length
            ? 'stage stage-done'
            : stageIndex === currentIndex
              ? 'stage stage-active'
              : 'stage';
        return (
          <div key={stage.key} className={cls}>
            <span aria-hidden>
              {stageIndex < currentIndex ? '✅' : stageIndex === currentIndex ? '⏳' : '⏸️'}
            </span>
            <span>
              {stage.icon} {LABEL[lang][stage.key]}
            </span>
          </div>
        );
      })}
    </div>
  );
}
