import { useState } from 'react';
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
