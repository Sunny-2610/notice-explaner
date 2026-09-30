import { Volume2, Play } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function VoicePlayer({ jobId, lang }: { jobId: string; lang: Lang }) {
  return (
    <div className="card-elevated bg-white flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center">
            <Volume2 size={16} />
          </div>
          <h3 className="font-bold text-gray-900 text-sm">नोटिस की व्याख्या सुनें<br/><span className="text-xs font-normal text-gray-500">Listen in Hindi (ऑडियो विवरण)</span></h3>
        </div>
        <button className="bg-gray-100 text-gray-600 text-xs font-bold px-2 py-1 rounded">1.0x</button>
      </div>
      <div className="flex items-center gap-2 sm:gap-3 bg-gray-50 p-2 rounded-lg border border-gray-100 overflow-hidden min-w-0">
        <button className="w-10 h-10 min-w-[40px] min-h-[40px] bg-primary text-white flex items-center justify-center rounded-full shrink-0 shadow-md">
           <Play size={18} fill="currentColor" className="ml-1" />
        </button>
        <div className="text-xs text-gray-500 font-medium w-10 text-center shrink-0 hidden sm:block">00:18</div>
        <div className="flex-1 min-w-0 flex items-center gap-0.5 h-6 overflow-hidden">
           {[...Array(16)].map((_, i) => (
              <div key={i} className={`w-1 rounded-full shrink-0 ${i < 5 ? 'bg-primary' : 'bg-gray-300'} ${i > 11 ? 'hidden sm:block' : ''}`} style={{ height: `${Math.max(4, 4 + (i%8)*2)}px` }}></div>
           ))}
        </div>
        <div className="text-xs text-gray-500 font-medium w-10 text-center shrink-0 hidden sm:block">01:24</div>
        <div className="text-gray-400 px-1">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20 M17 5v14 M22 10v4 M7 5v14 M2 10v4"/></svg>
        </div>
      </div>
    </div>
  );
}
