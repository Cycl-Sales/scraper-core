import CallTranscriptDialog from "@/components/call-transcript-dialog";
import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Clock, FileText, Filter, Phone, Search, TrendingUp, Users } from "lucide-react";
import { useState } from "react";

export default function Calls() { 
  const [searchTerm, setSearchTerm] = useState("");
  const [dateRange, setDateRange] = useState<string>("last_30_days");
  const [selectedCall, setSelectedCall] = useState<any>(null);
  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);

  // Sample call data - this would come from your API
  const sampleCallData = {
    id: "call_001",
    contactName: "Ashley Nicole Towles",
    contactPhone: "+1 (555) 123-4567",
    callDate: "Thursday, May 15, 2025",
    callTime: "2:45 PM",
    duration: "5:23",
    status: "Completed",
    agent: "John Smith",
    direction: "inbound" as const,
    recordingUrl: "/recordings/call_001.mp3",
    transcript: [
      {
        timestamp: "00:00",
        speaker: "agent" as const,
        speakerName: "John Smith",
        text: "Hello, thank you for calling Blue Peak Property & Investments. This is John, how can I help you today?"
      },
      {
        timestamp: "00:05",
        speaker: "contact" as const,
        speakerName: "Ashley Nicole",
        text: "Hi John, I'm calling about the property listing I saw online. I'm interested in getting more information about the mortgage options."
      },
      {
        timestamp: "00:15",
        speaker: "agent" as const,
        speakerName: "John Smith",
        text: "Absolutely! I'd be happy to help you with that. Can you tell me which property you're looking at?"
      },
      {
        timestamp: "00:22",
        speaker: "contact" as const,
        speakerName: "Ashley Nicole",
        text: "It's the three-bedroom house on Maple Street, listed at $245,000."
      },
      {
        timestamp: "00:30",
        speaker: "agent" as const,
        speakerName: "John Smith",
        text: "Perfect! That's a great property. We have several financing options available. Let me walk you through what we can offer..."
      },
      {
        timestamp: "00:45",
        speaker: "contact" as const,
        speakerName: "Ashley Nicole",
        text: "That sounds great! I'm particularly interested in FHA loans. Do you think I would qualify?"
      },
      {
        timestamp: "01:00",
        speaker: "agent" as const,
        speakerName: "John Smith",
        text: "Based on what you've told me, FHA could be a great option. With your credit score and income, you should have several good choices. Let me explain the different programs we have available."
      },
      {
        timestamp: "01:30",
        speaker: "contact" as const,
        speakerName: "Ashley Nicole",
        text: "I really appreciate all this information. When would be a good time to view the property?"
      },
      {
        timestamp: "01:45",
        speaker: "agent" as const,
        speakerName: "John Smith",
        text: "I can schedule a showing for you this week. How does Tuesday at 2 PM work for your schedule? I'll also prepare a pre-approval packet so we can move quickly if you decide to make an offer."
      },
      {
        timestamp: "02:00",
        speaker: "contact" as const,
        speakerName: "Ashley Nicole",
        text: "Tuesday at 2 PM works perfectly! Thank you so much for your help today."
      },
      {
        timestamp: "02:15",
        speaker: "agent" as const,
        speakerName: "John Smith",
        text: "You're very welcome! I'll send you a confirmation email with all the details and the mortgage information packet. Looking forward to showing you the property on Tuesday!"
      }
    ],
    summary: {
      outcome: "Customer interested in property financing. Scheduled follow-up appointment for property viewing.",
      keyPoints: [
        "Customer interested in $245,000 property on Maple Street",
        "Discussed multiple financing options",
        "Customer has good credit score (750+)",
        "Scheduled property viewing for next Tuesday"
      ],
      nextSteps: [
        "Send detailed mortgage information packet",
        "Schedule property viewing for Tuesday 2 PM",
        "Prepare loan pre-approval documents"
      ],
      sentiment: "positive" as const
    },
    aiAnalysis: {
      overallScore: 8.5,
      categories: {
        communication: 9,
        professionalism: 8,
        problemSolving: 8,
        followUp: 9
      },
      highlights: [
        "Excellent opening and professional greeting",
        "Clear explanation of financing options",
        "Proactive in scheduling follow-up",
        "Good listening skills and rapport building"
      ],
      improvements: [
        "Could have asked more qualifying questions earlier",
        "Opportunity to mention additional services",
        "Consider discussing timeline expectations"
      ],
      callIntent: "Property purchase inquiry with financing needs",
      satisfactionLevel: "high" as const
    }
  };

  const handleContactClick = () => {
    setSelectedCall(sampleCallData);
    setTranscriptDialogOpen(true);
  };

  const handleTranscriptClick = () => {
    setSelectedCall(sampleCallData);
    setTranscriptDialogOpen(true);
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      
      <main className="p-8 max-w-full">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Calls Dashboard</h1>
          <p className="text-slate-400">Monitor and analyze your call performance</p>
        </div>

        {/* Quick Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">Total Calls</CardTitle>
              <Phone className="w-4 h-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">2,847</div>
              <p className="text-xs text-green-500">
                +12.5% from last month
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">Avg Duration</CardTitle>
              <Clock className="w-4 h-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">4:32</div>
              <p className="text-xs text-green-500">
                +8.2% from last month
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">Answer Rate</CardTitle>
              <TrendingUp className="w-4 h-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">87.3%</div>
              <p className="text-xs text-green-500">
                +3.1% from last month
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">Active Agents</CardTitle>
              <Users className="w-4 h-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">24</div>
              <p className="text-xs text-slate-400">
                Currently online
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters Section */}
        <div className="bg-slate-900 rounded-lg p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Call Analytics & Data</h3>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search calls..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-64 bg-slate-800 border-slate-700"
                />
              </div>

              {/* Date Range */}
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <Select value={dateRange} onValueChange={setDateRange}>
                  <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
                    <SelectValue placeholder="Date Range" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="last_7_days">Last 7 Days</SelectItem>
                    <SelectItem value="last_30_days">Last 30 Days</SelectItem>
                    <SelectItem value="last_90_days">Last 90 Days</SelectItem>
                    <SelectItem value="custom">Custom Range</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Additional Filters */}
              <Button variant="outline" className="border-slate-700 hover:bg-slate-800">
                <Filter className="w-4 h-4 mr-2" />
                More Filters
              </Button>
            </div>
          </div>
        </div>



        {/* Call Log Table */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Recent Call Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Time</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Contact</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Phone</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Duration</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Agent</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="py-3 px-4 text-slate-300">2:45 PM</td>
                    <td className="py-3 px-4">
                      <button 
                        onClick={handleContactClick}
                        className="text-white hover:text-blue-400 transition-colors cursor-pointer"
                      >
                        Ashley Nicole Towles
                      </button>
                    </td>
                    <td className="py-3 px-4 text-slate-300">+1 (555) 123-4567</td>
                    <td className="py-3 px-4 text-slate-300">5:23</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400">
                        Completed
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">John Smith</td>
                    <td className="py-3 px-4">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={handleTranscriptClick}
                        className="border-slate-600 hover:border-blue-500 hover:text-blue-400"
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        Transcript
                      </Button>
                    </td>
                  </tr>
                  <tr className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="py-3 px-4 text-slate-300">2:30 PM</td>
                    <td className="py-3 px-4">
                      <button 
                        onClick={handleContactClick}
                        className="text-white hover:text-blue-400 transition-colors cursor-pointer"
                      >
                        Ira Newson Jr
                      </button>
                    </td>
                    <td className="py-3 px-4 text-slate-300">+1234567891</td>
                    <td className="py-3 px-4 text-slate-300">3:17</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400">
                        Completed
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">Sarah Wilson</td>
                    <td className="py-3 px-4">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={handleTranscriptClick}
                        className="border-slate-600 hover:border-blue-500 hover:text-blue-400"
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        Transcript
                      </Button>
                    </td>
                  </tr>
                  <tr className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="py-3 px-4 text-slate-300">2:15 PM</td>
                    <td className="py-3 px-4">
                      <span className="text-white">Jason W Wallace</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">+1234567892</td>
                    <td className="py-3 px-4 text-slate-300">--</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded-full text-xs bg-red-500/20 text-red-400">
                        Missed
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">--</td>
                    <td className="py-3 px-4">
                      <span className="text-slate-500 text-sm">No recording</span>
                    </td>
                  </tr>
                  <tr className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="py-3 px-4 text-slate-300">1:58 PM</td>
                    <td className="py-3 px-4">
                      <button 
                        onClick={handleContactClick}
                        className="text-white hover:text-blue-400 transition-colors cursor-pointer"
                      >
                        Sarah Johnson
                      </button>
                    </td>
                    <td className="py-3 px-4 text-slate-300">+1234567893</td>
                    <td className="py-3 px-4 text-slate-300">8:45</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400">
                        Completed
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">Mike Davis</td>
                    <td className="py-3 px-4">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={handleTranscriptClick}
                        className="border-slate-600 hover:border-blue-500 hover:text-blue-400"
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        Transcript
                      </Button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Call Transcript Dialog */}
        <CallTranscriptDialog 
          open={transcriptDialogOpen}
          onOpenChange={setTranscriptDialogOpen}
          callData={selectedCall}
        />
      </main>
    </div>
  );
}