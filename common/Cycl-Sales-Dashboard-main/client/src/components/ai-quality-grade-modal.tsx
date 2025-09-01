import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Brain, X, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";

interface AIQualityGradeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contactName: string;
  aiQualityGrade: string;
  aiReasoning: string;
  aiStatus?: string;
  aiSummary?: string;
}

export default function AIQualityGradeModal({ 
  open, 
  onOpenChange, 
  contactName, 
  aiQualityGrade, 
  aiReasoning,
  aiStatus,
  aiSummary
}: AIQualityGradeModalProps) {
  
  // Function to get grade color and label
  const getGradeInfo = (grade: string) => {
    switch (grade) {
      case 'grade_a':
        return { label: 'Lead Grade A', color: 'bg-green-900 text-green-300', bgColor: 'bg-green-900/20' };
      case 'grade_b':
        return { label: 'Lead Grade B', color: 'bg-blue-900 text-blue-300', bgColor: 'bg-blue-900/20' };
      case 'grade_c':
        return { label: 'Lead Grade C', color: 'bg-yellow-900 text-yellow-300', bgColor: 'bg-yellow-900/20' };
      case 'no_grade':
      default:
        return { label: 'No Grade', color: 'bg-slate-800 text-slate-400', bgColor: 'bg-slate-800/20' };
    }
  };

  const gradeInfo = getGradeInfo(aiQualityGrade);

  // Function to check for grade consistency
  const checkGradeConsistency = (reasoning: string, grade: string) => {
    const gradeLabels = {
      'grade_a': ['grade a', 'grade-a', 'a grade', 'a-grade', 'lead grade a'],
      'grade_b': ['grade b', 'grade-b', 'b grade', 'b-grade', 'lead grade b'],
      'grade_c': ['grade c', 'grade-c', 'c grade', 'c-grade', 'lead grade c'],
      'no_grade': ['no grade', 'no-grade', 'ungraded']
    };
    
    const expectedGradeTerms = gradeLabels[grade as keyof typeof gradeLabels] || [];
    const reasoningLower = reasoning.toLowerCase();
    
    // Check if the reasoning mentions the correct grade
    const gradeMentioned = expectedGradeTerms.some(term => reasoningLower.includes(term));
    
    // Also check for any other grade mentions that might conflict
    const allGradeTerms = ['grade a', 'grade b', 'grade c', 'grade d', 'grade f', 'a grade', 'b grade', 'c grade', 'd grade', 'f grade'];
    const conflictingGrades = allGradeTerms.filter(term => 
      reasoningLower.includes(term) && !expectedGradeTerms.includes(term)
    );
    
    return {
      isConsistent: gradeMentioned && conflictingGrades.length === 0,
      conflictingGrades,
      gradeMentioned
    };
  };

  const gradeConsistency = checkGradeConsistency(aiReasoning, aiQualityGrade);

  // Function to parse HTML content and extract sections
  const parseReasoning = (reasoning: string) => {
    // If the reasoning contains structured HTML, use it directly
    if (reasoning.includes('<h3>') && reasoning.includes('</h3>')) {
      return {
        hasStructuredContent: true,
        rawHtml: reasoning
      };
    }
    
    // Fallback: Remove HTML tags and extract content
    const cleanReasoning = reasoning.replace(/<[^>]*>/g, '');
    
    // Try to extract sections based on common patterns
    const sections = {
      hasStructuredContent: false,
      summary: '',
      gradeReasoning: '',
      nextSteps: ''
    };

    // Split by common section headers
    const parts = cleanReasoning.split(/(?:Overall Assessment|Summary|Grade Reasoning|Potential Next Steps|Next Steps|Recommendations)/i);
    
    if (parts.length >= 2) {
      sections.summary = parts[1]?.trim() || '';
    }
    if (parts.length >= 3) {
      sections.gradeReasoning = parts[2]?.trim() || '';
    }
    if (parts.length >= 4) {
      sections.nextSteps = parts[3]?.trim() || '';
    }

    // If no clear sections found, use the whole content as summary
    if (!sections.summary && !sections.gradeReasoning && !sections.nextSteps) {
      sections.summary = cleanReasoning;
    }

    return sections;
  };

  const reasoningSections = parseReasoning(aiReasoning);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto bg-slate-900 border-slate-800">
        <DialogHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-blue-400" />
            <div>
              <DialogTitle className="text-xl font-semibold text-white">
                AI Lead Quality Grade
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                Analysis for {contactName}
              </DialogDescription>
            </div>
          </div>
          <button
            onClick={() => onOpenChange(false)}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </DialogHeader>

        <div className="space-y-6 mt-6">
          {/* Grade Consistency Warning */}
          {!gradeConsistency.isConsistent && (
            <Card className="bg-orange-900/20 border-orange-700">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-orange-300">
                  <AlertCircle className="w-5 h-5" />
                  <div>
                    <h4 className="font-semibold">Grade Inconsistency Detected</h4>
                    <p className="text-sm text-orange-200">
                      The analysis reasoning mentions different grades than the assigned grade. 
                      {gradeConsistency.conflictingGrades.length > 0 && (
                        <span> Found conflicting grades: {gradeConsistency.conflictingGrades.join(', ')}</span>
                      )}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Overall Assessment */}
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Overall Assessment</h3>
                <Badge className={`${gradeInfo.color} border-0`}>
                  {gradeInfo.label}
                </Badge>
              </div>
              <p className="text-slate-300 leading-relaxed">
                {reasoningSections.hasStructuredContent ? 
                  "The lead has been analyzed by AI. Review the detailed breakdown below for specific insights and recommendations." :
                  (reasoningSections as any).summary || "The lead has been analyzed by AI. Review the detailed breakdown below for specific insights and recommendations."
                }
              </p>
            </CardContent>
          </Card>

          {/* Structured Content Display */}
          {reasoningSections.hasStructuredContent && (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-4">
                <div 
                  className="text-slate-300 leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: (reasoningSections as any).rawHtml }}
                />
              </CardContent>
            </Card>
          )}

          {/* Fallback Content Display */}
          {!reasoningSections.hasStructuredContent && (
            <>
              {/* Grade Reasoning */}
              {(reasoningSections as any).gradeReasoning && (
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-blue-400" />
                      <h3 className="text-lg font-semibold text-white">Grade Reasoning</h3>
                    </div>
                    <div className="text-slate-300 leading-relaxed space-y-2">
                      {(reasoningSections as any).gradeReasoning.split('\n').map((line: string, index: number) => (
                        <p key={index} className="text-sm">
                          {line.trim()}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Potential Next Steps */}
              {(reasoningSections as any).nextSteps && (
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <h3 className="text-lg font-semibold text-white">Potential Next Steps</h3>
                    </div>
                    <div className="text-slate-300 leading-relaxed space-y-2">
                      {(reasoningSections as any).nextSteps.split('\n').map((line: string, index: number) => (
                        <p key={index} className="text-sm">
                          {line.trim()}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {/* AI Status (if available) */}
          {aiStatus && (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="w-5 h-5 text-orange-400" />
                  <h3 className="text-lg font-semibold text-white">Current Status</h3>
                </div>
                <div 
                  className="text-slate-300"
                  dangerouslySetInnerHTML={{ __html: aiStatus }}
                />
              </CardContent>
            </Card>
          )}

          {/* Raw AI Reasoning (if no structured content and no parsed sections) */}
          {!reasoningSections.hasStructuredContent && !(reasoningSections as any).summary && !(reasoningSections as any).gradeReasoning && !(reasoningSections as any).nextSteps && (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-5 h-5 text-purple-400" />
                  <h3 className="text-lg font-semibold text-white">AI Analysis</h3>
                </div>
                <div 
                  className="text-slate-300 leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: aiReasoning }}
                />
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
