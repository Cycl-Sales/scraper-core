import { useLocation } from "wouter";
import { useState } from "react";
import { ArrowUpRight, Users, User, Filter, Share2, ChevronDown, X } from "lucide-react";
import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import CallTranscriptDialog from "@/components/call-transcript-dialog";
import CallVolumeChart from "@/components/charts/call-volume-chart";
import EngagementChart from "@/components/charts/engagement-chart";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

function useQuery() {
  const [location] = useLocation();
  return new URLSearchParams(location.split('?')[1] || '');
}

const parseTags = (tags: string | null) => tags ? tags.split(",") : [];

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
  const contact = query.get("contact") || "";
  const date = query.get("date") || "";
  const tags = parseTags(query.get("tags"));

  // Tab state
  const [activeTab, setActiveTab] = useState("calls");
  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  // Add filter states
  const [notMarketingSource, setNotMarketingSource] = useState("");
  const [marketingSource, setMarketingSource] = useState("");
  const [marketingChannel, setMarketingChannel] = useState("");
  const [creationMethod, setCreationMethod] = useState("");
  const [engagementStatus, setEngagementStatus] = useState("");
  const [lastMessageDirection, setLastMessageDirection] = useState("");
  const [doesntHaveTag, setDoesntHaveTag] = useState("");
  const [contactHasTag, setContactHasTag] = useState("");

  // Minimal mock CallData for dialog
  const mockCallData = {
    id: "1",
    contactName: contact,
    contactPhone: "(555) 123-4567",
    callDate: date.split(",")[1]?.trim() || "Jun 20, 2025",
    callTime: date.split(",")[0]?.trim() || "02:26 AM",
    duration: "00:02:15",
    status: "No Answer",
    agent: "Roberto F Flores",
    direction: "inbound" as "inbound",
    recordingUrl: "",
    transcript: [
      { timestamp: "00:00", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "Hello, this is Roberto from Cycl Sales." },
      { timestamp: "00:05", speaker: "contact" as "contact", speakerName: contact, text: "Hi, I missed your call earlier." },
      { timestamp: "00:10", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "No problem! I wanted to discuss your recent inquiry about our property listings." },
      { timestamp: "00:15", speaker: "contact" as "contact", speakerName: contact, text: "Yes, I'm interested in learning more about the available options." },
      { timestamp: "00:20", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "Great! Are you looking for a specific location or price range?" },
      { timestamp: "00:25", speaker: "contact" as "contact", speakerName: contact, text: "I'm mostly interested in properties in the downtown area, under $500,000." },
      { timestamp: "00:30", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "We have several options that might fit your criteria. Would you like to schedule a viewing?" },
      { timestamp: "00:35", speaker: "contact" as "contact", speakerName: contact, text: "Yes, that would be great. What times are available?" },
      { timestamp: "00:40", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "I have openings this Thursday and Friday afternoon. Does either work for you?" },
      { timestamp: "00:45", speaker: "contact" as "contact", speakerName: contact, text: "Thursday works for me." },
      { timestamp: "00:50", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "Perfect, I'll send you a confirmation email with the details. Is there anything else I can help you with today?" },
      { timestamp: "00:55", speaker: "contact" as "contact", speakerName: contact, text: "No, that's all for now. Thank you!" },
      { timestamp: "01:00", speaker: "agent" as "agent", speakerName: "Roberto F Flores", text: "You're welcome! Have a great day." }
    ],
    summary: {
      outcome: "No answer, left voicemail.",
      keyPoints: ["Attempted contact", "No answer", "Voicemail left"],
      nextSteps: ["Try again tomorrow"],
      sentiment: "neutral" as "neutral"
    },
    aiAnalysis: {
      overallScore: 7,
      categories: { communication: 7, professionalism: 8, problemSolving: 6, followUp: 7 },
      highlights: ["Clear introduction", "Polite tone"],
      improvements: ["Try calling at a different time"],
      callIntent: "Initial outreach",
      satisfactionLevel: "medium" as "medium"
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
                <tr className="border-b border-slate-800">
                  <td className="py-3 px-4 text-white font-semibold whitespace-nowrap">{contact}</td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-green-500 text-green-300 font-medium text-xs">→ Inbound</span>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-pink-500 text-pink-300 font-medium text-xs">No Answer</span>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400">N/A</td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400">N/A</td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400">N/A</td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-300">{date}</td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-300">Roberto F Flores</td>
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
                      onClick={() => setTranscriptDialogOpen(true)}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 mr-2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2a2 2 0 012-2h2a2 2 0 012 2v2m-6 0a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2m-6 0h6" /></svg>
                      Transcript
                    </Button>
                    <CallTranscriptDialog open={transcriptDialogOpen} onOpenChange={setTranscriptDialogOpen} callData={mockCallData} />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          {/* Pagination and Rows per page */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              <span className="text-slate-300">Rows per page:</span>
              <select className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                <option>10</option>
              </select>
            </div>
            <div className="text-slate-400">Showing 1-1 of 1 calls</div>
            <div className="flex gap-2">
              <button className="border border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs rounded-md" disabled>Previous</button>
              <span className="text-slate-300 text-sm my-auto">Page 1 of 1</span>
              <button className="border border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs rounded-md" disabled>Next</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 