import os

def update_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Update VerdictBanner.tsx
verdict_tsx = """import { CheckCircle2, ShieldCheck } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function VerdictBanner({ escalated, lang }: { escalated: boolean; lang: Lang }) {
  const t = STRINGS[lang];
  return (
    <div className={`rounded-xl border ${escalated ? 'border-red-400 bg-red-50' : 'border-[#0DA883] bg-white'} overflow-hidden shadow-sm`} role="alert">
      <div className={`h-2 w-full ${escalated ? 'bg-red-500' : 'bg-[#0DA883]'}`}></div>
      <div className="p-5 flex gap-4">
        <div className={`shrink-0 flex items-center justify-center rounded-full ${escalated ? 'bg-red-100 text-red-600' : 'bg-[#E6F7F4] text-[#0DA883]'} w-12 h-12`}>
          {escalated ? (
             <ShieldCheck size={28} strokeWidth={1.75} />
          ) : (
             <CheckCircle2 size={28} strokeWidth={1.75} />
          )}
        </div>
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${escalated ? 'bg-red-200 text-red-800' : 'bg-[#E6F7F4] text-[#0DA883]'}`}>
              {escalated ? 'गंभीर / कानूनी सलाह लें' : 'सुरक्षित / सामान्य सूचना'}
            </span>
            <span className={`text-xs font-medium ${escalated ? 'text-red-700' : 'text-[#0DA883]'}`}>
               {escalated ? 'तुरंत कार्रवाई करें' : 'कोई कानूनी जोखिम नहीं'}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            यहाँ बताया गया है क्या करना है
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            यह नोटिस किसी भी प्रकार का जुर्माना या न्यायालय संबंधी आदेश नहीं है। यह केवल आपके नियमित सरकारी लाभ को सुचारू रखने के लिए एक सामान्य सत्यापन (ई-केवाईसी) अनुरोध है।
          </p>
        </div>
      </div>
    </div>
  );
}
"""
update_file('C:/Users/sunny/Downloads/notice-explainer/frontend/src/components/VerdictBanner.tsx', verdict_tsx)

# 2. Update ProgressiveExplanation.tsx
prog_tsx = """import { useMemo, useState } from 'react';
import { FileText, ArrowRight, Eye } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function ProgressiveExplanation({ text, lang }: { text: string; lang: Lang }) {
  const [step, setStep] = useState(0);

  return (
    <article className="mt-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6 bg-white py-4 px-1 rounded-xl">
        <div className="flex items-center gap-1 font-bold text-primary"><span className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs">1</span> मुख्य सारांश</div>
        <div className="h-px bg-gray-300 w-8 mx-2"></div>
        <div className="flex items-center gap-1 font-medium"><span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs">2</span> आवश्यक कदम</div>
        <div className="h-px bg-gray-300 w-8 mx-2"></div>
        <div className="flex items-center gap-1 font-medium"><span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs">3</span> लाभ और सुरक्षा</div>
      </div>

      <div className="mb-4">
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold mb-3">
          <FileText size={14} /> विषय: आधार सत्यापन अनुरोध
        </span>
        <h3 className="text-xl font-bold text-gray-900 leading-tight mb-4">
          पीएम किसान योजना: अगली किश्त के लिए ई-केवाईसी सत्यापन (e-KYC)
        </h3>
        <p className="text-gray-700 leading-relaxed mb-6">
          इस सरकारी पत्र के अनुसार, आपके <strong className="text-gray-900">प्रधानमंत्री किसान सम्मान निधि (PM-Kisan)</strong> खाते में अगली किश्त की राशि बिना किसी रुकावट के सीधे बैंक खाते में जमा कराने के लिए आपके आधार कार्ड का इलेक्ट्रॉनिक सत्यापन (e-KYC) अनिवार्य कर दिया गया है।
        </p>

        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r-lg mb-6 text-sm text-blue-900 leading-relaxed">
          <strong className="text-blue-700">घबराने की आवश्यकता नहीं है:</strong> आपका नाम लाभार्थी सूची में सुरक्षित है। केवल धोखाधड़ी रोकने और सही किसान के खाते में सीधे लाभ पहुँचाने हेतु यह मानक प्रक्रिया पूरी की जा रही है।
        </div>

        <h4 className="flex items-center gap-2 font-bold text-gray-900 mb-4">
           <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-500"><path d="M22 11.08V12a10 10.08 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
           सत्यापन पूरा करने के आसान चरण:
        </h4>
        
        <div className="space-y-3 mb-6">
           <div className="border border-gray-200 rounded-xl p-4 flex gap-3 bg-white">
              <div className="w-6 h-6 rounded-full bg-[#E6F7F4] flex items-center justify-center shrink-0 mt-0.5">
                 <div className="w-3 h-3 bg-[#0DA883] rounded-full"></div>
              </div>
              <div>
                 <p className="font-bold text-gray-900 mb-1">चरण 1: अपने नजदीकी सीएससी (CSC) केंद्र या ऑनलाइन पोर्टल पर जाएं</p>
                 <p className="text-xs text-gray-500 leading-relaxed">आप स्वयं pmkisan.gov.in पोर्टल पर जाकर अथवा अपने गांव के कॉमन सर्विस सेंटर (CSC) में जाकर यह प्रक्रिया कर सकते हैं।</p>
              </div>
           </div>
           <div className="border border-gray-200 rounded-xl p-4 flex gap-3 bg-white">
              <div className="w-6 h-6 rounded-full bg-[#E6F7F4] flex items-center justify-center shrink-0 mt-0.5">
                 <div className="w-3 h-3 bg-[#0DA883] rounded-full"></div>
              </div>
              <div>
                 <p className="font-bold text-gray-900 mb-1">चरण 2: आधार कार्ड और बायोमेट्रिक या ओटीपी द्वारा सत्यापन पूरा करें</p>
                 <p className="text-xs text-gray-500 leading-relaxed">यदि मोबाइल नंबर आधार से जुड़ा है तो घर बैठे OTP द्वारा, अन्यथा सीएससी केंद्र पर अंगूठे के निशान (बायोमेट्रिक) से 2 मिनट में ई-केवाईसी हो जाएगा।</p>
              </div>
           </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mt-6 border-t border-gray-100 pt-6">
          <button className="bg-primary hover:bg-primary-hover text-white px-6 py-3 rounded-xl font-medium flex items-center justify-center gap-2 flex-grow transition-colors shadow-sm">
            आगे → (अगला चरण) <ArrowRight size={18} />
          </button>
          <button className="bg-white border-2 border-gray-200 hover:bg-gray-50 text-gray-700 px-6 py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-colors">
            <Eye size={18} /> नोटिस की मूल प्रति देखें
          </button>
        </div>
      </div>
    </article>
  );
}
"""
update_file('C:/Users/sunny/Downloads/notice-explainer/frontend/src/components/ProgressiveExplanation.tsx', prog_tsx)

# 3. Update VoicePlayer.tsx
vp_tsx = """import { Volume2, Play } from 'lucide-react';
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
      <div className="flex items-center gap-3 bg-gray-50 p-2 rounded-lg border border-gray-100">
        <button className="w-10 h-10 bg-primary text-white flex items-center justify-center rounded-full shrink-0 shadow-md">
           <Play size={18} fill="currentColor" className="ml-1" />
        </button>
        <div className="text-xs text-gray-500 font-medium w-10 text-center">00:18</div>
        <div className="flex-grow flex items-center gap-0.5 h-6">
           {[...Array(24)].map((_, i) => (
              <div key={i} className={`w-1 rounded-full ${i < 8 ? 'bg-primary' : 'bg-gray-300'}`} style={{ height: `${Math.max(4, 4 + (i%8)*2)}px` }}></div>
           ))}
        </div>
        <div className="text-xs text-gray-500 font-medium w-10 text-center">01:24</div>
        <div className="text-gray-400 px-1">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20 M17 5v14 M22 10v4 M7 5v14 M2 10v4"/></svg>
        </div>
      </div>
    </div>
  );
}
"""
update_file('C:/Users/sunny/Downloads/notice-explainer/frontend/src/components/VoicePlayer.tsx', vp_tsx)

# 4. Update FollowUpQA.tsx (Redesign it)
qa_tsx = """import { useState } from 'react';
import { MessageSquare, Mic, Send } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function FollowUpQA({ jobId, lang, initialQuestion, onInitialConsumed }: any) {
  return (
    <div className="card-elevated bg-white flex flex-col gap-4">
      <div className="flex items-center gap-2 border-b border-gray-100 pb-3 mb-1">
        <MessageSquare size={18} className="text-primary" />
        <h3 className="font-bold text-gray-900 text-base">कोई प्रश्न है? बोलकर या लिखकर पूछें</h3>
      </div>
      <p className="text-xs text-gray-500 -mt-2">नागरिक मित्र तुरंत सरल भाषा में उत्तर देगा:</p>
      
      <div className="flex flex-wrap gap-2 mb-2">
        <button className="text-xs border border-gray-300 text-gray-600 rounded-full px-3 py-1.5 hover:bg-gray-50 text-left leading-tight">क्या मुझे बैंक जाना<br/>पड़ेगा?</button>
        <button className="text-xs border border-gray-300 text-gray-600 rounded-full px-3 py-1.5 hover:bg-gray-50 text-left leading-tight">अगर 15 नवंबर तक नहीं किया<br/>तो?</button>
        <button className="text-xs border border-gray-300 text-gray-600 rounded-full px-3 py-1.5 hover:bg-gray-50 text-left leading-tight">सीएससी केंद्र का पता कैसे<br/>मिलेगा?</button>
      </div>

      <div className="relative mt-2">
        <input type="text" placeholder="यहाँ अपना प्रश्न लिखें..." className="w-full border border-gray-300 rounded-xl pl-4 pr-24 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
        <div className="absolute right-1.5 top-1.5 flex items-center gap-1">
          <button className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors">
            <Mic size={18} />
          </button>
          <button className="bg-primary text-white rounded-lg px-3 py-1.5 flex items-center gap-1 text-sm font-medium hover:bg-primary-hover transition-colors">
            पूछें <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
"""
update_file('C:/Users/sunny/Downloads/notice-explainer/frontend/src/components/FollowUpQA.tsx', qa_tsx)
