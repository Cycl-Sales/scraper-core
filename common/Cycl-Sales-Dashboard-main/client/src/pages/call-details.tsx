import { useLocation } from "wouter";
import { useState, useEffect } from "react";
import { ArrowUpRight, Users, User, Filter, Share2, ChevronDown, X, Phone, Clock, Calendar } from "lucide-react";
import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import CallTranscriptDialog from "@/components/call-transcript-dialog";
import CallVolumeChart from "@/components/charts/call-volume-chart";
import EngagementChart from "@/components/charts/engagement-chart";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

function useQuery() {
  return new URLSearchParams(window.location.search);
}

const parseTags = (tags: string | null) => tags ? tags.split(",") : [];

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

const marketingOptions = [
  "Paid Search",
  "Organic Search",
  "Direct Traffic",
  "Paid Social",
  "Organic Social",
  "CRM User",
  "Integration",
  "Direct Telecom",
  "Direct Social",
];
const marketingChannelOptions = [
  "Facebook",
  "Instagram",
  "Google",
  "Bing",
  "DuckDuckGo",
  "Meta Ads",
  "Other",
];
const creationMethodOptions = [
  "Chat Widget",
  "CRM User",
  "Phone Call",
  "Zapier",
  "OAuth App",
  "Meta Integration",
  "Other Integration",
  "Calendar",
  "Form",
  "Survey",
  "Workflow",
  "Notification",
  "Message",
  "CSV Import",
];
const engagementStatusOptions = [
  "No Touch, No Engagement",
  "Touched, Not Engaged",
  "Engaged, Not Touched",
  "Engaged & Touched",
  "No Touch",
];
const lastMessageDirectionOptions = [
  "Inbound",
  "Outbound",
];

export default function CallDetails() {
  const query = useQuery();
  const contactId = query.get("contact_id");
  const contact = query.get("contact") || "";
  const date = query.get("date") || "";
  const tags = parseTags(query.get("tags"));

  // State for call messages
  const [callMessages, setCallMessages] = useState<any[]>([]);
  const [contactData, setContactData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab state
  const [activeTab, setActiveTab] = useState("calls");
  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  const [selectedCallDetails, setSelectedCallDetails] = useState<any>(null);
  const [loadingCallDetails, setLoadingCallDetails] = useState(false);
  // Add filter states
  const [notMarketingSource, setNotMarketingSource] = useState("");
  const [marketingSource, setMarketingSource] = useState("");
  const [marketingChannel, setMarketingChannel] = useState("");
  const [creationMethod, setCreationMethod] = useState("");
  const [engagementStatus, setEngagementStatus] = useState("");
  const [lastMessageDirection, setLastMessageDirection] = useState("");
  const [doesntHaveTag, setDoesntHaveTag] = useState("");
  const [contactHasTag, setContactHasTag] = useState("");

  // Fetch call messages when component mounts
  useEffect(() => {
    if (!contactId) {
      setError("No contact ID provided");
      setLoading(false);
      return;
    }

    const fetchCallMessages = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`/api/contact-call-messages/${contactId}`);
        const data = await response.json();
        
        if (data.success) {
          setCallMessages(data.call_messages || []);
          setContactData(data.contact);
        } else {
          setError(data.error || "Failed to fetch call messages");
        }
      } catch (err) {
        setError("Failed to fetch call messages");
        console.error("Error fetching call messages:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchCallMessages();
  }, [contactId]);

  // Handler for fetching detailed call information
  const handleDetailsClick = async (messageId: number) => {
    try {
      setLoadingCallDetails(true);
      setTranscriptDialogOpen(true);
      
      const response = await fetch(`/api/call-details/${messageId}`);
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
    } finally {
      setLoadingCallDetails(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      <main className="p-8 max-w-full">
        {/* Filter Bar - matches Analytics */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 rounded-2xl p-6 shadow-lg mb-6">
          <div className="flex flex-wrap gap-2 items-center">
            <Button variant="secondary" className="bg-blue-900 text-blue-300 font-semibold flex gap-2 items-center">
              <Users className="w-4 h-4" />
              Blue Peak Property
            </Button>
            <Button variant="outline" className="bg-slate-800 text-slate-200 flex gap-2 items-center">
              <User className="w-4 h-4" />
              Choose user
              <ChevronDown className="w-4 h-4" />
            </Button>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="bg-slate-800 text-slate-200 flex gap-2 items-center">
                  <Filter className="w-4 h-4" />
                  More Filters (1)
                </Button>
              </PopoverTrigger>
              <PopoverContent className="bg-slate-900 border border-slate-700 w-[420px] p-4 text-slate-200 shadow-2xl rounded-2xl">
                <div className="flex flex-col gap-1 min-w-[340px]">
                  {/* Filter Row Template */}
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5 relative">
                    <span className="text-slate-100 text-xs">Not Marketing Source</span>
                    <div className="relative w-full">
                      <Select value={notMarketingSource} onValueChange={setNotMarketingSource}>
                        <SelectTrigger className="w-full h-8 bg-slate-950 border border-slate-700 rounded-md px-3 text-slate-200 text-sm focus:ring-2 focus:ring-blue-700">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border border-slate-700 rounded-md text-slate-200 text-sm">
                          {marketingOptions.map(opt => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      onClick={() => notMarketingSource && setNotMarketingSource("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${notMarketingSource ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!notMarketingSource}
                      tabIndex={-1}
                      aria-label="Clear Not Marketing Source"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5 relative">
                    <span className="text-slate-100 text-xs">Marketing Source</span>
                    <div className="relative w-full">
                      <Select value={marketingSource} onValueChange={setMarketingSource}>
                        <SelectTrigger className="w-full h-8 bg-slate-950 border border-slate-700 rounded-md px-3 text-slate-200 text-sm focus:ring-2 focus:ring-blue-700">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border border-slate-700 rounded-md text-slate-200 text-sm">
                          {marketingOptions.map(opt => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      onClick={() => marketingSource && setMarketingSource("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${marketingSource ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!marketingSource}
                      tabIndex={-1}
                      aria-label="Clear Marketing Source"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5 relative">
                    <span className="text-slate-100 text-xs">Marketing Channel</span>
                    <div className="relative w-full">
                      <Select value={marketingChannel} onValueChange={setMarketingChannel}>
                        <SelectTrigger className="w-full h-8 bg-slate-950 border border-slate-700 rounded-md px-3 text-slate-200 text-sm focus:ring-2 focus:ring-blue-700">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border border-slate-700 rounded-md text-slate-200 text-sm">
                          {marketingChannelOptions.map(opt => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      onClick={() => marketingChannel && setMarketingChannel("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${marketingChannel ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!marketingChannel}
                      tabIndex={-1}
                      aria-label="Clear Marketing Channel"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5 relative">
                    <span className="text-slate-100 text-xs">Creation Method</span>
                    <div className="relative w-full">
                      <Select value={creationMethod} onValueChange={setCreationMethod}>
                        <SelectTrigger className="w-full h-8 bg-slate-950 border border-slate-700 rounded-md px-3 text-slate-200 text-sm focus:ring-2 focus:ring-blue-700">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border border-slate-700 rounded-md text-slate-200 text-sm">
                          {creationMethodOptions.map(opt => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      onClick={() => creationMethod && setCreationMethod("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${creationMethod ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!creationMethod}
                      tabIndex={-1}
                      aria-label="Clear Creation Method"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5 relative">
                    <span className="text-slate-100 text-xs">Engagement Status</span>
                    <div className="relative w-full">
                      <Select value={engagementStatus} onValueChange={setEngagementStatus}>
                        <SelectTrigger className="w-full h-8 bg-slate-950 border border-slate-700 rounded-md px-3 text-slate-200 text-sm focus:ring-2 focus:ring-blue-700">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border border-slate-700 rounded-md text-slate-200 text-sm">
                          {engagementStatusOptions.map(opt => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      onClick={() => engagementStatus && setEngagementStatus("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${engagementStatus ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!engagementStatus}
                      tabIndex={-1}
                      aria-label="Clear Engagement Status"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5 relative">
                    <span className="text-slate-100 text-xs">Last Message Direction</span>
                    <div className="relative w-full">
                      <Select value={lastMessageDirection} onValueChange={setLastMessageDirection}>
                        <SelectTrigger className="w-full h-8 bg-slate-950 border border-slate-700 rounded-md px-3 text-slate-200 text-sm focus:ring-2 focus:ring-blue-700">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border border-slate-700 rounded-md text-slate-200 text-sm">
                          {lastMessageDirectionOptions.map(opt => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      onClick={() => lastMessageDirection && setLastMessageDirection("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${lastMessageDirection ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!lastMessageDirection}
                      tabIndex={-1}
                      aria-label="Clear Last Message Direction"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5">
                    <span className="text-slate-100 text-xs">Doesn't Have Tag</span>
                    <input
                      className="bg-slate-950 border border-slate-700 rounded-md px-3 pr-7 py-1.5 text-slate-200 w-full focus:outline-none focus:ring-2 focus:ring-blue-700 text-sm"
                      placeholder="Enter text..."
                      value={doesntHaveTag}
                      onChange={e => setDoesntHaveTag(e.target.value)}
                      style={{ minHeight: '32px' }}
                    />
                    <button
                      onClick={() => doesntHaveTag && setDoesntHaveTag("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${doesntHaveTag ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!doesntHaveTag}
                      tabIndex={-1}
                      aria-label="Clear Doesn't Have Tag"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  <div className="grid grid-cols-[1.5fr_2fr_32px] items-center gap-1 py-0.5">
                    <span className="text-slate-100 text-xs">Contact Has Tag</span>
                    <input
                      className="bg-slate-950 border border-slate-700 rounded-md px-3 pr-7 py-1.5 text-slate-200 w-full focus:outline-none focus:ring-2 focus:ring-blue-700 text-sm"
                      placeholder="Enter text..."
                      value={contactHasTag}
                      onChange={e => setContactHasTag(e.target.value)}
                      style={{ minHeight: '32px' }}
                    />
                    <button
                      onClick={() => contactHasTag && setContactHasTag("")}
                      className={`ml-1 flex items-center justify-center h-7 w-7 rounded-md ${contactHasTag ? 'hover:bg-slate-800 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
                      disabled={!contactHasTag}
                      tabIndex={-1}
                      aria-label="Clear Contact Has Tag"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex bg-slate-800 rounded-md p-0.5 gap-0.5">
              <button
                className={`px-3 py-0.5 rounded-md font-medium transition-colors focus:outline-none text-xs h-7 ${activeTab === "contacts" ? "bg-slate-900 text-white shadow" : "text-slate-400 hover:text-white"}`}
                onClick={() => setActiveTab("contacts")}
              >
                Contacts
              </button>
              <button
                className={`px-3 py-0.5 rounded-md font-medium transition-colors focus:outline-none text-xs h-7 ${activeTab === "calls" ? "bg-slate-900 text-white shadow" : "text-slate-400 hover:text-white"}`}
                onClick={() => setActiveTab("calls")}
              >
                Calls
              </button>
            </div>
            <Button variant="outline" className="bg-slate-900 border-slate-700 text-slate-200 font-medium flex gap-2 items-center min-w-[260px] justify-start">
              May 12, 2025 - May 18, 2025
            </Button>
            <Button variant="outline" className="bg-blue-900 text-blue-300 border-blue-700 flex gap-2 items-center">
              <Share2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6 items-stretch">
          <div className="lg:col-span-2 flex flex-col h-[420px]">
            <div className="h-full flex flex-col">
              <CallVolumeChart />
            </div>
          </div>
          <div className="lg:col-span-1 flex flex-col h-[420px]">
            <div className="h-full flex flex-col">
              <EngagementChart />
            </div>
          </div>
        </div>
        {/* Call Details Table */}
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
                <div className="text-slate-400">No call messages found for this contact</div>
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
                      <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Contact Tags</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-400 whitespace-nowrap">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {callMessages.map((message, index) => {
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
                      } else if (message.duration) {
                        // Check if duration is directly on the message object
                        duration = formatDuration(message.duration);
                      } else if (message.meta?.duration) {
                        // Check if duration is in meta.duration
                        duration = formatDuration(message.meta.duration);
                      }
                      
                      // Debug logging (remove in production)
                      if (index === 0) {
                        console.log('Message data for debugging:', {
                          id: message.id,
                          meta: message.meta,
                          duration: message.duration,
                          call_duration: message.meta?.call_duration,
                          meta_duration: message.meta?.duration
                        });
                      }

                      return (
                        <tr key={message.id} className="border-b border-slate-800">
                          <td className="py-3 px-4 text-white font-semibold whitespace-nowrap">
                            {contactData?.name || contact}
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
                          <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                            {message.meta?.call_status || 'N/A'}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap text-slate-300 max-w-[200px] truncate" title={message.body}>
                            {message.body || 'No summary available'}
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
                            <div className="flex flex-row overflow-x-auto whitespace-nowrap gap-1 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900">
                              {tags.map((tag, i) => (
                                <span key={i} className="inline-flex items-center px-2 py-0.5 rounded-md border border-slate-600 text-slate-300 font-medium text-xs mr-1">{tag}</span>
                              ))}
                            </div>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <Button
                              variant="outline"
                              className="bg-slate-900 border border-slate-700 text-slate-200 flex gap-2 items-center px-2 py-1 rounded-md text-xs font-medium shadow hover:bg-slate-800"
                              onClick={() => handleDetailsClick(message.id)}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-1"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2a2 2 0 012-2h2a2 2 0 012 2v2m-6 0a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2m-6 0h6" /></svg>
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
                    <select className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                      <option>10</option>
                    </select>
                  </div>
                  <div className="text-slate-400">Showing 1-{callMessages.length} of {callMessages.length} calls</div>
                  <div className="flex gap-2">
                    <button className="border border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs rounded-md" disabled>Previous</button>
                    <span className="text-slate-300 text-sm my-auto">Page 1 of 1</span>
                    <button className="border border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs rounded-md" disabled>Next</button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
      
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
      />
    </div>
  );
} 