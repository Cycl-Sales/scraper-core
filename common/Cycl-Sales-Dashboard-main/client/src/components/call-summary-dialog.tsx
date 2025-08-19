import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Brain, Eye, Sparkles, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

interface CallSummaryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  summaryHtml: string;
  callGrade?: string;
  callDate?: string;
  contactName?: string;
  hasSummary?: boolean;
  messageId?: number;
  onGenerateSummary?: (messageId: number) => Promise<void>;
  // Additional call details
  callDirection?: "inbound" | "outbound";
  agent?: string;
  duration?: string;
  status?: string;
  contactPhone?: string;
  callTime?: string;
  aiAnalysis?: {
    overallScore: number;
    categories: {
      communication: number;
      professionalism: number;
      problemSolving: number;
      followUp: number;
    };
    highlights: string[];
    improvements: string[];
    callIntent: string;
    satisfactionLevel: "high" | "medium" | "low";
  };
}

export default function CallSummaryDialog({ 
  open, 
  onOpenChange, 
  summaryHtml, 
  callGrade, 
  callDate, 
  contactName,
  hasSummary = true,
  messageId,
  onGenerateSummary,
  callDirection,
  agent,
  duration,
  status,
  contactPhone,
  callTime,
  aiAnalysis
}: CallSummaryDialogProps) {
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'text-green-400';
      case 'B': return 'text-blue-400';
      case 'C': return 'text-yellow-400';
      case 'D': return 'text-orange-400';
      case 'F': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const getSatisfactionColor = (level: string) => {
    switch (level) {
      case "high": return "text-green-400";
      case "low": return "text-red-400";
      default: return "text-yellow-400";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl h-[90vh] bg-slate-900 border-slate-800 text-slate-50 flex flex-col overflow-hidden">
        <DialogHeader className="pb-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
                <Phone className="w-5 h-5 text-blue-500" />
                Call Details - {contactName}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                View call recording, transcript, and AI analysis for this conversation.
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              {messageId && onGenerateSummary && (
                <Button
                  onClick={() => onGenerateSummary(messageId)}
                  className={`${hasSummary ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'} text-white border-0`}
                  size="sm"
                >
                  <Brain className="w-4 h-4 mr-2" />
                  {hasSummary ? 'Regenerate AI Summary' : 'Generate AI Summary'}
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        {/* Full-Width Layout */}
        <div className="flex-1 overflow-hidden min-h-0">
          {/* Full-Width Panel: Call Details, Summary, AI Analysis */}
          <Card className="bg-slate-800 border-slate-700 flex flex-col overflow-y-auto max-h-full">
            <CardContent className="space-y-6 p-6">
              {/* Call Details Row */}
              <div className="flex flex-wrap items-center gap-4 mb-2">
                <div className="flex flex-col gap-1 min-w-[180px]">
                  <span className="text-xs text-slate-400">Call Date</span>
                  <span className="text-sm text-slate-200 font-medium">{callDate}</span>
                </div>
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-xs text-slate-400">Call Direction</span>
                  <Badge className={`border-0 ${callDirection === 'inbound' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                    {callDirection ? callDirection.charAt(0).toUpperCase() + callDirection.slice(1) : 'Unknown'}
                  </Badge>
                </div>
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-xs text-slate-400">Lead Grade</span>
                  <Badge className={`border-0 ${getGradeColor(callGrade || 'N/A')}`}>
                    {callGrade ? `Lead Grade ${callGrade}` : 'N/A'}
                  </Badge>
                </div>
                <div className="flex flex-col gap-1 min-w-[180px]">
                  <span className="text-xs text-slate-400">Contact</span>
                  <span className="text-sm text-slate-200 font-medium">{contactName}</span>
                </div>
                <div className="flex flex-col gap-1 min-w-[180px]">
                  <span className="text-xs text-slate-400">User</span>
                  <span className="text-sm text-slate-200 font-medium">{agent || 'Unknown'}</span>
                </div>
              </div>
              <Separator className="bg-slate-700" />

              {/* AI Call Summary */}
              {hasSummary && summaryHtml ? (
                <>
                  <div>
                    <span className="text-base font-semibold text-white flex items-center gap-2">
                      <Brain className="w-4 h-4 text-blue-400" />
                      AI Call Summary
                      {callDate && (
                        <span className="text-xs text-slate-400">
                          {new Date(callDate).toLocaleDateString()}
                        </span>
                      )}
                    </span>
                    {/* Debug: Show raw HTML content */}
                    {process.env.NODE_ENV === 'development' && (
                      <details className="mt-2 p-2 bg-slate-800 rounded text-xs">
                        <summary className="cursor-pointer text-slate-400">Debug: Raw HTML</summary>
                        <pre className="mt-2 text-slate-300 whitespace-pre-wrap">{summaryHtml}</pre>
                      </details>
                    )}
                    <div 
                      className="text-sm text-slate-300 mt-2 max-w-none ai-summary-html"
                      dangerouslySetInnerHTML={{ __html: summaryHtml }}
                      style={{
                        lineHeight: '1.6',
                      }}
                    />
                  </div>
                  <Separator className="bg-slate-700" />
                </>
              ) : (
                <>
                  <div className="flex flex-col items-center justify-center text-center p-8">
                    <Eye className="w-16 h-16 text-slate-500 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-200 mb-2">No AI Summary Available</h3>
                    <p className="text-slate-400 mb-6 max-w-md">
                      This call doesn't have an AI-generated summary yet. Generate one to get insights about the conversation.
                    </p>
                  </div>
                  <Separator className="bg-slate-700" />
                </>
              )}

              {/* AI Analysis */}
              {aiAnalysis && (
                <>
                  <div>
                    <span className="text-base font-semibold text-white flex items-center gap-2">
                      <Brain className="w-4 h-4 text-purple-400" />
                      AI Analysis
                      <Badge className="bg-purple-500/20 text-purple-400 border-0 ml-2">
                        {aiAnalysis.overallScore}/10
                      </Badge>
                    </span>
                    <div className="space-y-3 mt-2">
                      <div className="text-xs text-slate-400 font-medium">Performance Breakdown</div>
                      {Object.entries(aiAnalysis.categories).map(([category, score]) => (
                        <div key={category} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-300 capitalize">{category}</span>
                            <span className="text-slate-400">{score}/10</span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-1.5">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full"
                              style={{ width: `${score * 10}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <Separator className="bg-slate-700" />

                  {/* Highlights */}
                  {aiAnalysis.highlights && aiAnalysis.highlights.length > 0 && (
                    <>
                      <div>
                        <span className="text-base font-semibold text-white">Highlights</span>
                        <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                          {aiAnalysis.highlights.map((highlight, idx) => (
                            <li key={idx}>{highlight}</li>
                          ))}
                        </ul>
                      </div>
                      <Separator className="bg-slate-700" />
                    </>
                  )}

                  {/* Improvements */}
                  {aiAnalysis.improvements && aiAnalysis.improvements.length > 0 && (
                    <>
                      <div>
                        <span className="text-base font-semibold text-white">Areas for Improvement</span>
                        <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                          {aiAnalysis.improvements.map((improvement, idx) => (
                            <li key={idx}>{improvement}</li>
                          ))}
                        </ul>
                      </div>
                      <Separator className="bg-slate-700" />
                    </>
                  )}

                  {/* Call Intent & Satisfaction */}
                  <div>
                    <span className="text-base font-semibold text-white">Call Intent & Satisfaction</span>
                    <div className="space-y-2 mt-2">
                      <div>
                        <span className="text-xs text-slate-400">Intent:</span>
                        <p className="text-sm text-slate-300">{aiAnalysis.callIntent}</p>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400">Satisfaction Level:</span>
                        <span className={`text-sm font-medium ml-2 ${getSatisfactionColor(aiAnalysis.satisfactionLevel)}`}>
                          {aiAnalysis.satisfactionLevel.charAt(0).toUpperCase() + aiAnalysis.satisfactionLevel.slice(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
