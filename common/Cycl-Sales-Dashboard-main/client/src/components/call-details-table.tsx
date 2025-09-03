import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Phone, Clock, Calendar, Eye } from "lucide-react";
import { PROD_BASE_URL, CYCLSALES_APP_ID } from "@/lib/constants";
import CallTranscriptDialog from "@/components/call-transcript-dialog";
import CallSummaryDialog from "@/components/call-summary-dialog";

interface CallMessage {
  id: number;
  ghl_id: string;
  message_type: string;
  body: string;
  direction: string;
  status: string;
  content_type: string;
  source: string;
  user_id: string;
  conversation_provider_id: string;
  date_added: string;
  conversation_id: string;
  location_id: string;
  meta: {
    call_duration: number;
    call_status: string;
  } | null;
  ai_call_grade: string;
  ai_call_summary_generated: boolean;
  ai_call_summary_date: string | null;
  contact: {
    id: number;
    name: string;
    external_id: string;
    email: string;
    phone: string;
  };
  recording_url: string | null;
  recording_filename: string | null;
  recording_size: number | null;
  recording_content_type: string | null;
  transcript_fetched: boolean;
  transcript_ids?: Array<{
    id: number;
    sentence_index: number;
    start_time_seconds: number;
    end_time_seconds: number;
    transcript: string;
    confidence: number;
    duration: number;
  }>;
}

interface CallDetailsTableProps {
  loading: boolean;
  locationId: string;
  selectedUser: string;
  activeFilters: any;
}

// Helper function to format duration in seconds to 10m 15s or 1h 05m 09s
const formatDuration = (seconds: number): string => {
  if (!seconds || seconds <= 0) return 'N/A';
  const totalSeconds = Math.floor(seconds); // Ensure whole seconds
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs.toString().padStart(2, '0')}s`;
  } else {
    return `${secs}s`;
  }
};

export default function CallDetailsTable({ 
  loading, 
  locationId, 
  selectedUser, 
  activeFilters 
}: CallDetailsTableProps) {
  const [callMessages, setCallMessages] = useState<CallMessage[]>([]);
  const [totalCalls, setTotalCalls] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  const [selectedCallDetails, setSelectedCallDetails] = useState<any>(null);
  const [summaryDialogOpen, setSummaryDialogOpen] = useState(false);
  const [selectedCallSummary, setSelectedCallSummary] = useState<any>(null);

  // Fetch call messages data
  const fetchCallMessages = async (page: number, limit: number) => {
    if (!locationId) return;

    try {
      setError(null);
      const url = `${PROD_BASE_URL}/api/location-calls/${locationId}?page=${page}&limit=${limit}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}`;
      
      console.log('Fetching call messages from URL:', url);
      console.log('Location ID:', locationId);
      console.log('Selected User:', selectedUser);
      
      const response = await fetch(url);
      const data = await response.json();

      if (data.success) {
        console.log('Backend response data:', data);
        console.log('Total calls from backend:', data.total_calls);
        console.log('Calls array length:', data.calls?.length);
        setCallMessages(data.calls || []);
        setTotalCalls(data.total_calls || 0);
      } else {
        setError(data.error || 'Failed to fetch call messages');
        setCallMessages([]);
        setTotalCalls(0);
      }
    } catch (err) {
      console.error('Error fetching call messages:', err);
      setError('Failed to fetch call messages');
      setCallMessages([]);
      setTotalCalls(0);
    }
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  // Handle rows per page change
  const handleRowsPerPageChange = (newRowsPerPage: number) => {
    setRowsPerPage(newRowsPerPage);
    setCurrentPage(1); // Reset to first page
  };

  // Handle view summary
  const handleViewSummary = (messageId: number) => {
    const message = callMessages.find(m => m.id === messageId);
    if (message) {
      setSelectedCallSummary({
        messageId: message.id,
        hasSummary: message.ai_call_summary_generated,
        callGrade: message.ai_call_grade,
        callDate: message.date_added,
        contactName: message.contact?.name || 'Unknown',
        callDirection: message.direction,
        agent: message.user_id,
        duration: message.meta?.call_duration,
        status: message.status,
        contactPhone: message.contact?.phone,
        callTime: message.date_added,
        aiAnalysis: null
      });
      setSummaryDialogOpen(true);
    }
  };

  // Handle details click
  const handleDetailsClick = (messageId: number) => {
    const message = callMessages.find(m => m.id === messageId);
    if (message) {
      // Transform the backend message data into the format expected by CallTranscriptDialog
      const transformedCallData = {
        id: message.id.toString(),
        contactName: message.contact?.name || 'Unknown',
        contactPhone: message.contact?.phone || '',
        callDate: message.date_added ? new Date(message.date_added).toLocaleDateString() : 'N/A',
        callTime: message.date_added ? new Date(message.date_added).toLocaleTimeString() : 'N/A',
        duration: message.meta?.call_duration ? formatDuration(message.meta.call_duration) : 'N/A',
        status: message.status || 'Unknown',
        agent: message.user_id || 'Unknown',
        direction: message.direction || 'outbound',
        recordingUrl: message.recording_url || undefined,
        recording_filename: message.recording_filename || undefined,
        recording_size: message.recording_size || undefined,
        recording_content_type: message.recording_content_type || undefined,
        transcript: message.transcript_ids && message.transcript_ids.length > 0 ? 
          message.transcript_ids.map((transcript: any, index: number) => ({
            timestamp: `${transcript.start_time_seconds || 0}s`,
            speaker: 'agent' as const,
            speakerName: 'Agent',
            text: transcript.transcript || ''
          })) : [],
        summary: {
          outcome: 'Not available',
          keyPoints: [],
          nextSteps: [],
          sentiment: 'neutral'
        },
        aiAnalysis: {
          overallScore: 0,
          categories: {
            communication: 0,
            professionalism: 0,
            problemSolving: 0,
            followUp: 0
          },
          highlights: [],
          improvements: [],
          callIntent: 'Not analyzed',
          satisfactionLevel: 'medium'
        },
        aiCallSummary: {
          html: '',
          generated: message.ai_call_summary_generated || false,
          date: message.ai_call_summary_date || null
        },
        callGrade: message.ai_call_grade || 'N/A'
      };
      
      setSelectedCallDetails(transformedCallData);
      setTranscriptDialogOpen(true);
    }
  };

  // Refresh call details
  const refreshCallDetails = () => {
    fetchCallMessages(currentPage, rowsPerPage);
  };

  // Generate summary (placeholder function)
  const handleGenerateSummary = async (messageId: number) => {
    // This would typically call an API to generate a summary
    console.log('Generating summary for message:', messageId);
    // You can implement the actual API call here
  };

  // Fetch data when component mounts or dependencies change
  useEffect(() => {
    if (locationId) {
      fetchCallMessages(currentPage, rowsPerPage);
    }
  }, [locationId, selectedUser, currentPage, rowsPerPage]);

  return (
    <div className="bg-slate-900 rounded-2xl p-6 shadow-lg overflow-x-auto">
      <div className="min-w-[1200px]">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-slate-400">Loading call messages...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-red-400">Error: {error}</div>
          </div>
        ) : callMessages.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-slate-400">No call messages found for this location</div>
          </div>
        ) : (
          <>
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Contact Name</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Call Direction</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Call Duration</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Call Grade</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Summary</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Call Date</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">User Name</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody>
                {callMessages.map((message) => {
                  const callDate = message.date_added ? new Date(message.date_added) : null;
                  const formattedDate = callDate ? callDate.toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric' 
                  }) : 'N/A';
                  const formattedTime = callDate ? callDate.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  }) : '';
                  
                  // Enhanced duration formatting with debugging and fallbacks
                  let duration = 'N/A';
                  if (message.meta?.call_duration) {
                    duration = formatDuration(message.meta.call_duration);
                  }

                  return (
                    <tr key={message.id} className="border-b border-slate-800">
                      <td className="py-3 px-4 text-white font-semibold whitespace-nowrap">
                        {message.contact?.name || 'Unknown'}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium text-xs ${
                          message.direction === 'inbound' 
                            ? 'border-green-500 text-green-300' 
                            : 'border-blue-500 text-blue-300'
                        }`}>
                          <Phone className="w-3 h-3" />
                          {message.direction === 'inbound' ? 'Inbound' : 'Outbound'}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium text-xs ${
                          message.status === 'completed' 
                            ? 'border-green-500 text-green-300'
                            : message.status === 'no-answer' || message.status === 'missed'
                            ? 'border-red-500 text-red-300'
                            : 'border-yellow-500 text-yellow-300'
                        }`}>
                          {message.status || 'Unknown'}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                        {duration !== 'N/A' && <Clock className="w-3 h-3 inline mr-1" />}
                        {duration}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium text-xs ${
                          message.ai_call_grade === 'A' ? 'border-green-500 text-green-300' :
                          message.ai_call_grade === 'B' ? 'border-blue-500 text-blue-300' :
                          message.ai_call_grade === 'C' ? 'border-yellow-500 text-yellow-300' :
                          message.ai_call_grade === 'D' ? 'border-orange-500 text-orange-300' :
                          message.ai_call_grade === 'F' ? 'border-red-500 text-red-300' :
                          'border-slate-500 text-slate-400'
                        }`}>
                          {message.ai_call_grade === 'A' ? 'A - Excellent' :
                           message.ai_call_grade === 'B' ? 'B - Good' :
                           message.ai_call_grade === 'C' ? 'C - Average' :
                           message.ai_call_grade === 'D' ? 'D - Below Average' :
                           message.ai_call_grade === 'F' ? 'F - Poor' :
                           'N/A'}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <Button
                          variant="outline"
                          size="sm"
                          className="bg-slate-800 border border-blue-500 text-blue-400 hover:bg-slate-700 px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1"
                          onClick={() => handleViewSummary(message.id)}
                        >
                          <Eye className="w-3 h-3" />
                          Read
                        </Button>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formattedDate}
                          {formattedTime && <span className="text-slate-400 text-xs">({formattedTime})</span>}
                        </div>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                        {message.user_id || 'Unknown'}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <Button
                          variant="outline"
                          className="bg-slate-900 border border-slate-700 text-slate-200 flex gap-2 items-center px-2 py-1 rounded-md text-xs font-medium shadow hover:bg-slate-800"
                          onClick={() => handleDetailsClick(message.id)}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-1"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2a2 2 0 012-2h2a2 0 012 2v2m-6 0a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2m-6 0h6" /></svg>
                          Details
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {/* Pagination and Rows per page */}
            <div className="flex items-center justify-between mt-4">
              <div className="flex items-center gap-2">
                <span className="text-slate-300">Rows per page:</span>
                <select 
                  value={rowsPerPage} 
                  onChange={(e) => handleRowsPerPageChange(parseInt(e.target.value))}
                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="text-slate-400">
                Showing {((currentPage - 1) * rowsPerPage) + 1}-{Math.min(currentPage * rowsPerPage, totalCalls)} of {totalCalls} calls
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs"
                >
                  Previous
                </Button>
                <span className="text-slate-300 text-sm my-auto">
                  Page {currentPage} of {Math.ceil(totalCalls / rowsPerPage)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= Math.ceil(totalCalls / rowsPerPage)}
                  className="border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs"
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Call Transcript Dialog */}
      <CallTranscriptDialog
        open={transcriptDialogOpen}
        onOpenChange={(open) => {
          setTranscriptDialogOpen(open);
          if (!open) {
            setSelectedCallDetails(null);
          }
        }}
        callData={selectedCallDetails}
        onDataRefresh={refreshCallDetails}
      />

      {/* Call Summary Dialog */}
      <CallSummaryDialog
        open={summaryDialogOpen}
        onOpenChange={(open) => {
          setSummaryDialogOpen(open);
          if (!open) {
            setSelectedCallSummary(null);
          }
        }}
        summaryHtml={selectedCallSummary?.html || ''}
        callGrade={selectedCallSummary?.callGrade}
        callDate={selectedCallSummary?.callDate}
        contactName={selectedCallSummary?.contactName}
        hasSummary={selectedCallSummary?.hasSummary}
        messageId={selectedCallSummary?.messageId}
        onGenerateSummary={handleGenerateSummary}
        callDirection={selectedCallSummary?.callDirection}
        agent={selectedCallSummary?.agent}
        duration={selectedCallSummary?.duration}
        status={selectedCallSummary?.status}
        contactPhone={selectedCallSummary?.contactPhone}
        callTime={selectedCallSummary?.callTime}
        aiAnalysis={selectedCallSummary?.aiAnalysis}
      />
    </div>
  );
}
