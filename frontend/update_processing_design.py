import os

file_path = "C:/Users/sunny/Downloads/notice-explainer/frontend/src/components/ProcessingStages.tsx"

new_code = """import { Clock, ShieldCheck, AlertCircle, Languages, AlertTriangle } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

const STAGES = [
  { key: 'extracting', icon: 'file', hi: 'नोटिस पढ़ा जा रहा है', en: 'Reading notice scan & text', mr: 'नोटीस वाचली जात आहे' },
  { key: 'classifying', icon: 'file', hi: 'प्रकार पहचाना जा रहा है', en: 'Identifying document category & issuing authority', mr: 'प्रकार ओळखला जात आहे' },
  { key: 'extracting_fields', icon: 'extract', hi: 'जानकारी निकाली जा रही है', en: 'Extracting important dates & penalty amounts', mr: 'माहिती काढली जात आहे' },
  { key: 'generating_explanation', icon: 'translate', hi: 'सरल भाषा में समझाया जा रहा है', en: 'Generating plain language legal summary', mr: 'सोप्या भाषेत समजावले जात आहे' },
  { key: 'checking_escalation', icon: 'alert', hi: 'गंभीरता जाँची जा रही है', en: 'Assessing urgency, risk level & deadlines', mr: 'गांभीर्य तपासले जात आहे' },
] as const;

export default function ProcessingStages({ status, lang }: { status: string; lang: Lang }) {
  const order = ['queued', ...STAGES.map((s) => s.key)];
  // If status is not in order (like a delay), cap it, otherwise find index
  let currentIndex = order.indexOf(status);
  if (currentIndex === -1) currentIndex = 0; // Default if not found

  // Map backend status to 0-4 for UI steps
  const activeStep = Math.max(0, currentIndex - 1); 
  
  // Calculate progress percentage based on 5 steps
  const progressPercent = Math.min(((activeStep + 0.5) / STAGES.length) * 100, 100);

  return (
    <div className="w-full flex flex-col gap-6" aria-live="polite">
      {/* Header and Title */}
      <div className="text-center pt-8 mb-2">
         <h2 className="text-2xl font-bold text-gray-900 mb-1">दस्तावेज़ का विश्लेषण हो रहा है</h2>
         <p className="text-gray-500 text-sm mb-6">Analyzing your document</p>
         <div className="inline-flex items-center gap-1.5 bg-[#F3F4F6] text-gray-600 px-4 py-1.5 rounded-full text-xs font-semibold shadow-sm">
            <Clock size={14} className="text-primary" /> अनुमानित समय: ~15 सेकंड (Est. 15s)
         </div>
      </div>

      {/* Main Stepper Card */}
      <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm overflow-hidden relative">
         
         {/* Vertical Stepper Container */}
         <div className="relative z-10 flex flex-col gap-0 pb-6 mb-2">
            {STAGES.map((stage, i) => {
               const isDone = i < activeStep;
               const isActive = i === activeStep;
               const isPending = i > activeStep;

               return (
                 <div key={stage.key} className="relative flex gap-4 min-h-[5rem]">
                   {/* Line Connector connecting items */}
                   {i !== STAGES.length - 1 && (
                      <div className={`absolute left-[15px] top-[32px] bottom-[-8px] w-0.5 ${isDone ? 'bg-green-300' : 'bg-gray-200'}`}></div>
                   )}
                   
                   {/* Icons Container */}
                   <div className="relative shrink-0 w-8 flex justify-center pt-1 z-10">
                     {isDone && (
                        <div className="w-8 h-8 rounded-full border border-green-200 bg-white text-green-500 flex items-center justify-center">
                           <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        </div>
                     )}
                     {isActive && (
                        <div className="relative w-8 h-8 flex items-center justify-center">
                           <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
                           <div className="w-2 h-2 rounded-full bg-primary mx-auto"></div>
                        </div>
                     )}
                     {isPending && (
                        <div className="w-8 h-8 rounded-full bg-gray-100 text-gray-400 border border-gray-200 flex items-center justify-center">
                           {stage.icon === 'translate' ? <Languages size={14} strokeWidth={2}/> : <AlertCircle size={14} strokeWidth={2}/> }
                        </div>
                     )}
                   </div>

                   {/* Content */}
                   <div className={`flex-1 pb-6 ${isActive ? 'bg-blue-50/40 rounded-xl px-3 py-2 -mt-1 -mx-3 border border-blue-100' : 'pt-1'}`}>
                      <div className="flex items-start justify-between">
                         <div className="">
                            <h4 className={`text-lg font-bold leading-tight ${isPending ? 'text-gray-400' : 'text-gray-900'} mb-1`}>{lang === 'mr' ? stage.mr : stage.hi}</h4>
                            <p className={`${isActive ? 'text-primary' : 'text-gray-500'} text-xs font-medium`}>{stage.en}</p>
                         </div>
                         {/* Badges */}
                         {isDone && (
                            <span className="bg-green-50 text-green-600 border border-green-200 text-[10px] font-bold px-2.5 py-0.5 rounded ml-2 shrink-0">पूर्ण</span>
                         )}
                         {isActive && (
                             <span className="bg-blue-100 text-primary border border-blue-200 text-[10px] font-bold px-2 py-0.5 rounded-full ml-2 shrink-0 flex items-center gap-1 leading-tight text-center">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block"></span> प्रक्रिया<br/>चालू
                             </span>
                         )}
                      </div>
                   </div>

                 </div>
               );
            })}
         </div>

         {/* Progress bar line */}
         <div className="relative h-1.5 bg-gray-100/80 rounded-full w-full overflow-hidden">
            <div className="absolute top-0 bottom-0 left-0 bg-primary/80 transition-all duration-300" style={{ width: `${progressPercent}%` }}></div>
         </div>

         {/* Footer text */}
         <div className="mt-4 flex items-center justify-center gap-1.5 text-xs font-medium text-gray-500">
            <Clock size={14} /> आमतौर पर 15 सेकंड से कम समय लगता है (Usually {"<"}15 seconds)
         </div>
      </div>
    </div>
  );
}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_code)


app_file_path = "C:/Users/sunny/Downloads/notice-explainer/frontend/src/App.tsx"
with open(app_file_path, "r", encoding="utf-8") as f:
    app_code = f.read()

# Replace the specific block where ProcessingStages is wrapped
app_target_old = """            <div className="mx-auto w-full max-w-xl">
              {jobId && !terminal && !pollError && !timedOut && (
                <div className="mt-4">
                  <ProcessingStages status={result?.status ?? 'queued'} lang={lang} />
                </div>
              )}"""

app_target_new = """            <div className="mx-auto w-full max-w-xl">
              {jobId && !terminal && !pollError && !timedOut && (
                <div className="mt-4 flex flex-col items-center">
                  <ProcessingStages status={result?.status ?? 'queued'} lang={lang} />
                  
                  {/* Extra layout specified in Figma */}
                  <div className="w-full mt-6 bg-white border border-gray-100 shadow-sm rounded-xl px-4 py-3 flex gap-3 text-left">
                     <ShieldCheck className="text-[#0DA883] shrink-0 fill-[#0DA883]/10" size={24} />
                     <p className="text-sm text-gray-600"><strong className="text-gray-900">डेटा सुरक्षा:</strong> आपके दस्तावेज़ का डेटा 256-बिट एन्क्रिप्टेड और पूरी तरह सुरक्षित है।</p>
                  </div>
                  
                  <button onClick={() => setJobId(null)} className="mt-8 mb-6 text-gray-600 font-bold text-sm bg-transparent hover:bg-gray-100 px-6 py-2 rounded-full transition-colors">
                     रद्द करें (Cancel Analysis)
                  </button>
                </div>
              )}"""

app_code = app_code.replace(app_target_old, app_target_new)
with open(app_file_path, "w", encoding="utf-8") as f:
    f.write(app_code)
