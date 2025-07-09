import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertCircle,
  Brain,
  CheckCircle,
  Download,
  Pause,
  Phone,
  Play,
  SkipBack,
  SkipForward,
  TrendingUp,
  Volume2
} from "lucide-react";
import { useState } from "react";

interface CallData {
  id: string;
  contactName: string;
  contactPhone: string;
  callDate: string;
  callTime: string;
  duration: string;
  status: string;
  agent: string;
  direction: "inbound" | "outbound";
  recordingUrl?: string;
  transcript: TranscriptEntry[];
  summary: CallSummary;
  aiAnalysis: AIAnalysis;
}

interface TranscriptEntry {
  timestamp: string;
  speaker: "agent" | "contact";
  speakerName: string;
  text: string;
}

interface CallSummary {
  outcome: string;
  keyPoints: string[];
  nextSteps: string[];
  sentiment: "positive" | "neutral" | "negative";
}

interface AIAnalysis {
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
}

interface CallTranscriptDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  callData: CallData | null;
}

export default function CallTranscriptDialog({ open, onOpenChange, callData }: CallTranscriptDialogProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  if (!callData) return null;

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive": return "text-green-400 bg-green-500/20";
      case "negative": return "text-red-400 bg-red-500/20";
      default: return "text-yellow-400 bg-yellow-500/20";
    }
  };

  const getSatisfactionColor = (level: string) => {
    switch (level) {
      case "high": return "text-green-400";
      case "low": return "text-red-400";
      default: return "text-yellow-400";
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl h-[90vh] bg-slate-900 border-slate-800 text-slate-50 flex flex-col overflow-hidden">
        <DialogHeader className="pb-4 flex-shrink-0">
          <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
            <Phone className="w-5 h-5 text-blue-500" />
            Call Details - {callData.contactName}
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            View call recording, transcript, and AI analysis for this conversation.
          </DialogDescription>
        </DialogHeader>

        {/* New Two-Column Layout with custom widths */}
        <div className="grid grid-cols-[1fr_2fr] gap-6 flex-1 overflow-hidden min-h-0">
          {/* Left Panel: Call Details, Summary, Inquiry, Financial, Property, AI Analysis, Highlights, Improvements, Next Steps */}
          <Card className="bg-slate-800 border-slate-700 flex flex-col overflow-y-auto max-h-full">
            <CardContent className="space-y-6 p-6">
              {/* Call Details Row */}
              <div className="flex flex-wrap items-center gap-4 mb-2">
                <div className="flex flex-col gap-1 min-w-[180px]">
                  <span className="text-xs text-slate-400">Call Date</span>
                  <span className="text-sm text-slate-200 font-medium">{callData.callDate}</span>
                </div>
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-xs text-slate-400">Call Direction</span>
                  <Badge className={`border-0 ${callData.direction === 'inbound' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>{callData.direction.charAt(0).toUpperCase() + callData.direction.slice(1)}</Badge>
                </div>
                <div className="flex flex-col gap-1 min-w-[120px]">
                  <span className="text-xs text-slate-400">Lead Grade</span>
                  <Badge className="bg-yellow-500/20 text-yellow-400 border-0">Lead Grade C</Badge>
                </div>
                <div className="flex flex-col gap-1 min-w-[180px]">
                  <span className="text-xs text-slate-400">Contact</span>
                  <span className="text-sm text-slate-200 font-medium">{callData.contactName}</span>
                </div>
                <div className="flex flex-col gap-1 min-w-[180px]">
                  <span className="text-xs text-slate-400">User</span>
                  <span className="text-sm text-slate-200 font-medium">{callData.agent}</span>
                </div>
              </div>
              <Separator className="bg-slate-700" />

              {/* Call Summary */}
              <div>
                <span className="text-base font-semibold text-white">Call Summary</span>
                <p className="text-sm text-slate-300 mt-2">{callData.summary.outcome}</p>
              </div>
              <Separator className="bg-slate-700" />

              {/* Inquiry Details */}
              <div>
                <span className="text-base font-semibold text-white">Inquiry Details</span>
                <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                  {callData.summary.keyPoints.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
              <Separator className="bg-slate-700" />

              {/* Financial Details */}
              <div>
                <span className="text-base font-semibold text-white">Financial Details</span>
                <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                  <li>Payments Behind: 9</li>
                  <li>Monthly Mortgage Payment: $1,900</li>
                  <li>Household Income: $7,400 per month (with wife)</li>
                  <li>Estimated Mortgage Owed: $244,000</li>
                </ul>
              </div>
              <Separator className="bg-slate-700" />

              {/* Property & Occupancy Details */}
              <div>
                <span className="text-base font-semibold text-white">Property & Occupancy Details</span>
                <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                  <li>Occupancy: Owner occupied, spouse lives in the property</li>
                  <li>Property Type: Single family home</li>
                  <li>Location: Middleville</li>
                </ul>
              </div>
              <Separator className="bg-slate-700" />

              {/* AI Analysis */}
              <div>
                <span className="text-base font-semibold text-white flex items-center gap-2">
                  <Brain className="w-4 h-4 text-purple-400" />
                  AI Analysis
                  <Badge className="bg-purple-500/20 text-purple-400 border-0 ml-2">
                    {callData.aiAnalysis.overallScore}/10
                  </Badge>
                </span>
                <div className="space-y-3 mt-2">
                  <div className="text-xs text-slate-400 font-medium">Performance Breakdown</div>
                  {Object.entries(callData.aiAnalysis.categories).map(([category, score]) => (
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
                <Separator className="bg-slate-700 my-3" />
                <div className="space-y-2">
                  <div>
                    <span className="text-xs text-slate-400">Call Intent:</span>
                    <p className="text-sm text-white">{callData.aiAnalysis.callIntent}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Customer Satisfaction:</span>
                    <Badge className={`${getSatisfactionColor(callData.aiAnalysis.satisfactionLevel)} bg-transparent border-0`}>
                      {callData.aiAnalysis.satisfactionLevel}
                    </Badge>
                  </div>
                </div>
              </div>
              <Separator className="bg-slate-700" />

              {/* Highlights & Improvements Tabs */}
              <Tabs defaultValue="highlights" className="w-full">
                <TabsList className="grid w-full grid-cols-2 bg-slate-800">
                  <TabsTrigger value="highlights" className="data-[state=active]:bg-slate-700">
                    Highlights
                  </TabsTrigger>
                  <TabsTrigger value="improvements" className="data-[state=active]:bg-slate-700">
                    Improvements
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="highlights" className="mt-4">
                  <ul className="space-y-2">
                    {callData.aiAnalysis.highlights.map((highlight, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-300">{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </TabsContent>
                <TabsContent value="improvements" className="mt-4">
                  <ul className="space-y-2">
                    {callData.aiAnalysis.improvements.map((improvement, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-300">{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </TabsContent>
              </Tabs>
              <Separator className="bg-slate-700" />

              {/* Next Steps */}
              <div>
                <span className="text-base font-semibold text-white flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-orange-400" />
                  Next Steps
                </span>
                <ul className="space-y-2 mt-2">
                  {callData.summary.nextSteps.map((step, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <div className="w-4 h-4 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center mt-0.5 flex-shrink-0">
                        {index + 1}
                      </div>
                      <span className="text-slate-300">{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Right Panel: Audio Player & Transcript (wider) */}
          <Card className="bg-slate-800 border-slate-700 flex flex-col overflow-hidden max-h-full">
            <CardContent className="flex flex-col p-6 h-full">
              {/* Audio Player */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-slate-400">Audio</span>
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white ml-auto">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
                {/* Audio Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>{formatTime(currentTime)}</span>
                    <span>{callData.duration}</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: "35%" }}
                    />
                  </div>
                </div>
                {/* Audio Controls */}
                <div className="flex items-center justify-center gap-4 mt-2">
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                    <SkipBack className="w-4 h-4" />
                  </Button>
                  <Button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="bg-blue-600 hover:bg-blue-700 rounded-full w-10 h-10 p-0"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                    <SkipForward className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                    <Volume2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              {/* Transcript */}
              <div className="flex-1 overflow-y-auto pr-2">
                <div className="space-y-4 pb-4">
                  {callData.transcript.map((entry, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-slate-400">{entry.timestamp}</span>
                        <Badge
                          variant="outline"
                          className={`border-slate-600 text-xs ${entry.speaker === 'agent' ? 'text-blue-400' : 'text-green-400'
                            }`}
                        >
                          {entry.speakerName}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-200 pl-4 border-l-2 border-slate-700">
                        {entry.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}