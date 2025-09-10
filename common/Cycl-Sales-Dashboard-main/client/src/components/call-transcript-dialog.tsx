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
  Volume2,
  VolumeX
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { PROD_BASE_URL } from "@/lib/constants";

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
  recording_filename?: string;
  recording_size?: number;
  recording_content_type?: string;
  transcript: TranscriptEntry[];
  summary: CallSummary;
  aiAnalysis: AIAnalysis;
  aiCallSummary?: {
    html: string;
    generated: boolean;
    date: string | null;
  };
  callGrade?: string;
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
  onDataRefresh?: () => void; // Callback to refresh parent data
}

// Helper to parse timestamp string to seconds
function parseTimestamp(ts: string): number {
  const parts = ts.split(":").map(Number);
  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    return parts[0] * 60 + parts[1];
  }
  return 0;
}

export default function CallTranscriptDialog({ open, onOpenChange, callData, onDataRefresh }: CallTranscriptDialogProps) {
  // Don't render if no call data is provided
  if (!callData) {
    return null;
  }

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [audioRef, setAudioRef] = useState<HTMLAudioElement | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isFetchingTranscript, setIsFetchingTranscript] = useState(false);
  const [isFetchingRecording, setIsFetchingRecording] = useState(false);
  const [localTranscript, setLocalTranscript] = useState(callData.transcript || []);
  const [localRecordingUrl, setLocalRecordingUrl] = useState(callData.recordingUrl || '');
  const transcriptRefs = useRef<(HTMLDivElement | null)[]>([]);
  const recordingFetchAttemptedRef = useRef(false);
  const transcriptFetchAttemptedRef = useRef(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

  // Update local transcript and recording when callData changes and check for existing data
  useEffect(() => {
    setLocalTranscript(callData.transcript || []);
    // Ensure recording URL uses the correct base URL
    const recordingUrl = callData.recordingUrl || '';
    const fullRecordingUrl = recordingUrl.startsWith('http') ? recordingUrl : `${PROD_BASE_URL}${recordingUrl}`;
    setLocalRecordingUrl(fullRecordingUrl);
    
    // Reset the fetch attempt flags when callData changes
    recordingFetchAttemptedRef.current = false;
    transcriptFetchAttemptedRef.current = false;
    
    // Check for transcripts if we don't have any and haven't already fetched them
    if ((!callData.transcript || callData.transcript.length === 0) && callData.id && !isFetchingTranscript && !transcriptFetchAttemptedRef.current) {
      // Use setTimeout to avoid calling the function during render
      setTimeout(() => {
        if (!isFetchingTranscript && !transcriptFetchAttemptedRef.current) {
          handleCheckExistingTranscript();
        }
      }, 100);
    }

    // Check for recordings if we don't have any and haven't already fetched them
    // Only check if we haven't already attempted to fetch and don't have a local recording URL
    if (!localRecordingUrl && callData.id && !isFetchingRecording && !recordingFetchAttemptedRef.current) {
      // Use setTimeout to avoid calling the function during render
      setTimeout(() => {
        if (!isFetchingRecording && !recordingFetchAttemptedRef.current) {
          handleCheckExistingRecording();
        }
      }, 100);
    }
  }, [callData.transcript, callData.recordingUrl, callData.id, isFetchingTranscript, isFetchingRecording]);

  // Auto-scroll to active transcript entry
  useEffect(() => {
    if (!callData) return;
    
    // Find the active transcript index
    let activeIndex = -1;
    const transcriptTimes = callData.transcript.map(entry => parseTimestamp(entry.timestamp));
    for (let i = 0; i < transcriptTimes.length; i++) {
      const time = transcriptTimes[i];
      const nextTime = transcriptTimes[i + 1] ?? Infinity;
      if (currentTime >= time && currentTime < nextTime) {
        activeIndex = i;
        break;
      }
    }
    if (activeIndex === -1 && transcriptTimes.length > 0 && currentTime >= transcriptTimes[transcriptTimes.length - 1]) {
      activeIndex = transcriptTimes.length - 1;
    }

    if (activeIndex !== -1 && transcriptRefs.current[activeIndex]) {
      transcriptRefs.current[activeIndex]?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [currentTime, callData]);

  // Show loading state when callData is null
  if (!callData) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-6xl h-[90vh] bg-slate-900 border-slate-800 text-slate-50 flex flex-col overflow-hidden">
          <DialogHeader className="pb-4 flex-shrink-0">
            <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
              <Phone className="w-5 h-5 text-blue-500" />
              Call Details
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Loading call information...
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 flex items-center justify-center">
            <div className="text-slate-400">Loading call details...</div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  // Removed unused getSentimentColor helper

  const getSatisfactionColor = (level: string) => {
    switch (level) {
      case "high": return "text-green-400";
      case "low": return "text-red-400";
      default: return "text-yellow-400";
    }
  };

  const formatTime = (seconds: number) => {
    if (!isFinite(seconds) || seconds < 0) return "00:00";
    const rounded = Math.floor(seconds);
    const mins = Math.floor(rounded / 60);
    const secs = rounded % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    if (audioRef) {
      if (isPlaying) {
        audioRef.pause();
      } else {
        audioRef.play();
      }
    }
  };

  const handleSkipBack = () => {
    if (audioRef) {
      audioRef.currentTime = Math.max(0, audioRef.currentTime - 10);
    }
  };

  const handleSkipForward = () => {
    if (audioRef) {
      audioRef.currentTime = Math.min(audioRef.duration, audioRef.currentTime + 10);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef) {
      setCurrentTime(audioRef.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef) {
      console.log('Audio metadata loaded:', {
        duration: audioRef.duration,
        src: audioRef.src,
        readyState: audioRef.readyState
      });
      setDuration(audioRef.duration);
    }
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (audioRef && audioRef.duration) {
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const percentage = Math.max(0, Math.min(1, clickX / rect.width));
      const newTime = percentage * audioRef.duration;
      
      audioRef.currentTime = newTime;
      console.log(`Seeking to ${newTime}s (${(percentage * 100).toFixed(1)}%)`);
    }
  };

  const handleMuteToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (audioRef) {
      audioRef.muted = !audioRef.muted;
      setIsMuted(audioRef.muted);
    }
  };

  const handleDownload = () => {
    if (localRecordingUrl) {
      const link = document.createElement('a');
      link.href = localRecordingUrl;
      link.download = localRecordingUrl.split('/').pop() || 'recording.mp3';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleCheckExistingTranscript = async () => {
    if (!callData) return;
    
    // Mark that we've attempted to fetch
    transcriptFetchAttemptedRef.current = true;
    
    try {
      console.log('Checking for existing transcript for call:', callData.id);

      const response = await fetch(`${PROD_BASE_URL}/api/get-transcript/${callData.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Existing transcript API Response status:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('Existing transcript API Response result:', result);
        
        if (result.success && result.transcript && result.transcript.length > 0) {
          // Update local transcript state with existing data
          setLocalTranscript(result.transcript);
          console.log(`Found existing transcript with ${result.transcript_count} segments`);
          return; // Don't fetch if we already have transcripts
        }
      }
      
      // If no existing transcript found, fetch from GHL API
      console.log('No existing transcript found, fetching from GHL API...');
      await handleFetchTranscript();
      
    } catch (error) {
      console.error('Error checking existing transcript:', error);
      // Fallback to fetching from GHL API
      await handleFetchTranscript();
    }
  };

  const handleFetchTranscript = async () => {
    if (!callData) return;
    
    // Mark that we've attempted to fetch
    transcriptFetchAttemptedRef.current = true;
    setIsFetchingTranscript(true);
    try {
      console.log('Fetching transcript for call:', callData.id);

      const response = await fetch(`${PROD_BASE_URL}/api/fetch-transcript/${callData.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          appId: '6867d1537079188afca5013c' // Default app ID
        }),
      });

      console.log('Transcript API Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Transcript API Error response:', errorText);
        throw new Error(`Failed to fetch transcript: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Transcript API Response result:', result);
      
      if (result.success) {
        // Update local transcript state
        setLocalTranscript(result.transcript);
        alert(`Transcript fetched successfully! ${result.total_sentences} sentences found.`);
        
        // Trigger data refresh
        if (onDataRefresh) {
          await onDataRefresh();
        } else {
          // Fallback: close and reopen dialog to trigger refresh
          onOpenChange(false);
          setTimeout(() => onOpenChange(true), 100);
        }
      } else {
        throw new Error(result.error || 'Failed to fetch transcript');
      }
    } catch (error) {
      console.error('Error fetching transcript:', error);
      alert(`Error fetching transcript: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsFetchingTranscript(false);
    }
  };

  const handleCheckExistingRecording = async () => {
    if (!callData) return;
    
    // Mark that we've attempted to fetch
    recordingFetchAttemptedRef.current = true;
    
    try {
      console.log('Checking for existing recording for call:', callData.id);

      // If we already have a recording URL, no need to fetch
      if (callData.recordingUrl) {
        const fullRecordingUrl = callData.recordingUrl.startsWith('http') ? callData.recordingUrl : `${PROD_BASE_URL}${callData.recordingUrl}`;
        setLocalRecordingUrl(fullRecordingUrl);
        return;
      }

      // If no recording URL, fetch it
      console.log('No existing recording found, fetching from GHL API...');
      await handleFetchRecording();
      
    } catch (error) {
      console.error('Error checking existing recording:', error);
      // Fallback to fetching from GHL API
      await handleFetchRecording();
    }
  };

  const handleFetchRecording = async () => {
    if (!callData) return;
    
    // Mark that we've attempted to fetch
    recordingFetchAttemptedRef.current = true;
    setIsFetchingRecording(true);
    try {
      console.log('Fetching recording for call:', callData.id);

      const response = await fetch(`${PROD_BASE_URL}/api/fetch-recording/${callData.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          appId: '6867d1537079188afca5013c' // Default app ID
        }),
      });

      console.log('Recording API Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Recording API Error response:', errorText);
        throw new Error(`Failed to fetch recording: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Recording API Response result:', result);
      
      if (result.success) {
        // Update local recording state with full URL
        const fullRecordingUrl = result.recording_url.startsWith('http') ? result.recording_url : `${PROD_BASE_URL}${result.recording_url}`;
        setLocalRecordingUrl(fullRecordingUrl);
        alert(`Recording fetched successfully!`);
        
        // Trigger data refresh
        if (onDataRefresh) {
          await onDataRefresh();
        } else {
          // Fallback: close and reopen dialog to trigger refresh
          onOpenChange(false);
          setTimeout(() => onOpenChange(true), 100);
        }
      } else {
        throw new Error(result.error || 'Failed to fetch recording');
      }
    } catch (error) {
      console.error('Error fetching recording:', error);
      alert(`Error fetching recording: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsFetchingRecording(false);
    }
  };

  const handleGenerateAISummary = async () => {
    if (!callData) return;
    
    setIsGeneratingSummary(true);
    try {
      console.log('Generating AI summary for call:', callData.id);

      const response = await fetch(`${PROD_BASE_URL}/api/generate-call-summary/${callData.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}), // No API key needed - backend handles it
      });

      console.log('API Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error response:', errorText);
        throw new Error(`Failed to generate AI summary: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log('API Response result:', result);
      
      if (result.success) {
        // Show success message
        alert('AI Summary generated successfully! Refreshing data...');
        
        // Trigger data refresh
        if (onDataRefresh) {
          await onDataRefresh();
        } else {
          // Fallback: close and reopen dialog to trigger refresh
          onOpenChange(false);
          setTimeout(() => onOpenChange(true), 100);
        }
      } else {
        throw new Error(result.error || 'Failed to generate AI summary');
      }
    } catch (error) {
      console.error('Error generating AI summary:', error);
      alert(`Error generating AI summary: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  // Find the active transcript index for highlighting
  let activeIndex = -1;
  const transcriptTimes = localTranscript?.map(entry => parseTimestamp(entry.timestamp)) || [];
  for (let i = 0; i < transcriptTimes.length; i++) {
    const time = transcriptTimes[i];
    const nextTime = transcriptTimes[i + 1] ?? Infinity;
    if (currentTime >= time && currentTime < nextTime) {
      activeIndex = i;
      break;
    }
  }
  if (activeIndex === -1 && transcriptTimes.length > 0 && currentTime >= transcriptTimes[transcriptTimes.length - 1]) {
    activeIndex = transcriptTimes.length - 1;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl h-[90vh] bg-slate-900 border-slate-800 text-slate-50 flex flex-col overflow-hidden">
        <DialogHeader className="pb-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
                <Phone className="w-5 h-5 text-blue-500" />
                Call Details - {callData.contactName}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                View call recording, transcript, and AI analysis for this conversation.
                {isFetchingTranscript && (
                  <span className="ml-2 text-blue-400">
                    📥 Fetching transcript...
                  </span>
                )}
                {isFetchingRecording && (
                  <span className="ml-2 text-blue-400">
                    📥 Fetching recording...
                  </span>
                )}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={handleGenerateAISummary}
                disabled={isGeneratingSummary}
                className={`${callData.aiCallSummary?.generated ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'} text-white border-0`}
                size="sm"
              >
                {isGeneratingSummary ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    {callData.aiCallSummary?.generated ? 'Regenerate AI Summary' : 'Generate AI Summary'}
                  </>
                )}
              </Button>
            </div>
          </div>
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

              {/* AI Call Summary */}
              {callData.aiCallSummary?.generated && callData.aiCallSummary.html ? (
                <>
                  <div>
                    <span className="text-base font-semibold text-white flex items-center gap-2">
                      <Brain className="w-4 h-4 text-blue-400" />
                      AI Call Summary
                      {callData.aiCallSummary.date && (
                        <span className="text-xs text-slate-400">
                          {new Date(callData.aiCallSummary.date).toLocaleDateString()}
                        </span>
                      )}
                    </span>
                    {/* Debug: Show raw HTML content */}
                    {process.env.NODE_ENV === 'development' && (
                      <details className="mt-2 p-2 bg-slate-800 rounded text-xs">
                        <summary className="cursor-pointer text-slate-400">Debug: Raw HTML</summary>
                        <pre className="mt-2 text-slate-300 whitespace-pre-wrap">{callData.aiCallSummary.html}</pre>
                      </details>
                    )}
                    <div 
                      className="text-sm text-slate-300 mt-2 max-w-none ai-summary-html"
                      dangerouslySetInnerHTML={{ __html: callData.aiCallSummary.html }}
                      style={{
                        lineHeight: '1.6',
                      }}
                    />
                  </div>
                  <Separator className="bg-slate-700" />
                </>
              ) : (
                <>
                  {/* Fallback Call Summary */}
                  <div>
                    <span className="text-base font-semibold text-white">Call Summary</span>
                    <p className="text-sm text-slate-300 mt-2">{callData.summary.outcome}</p>
                  </div>
                  <Separator className="bg-slate-700" />

                  {/* Fallback Inquiry Details */}
                  <div>
                    <span className="text-base font-semibold text-white">Inquiry Details</span>
                    <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                      {callData.summary.keyPoints.map((point, idx) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="bg-slate-700" />

                  {/* Fallback Financial Details */}
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

                  {/* Fallback Property & Occupancy Details */}
                  <div>
                    <span className="text-base font-semibold text-white">Property & Occupancy Details</span>
                    <ul className="text-sm text-slate-300 mt-2 space-y-1 list-disc list-inside">
                      <li>Occupancy: Owner occupied, spouse lives in the property</li>
                      <li>Property Type: Single family home</li>
                      <li>Location: Middleville</li>
                    </ul>
                  </div>
                  <Separator className="bg-slate-700" />
                </>
              )}

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
                {/* Hidden Audio Element */}
                {localRecordingUrl && (
                  <audio
                    ref={(el) => setAudioRef(el)}
                    src={localRecordingUrl}
                    onTimeUpdate={handleTimeUpdate}
                    onLoadedMetadata={handleLoadedMetadata}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    onEnded={() => setIsPlaying(false)}
                    onError={(e) => {
                      console.error('Audio loading error:', e);
                      console.error('Audio error details:', {
                        error: e.currentTarget.error,
                        src: e.currentTarget.src,
                        networkState: e.currentTarget.networkState,
                        readyState: e.currentTarget.readyState
                      });
                    }}
                    onLoadStart={() => console.log('Audio load started:', localRecordingUrl)}
                    onCanPlay={() => console.log('Audio can play:', localRecordingUrl)}
                    preload="metadata"
                  />
                )}
                
                {/* Modern Audio Player */}
                {localRecordingUrl ? (
                  <div className="bg-slate-700 rounded-lg p-3 flex items-center gap-3">
                    {/* Play Button */}
                    <button
                      onClick={handlePlayPause}
                      className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center hover:bg-slate-500 transition-colors"
                      disabled={!callData.recordingUrl}
                    >
                      {isPlaying ? (
                        <Pause className="w-4 h-4 text-white" />
                      ) : (
                        <Play className="w-4 h-4 text-white ml-0.5" />
                      )}
                    </button>
                    
                    {/* Time Display */}
                    <div className="text-sm text-slate-200 font-medium">
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </div>
                    
                    {/* Progress Bar */}
                    <div 
                      className="flex-1 bg-slate-600 rounded-full h-2 cursor-pointer relative"
                      onClick={handleProgressClick}
                    >
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300 pointer-events-none"
                        style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
                      />
                    </div>
                    
                    {/* Volume Icon */}
                    <button 
                      className="w-6 h-6 flex items-center justify-center hover:bg-slate-600 rounded transition-colors"
                      onClick={handleMuteToggle}
                    >
                      {isMuted ? (
                        <VolumeX className="w-4 h-4 text-slate-300" />
                      ) : (
                        <Volume2 className="w-4 h-4 text-slate-300" />
                      )}
                    </button>
                    
                    {/* More Options Icon */}
                    <button className="w-6 h-6 flex items-center justify-center">
                      <div className="flex flex-col gap-0.5">
                        <div className="w-1 h-1 bg-slate-300 rounded-full"></div>
                        <div className="w-1 h-1 bg-slate-300 rounded-full"></div>
                        <div className="w-1 h-1 bg-slate-300 rounded-full"></div>
                      </div>
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-4 text-slate-400 text-sm">
                    {isFetchingRecording ? (
                      <>
                        <div className="text-slate-400 text-sm">📥 Fetching recording from GHL API...</div>
                        <div className="text-slate-500 text-xs mt-2">This may take a few moments</div>
                      </>
                    ) : (
                      <>
                        <div className="text-slate-400 text-sm">No recording available for this call</div>
                        <div className="text-slate-500 text-xs mt-2">Click the button below to fetch recording from GHL API</div>
                        <Button
                          onClick={handleFetchRecording}
                          className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
                          size="sm"
                        >
                          📥 Fetch Recording
                        </Button>
                      </>
                    )}
                  </div>
                )}
              </div>
              {/* Transcript */}
              <div className="flex-1 overflow-y-auto pr-2">
                <div className="space-y-4 pb-4">
                  {isFetchingTranscript ? (
                    <div className="text-center py-8">
                      <div className="text-slate-400 text-sm">📥 Fetching transcript from GHL API...</div>
                      <div className="text-slate-500 text-xs mt-2">This may take a few moments</div>
                    </div>
                  ) : localTranscript && localTranscript.length > 0 ? (
                    localTranscript.map((entry, index) => (
                      <div
                        key={index}
                        ref={el => (transcriptRefs.current[index] = el)}
                        className={`space-y-2 transition-colors duration-200 ${
                          index === activeIndex ? "bg-blue-900/40 border-l-4 border-blue-400" : ""
                        }`}
                      >
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-slate-400">{entry.timestamp}</span>
                          <Badge
                            variant="outline"
                            className={`border-slate-600 text-xs ${entry.speaker === 'agent' ? 'text-blue-400' : 'text-green-400'}`}
                          >
                            {entry.speakerName}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-200 pl-4 border-l-2 border-slate-700">
                          {entry.text}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-slate-400 text-sm">No transcript available for this call</div>
                      <div className="text-slate-500 text-xs mt-2">
                        {isFetchingTranscript ? 
                          '📥 Fetching transcript from GHL API...' : 
                          'Click the button below to fetch transcript from GHL API'
                        }
                      </div>
                      {!isFetchingTranscript && (
                        <Button
                          onClick={handleFetchTranscript}
                          className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
                          size="sm"
                        >
                          📥 Fetch Transcript
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}