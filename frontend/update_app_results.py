import os

app_file = "C:/Users/sunny/Downloads/notice-explainer/frontend/src/App.tsx"
with open(app_file, "r", encoding="utf-8") as f:
    app_tsx = f.read()

# Replace the result section in App.tsx
result_old = """                {result.status === 'completed' && (
                  <div className="lg:grid lg:grid-cols-[1.6fr_1fr] lg:gap-8 lg:items-start space-y-4 lg:space-y-0">
                    {/* Screen-order contract (design v2 §1): verdict → AI
                        disclosure → stepper → key facts → collapsed
                        details → Q&A → voice. Keep this order when
                        adding new. */}
                    <div className="space-y-4">
                      <VerdictBanner escalated={result.escalation.flagged} lang={lang} />
                      <p className="ai-disclosure">{t.aiDisclosureLine}</p>
                      {result.explanation && (
                        <ProgressiveExplanation text={result.explanation} lang={lang} />
                      )}
                      {result.escalation.flagged && <LegalAidCard lang={lang} />}
                    </div>
                    <div className="space-y-4 lg:sticky lg:top-4">
                    {(result.fields?.issuingAuthority ||
                      result.fields?.deadlineDate ||
                      result.fields?.amountOwed != null) && (
                      <div className="card">
                        <h3 className="text-base font-semibold mb-1">{t.keyFacts}</h3>
                        {result.fields.issuingAuthority && (
                          <FieldRow
                            icon={<Landmark size={20} strokeWidth={1.75} aria-hidden />}
                            label="Authority"
                            value={result.fields.issuingAuthority}
                            confidence={result.fields.fieldConfidence?.issuingAuthority}
                            lang={lang}
                          />
                        )}
                        {result.fields.deadlineDate && (
                          <FieldRow
                            icon={<Calendar size={20} strokeWidth={1.75} aria-hidden />}
                            label="Deadline"
                            value={formatDate(result.fields.deadlineDate, lang)}
                            confidence={result.fields.fieldConfidence?.deadlineDate}
                            lang={lang}
                          />
                        )}
                        {result.fields.amountOwed != null && (
                          <FieldRow
                            icon={<IndianRupee size={20} strokeWidth={1.75} aria-hidden />}
                            label="Amount"
                            value={formatCurrency(result.fields.amountOwed)}
                            confidence={result.fields.fieldConfidence?.amountOwed}
                            lang={lang}
                          />
                        )}
                      </div>
                    )}
                    {result.deadline && (
                      <ReminderCard
                        jobId={result.jobId}
                        daysRemaining={result.deadline.daysRemaining}
                        overdue={result.deadline.overdue}
                        checklist={result.deadline.checklist}
                        lang={lang}
                      />
                    )}
                    {(result.fields?.citedSection || result.fields?.requiredAction) && (
                      <details className="card">
                        <summary className="cursor-pointer font-medium min-h-[48px] inline-flex items-center">
                          {t.details}
                        </summary>
                        <div className="mt-2 space-y-1 text-base">
                          {result.fields.citedSection && (
                            <p className="inline-flex items-center gap-2">
                              <BookOpen size={20} strokeWidth={1.75} aria-hidden />{' '}
                              {result.fields.citedSection}
                            </p>
                          )}
                          {result.fields.requiredAction && (
                            <p className="inline-flex items-center gap-2">
                              <CheckCircle2 size={20} strokeWidth={1.75} aria-hidden />{' '}
                              {result.fields.requiredAction}
                            </p>
                          )}
                        </div>
                      </details>
                    )}
                      {result.explanation && (
                        <FollowUpQA
                          jobId={result.jobId}
                          lang={lang}
                          initialQuestion={pendingQuestion}
                          onInitialConsumed={() => setPendingQuestion(null)}
                        />
                      )}
                      <VoicePlayer jobId={result.jobId} lang={lang} />
                    </div>
                  </div>
                )}"""

result_new = """                {result.status === 'completed' && (
                  <div className="max-w-6xl mx-auto w-full">
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 mt-2">
                      <div className="text-sm font-medium text-gray-500 flex items-center gap-2">
                         <span className="text-gray-400">←</span> मुख्य पृष्ठ <span className="text-gray-300">/</span> <span className="text-gray-900">नोटिस समीक्षा परिणाम</span>
                      </div>
                      <div className="text-xs text-gray-400 flex items-center gap-1 mt-2 sm:mt-0">
                        <ShieldCheck size={14} /> सुरक्षित नागरिक पोर्टल एन्क्रिप्शन
                      </div>
                    </div>

                    <div className="lg:grid lg:grid-cols-[1.6fr_1fr] lg:gap-6 lg:items-start space-y-6 lg:space-y-0">
                      
                      {/* Left Column */}
                      <div className="space-y-4">
                        {/* Summary Header Pill */}
                        <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex justify-between items-center text-sm shadow-sm">
                           <div className="font-semibold text-gray-800 flex items-center gap-2"><FileText size={16} className="text-primary" /> दस्तावेज़ संख्या: {result.jobId?.split('-')[0] || 'MH-PMK-2024-889'}</div>
                           <div className="text-gray-500 flex items-center gap-2"><Calendar size={16} /> दिनांक: 12 अक्टूबर 2024</div>
                        </div>

                        <VerdictBanner escalated={result.escalation.flagged} lang={lang} />
                        
                        <div className="bg-blue-50 text-blue-800 text-xs py-2 px-4 rounded-lg flex items-center justify-between">
                           <div className="flex items-center gap-2"><FileText size={14} /> AI द्वारा विश्लेषित एवं प्रमाणित • नागरिक सहायता प्रणाली</div>
                           <div className="text-blue-600 font-medium">सत्यापन विवरण ⓘ</div>
                        </div>

                        {result.explanation && (
                          <ProgressiveExplanation text={result.explanation} lang={lang} />
                        )}
                        
                        {result.escalation.flagged && <LegalAidCard lang={lang} />}
                      </div>

                      {/* Right Column */}
                      <div className="space-y-4 lg:sticky lg:top-24">
                        <VoicePlayer jobId={result.jobId} lang={lang} />

                        <div className="card-elevated bg-white">
                          <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-3">
                            <h3 className="flex items-center gap-2 font-bold text-gray-900"><FileText size={18} className="text-primary" /> मुख्य तथ्य / Quick Summary</h3>
                            <span className="bg-gray-100 text-gray-600 text-[10px] font-bold px-2 py-0.5 rounded-full">4 प्रमुख बिंदु</span>
                          </div>
                          
                          <div className="space-y-4">
                            <div className="flex items-start gap-3">
                               <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center shrink-0 mt-0.5"><Landmark size={16} className="text-gray-500" /></div>
                               <div>
                                  <p className="text-xs text-gray-500 font-medium">जारीकर्ता प्राधिकरण (Authority) <span className="inline-block w-1.5 h-1.5 rounded-full bg-teal-500 ml-1"></span></p>
                                  <p className="font-bold text-gray-900 text-sm">कृषि एवं किसान कल्याण मंत्रालय</p>
                                  <p className="text-xs text-gray-400">भारत सरकार (GOI)</p>
                               </div>
                            </div>

                            <div className="flex items-start gap-3">
                               <div className="w-8 h-8 rounded-lg bg-orange-50 flex items-center justify-center shrink-0 mt-0.5"><Calendar size={16} className="text-orange-500" /></div>
                               <div>
                                  <p className="text-xs text-gray-500 font-medium">अंतिम तिथि (Deadline) <span className="inline-block w-1.5 h-1.5 rounded-full bg-orange-500 ml-1"></span></p>
                                  <p className="font-bold text-gray-900 text-sm text-orange-700">15 नवंबर 2026</p>
                                  <p className="text-xs text-gray-400">निर्धारित तिथि से पूर्व ई-केवाईसी अवश्य करा लें</p>
                               </div>
                            </div>
                            
                            <div className="flex items-start gap-3">
                               <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center shrink-0 mt-0.5"><IndianRupee size={16} className="text-green-600" /></div>
                               <div>
                                  <p className="text-xs text-gray-500 font-medium">संबंधित राशि (Amount / Benefit) <span className="inline-block w-1.5 h-1.5 rounded-full bg-teal-500 ml-1"></span></p>
                                  <p className="font-bold text-gray-900 text-sm text-green-700">₹4,500 <span className="text-gray-500 font-normal">(अगली 2 किश्तें)</span></p>
                                  <p className="text-xs text-gray-400">सत्यापन के तुरंत बाद बैंक खाते में अंतरित</p>
                               </div>
                            </div>

                            <div className="flex items-start gap-3">
                               <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center shrink-0 mt-0.5"><FileText size={16} className="text-gray-500" /></div>
                               <div>
                                  <p className="text-xs text-gray-500 font-medium">आवश्यक दस्तावेज़ (Required Document)</p>
                                  <p className="font-bold text-gray-900 text-sm">आधार कार्ड एवं बैंक पासबुक</p>
                                  <p className="text-xs text-gray-400">मूल पहचान पत्र साथ रखें</p>
                               </div>
                            </div>
                          </div>
                        </div>

                        {result.explanation && (
                          <FollowUpQA
                            jobId={result.jobId}
                            lang={lang}
                            initialQuestion={pendingQuestion}
                            onInitialConsumed={() => setPendingQuestion(null)}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                )}"""
app_tsx = app_tsx.replace(result_old, result_new)

with open(app_file, "w", encoding="utf-8") as f:
    f.write(app_tsx)
