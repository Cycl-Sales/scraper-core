import { useState, useEffect } from "react";
import { Search, Plus, Eye, Phone, Edit, Zap, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useContacts } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import type { Contact as BaseContact } from "@shared/schema";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { CYCLSALES_APP_ID, PROD_BASE_URL } from "@/lib/constants";

// Extend Contact type to include details_fetched
interface Contact extends BaseContact {
  details_fetched?: boolean;
}

function getSourceBadgeClass(source: string | null) {
  if (!source) return "bg-slate-500/10 text-slate-500 hover:bg-slate-500/20";
  
  switch (source.toLowerCase()) {
    case "website":
      return "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20";
    case "referral":
      return "bg-green-500/10 text-green-500 hover:bg-green-500/20";
    case "social_media":
      return "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20";
    case "email_campaign":
      return "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20";
    case "phone":
      return "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20";
    default:
      return "bg-slate-500/10 text-slate-500 hover:bg-slate-500/20";
  }
}

function getTagsBadgeClass(tags: string[] | null) {
  if (!tags || tags.length === 0) return "bg-slate-500/10 text-slate-500 hover:bg-slate-500/20";
  
  if (tags.some(tag => tag.toLowerCase().includes("hot") || tag.toLowerCase().includes("interested"))) {
    return "bg-red-500/10 text-red-500 hover:bg-red-500/20";
  }
  if (tags.some(tag => tag.toLowerCase().includes("lead"))) {
    return "bg-green-500/10 text-green-500 hover:bg-green-500/20";
  }
  return "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20";
}

function formatTimeAgo(date: Date | string | null): string {
  if (!date) return "Never";
  
  const now = new Date();
  const past = new Date(date);
  const diffMs = now.getTime() - past.getTime();
  
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMins < 60) {
    return `${diffMins} minutes ago`;
  } else if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  } else {
    return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
  }
}

export default function ContactsTable() {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [details, setDetails] = useState<any>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState<string | null>(null);
  
  // AI Analysis state
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState<{ [key: string]: boolean }>({});
  
  // AI Summary Dialog state
  const [aiSummaryDialog, setAiSummaryDialog] = useState<{
    open: boolean;
    contactName: string;
    aiSummary: string;
    aiStatus: string;
    aiQualityGrade: string;
    aiSalesGrade: string;
  }>({
    open: false,
    contactName: '',
    aiSummary: '',
    aiStatus: '',
    aiQualityGrade: '',
    aiSalesGrade: ''
  });
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [allContacts, setAllContacts] = useState<Contact[]>([]);
  
  const { 
    data: contacts, 
    loading: isLoading, 
    error: contactsError, 
    execute: loadContacts 
  } = useContacts();

  useEffect(() => {
    const loadContactsData = async () => {
      try {
        await loadContacts();
      } catch (error) {
        console.error("Failed to load contacts:", error);
        toast({
          title: "Error",
          description: "Failed to load contacts. Please try again.",
          variant: "destructive",
        });
      }
    };
    loadContactsData();
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update allContacts when initial contacts load
  useEffect(() => {
    if (contacts && contacts.length > 0) {
      setAllContacts(contacts);
      setCurrentPage(1);
      setHasMore(true);
    }
  }, [contacts]);

  // Load more contacts function
  const loadMoreContacts = async () => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    try {
      // Get location_id from the first contact (assuming all contacts are from same location)
      const locationId = allContacts[0]?.locationId;
      if (!locationId) {
        console.error("No location ID found");
        return;
      }
      
      const response = await fetch(`${PROD_BASE_URL}/api/load-more-contacts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location_id: locationId,
          page: currentPage + 1,
          page_size: 100
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setAllContacts(prev => [...prev, ...data.contacts]);
        setCurrentPage(prev => prev + 1);
        setHasMore(data.has_more);
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to load more contacts",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to load more contacts:", error);
      toast({
        title: "Error",
        description: "Failed to load more contacts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoadingMore(false);
    }
  };

  // Infinite scroll handler
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (scrollHeight - scrollTop <= clientHeight * 1.5) {
      loadMoreContacts();
    }
  };

  // Handle API errors
  useEffect(() => {
    if (contactsError) {
      toast({
        title: "Error",
        description: `Failed to load contacts: ${contactsError.message}`,
        variant: "destructive",
      });
    }
  }, [contactsError, toast]);

  const filteredContacts = allContacts?.filter((contact) => {
    const fullName = `${contact.firstName || ''} ${contact.lastName || ''}`.trim();
    const searchLower = searchTerm.toLowerCase();
    
    return fullName.toLowerCase().includes(searchLower) ||
           (contact.email && contact.email.toLowerCase().includes(searchLower)) ||
           (contact.phone && contact.phone.toLowerCase().includes(searchLower)) ||
           (contact.companyName && contact.companyName.toLowerCase().includes(searchLower)) ||
           (contact.source && contact.source.toLowerCase().includes(searchLower));
  }) || [];

  const handleViewDetails = async (contact: Contact) => {
    setSelectedContact(contact);
    setDetails(null);
    setDetailsError(null);
    if (contact.details_fetched) {
      setDetails(contact);
      return;
    }
    setDetailsLoading(true);
    try {
      const res = await fetch(`${PROD_BASE_URL}/api/contact-details`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contact_id: contact.id }),
      });
      const data = await res.json();
      if (data.success) {
        setDetails(data.contact);
      } else {
        setDetailsError(data.error || "Failed to fetch details");
      }
    } catch (e) {
      setDetailsError("Failed to fetch details");
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleRunAiAnalysis = async (contact: Contact) => {
    if (aiAnalysisLoading[contact.id]) return;
    
    setAiAnalysisLoading(prev => ({ ...prev, [contact.id]: true }));
    
    try {
      const response = await fetch(`${PROD_BASE_URL}/api/run-ai-analysis/${contact.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "AI Analysis Complete",
          description: data.message,
          variant: "default",
        });
        
        // Refresh the contact details
        if (selectedContact && selectedContact.id === contact.id) {
          handleViewDetails(contact);
        }
      } else {
        toast({
          title: "AI Analysis Failed",
          description: data.error || "Failed to run AI analysis",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to run AI analysis:", error);
      toast({
        title: "Error",
        description: "Failed to run AI analysis. Please try again.",
        variant: "destructive",
      });
    } finally {
      setAiAnalysisLoading(prev => ({ ...prev, [contact.id]: false }));
    }
  };

  const handleOpenAiSummaryDialog = (contact: Contact, details: any) => {
    const fullName = `${contact.firstName || ''} ${contact.lastName || ''}`.trim() || 'Unknown Contact';
    setAiSummaryDialog({
      open: true,
      contactName: fullName,
      aiSummary: details.ai_summary || 'No AI summary available',
      aiStatus: details.ai_status || 'No status',
      aiQualityGrade: details.ai_quality_grade || 'No grade',
      aiSalesGrade: details.ai_sales_grade || 'No grade'
    });
  };

  if (isLoading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <Skeleton className="h-6 w-48 bg-slate-700" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full bg-slate-700" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold text-white">Recent Contact Activity</CardTitle>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Search contacts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-slate-700 border-slate-600 text-slate-300 placeholder-slate-400 focus:border-blue-500"
            />
          </div>
          <Button className="bg-blue-600 text-white hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Contact
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="max-h-96 overflow-y-auto" onScroll={handleScroll}>
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700 hover:bg-transparent">
                  <TableHead className="text-slate-400">Contact Name</TableHead>
                  <TableHead className="text-slate-400">Email</TableHead>
                  <TableHead className="text-slate-400">Phone</TableHead>
                  <TableHead className="text-slate-400">Company</TableHead>
                  <TableHead className="text-slate-400">Source</TableHead>
                  <TableHead className="text-slate-400">Tags</TableHead>
                  <TableHead className="text-slate-400">Created</TableHead>
                  <TableHead className="text-slate-400">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredContacts.map((contact) => {
                  const fullName = `${contact.firstName || ''} ${contact.lastName || ''}`.trim() || 'Unknown';
                  const initials = contact.firstName && contact.lastName 
                    ? `${contact.firstName[0]}${contact.lastName[0]}` 
                    : fullName.split(' ').map(n => n[0]).join('').slice(0, 2);
                  
                  return (
                    <TableRow 
                      key={contact.id} 
                      className="border-slate-700 hover:bg-slate-700/50 transition-colors"
                    >
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                            <span className="text-sm font-medium text-white">
                              {initials}
                            </span>
                          </div>
                          <span className="text-white font-medium">{fullName}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-slate-300">{contact.email || '-'}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-slate-300">{contact.phone || '-'}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-slate-300">{contact.companyName || '-'}</span>
                      </TableCell>
                      <TableCell>
                        <Badge className={getSourceBadgeClass(contact.source)}>
                          {contact.source ? contact.source.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : "Unknown"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {contact.tags && contact.tags.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {contact.tags.slice(0, 2).map((tag: string, index: number) => (
                              <Badge key={index} className={getTagsBadgeClass(contact.tags)} variant="outline">
                                {tag}
                              </Badge>
                            ))}
                            {contact.tags.length > 2 && (
                              <Badge variant="outline" className="bg-slate-500/10 text-slate-500">
                                +{contact.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400">No tags</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-slate-300">
                          {formatTimeAgo(contact.dateCreated)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white" onClick={() => handleViewDetails(contact)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                            <Phone className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className={`text-slate-400 hover:text-white ${aiAnalysisLoading[contact.id] ? 'opacity-50 cursor-not-allowed' : ''}`}
                                  onClick={() => handleRunAiAnalysis(contact)}
                                  disabled={aiAnalysisLoading[contact.id]}
                                >
                                  {aiAnalysisLoading[contact.id] ? (
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                                  ) : (
                                    <Zap className="w-4 h-4" />
                                  )}
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Run AI analysis to determine contact status, quality grade, and sales potential.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {loadingMore && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                        <span className="ml-2 text-slate-400">Loading more contacts...</span>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
      <Dialog open={!!selectedContact} onOpenChange={() => setSelectedContact(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Contact Details</DialogTitle>
          </DialogHeader>
          {detailsLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-slate-400">Loading contact details...</span>
            </div>
          ) : detailsError ? (
            <div className="text-red-500 p-4 bg-red-50 rounded-lg">{detailsError}</div>
          ) : details ? (
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="bg-slate-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-3 text-slate-800">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-medium text-slate-600">Name:</span>
                    <span className="ml-2 text-slate-800">{details.firstName} {details.lastName}</span>
                  </div>
                  <div>
                    <span className="font-medium text-slate-600">Email:</span>
                    <span className="ml-2 text-slate-800">{details.email || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="font-medium text-slate-600">Phone:</span>
                    <span className="ml-2 text-slate-800">{details.phone || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="font-medium text-slate-600">Company:</span>
                    <span className="ml-2 text-slate-800">{details.companyName || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="font-medium text-slate-600">Source:</span>
                    <span className="ml-2 text-slate-800">{details.source || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="font-medium text-slate-600">Created:</span>
                    <span className="ml-2 text-slate-800">
                      {details.dateCreated ? new Date(details.dateCreated).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* AI Analysis Status */}
              <div className="bg-slate-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-3 text-slate-800">AI Analysis Status</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-medium text-slate-600">Status:</span>
                    <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                      details.ai_analysis_status === 'completed' ? 'bg-green-100 text-green-800' :
                      details.ai_analysis_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                      details.ai_analysis_status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {details.ai_analysis_status || 'pending'}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-slate-600">Last Analysis:</span>
                    <span className="ml-2 text-slate-800">
                      {details.ai_analysis_date ? new Date(details.ai_analysis_date).toLocaleString() : 'Never'}
                    </span>
                  </div>
                  {details.ai_status && (
                    <div>
                      <span className="font-medium text-slate-600">AI Status:</span>
                      <span className="ml-2 text-slate-800">{details.ai_status}</span>
                    </div>
                  )}
                  {details.ai_summary && (
                    <div>
                      <span className="font-medium text-slate-600">AI Summary:</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-2 inline-flex items-center gap-2 px-2 py-1 rounded-md border border-blue-500 text-blue-600 font-medium text-xs hover:bg-blue-50"
                        onClick={() => handleOpenAiSummaryDialog(selectedContact!, details)}
                      >
                        <Eye className="w-3 h-3" />
                        Read
                      </Button>
                    </div>
                  )}
                  {details.ai_quality_grade && (
                    <div>
                      <span className="font-medium text-slate-600">AI Quality Grade:</span>
                      <span className="ml-2 text-slate-800">{details.ai_quality_grade}</span>
                    </div>
                  )}
                  {details.ai_sales_grade && (
                    <div>
                      <span className="font-medium text-slate-600">AI Sales Grade:</span>
                      <span className="ml-2 text-slate-800">{details.ai_sales_grade}</span>
                    </div>
                  )}
                  {details.ai_analysis_error && (
                    <div className="col-span-2">
                      <span className="font-medium text-slate-600">Error:</span>
                      <span className="ml-2 text-red-600">{details.ai_analysis_error}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Tasks */}
              {details.tasks && details.tasks.length > 0 && (
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-slate-800">Tasks ({details.tasks.length})</h3>
                  <div className="space-y-3">
                    {details.tasks.map((task: any, index: number) => (
                      <div key={index} className="bg-white p-3 rounded border">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-medium text-slate-800">{task.title}</h4>
                            {task.description && (
                              <p className="text-sm text-slate-600 mt-1">{task.description}</p>
                            )}
                          </div>
                          <div className="text-right">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              task.status === 'completed' ? 'bg-green-100 text-green-800' :
                              task.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-slate-100 text-slate-800'
                            }`}>
                              {task.status}
                            </span>
                          </div>
                        </div>
                        {task.due_date && (
                          <div className="text-xs text-slate-500 mt-2">
                            Due: {new Date(task.due_date).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Conversations */}
              {details.conversations && details.conversations.length > 0 && (
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-slate-800">Conversations ({details.conversations.length})</h3>
                  <div className="space-y-3">
                    {details.conversations.map((conv: any, index: number) => (
                      <div key={index} className="bg-white p-3 rounded border">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-medium text-slate-800">{conv.subject || 'No Subject'}</h4>
                            <p className="text-sm text-slate-600 mt-1">Channel: {conv.channel}</p>
                            {conv.last_message && (
                              <p className="text-sm text-slate-600 mt-1">{conv.last_message}</p>
                            )}
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            conv.status === 'active' ? 'bg-green-100 text-green-800' :
                            conv.status === 'closed' ? 'bg-red-100 text-red-800' :
                            'bg-slate-100 text-slate-800'
                          }`}>
                            {conv.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Opportunities */}
              {details.opportunities && details.opportunities.length > 0 && (
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-slate-800">Opportunities ({details.opportunities.length})</h3>
                  <div className="space-y-3">
                    {details.opportunities.map((opp: any, index: number) => (
                      <div key={index} className="bg-white p-3 rounded border">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-medium text-slate-800">{opp.name || opp.title}</h4>
                            {opp.description && (
                              <p className="text-sm text-slate-600 mt-1">{opp.description}</p>
                            )}
                            <div className="flex gap-4 mt-2 text-sm text-slate-600">
                              <span>Stage: {opp.stage}</span>
                              {opp.monetary_value && (
                                <span>Value: ${opp.monetary_value.toLocaleString()}</span>
                              )}
                            </div>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            opp.status === 'open' ? 'bg-blue-100 text-blue-800' :
                            opp.status === 'won' ? 'bg-green-100 text-green-800' :
                            opp.status === 'lost' ? 'bg-red-100 text-red-800' :
                            'bg-slate-100 text-slate-800'
                          }`}>
                            {opp.status}
                          </span>
                        </div>
                        {opp.expected_close_date && (
                          <div className="text-xs text-slate-500 mt-2">
                            Expected Close: {new Date(opp.expected_close_date).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No Details Message */}
              {(!details.tasks || details.tasks.length === 0) && 
               (!details.conversations || details.conversations.length === 0) && 
               (!details.opportunities || details.opportunities.length === 0) && (
                <div className="text-center py-8 text-slate-500">
                  <p>No detailed information available for this contact.</p>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* AI Summary Dialog */}
      <Dialog open={aiSummaryDialog.open} onOpenChange={(open) => setAiSummaryDialog(prev => ({ ...prev, open }))}>
        <DialogContent className="max-w-4xl max-h-[90vh] bg-slate-900 border-slate-800 text-slate-50 overflow-hidden">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-400" />
              AI Analysis Summary
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 overflow-y-auto max-h-[calc(90vh-120px)] pr-2">
            {/* Contact Name */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">{aiSummaryDialog.contactName}</h3>
            </div>

            {/* AI Summary */}
            <div>
              <h4 className="text-md font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" />
                AI Summary
              </h4>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div 
                  className="text-slate-200 leading-relaxed ai-summary-html"
                  dangerouslySetInnerHTML={{ __html: aiSummaryDialog.aiSummary }}
                  style={{
                    lineHeight: '1.6',
                  }}
                />
              </div>
            </div>

            {/* AI Analysis Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h5 className="text-sm font-medium text-slate-400 mb-2">AI Status</h5>
                <div 
                  className="text-white font-semibold"
                  dangerouslySetInnerHTML={{ __html: aiSummaryDialog.aiStatus }}
                />
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h5 className="text-sm font-medium text-slate-400 mb-2">Quality Grade</h5>
                <p className="text-white font-semibold">{aiSummaryDialog.aiQualityGrade}</p>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h5 className="text-sm font-medium text-slate-400 mb-2">Sales Grade</h5>
                <p className="text-white font-semibold">{aiSummaryDialog.aiSalesGrade}</p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
