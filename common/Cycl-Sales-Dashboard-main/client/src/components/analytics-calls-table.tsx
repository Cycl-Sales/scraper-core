import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Phone, Search, Filter, Eye, Calendar, Clock, ChevronLeft, ChevronRight } from "lucide-react";
import { PROD_BASE_URL, CYCLSALES_APP_ID } from "@/lib/constants";
import CallTranscriptDialog from "@/components/call-transcript-dialog";
import CallSummaryDialog from "@/components/call-summary-dialog";

interface Call {
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
}

interface AnalyticsCallsTableProps {
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

export default function AnalyticsCallsTable({ 
  loading, 
  locationId, 
  selectedUser, 
  activeFilters 
}: AnalyticsCallsTableProps) {
  const [calls, setCalls] = useState<Call[]>([]);
  const [totalCalls, setTotalCalls] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  const [selectedCallDetails, setSelectedCallDetails] = useState<any>(null);
  const [summaryDialogOpen, setSummaryDialogOpen] = useState(false);
  const [selectedCallSummary, setSelectedCallSummary] = useState<any>(null);

  // Fetch calls data
  const fetchCalls = async (page: number, limit: number, search?: string) => {
    if (!locationId) return;

    try {
      setError(null);
      const url = `${PROD_BASE_URL}/api/location-calls/${locationId}?page=${page}&limit=${limit}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}${search ? `&search=${encodeURIComponent(search)}` : ''}`;
      
      console.log('Fetching calls from URL:', url);
      console.log('Location ID:', locationId);
      console.log('Selected User:', selectedUser);
      
      const response = await fetch(url);
      const data = await response.json();

      console.log('Calls API response:', data);

      if (data.success) {
        setCalls(data.calls || []);
        setTotalCalls(data.total_calls || 0);
        setCurrentPage(data.page || 1);
        console.log('Successfully set calls data:', data.calls);
      } else {
        setError(data.error || "Failed to fetch calls");
        console.error("Failed to fetch calls:", data.error);
      }
    } catch (err) {
      setError("Failed to fetch calls");
      console.error("Error fetching calls:", err);
    }
  };

  // Search calls
  const handleSearch = async () => {
    if (!locationId) return;
    
    setSearchLoading(true);
    setCurrentPage(1);
    await fetchCalls(1, rowsPerPage, searchTerm);
    setSearchLoading(false);
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    fetchCalls(newPage, rowsPerPage, searchTerm);
  };

  // Handle rows per page change
  const handleRowsPerPageChange = (newLimit: number) => {
    setRowsPerPage(newLimit);
    setCurrentPage(1);
    fetchCalls(1, newLimit, searchTerm);
  };

  // Handler for fetching detailed call information
  const handleDetailsClick = async (messageId: number) => {
    try {
      setTranscriptDialogOpen(true);
      
      const response = await fetch(`${PROD_BASE_URL}/api/call-details/${messageId}?appId=${CYCLSALES_APP_ID}`);
      const data = await response.json();
      
      if (data.success) {
        setSelectedCallDetails(data.call_details);
      } else {
        console.error("Failed to fetch call details:", data.error);
        setSelectedCallDetails(null);
      }
    } catch (err) {
      console.error("Error fetching call details:", err);
      setSelectedCallDetails(null);
    }
  };

  // Function to refresh call details data
  const refreshCallDetails = async () => {
    if (selectedCallDetails?.id) {
      try {
        const response = await fetch(`${PROD_BASE_URL}/api/call-details/${selectedCallDetails.id}?appId=${CYCLSALES_APP_ID}`);
        const data = await response.json();
        
        if (data.success) {
          setSelectedCallDetails(data.call_details);
        }
      } catch (err) {
        console.error("Error refreshing call details:", err);
      }
    }
  };

  // Function to handle viewing call summary
  const handleViewSummary = async (messageId: number) => {
    try {
      const response = await fetch(`${PROD_BASE_URL}/api/call-details/${messageId}?appId=${CYCLSALES_APP_ID}`);
      const data = await response.json();
      
      if (data.success) {
        const callDetails = data.call_details;
        if (callDetails.aiCallSummary?.generated) {
          setSelectedCallSummary({
            html: callDetails.aiCallSummary.html,
            callGrade: callDetails.callGrade,
            callDate: callDetails.callDate,
            contactName: callDetails.contactName,
            hasSummary: true,
            // Additional call details
            callDirection: callDetails.direction,
            agent: callDetails.agent,
            duration: callDetails.duration,
            status: callDetails.status,
            contactPhone: callDetails.contactPhone,
            callTime: callDetails.callTime,
            aiAnalysis: callDetails.aiAnalysis
          });
        } else {
          setSelectedCallSummary({
            html: '',
            callGrade: callDetails.callGrade,
            callDate: callDetails.callDate,
            contactName: callDetails.contactName,
            hasSummary: false,
            messageId: messageId,
            // Additional call details
            callDirection: callDetails.direction,
            agent: callDetails.agent,
            duration: callDetails.duration,
            status: callDetails.status,
            contactPhone: callDetails.contactPhone,
            callTime: callDetails.callTime,
            aiAnalysis: callDetails.aiAnalysis
          });
        }
        setSummaryDialogOpen(true);
      } else {
        alert('Failed to fetch call details');
      }
    } catch (err) {
      console.error("Error fetching call summary:", err);
      alert('Error fetching call summary');
    }
  };

  // Function to handle generating AI summary
  const handleGenerateSummary = async (messageId: number) => {
    try {
      const response = await fetch(`${PROD_BASE_URL}/api/generate-call-summary/${messageId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to generate AI summary: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success) {
        alert('AI Summary generated successfully! Refreshing data...');
        // Refresh the calls data
        fetchCalls(currentPage, rowsPerPage, searchTerm);
      } else {
        throw new Error(result.error || 'Failed to generate AI summary');
      }
    } catch (error) {
      console.error('Error generating AI summary:', error);
      alert(`Error generating AI summary: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Fetch calls when component mounts or dependencies change
  useEffect(() => {
    if (locationId) {
      fetchCalls(currentPage, rowsPerPage, searchTerm);
    }
  }, [locationId, selectedUser, currentPage, rowsPerPage]);

  // Handle search on Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  if (!locationId) {
    return (
      <div className="text-center py-8">
        <Phone className="w-12 h-12 text-slate-400 mx-auto mb-4" />
        <p className="text-slate-400">Please select a location to view calls</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-slate-400">Loading calls...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search calls by contact name or phone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={handleKeyPress}
              className="pl-10 w-64 bg-slate-800 border-slate-700 text-slate-200"
            />
          </div>
          <Button 
            onClick={handleSearch}
            disabled={searchLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {searchLoading ? "Searching..." : "Search"}
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <select 
            value={rowsPerPage} 
            onChange={(e) => handleRowsPerPageChange(parseInt(e.target.value))}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200"
          >
            <option value={10}>10 rows</option>
            <option value={25}>25 rows</option>
            <option value={50}>50 rows</option>
            <option value={100}>100 rows</option>
          </select>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4">
          <p className="text-red-300">{error}</p>
        </div>
      )}

      {/* Calls Table - Using the existing structure from call-details.tsx */}
      <div className="bg-slate-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <div className="min-w-[1200px]">
            {calls.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-slate-400">
                  {searchTerm ? "No calls found matching your search" : "No calls found for this location"}
                </div>
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
                    {calls.map((call) => {
                      const callDate = call.date_added ? new Date(call.date_added) : null;
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
                      if (call.meta?.call_duration) {
                        duration = formatDuration(call.meta.call_duration);
                      }

                      return (
                        <tr key={call.id} className="border-b border-slate-800">
                          <td className="py-3 px-4 text-white font-semibold whitespace-nowrap">
                            {call.contact.name}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium text-xs ${
                              call.direction === 'inbound' 
                                ? 'border-green-500 text-green-300' 
                                : 'border-blue-500 text-blue-300'
                            }`}>
                              <Phone className="w-3 h-3" />
                              {call.direction === 'inbound' ? 'Inbound' : 'Outbound'}
                            </span>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium text-xs ${
                              call.status === 'completed' 
                                ? 'border-green-500 text-green-300'
                                : call.status === 'no-answer' || call.status === 'missed'
                                ? 'border-red-500 text-red-300'
                                : 'border-yellow-500 text-yellow-300'
                            }`}>
                              {call.status || 'Unknown'}
                            </span>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                            {duration !== 'N/A' && <Clock className="w-3 h-3 inline mr-1" />}
                            {duration}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium text-xs ${
                              call.ai_call_grade === 'A' ? 'border-green-500 text-green-300' :
                              call.ai_call_grade === 'B' ? 'border-blue-500 text-blue-300' :
                              call.ai_call_grade === 'C' ? 'border-yellow-500 text-yellow-300' :
                              call.ai_call_grade === 'D' ? 'border-orange-500 text-orange-300' :
                              call.ai_call_grade === 'F' ? 'border-red-500 text-red-300' :
                              'border-slate-500 text-slate-400'
                            }`}>
                              {call.ai_call_grade === 'A' ? 'A - Excellent' :
                               call.ai_call_grade === 'B' ? 'B - Good' :
                               call.ai_call_grade === 'C' ? 'C - Average' :
                               call.ai_call_grade === 'D' ? 'D - Below Average' :
                               call.ai_call_grade === 'F' ? 'F - Poor' :
                               'N/A'}
                            </span>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <Button
                              variant="outline"
                              size="sm"
                              className="bg-slate-800 border border-blue-500 text-blue-400 hover:bg-slate-700 px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1"
                              onClick={() => handleViewSummary(call.id)}
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
                            {call.user_id || 'Unknown'}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <Button
                              variant="outline"
                              className="bg-slate-900 border border-slate-700 text-slate-200 flex gap-2 items-center px-2 py-1 rounded-md text-xs font-medium shadow hover:bg-slate-800"
                              onClick={() => handleDetailsClick(call.id)}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-1"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2a2 2 0 012-2h2a2 2 0 012 2v2m-6 0a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v8m-6 0h6" /></svg>
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
        </div>
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
