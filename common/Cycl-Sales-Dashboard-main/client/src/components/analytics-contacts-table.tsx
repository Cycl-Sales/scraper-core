import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { format } from "date-fns";
import { ArrowUpRight, Calendar, CheckSquare, ClipboardList, Filter, Info, Mail, MessageCircle, MessageSquare, Phone, Plug, Search, User, Target, Star, Activity, Zap, Eye } from "lucide-react";
import AIQualityGradeModal from "./ai-quality-grade-modal";
import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { CYCLSALES_APP_ID, PROD_BASE_URL } from "@/lib/constants";
import { useToast } from "@/hooks/use-toast";

// Add mapping for lastMessageType human-readable labels
const lastMessageTypeLabels: Record<string, string> = {
  TYPE_CALL: "Call",
  TYPE_SMS: "SMS",
  TYPE_EMAIL: "Email",
  TYPE_SMS_REVIEW_REQUEST: "SMS Review Request",
  TYPE_WEBCHAT: "Webchat",
  TYPE_SMS_NO_SHOW_REQUEST: "SMS No Show Request",
  TYPE_CAMPAIGN_SMS: "Campaign SMS",
  TYPE_CAMPAIGN_CALL: "Campaign Call",
  TYPE_CAMPAIGN_EMAIL: "Campaign Email",
  TYPE_CAMPAIGN_VOICEMAIL: "Campaign Voicemail",
  TYPE_FACEBOOK: "Facebook",
  TYPE_CAMPAIGN_FACEBOOK: "Campaign Facebook",
  TYPE_CAMPAIGN_MANUAL_CALL: "Campaign Manual Call",
  TYPE_CAMPAIGN_MANUAL_SMS: "Campaign Manual SMS",
  TYPE_GMB: "Google My Business",
  TYPE_CAMPAIGN_GMB: "Campaign Google My Business",
  TYPE_REVIEW: "Review",
  TYPE_INSTAGRAM: "Instagram",
  TYPE_WHATSAPP: "WhatsApp",
  TYPE_CUSTOM_SMS: "Custom SMS",
  TYPE_CUSTOM_EMAIL: "Custom Email",
  TYPE_CUSTOM_PROVIDER_SMS: "Custom Provider SMS",
  TYPE_CUSTOM_PROVIDER_EMAIL: "Custom Provider Email",
  TYPE_IVR_CALL: "IVR Call",
  TYPE_ACTIVITY_CONTACT: "Activity Contact",
  TYPE_ACTIVITY_INVOICE: "Activity Invoice",
  TYPE_ACTIVITY_PAYMENT: "Activity Payment",
  TYPE_ACTIVITY_OPPORTUNITY: "Activity Opportunity",
  TYPE_LIVE_CHAT: "Live Chat",
  TYPE_LIVE_CHAT_INFO_MESSAGE: "Live Chat Info Message",
  TYPE_ACTIVITY_APPOINTMENT: "Activity Appointment",
  TYPE_FACEBOOK_COMMENT: "Facebook Comment",
  TYPE_INSTAGRAM_COMMENT: "Instagram Comment",
  TYPE_CUSTOM_CALL: "Custom Call",
  TYPE_INTERNAL_COMMENT: "Internal Comment",
};

// Function to parse touch summary and return separate chips
function parseTouchSummary(touchSummary: string) {
  if (!touchSummary || touchSummary === 'no_touches') {
    return [{
      text: 'no_touches',
      border: 'border-slate-600',
      textColor: 'text-slate-400',
      iconColor: 'text-slate-400',
      icon: <span className="text-lg">&#10005;</span>
    }];
  }

  // Split by comma and parse each part
  const parts = touchSummary.split(',').map(part => part.trim());
  const chips = [];

  for (const part of parts) {
    // Extract count and type (e.g., "8 SMS" -> count: 8, type: "SMS")
    const match = part.match(/^(\d+)\s+(.+)$/);
    if (match) {
      const type = match[2].toUpperCase();

      // Determine colors and icons based on message type
      let border, textColor, iconColor, icon;

      if (type.includes('SMS')) {
        border = 'border-blue-500';
        textColor = 'text-blue-300';
        iconColor = 'text-blue-300';
        icon = <MessageSquare className="w-4 h-4" />;
      } else if (type.includes('PHONE CALL') || type.includes('CALL')) {
        border = 'border-green-500';
        textColor = 'text-green-300';
        iconColor = 'text-green-300';
        icon = <Phone className="w-4 h-4" />;
      } else if (type.includes('EMAIL')) {
        border = 'border-purple-500';
        textColor = 'text-purple-300';
        iconColor = 'text-purple-300';
        icon = <Mail className="w-4 h-4" />;
      } else if (type.includes('OPPORTUNITY')) {
        border = 'border-orange-500';
        textColor = 'text-orange-300';
        iconColor = 'text-orange-300';
        icon = <Target className="w-4 h-4" />;
      } else if (type.includes('FACEBOOK')) {
        border = 'border-blue-600';
        textColor = 'text-blue-400';
        iconColor = 'text-blue-400';
        icon = <MessageSquare className="w-4 h-4" />;
      } else if (type.includes('WHATSAPP')) {
        border = 'border-green-600';
        textColor = 'text-green-400';
        iconColor = 'text-green-400';
        icon = <MessageCircle className="w-4 h-4" />;
      } else if (type.includes('WEBCHAT')) {
        border = 'border-cyan-500';
        textColor = 'text-cyan-300';
        iconColor = 'text-cyan-300';
        icon = <MessageSquare className="w-4 h-4" />;
      } else if (type.includes('REVIEW')) {
        border = 'border-yellow-500';
        textColor = 'text-yellow-300';
        iconColor = 'text-yellow-300';
        icon = <Star className="w-4 h-4" />;
      } else if (type.includes('APPOINTMENT')) {
        border = 'border-indigo-500';
        textColor = 'text-indigo-300';
        iconColor = 'text-indigo-300';
        icon = <Calendar className="w-4 h-4" />;
      } else if (type.includes('ACTIVITY')) {
        border = 'border-pink-500';
        textColor = 'text-pink-300';
        iconColor = 'text-pink-300';
        icon = <Activity className="w-4 h-4" />;
      } else {
        // Default for unknown types
        border = 'border-slate-500';
        textColor = 'text-slate-300';
        iconColor = 'text-slate-300';
        icon = <MessageSquare className="w-4 h-4" />;
      }

      chips.push({
        text: part,
        border,
        textColor,
        iconColor,
        icon
      });
    } else {
      // If it doesn't match the pattern, treat as a single chip
      chips.push({
        text: part,
        border: 'border-slate-500',
        textColor: 'text-slate-300',
        iconColor: 'text-slate-300',
        icon: <MessageSquare className="w-4 h-4" />
      });
    }
  }

  return chips;
}

interface Filters {
  contactName: string;
  aiStatus: string[];
  aiSummary: string[];
  aiQuality: string[];
  aiSales: string[];
  crmTasks: string[];
  category: string[];
  channel: string[];
  assignedTo: string[];
  touchSummary: string[];
  engagementSummary: string[];
  opportunities: { min: string; max: string };
}

const aiStatusOptions = [
  { label: "Valid Lead", color: "bg-blue-900 text-blue-300", icon: "👤" },
  { label: "Wants to Stay - Retention Path", color: "bg-green-900 text-green-300", icon: "🟢" },
  { label: "Unqualified", color: "bg-slate-800 text-slate-400", icon: "👤" },
  { label: "Not Contacted", color: "bg-slate-800 text-slate-400", icon: "👤" },
  { label: "❄️ Cold Lead - No Recent Activity", color: "bg-red-900 text-red-300", icon: "❄️" },
  { label: "🔥 Hot Lead - Highly Engaged", color: "bg-green-900 text-green-300", icon: "🔥" },
  { label: "❌ API Error", color: "bg-red-900 text-red-300", icon: "❌" },
  { label: "❌ Analysis Failed", color: "bg-red-900 text-red-300", icon: "❌" },
  { label: "❌ No API Key", color: "bg-red-900 text-red-300", icon: "❌" },
  { label: "❌ Invalid API Key", color: "bg-red-900 text-red-300", icon: "❌" },
  { label: "❌ Data Too Large", color: "bg-red-900 text-red-300", icon: "❌" }
];
const aiSummaryOptions = ["Read"];
const aiQualityOptions = [
  { label: "Lead Grade A", color: "bg-green-900 text-green-300" },
  { label: "Lead Grade B", color: "bg-blue-900 text-blue-300" },
  { label: "Lead Grade C", color: "bg-yellow-900 text-yellow-300" },
  { label: "No Grade", color: "bg-slate-800 text-slate-400" }
];
const aiSalesOptions = [
  { label: "Sales Grade A", color: "bg-green-900 text-green-300" },
  { label: "Sales Grade B", color: "bg-blue-900 text-blue-300" },
  { label: "Sales Grade C", color: "bg-yellow-900 text-yellow-300" },
  { label: "Sales Grade D", color: "bg-orange-900 text-orange-300" },
  { label: "No Grade", color: "bg-slate-800 text-slate-400" }
];
const crmTasksOptions = [
  { label: "1 Overdue", color: "bg-red-900 text-red-400" },
  { label: "2 Upcoming", color: "bg-yellow-900 text-yellow-300" },
  { label: "No Tasks", color: "bg-slate-800 text-slate-400" },
  { label: "", color: "" }
];
const categoryOptions = ["Integration", "Manual", "Automated", "Referral"];
const channelOptions = ["Integration", "Manual", "Automated", "Referral"];
const assignedToOptions = ["SignalWire SMS User", "SignalWire", "API User", "Admin"];
const touchSummaryOptions = ["no_touches", "SMS", "PHONE CALL", "EMAIL", "OPPORTUNITY", "FACEBOOK", "WHATSAPP", "WEBCHAT", "REVIEW", "APPOINTMENT", "ACTIVITY"];
const engagementTypes = [
  { type: "Call", icon: <Phone className="w-4 h-4" />, color: "border-green-400 text-green-300" },
  { type: "SMS", icon: <MessageCircle className="w-4 h-4" />, color: "border-yellow-400 text-yellow-300" },
  { type: "Email", icon: <Mail className="w-4 h-4" />, color: "border-blue-400 text-blue-300" },
  { type: "Chat", icon: <MessageSquare className="w-4 h-4" />, color: "border-purple-400 text-purple-300" },
];
// Removed mock data block as it's unused

const columns = [
  "Contact Name",
  "AI Status",
  "AI Summary",
  "AI Quality Grade",
  "AI Sales Grade",
  "CRM Tasks",
  "Conversations",
  "Category",
  "Channel",
  "Created By",
  "Attribution",
  "Assigned To",
  "Speed to Lead",
  "Touch Summary",
  "Engagement Summary",
  "Last Touch Date",
  "Last Message",
  "Total Pipeline Value",
  "Opportunities",
  "Contact Tags",
  "View Calls",
  "Date Created",
  "Actions"
];

function getChipProps(type: string, value: string) {
  // Returns { border, text, iconColor, icon, bg } for each chip type/value
  switch (type) {
    case 'aiStatus':
      if (value === 'Valid Lead') return { border: 'border-blue-500', text: 'text-blue-300', iconColor: 'text-blue-300', icon: <User className="w-4 h-4" /> };
      if (value === 'Wants to Stay - Retention Path') return { border: 'border-green-500', text: 'text-green-300', iconColor: 'text-green-300', icon: <User className="w-4 h-4" /> };
      if (value.includes('❄️ Cold Lead')) return { border: 'border-red-500', text: 'text-red-300', iconColor: 'text-red-300', icon: <User className="w-4 h-4" /> };
      if (value.includes('🔥 Hot Lead')) return { border: 'border-green-500', text: 'text-green-300', iconColor: 'text-green-300', icon: <User className="w-4 h-4" /> };
      if (value.includes('❌')) return { border: 'border-red-500', text: 'text-red-300', iconColor: 'text-red-300', icon: <User className="w-4 h-4" /> };
      return { border: 'border-slate-600', text: 'text-slate-300', iconColor: 'text-slate-300', icon: <User className="w-4 h-4" /> };
    case 'aiSummary':
      return { border: 'border-slate-600', text: 'text-slate-300', iconColor: 'text-slate-300', icon: <ClipboardList className="w-4 h-4" /> };
    case 'aiQuality':
      if (value.includes('C')) return { border: 'border-yellow-500', text: 'text-yellow-300', iconColor: 'text-yellow-300', icon: <ClipboardList className="w-4 h-4" /> };
      if (value.includes('D')) return { border: 'border-orange-500', text: 'text-orange-300', iconColor: 'text-orange-300', icon: <ClipboardList className="w-4 h-4" /> };
      if (value.includes('F')) return { border: 'border-red-500', text: 'text-red-400', iconColor: 'text-red-400', icon: <ClipboardList className="w-4 h-4" /> };
      return { border: 'border-slate-600', text: 'text-slate-300', iconColor: 'text-slate-300', icon: <ClipboardList className="w-4 h-4" /> };
    case 'aiSales':
      if (value.includes('C')) return { border: 'border-yellow-500', text: 'text-yellow-300', iconColor: 'text-yellow-300', icon: <ClipboardList className="w-4 h-4" /> };
      if (value.includes('D')) return { border: 'border-orange-500', text: 'text-orange-300', iconColor: 'text-orange-300', icon: <ClipboardList className="w-4 h-4" /> };
      if (value.includes('F')) return { border: 'border-red-500', text: 'text-red-400', iconColor: 'text-red-400', icon: <ClipboardList className="w-4 h-4" /> };
      return { border: 'border-slate-600', text: 'text-slate-300', iconColor: 'text-slate-300', icon: <ClipboardList className="w-4 h-4" /> };
    case 'crmTasks':
      if (value.includes('Overdue')) return { border: 'border-red-500', text: 'text-red-400', iconColor: 'text-red-400', icon: <CheckSquare className="w-4 h-4" /> };
      if (value.includes('Upcoming')) return { border: 'border-yellow-500', text: 'text-yellow-300', iconColor: 'text-yellow-300', icon: <CheckSquare className="w-4 h-4" /> };
      return { border: 'border-slate-600', text: 'text-slate-300', iconColor: 'text-slate-300', icon: <CheckSquare className="w-4 h-4" /> };
    case 'category':
      return { border: 'border-pink-500', text: 'text-pink-300', iconColor: 'text-pink-300', icon: <Plug className="w-4 h-4" /> };
    case 'channel':
      return { border: 'border-pink-500', text: 'text-pink-300', iconColor: 'text-pink-300', icon: <Plug className="w-4 h-4" /> };
    case 'touchSummary':
      // Parse touch summary to determine colors based on message types
      if (value === 'no_touches') {
        return { border: 'border-slate-600', text: 'text-slate-400', iconColor: 'text-slate-400', icon: <span className="text-lg">&#10005;</span> };
      }

      // Check for different message types and assign colors
      if (value.includes('SMS')) {
        return { border: 'border-blue-500', text: 'text-blue-300', iconColor: 'text-blue-300', icon: <MessageSquare className="w-4 h-4" /> };
      }
      if (value.includes('PHONE CALL') || value.includes('CALL')) {
        return { border: 'border-green-500', text: 'text-green-300', iconColor: 'text-green-300', icon: <Phone className="w-4 h-4" /> };
      }
      if (value.includes('EMAIL')) {
        return { border: 'border-purple-500', text: 'text-purple-300', iconColor: 'text-purple-300', icon: <Mail className="w-4 h-4" /> };
      }
      if (value.includes('OPPORTUNITY')) {
        return { border: 'border-orange-500', text: 'text-orange-300', iconColor: 'text-orange-300', icon: <Target className="w-4 h-4" /> };
      }
      if (value.includes('FACEBOOK')) {
        return { border: 'border-blue-600', text: 'text-blue-400', iconColor: 'text-blue-400', icon: <MessageSquare className="w-4 h-4" /> };
      }
      if (value.includes('WHATSAPP')) {
        return { border: 'border-green-600', text: 'text-green-400', iconColor: 'text-green-400', icon: <MessageCircle className="w-4 h-4" /> };
      }
      if (value.includes('WEBCHAT')) {
        return { border: 'border-cyan-500', text: 'text-cyan-300', iconColor: 'text-cyan-300', icon: <MessageSquare className="w-4 h-4" /> };
      }
      if (value.includes('REVIEW')) {
        return { border: 'border-yellow-500', text: 'text-yellow-300', iconColor: 'text-yellow-300', icon: <Star className="w-4 h-4" /> };
      }
      if (value.includes('APPOINTMENT')) {
        return { border: 'border-indigo-500', text: 'text-indigo-300', iconColor: 'text-indigo-300', icon: <Calendar className="w-4 h-4" /> };
      }
      if (value.includes('ACTIVITY')) {
        return { border: 'border-pink-500', text: 'text-pink-300', iconColor: 'text-pink-300', icon: <Activity className="w-4 h-4" /> };
      }

      // Default for other types
      return { border: 'border-slate-500', text: 'text-slate-300', iconColor: 'text-slate-300', icon: <MessageSquare className="w-4 h-4" /> };
    case 'engagementSummary':
      if (value.includes('SMS')) return { border: 'border-yellow-400', text: 'text-yellow-300', iconColor: 'text-yellow-300', icon: <Search className="w-4 h-4" /> };
      if (value.includes('Email')) return { border: 'border-blue-400', text: 'text-blue-300', iconColor: 'text-blue-300', icon: <Search className="w-4 h-4" /> };
      if (value.includes('Call')) return { border: 'border-green-400', text: 'text-green-300', iconColor: 'text-green-300', icon: <Search className="w-4 h-4" /> };
      if (value.includes('No Engagement')) return { border: 'border-slate-500', text: 'text-slate-400', iconColor: 'text-slate-400', icon: <Search className="w-4 h-4" /> };
      return { border: 'border-slate-500', text: 'text-slate-400', iconColor: 'text-slate-400', icon: <Search className="w-4 h-4" /> };
    case 'lastMessage':
      // handled inline for multiple chips
      return { border: '', text: '', iconColor: '', icon: null };
    default:
      return { border: 'border-slate-600', text: 'text-slate-300', iconColor: 'text-slate-300', icon: null };
  }
}

interface AnalyticsContactsTableProps {
  loading?: boolean;
  locationId: string;
  selectedUser?: string;
  activeFilters?: {
    aiStatus: string[];
    aiQualityGrade: string[];
    aiSalesGrade: string[];
    crmTasks: string[];
    category: string[];
    channel: string[];
    touchSummary: string[];
  };
}

/**
 * Analytics Contacts Table Component
 * 
 * Displays a table of contacts with filtering capabilities including:
 * - User filtering: Filter contacts by assigned user (selectedUser prop)
 * - Search functionality: Search contacts by name
 * - Column filtering: Filter by various contact attributes
 * - Pagination: Lazy loading with configurable page size
 * 
 * Props:
 * - loading: Boolean to show loading state
 * - locationId: String identifier for the location
 * - selectedUser: Optional string to filter contacts by assigned user
 */
export default function AnalyticsContactsTable({ loading = false, locationId, selectedUser, activeFilters = {
  aiStatus: [],
  aiQualityGrade: [],
  aiSalesGrade: [],
  crmTasks: [],
  category: [],
  channel: [],
  touchSummary: [],
} }: AnalyticsContactsTableProps) {
  const { toast } = useToast();

  // --- New state for lazy loading ---
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [page, setPage] = useState(1);
  const [totalContacts, setTotalContacts] = useState<number>(0);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [contactsData, setContactsData] = useState<any[]>([]);
  // Removed unused countLoading and syncStatus state
  const [hasMore, setHasMore] = useState(false);

  // Search state
  const [search, setSearch] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(false);

  // --- New state for detailed data loading ---


  // AI Analysis state
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState<{ [key: string]: boolean }>({});
  const [syncDataLoading, setSyncDataLoading] = useState<{ [key: string]: boolean }>({});

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

  // AI Quality Grade Modal state
  const [aiQualityGradeModal, setAiQualityGradeModal] = useState<{
    open: boolean;
    contactName: string;
    aiQualityGrade: string;
    aiReasoning: string;
    aiStatus?: string;
    aiSummary?: string;
  }>({
    open: false,
    contactName: '',
    aiQualityGrade: '',
    aiReasoning: '',
    aiStatus: '',
    aiSummary: ''
  });

  // AI Sales Grade Modal state
  const [aiSalesGradeModal, setAiSalesGradeModal] = useState<{
    open: boolean;
    contactName: string;
    aiSalesGrade: string;
    aiSalesReasoning: string;
    aiStatus?: string;
    aiSummary?: string;
  }>({
    open: false,
    contactName: '',
    aiSalesGrade: '',
    aiSalesReasoning: '',
    aiStatus: '',
    aiSummary: ''
  });

  const [detailedDataLoading, setDetailedDataLoading] = useState<Record<number, boolean>>({});

  // Store polling intervals for cleanup - DISABLED
  // const [pollingIntervals, setPollingIntervals] = useState<Set<NodeJS.Timeout>>(new Set());

  // Track if polling is active - DISABLED
  // const [isPolling, setIsPolling] = useState(false);

  // Fetch total contacts count and first page when locationId or selectedUser changes
  useEffect(() => {
    if (!locationId) return;
    setContactsLoading(true);
    setContactsData([]);
    setTotalContacts(0);
    setPage(1);
    
    // Build count URL with user filter if applicable
    const countUrl = `${PROD_BASE_URL}/api/location-contacts-count?location_id=${locationId}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}`;
    console.log('Fetching count from URL:', countUrl);
    
    // Fetch count
    fetch(countUrl)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          console.log('Count response:', data);
          setTotalContacts(data.total_contacts || 0);
        } else {
          setTotalContacts(0);
        }
      })
      .catch(err => {
        console.error('Error fetching count:', err);
        setTotalContacts(0);
      })
      .finally(() => { });
  }, [locationId, selectedUser]);

  // Fetch contacts for current page
  useEffect(() => {
    if (!locationId || isSearching) {
      console.log('Skipping contact fetch: locationId=', locationId, 'isSearching=', isSearching);
      return; // Don't fetch if we're searching
    }
    
    console.log('Fetching contacts for locationId:', locationId, 'page:', page, 'limit:', rowsPerPage, 'selectedUser:', selectedUser);
    console.log('selectedUser type:', typeof selectedUser, 'length:', selectedUser?.length);
    setContactsLoading(true);

    // Use the new optimized endpoint
    const url = `${PROD_BASE_URL}/api/location-contacts-optimized?location_id=${locationId}&page=${page}&limit=${rowsPerPage}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}`;
    console.log('Fetching from URL:', url);
    
    fetch(url)
      .then(res => {
        console.log('Response status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('Contacts API response:', data);
        if (data.success) {
          console.log('Setting contacts data:', data.contacts);
          setContactsData(data.contacts || []);
          setHasMore(data.has_more || false);
          // Don't automatically fetch details - let frontend request them on-demand
          // Details will be fetched when user interacts with specific contacts
        } else {
          console.error('Contacts API failed:', data.error);
          setContactsData([]);
          setHasMore(false);
        }
      })
      .catch(error => {
        console.error('Error fetching contacts:', error);
        setContactsData([]);
        setHasMore(false);
      })
      .finally(() => setContactsLoading(false));
  }, [locationId, page, rowsPerPage, selectedUser]);

  // Real-time auto-refresh effect
  useEffect(() => {
    if (!locationId || isSearching) {
      return; // Don't auto-refresh if we're searching
    }

    // Set up auto-refresh every 30 seconds
    const refreshInterval = setInterval(() => {
      console.log('Auto-refreshing contacts data...');
      fetchContacts(true); // Pass true to indicate this is an auto-refresh
    }, 30000); // 30 seconds

    // Cleanup interval on unmount or when dependencies change
    return () => {
      clearInterval(refreshInterval);
    };
  }, [locationId, selectedUser, isSearching]); // Re-run when these change

  // Cleanup polling intervals when component unmounts or locationId changes - DISABLED
  // useEffect(() => {
  //   return () => {
  //     // Clear all polling intervals
  //     pollingIntervals.forEach(interval => clearInterval(interval));
  //     setPollingIntervals(new Set());
  //   };
  // }, [locationId]); // Re-run when locationId changes

  // --- New function to poll for contact sync status - DISABLED ---
  // const startPollingForDetails = (contactIds: number[]) => {
  //   // Function disabled since background sync is turned off
  // };



  // --- Function to fetch detailed contact data ---
  const fetchContactDetails = async (contactId: number) => {
    if (detailedDataLoading[contactId]) return; // Already loading

    setDetailedDataLoading(prev => ({ ...prev, [contactId]: true }));

    try {
      const response = await fetch(`${PROD_BASE_URL}/api/contact-details?contact_id=${contactId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        // Update the contact data with the fetched details
        setContactsData(prev => prev.map(contact => {
          if (contact.id === contactId) {
            return {
              ...contact,
              tasks: data.contact.tasks || [],
              tasks_count: data.contact.tasks_count || 0,
              conversations: data.contact.conversations || [],
              conversations_count: data.contact.conversations_count || 0,
              // Update touch summary data from the API response
              touch_summary: data.contact.touch_summary || contact.touch_summary || 'no_touches',
              last_touch_date: data.contact.last_touch_date || contact.last_touch_date || '',
              last_message: data.contact.last_message || contact.last_message || '',
              details_fetched: true,
              has_tasks: data.contact.tasks_count > 0,
              has_conversations: data.contact.conversations_count > 0,
              loading_details: false,
            };
          }
          return contact;
        }));
      } else {
        console.error('Failed to fetch contact details:', data.error);
      }
    } catch (error) {
      console.error('Error fetching contact details:', error);
    } finally {
      setDetailedDataLoading(prev => ({ ...prev, [contactId]: false }));
    }
  };

  // --- Function to fetch details for specific contacts only ---
  const fetchContactDetailsOnDemand = async (contactId: number) => {
    // Only fetch details for a specific contact when needed
    await fetchContactDetails(contactId);
  };

  // --- Function to trigger background sync - DISABLED ---
  // const triggerBackgroundSync = async () => {
  //   // Function disabled to prevent automatic background sync
  // };

  // Removed details polling effect as background sync is disabled

  // Search functionality
  const handleSearch = async (searchTerm: string) => {
    if (!locationId) return;

    setSearchLoading(true);
    setIsSearching(true);
    
    try {
      const url = `${PROD_BASE_URL}/api/location-contacts-search?location_id=${locationId}&search=${encodeURIComponent(searchTerm)}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setContactsData(data.contacts || []);
        setTotalContacts(data.total_contacts || 0);
        setPage(1); // Reset to first page when searching
      } else {
        console.error('Search failed:', data.error);
        setContactsData([]);
        setTotalContacts(0);
      }
    } catch (error) {
      console.error('Error searching contacts:', error);
      setContactsData([]);
      setTotalContacts(0);
    } finally {
      setSearchLoading(false);
      setIsSearching(false);
    }
  };

  // Function to fetch normal contacts (without search)
  const fetchContacts = async (isAutoRefresh = false) => {
    if (!locationId) return;
    
    if (isAutoRefresh) {
      setIsAutoRefreshing(true);
    } else {
      setContactsLoading(true);
    }
    setIsSearching(false);
    
    try {
      const response = await fetch(`${PROD_BASE_URL}/api/location-contacts-optimized?location_id=${locationId}&page=${page}&limit=${rowsPerPage}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}&_t=${Date.now()}`);
      const data = await response.json();
      
      if (data.success) {
        setContactsData(data.contacts || []);
        setTotalContacts(data.total_contacts || 0);
        setHasMore(data.has_more || false);
        setLastRefreshTime(new Date());
        console.log('Contacts data refreshed successfully');
      } else {
        setContactsData([]);
        setTotalContacts(0);
        setHasMore(false);
      }
    } catch (error) {
      console.error('Error fetching contacts:', error);
      setContactsData([]);
      setTotalContacts(0);
      setHasMore(false);
    } finally {
      if (isAutoRefresh) {
        setIsAutoRefreshing(false);
      } else {
        setContactsLoading(false);
      }
    }
  };

  // Debounced search effect
  useEffect(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (search.trim() === '') {
      // If search is empty, let the normal fetching effect handle it
      setIsSearching(false);
    } else {
      // Debounce search to avoid too many API calls
      const timeout = setTimeout(() => {
        handleSearch(search);
      }, 300);
      setSearchTimeout(timeout);
    }

    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    };
  }, [search, locationId]);

  const allColumns = columns;
  const requiredColumns = ["Contact Name", "Actions"]; // Make Actions always visible
  const optionalColumns = allColumns.filter((col) => !requiredColumns.includes(col));
  const [visibleColumns, setVisibleColumns] = useState<string[]>(allColumns);

  const handleToggleColumn = (col: string) => {
    if (requiredColumns.includes(col)) return; // Prevent hiding required columns
    setVisibleColumns((prev) =>
      prev.includes(col)
        ? prev.filter((c) => c !== col)
        : [...prev, col]
    );
  };
  const handleToggleHideAll = () => {
    if (visibleColumns.length === requiredColumns.length && requiredColumns.every(col => visibleColumns.includes(col))) {
      setVisibleColumns([...allColumns]);
    } else {
      setVisibleColumns([...requiredColumns]);
    }
  };

  const handleRunAiAnalysis = async (contact: any) => {
    if (aiAnalysisLoading[contact.id]) return;

    setAiAnalysisLoading(prev => ({ ...prev, [contact.id]: true }));

    try {
      // Run the main AI analysis
      const response = await fetch(`${PROD_BASE_URL}/api/run-ai-analysis/${contact.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();

      if (result.success) {
        // Also run the AI sales grade analysis
        try {
          const salesGradeResponse = await fetch(`${PROD_BASE_URL}/api/run-ai-sales-grade-analysis/${contact.id}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          const salesGradeResult = await salesGradeResponse.json();
          
          if (salesGradeResult.success) {
            toast({
              title: "AI Analysis Complete",
              description: "AI analysis and sales grade analysis have been completed successfully.",
            });
          } else {
            toast({
              title: "AI Analysis Partially Complete",
              description: "Main AI analysis completed, but sales grade analysis failed.",
              variant: "destructive",
            });
          }
        } catch (salesGradeError) {
          console.error('Error running AI sales grade analysis:', salesGradeError);
          toast({
            title: "AI Analysis Partially Complete",
            description: "Main AI analysis completed, but sales grade analysis failed.",
            variant: "destructive",
          });
        }
        
        // Add a small delay to ensure the backend has processed the changes
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Refresh the contacts data to show updated AI analysis
        // Trigger a re-fetch of the current page
        const refreshResponse = await fetch(`${PROD_BASE_URL}/api/location-contacts-optimized?location_id=${locationId}&page=${page}&limit=${rowsPerPage}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}&_t=${Date.now()}`);
        const refreshData = await refreshResponse.json();

        if (refreshData.success) {
          console.log('Refreshed contacts data:', refreshData.contacts);
          setContactsData(refreshData.contacts || []);
        } else {
          console.error('Failed to refresh contacts data:', refreshData);
        }
      } else {
        toast({
          title: "AI Analysis Failed",
          description: result.error || "Failed to run AI analysis. Please try again.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error running AI analysis:', error);
      toast({
        title: "Error",
        description: "An error occurred while running AI analysis. Please try again.",
        variant: "destructive",
      });
    } finally {
      setAiAnalysisLoading(prev => ({ ...prev, [contact.id]: false }));
    }
  };

  const handleSyncContactData = async (contact: any) => {
    if (syncDataLoading[contact.id]) return;

    setSyncDataLoading(prev => ({ ...prev, [contact.id]: true }));

    try {
      const response = await fetch(`${PROD_BASE_URL}/api/sync-contact-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contact_id: contact.id,
          location_id: locationId,
          app_id: CYCLSALES_APP_ID
        })
      });

      const result = await response.json();

      if (result.success) {
        toast({
          title: "Data Sync Complete",
          description: `Successfully synced data for ${contact.name}. Found ${result.messages_found} messages.`,
        });
        
        // Add a small delay to ensure the backend has processed the changes
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Refresh the contacts data to show updated information
        const refreshResponse = await fetch(`${PROD_BASE_URL}/api/location-contacts-optimized?location_id=${locationId}&page=${page}&limit=${rowsPerPage}&appId=${CYCLSALES_APP_ID}${selectedUser ? `&selected_user=${encodeURIComponent(selectedUser)}` : ''}&_t=${Date.now()}`);
        const refreshData = await refreshResponse.json();

        if (refreshData.success) {
          console.log('Refreshed contacts data after sync:', refreshData.contacts);
          setContactsData(refreshData.contacts || []);
        } else {
          console.error('Failed to refresh contacts data after sync:', refreshData);
        }
      } else {
        toast({
          title: "Data Sync Failed",
          description: result.error || "Failed to sync data from GHL. Please try again.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error syncing contact data:', error);
      toast({
        title: "Error",
        description: "An error occurred while syncing data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSyncDataLoading(prev => ({ ...prev, [contact.id]: false }));
    }
  };

  const handleOpenAiSummaryDialog = (contact: any) => {
    setAiSummaryDialog({
      open: true,
      contactName: contact.name || 'Unknown Contact',
      aiSummary: contact.aiSummary || 'No AI summary available',
      aiStatus: contact.aiStatus?.label || 'No status',
      aiQualityGrade: contact.aiQuality?.label || 'No grade',
      aiSalesGrade: contact.aiSales?.label || 'No grade'
    });
  };

  const handleOpenAiQualityGradeModal = (contact: any) => {
    setAiQualityGradeModal({
      open: true,
      contactName: contact.name || 'Unknown Contact',
      aiQualityGrade: contact.ai_quality_grade || 'no_grade',
      aiReasoning: contact.ai_reasoning || '<span style="color: #6b7280;">No analysis available</span>',
      aiStatus: contact.ai_status,
      aiSummary: contact.ai_summary
    });
  };

  const handleOpenAiSalesGradeModal = (contact: any) => {
    setAiSalesGradeModal({
      open: true,
      contactName: contact.name || 'Unknown Contact',
      aiSalesGrade: contact.ai_sales_grade || 'no_grade',
      aiSalesReasoning: contact.ai_sales_reasoning || '<span style="color: #6b7280;">No sales grade analysis available</span>',
      aiStatus: contact.ai_status,
      aiSummary: contact.ai_summary
    });
  };

  const [filters, setFilters] = useState<Filters>({
    contactName: "",
    aiStatus: [],
    aiSummary: [],
    aiQuality: [],
    aiSales: [],
    crmTasks: [],
    category: [],
    channel: [],
    assignedTo: [],
    touchSummary: [],
    engagementSummary: [],
    opportunities: { min: "", max: "" },
  });

  // Transform contacts data to match the expected format
  console.log('Transforming contacts data:', contactsData);
  const transformedContacts = contactsData.map((contact: any) => {


    // Map AI status - handle both HTML content and simple strings
    const getAiStatusInfo = (aiStatus: string) => {
      // If it's HTML content, extract the text and determine color
      if (aiStatus && aiStatus.includes('<span')) {
        // Extract text content from HTML
        const textMatch = aiStatus.match(/>([^<]+)</);
        const text = textMatch ? textMatch[1] : 'Unknown';
        
        // Determine color based on content
        if (aiStatus.includes('color: #dc2626')) {
          return { label: text, color: 'bg-red-900 text-red-300', icon: '❄️', html: aiStatus };
        } else if (aiStatus.includes('color: #059669')) {
          return { label: text, color: 'bg-green-900 text-green-300', icon: '🔥', html: aiStatus };
        } else if (aiStatus.includes('color: #6b7280')) {
          return { label: text, color: 'bg-slate-800 text-slate-400', icon: '👤', html: aiStatus };
        } else {
          return { label: text, color: 'bg-blue-900 text-blue-300', icon: '👤', html: aiStatus };
        }
      }
      
      // Fallback to simple string mapping
      const aiStatusMap: { [key: string]: any } = {
        'valid_lead': { label: 'Valid Lead', color: 'bg-blue-900 text-blue-300', icon: '👤' },
        'retention_path': { label: 'Wants to Stay - Retention Path', color: 'bg-green-900 text-green-300', icon: '🟢' },
        'unqualified': { label: 'Unqualified', color: 'bg-slate-800 text-slate-400', icon: '👤' },
        'not_contacted': { label: 'Not Contacted', color: 'bg-slate-800 text-slate-400', icon: '👤' }
      };
      
      return aiStatusMap[aiStatus] || aiStatusMap.not_contacted;
    };

    // Map AI quality grades
    const aiQualityMap: { [key: string]: any } = {
      'grade_a': { label: 'Lead Grade A', color: 'bg-green-900 text-green-300' },
      'grade_b': { label: 'Lead Grade B', color: 'bg-blue-900 text-blue-300' },
      'grade_c': { label: 'Lead Grade C', color: 'bg-yellow-900 text-yellow-300' },
      'no_grade': { label: 'No Grade', color: 'bg-slate-800 text-slate-400' }
    };

    // Dynamic AI sales grade mapping - handles any user-defined grade
    const getAiSalesGradeInfo = (gradeValue: string) => {
      if (!gradeValue || gradeValue === 'no_grade') {
        return { label: 'No Grade', color: 'bg-slate-800 text-slate-400' };
      }
      
      // Convert grade value to display format (e.g., "grade_a" -> "Sales Grade A")
      const gradeKey = gradeValue.toLowerCase();
      let displayLabel = gradeValue;
      
      // Handle common grade patterns
      if (gradeKey.startsWith('grade_')) {
        const gradeLetter = gradeKey.replace('grade_', '').toUpperCase();
        displayLabel = `Sales Grade ${gradeLetter}`;
      } else if (gradeKey.includes('_')) {
        // Convert snake_case to Title Case
        displayLabel = gradeValue.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        displayLabel = `Sales ${displayLabel}`;
      } else {
        // Capitalize first letter
        displayLabel = `Sales ${gradeValue.charAt(0).toUpperCase() + gradeValue.slice(1)}`;
      }
      
      // Assign colors based on grade patterns or default to a neutral color
      let color = 'bg-slate-700 text-slate-300'; // Default neutral color
      
      if (gradeKey.includes('a') || gradeKey.includes('premium') || gradeKey.includes('excellent')) {
        color = 'bg-green-900 text-green-300';
      } else if (gradeKey.includes('b') || gradeKey.includes('good') || gradeKey.includes('standard')) {
        color = 'bg-blue-900 text-blue-300';
      } else if (gradeKey.includes('c') || gradeKey.includes('average') || gradeKey.includes('basic')) {
        color = 'bg-yellow-900 text-yellow-300';
      } else if (gradeKey.includes('d') || gradeKey.includes('poor') || gradeKey.includes('below')) {
        color = 'bg-orange-900 text-orange-300';
      } else if (gradeKey.includes('f') || gradeKey.includes('fail') || gradeKey.includes('unqualified')) {
        color = 'bg-red-900 text-red-300';
      }
      
      return { label: displayLabel, color };
    };

    // Map CRM tasks
    const crmTasksMap: { [key: string]: any } = {
      'overdue': { label: '1 Overdue', color: 'bg-red-900 text-red-400' },
      'upcoming': { label: '2 Upcoming', color: 'bg-yellow-900 text-yellow-300' },
      'no_tasks': { label: 'No Tasks', color: 'bg-slate-800 text-slate-400' },
      'empty': { label: '', color: '' }
    };

    return {
      id: contact.id, // Add the contact ID
      name: contact.name || '',
      aiStatus: getAiStatusInfo(contact.ai_status),
      aiSummary: contact.ai_summary || 'Read',
      aiQuality: aiQualityMap[contact.ai_quality_grade] || aiQualityMap.no_grade,
      aiSales: getAiSalesGradeInfo(contact.ai_sales_grade),
      crmTasks: crmTasksMap[contact.crm_tasks] || crmTasksMap.no_tasks,
      category: contact.category || 'manual',
      channel: contact.channel || 'manual',
      createdBy: contact.created_by || '',
      attribution: contact.attribution || '',
      assignedTo: contact.assigned_to || '',
      speedToLead: contact.speed_to_lead || '',
      touchSummary: contact.touch_summary || 'no_touches',
      engagementSummary: Array.isArray(contact.engagement_summary) ? contact.engagement_summary : [],
      // Use last message date as last touch date for more meaningful data
      lastTouchDate: (() => {
        if (Array.isArray(contact.conversations) && contact.conversations.length > 0) {
          // Sort conversations by write_date (most recent first) and get the latest one
          const sortedConversations = [...contact.conversations].sort((a, b) =>
            new Date(b.write_date || b.create_date || 0).getTime() -
            new Date(a.write_date || a.create_date || 0).getTime()
          );
          const latestConversation = sortedConversations[0];

          if (latestConversation && (latestConversation.write_date || latestConversation.create_date)) {
            return latestConversation.write_date || latestConversation.create_date;
          }
        }
        // Fallback to original last_touch_date if no conversations
        return contact.last_touch_date || '';
      })(),
      // Get last message from the actual last_message field
      lastMessage: (() => {
        // First try to use the actual last_message data from backend
        if (contact.last_message && typeof contact.last_message === 'object') {
          return {
            body: contact.last_message.body || '',
            type: contact.last_message.type || '',
            direction: contact.last_message.direction || '',
            source: contact.last_message.source || '',
            typeLabel: lastMessageTypeLabels[contact.last_message.type] || contact.last_message.type?.replace('TYPE_', '') || '',
            date: contact.last_message.date_added || contact.last_message.date || '',
            unread_count: contact.last_message.unread_count || 0
          };
        }
        
        // Fallback to conversations if last_message is not available
        if (Array.isArray(contact.conversations) && contact.conversations.length > 0) {
          // Sort conversations by write_date (most recent first) and get the latest one
          const sortedConversations = [...contact.conversations].sort((a, b) =>
            new Date(b.write_date || b.create_date || 0).getTime() -
            new Date(a.write_date || a.create_date || 0).getTime()
          );
          const latestConversation = sortedConversations[0];

          if (latestConversation && latestConversation.last_message_body) {
            return {
              body: latestConversation.last_message_body,
              type: latestConversation.last_message_type,
              typeLabel: lastMessageTypeLabels[latestConversation.last_message_type] || latestConversation.last_message_type,
              date: latestConversation.write_date || latestConversation.create_date,
              unread_count: latestConversation.unread_count || 0
            };
          }
        }
        return null;
      })(),
      totalPipelineValue: contact.total_pipeline_value ? `$${contact.total_pipeline_value.toFixed(2)}` : '$0.00',
      opportunities: String(contact.opportunities || 0),
      contactTags: Array.isArray(contact.contact_tags) ? contact.contact_tags : [],
      viewCalls: true,
      dateCreated: contact.date_added || new Date().toISOString(),
      // OPTIMIZATION: Use detailed data if available, otherwise show loading state
      tasks: Array.isArray(contact.tasks) ? contact.tasks : [],
      tasksCount: contact.tasks_count || 0,
      conversations: Array.isArray(contact.conversations) ? contact.conversations : [],
      conversationsCount: contact.conversations_count || 0,
      detailsFetched: contact.details_fetched || false,
      detailsLoading: detailedDataLoading[contact.id] || false,
    };
  });

  // Filtering logic for all columns (excluding user filtering which is now done server-side)
  const filteredRows = transformedContacts.filter(row => {
    // Apply existing filters
    if (filters.contactName && !row.name.toLowerCase().includes(filters.contactName.toLowerCase())) return false;
    if (filters.aiStatus.length && !filters.aiStatus.includes(row.aiStatus?.label || row.aiStatus?.text || '')) return false;
    if (filters.aiSummary.length && !filters.aiSummary.includes(row.aiSummary)) return false;
    if (filters.aiQuality.length && !filters.aiQuality.includes(row.aiQuality.label)) return false;
    if (filters.aiSales.length && !filters.aiSales.includes(row.aiSales.label)) return false;
    if (filters.crmTasks.length && !filters.crmTasks.includes(row.crmTasks.label)) return false;
    if (filters.category.length && !filters.category.includes(row.category)) return false;
    if (filters.channel.length && !filters.channel.includes(row.channel)) return false;
    if (filters.assignedTo.length && !filters.assignedTo.includes(row.assignedTo)) return false;
    if (filters.touchSummary.length) {
      // Check if any part of the touch summary contains the selected filter
      const touchSummaryLower = (row.touchSummary ?? '').toLowerCase();
      const hasMatchingTouchSummary = filters.touchSummary.some(filter => {
        if (filter === 'no_touches') {
          return touchSummaryLower === 'no_touches';
        }
        return touchSummaryLower.includes(filter.toLowerCase());
      });
      if (!hasMatchingTouchSummary) return false;
    }
    if (filters.engagementSummary.length) {
      // engagementSummary is an array of objects, match if any type in row.engagementSummary matches a selected filter
      const types = Array.isArray(row.engagementSummary) ? row.engagementSummary.map(e => e.type) : [];
      if (!filters.engagementSummary.some(type => types.includes(type))) return false;
    }
    if (filters.opportunities.min && Number(row.opportunities) < Number(filters.opportunities.min)) return false;
    if (filters.opportunities.max && Number(row.opportunities) > Number(filters.opportunities.max)) return false;
    
    // Apply new activeFilters from parent component
    if (activeFilters.aiStatus.length > 0 && !activeFilters.aiStatus.includes(row.aiStatus?.label || row.aiStatus?.text || '')) {
      return false;
    }
    
    if (activeFilters.aiQualityGrade.length > 0) {
      const qualityGrade = row.aiQuality?.label || 'No Grade';
      if (!activeFilters.aiQualityGrade.includes(qualityGrade)) {
        return false;
      }
    }
    
    if (activeFilters.aiSalesGrade.length > 0) {
      const salesGrade = row.aiSales?.label || 'No Grade';
      if (!activeFilters.aiSalesGrade.includes(salesGrade)) {
        return false;
      }
    }
    
    if (activeFilters.crmTasks.length > 0) {
      const crmTasks = row.crmTasks?.label || 'No Tasks';
      if (!activeFilters.crmTasks.includes(crmTasks)) {
        return false;
      }
    }
    
    if (activeFilters.category.length > 0 && !activeFilters.category.includes(row.category)) {
      return false;
    }
    
    if (activeFilters.channel.length > 0 && !activeFilters.channel.includes(row.channel)) {
      return false;
    }
    
    if (activeFilters.touchSummary.length > 0) {
      const touchSummary = row.touchSummary || 'no_touches';
      if (!activeFilters.touchSummary.includes(touchSummary)) {
        return false;
      }
    }
    
    return true;
  });

  // Pagination logic
  const totalRows = totalContacts;
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  // No need to slice, backend already paginates and handles user filtering
  const paginatedRows = filteredRows;

  const [, setLocation] = useLocation();

  // Debug: log the fetched contacts
  console.log('Debug info:', {
    contactsDataLength: contactsData.length,
    transformedContactsLength: transformedContacts.length,
    filteredRowsLength: filteredRows.length,
    paginatedRowsLength: paginatedRows.length,
    totalContacts,
    page,
    rowsPerPage,
    selectedUser: selectedUser || 'None',
    userFilterActive: selectedUser && selectedUser.trim() !== ""
  });

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900 p-0">
      {/* Show total contacts and loading state */}
      {/* <div className="flex items-center gap-4 px-4 pt-4 pb-2">
        <span className="text-lg font-semibold text-white">Contactss</span>
        {countLoading ? (
          <span className="text-blue-300 text-sm animate-pulse">Loading total...</span>
        ) : (
          <span className="text-slate-400 text-sm">Total: {totalContacts}</span>
        )}
        {contactsLoading && <span className="text-blue-300 text-xs animate-pulse ml-2">Loading contacts...</span>}
      </div> */}
      {/* Header with title, search bar, filter, and customize columns button */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold text-white">Contacts</span>
          {/* Real-time status indicator */}
          <div className="flex items-center gap-2">
            {isAutoRefreshing && (
              <div className="flex items-center gap-1 px-2 py-1 bg-blue-900/30 border border-blue-700 rounded-md">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                <span className="text-blue-300 text-xs">Updating...</span>
              </div>
            )}
            {lastRefreshTime && (
              <div className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded-md">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-slate-300 text-xs">
                  Updated {format(lastRefreshTime, 'HH:mm:ss')}
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2 items-center">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => {
        
                setSearch(e.target.value);
              }}
              className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-400 w-64 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {searchLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              </div>
            )}
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="flex gap-2 items-center bg-slate-900 text-slate-200 border-slate-700 px-4 py-1.5 h-9 text-sm font-medium">
                <Filter className="w-4 h-4" />
                Filters
              </Button>
            </PopoverTrigger>
            <PopoverContent className="bg-slate-900 border border-slate-700 w-[420px] p-4 shadow-2xl rounded-2xl">
              <div className="flex flex-col gap-3 max-h-[500px] overflow-y-auto">
                {/* Contact Name */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Contact Name</span>
                  <Input
                    placeholder="Contact Name"
                    value={filters.contactName}
                    onChange={e => setFilters(f => ({ ...f, contactName: e.target.value }))}
                    className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"
                  />
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, contactName: "" }))} disabled={!filters.contactName}>×</Button>
                </div>
                {/* AI Status */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">AI Status</span>
                  <Select value={filters.aiStatus[0] || ""} onValueChange={val => setFilters(f => ({ ...f, aiStatus: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {aiStatusOptions.filter(opt => opt.label !== "").map(opt => (
                        <SelectItem key={opt.label} value={opt.label}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, aiStatus: [] }))} disabled={filters.aiStatus.length === 0}>×</Button>
                </div>
                {/* AI Summary */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">AI Summary</span>
                  <Select value={filters.aiSummary[0] || ""} onValueChange={val => setFilters(f => ({ ...f, aiSummary: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {aiSummaryOptions.filter(opt => opt !== "").map(opt => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, aiSummary: [] }))} disabled={filters.aiSummary.length === 0}>×</Button>
                </div>
                {/* AI Quality */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">AI Quality</span>
                  <Select value={filters.aiQuality[0] || ""} onValueChange={val => setFilters(f => ({ ...f, aiQuality: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {aiQualityOptions.filter(opt => opt.label !== "").map(opt => (
                        <SelectItem key={opt.label} value={opt.label}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, aiQuality: [] }))} disabled={filters.aiQuality.length === 0}>×</Button>
                </div>
                {/* AI Sales */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">AI Sales</span>
                  <Select value={filters.aiSales[0] || ""} onValueChange={val => setFilters(f => ({ ...f, aiSales: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {aiSalesOptions.filter(opt => opt.label !== "").map(opt => (
                        <SelectItem key={opt.label} value={opt.label}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, aiSales: [] }))} disabled={filters.aiSales.length === 0}>×</Button>
                </div>
                {/* CRM Tasks */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">CRM Tasks</span>
                  <Select value={filters.crmTasks[0] || ""} onValueChange={val => setFilters(f => ({ ...f, crmTasks: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {crmTasksOptions.filter(opt => opt.label !== "").map(opt => (
                        <SelectItem key={opt.label} value={opt.label}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, crmTasks: [] }))} disabled={filters.crmTasks.length === 0}>×</Button>
                </div>
                {/* Category */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Category</span>
                  <Select value={filters.category[0] || ""} onValueChange={val => setFilters(f => ({ ...f, category: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {categoryOptions.filter(opt => opt !== "").map(opt => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, category: [] }))} disabled={filters.category.length === 0}>×</Button>
                </div>
                {/* Channel */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Channel</span>
                  <Select value={filters.channel[0] || ""} onValueChange={val => setFilters(f => ({ ...f, channel: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {channelOptions.filter(opt => opt !== "").map(opt => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, channel: [] }))} disabled={filters.channel.length === 0}>×</Button>
                </div>
                {/* Assigned To */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Assigned To</span>
                  <Select value={filters.assignedTo[0] || ""} onValueChange={val => setFilters(f => ({ ...f, assignedTo: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {assignedToOptions.filter(opt => opt !== "").map(opt => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, assignedTo: [] }))} disabled={filters.assignedTo.length === 0}>×</Button>
                </div>
                {/* Touch Summary */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Touch Summary</span>
                  <Select value={filters.touchSummary[0] || ""} onValueChange={val => setFilters(f => ({ ...f, touchSummary: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {touchSummaryOptions.filter(opt => opt !== "").map(opt => (
                        <SelectItem key={opt} value={opt}>
                          {opt === 'no_touches' ? 'No Touches' :
                            opt === 'PHONE CALL' ? 'Phone Call' :
                              opt === 'WEBCHAT' ? 'Web Chat' :
                                opt}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, touchSummary: [] }))} disabled={filters.touchSummary.length === 0}>×</Button>
                </div>
                {/* Engagement Summary */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Engagement</span>
                  <Select value={filters.engagementSummary[0] || ""} onValueChange={val => setFilters(f => ({ ...f, engagementSummary: val ? [val] : [] }))}>
                    <SelectTrigger className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm h-8"><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {engagementTypes.filter(opt => opt.type !== "").map(opt => (
                        <SelectItem key={opt.type} value={opt.type}>{opt.type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, engagementSummary: [] }))} disabled={filters.engagementSummary.length === 0}>×</Button>
                </div>
                {/* Opportunities */}
                <div className="flex items-center gap-2">
                  <span className="w-48 text-slate-200 text-sm">Opportunities</span>
                  <Input
                    type="number"
                    placeholder="Min"
                    value={filters.opportunities.min}
                    onChange={e => setFilters(f => ({ ...f, opportunities: { ...f.opportunities, min: e.target.value } }))}
                    className="w-20 bg-slate-800 border-slate-700 text-slate-200 text-sm h-8"
                  />
                  <span className="text-slate-400 text-xs">-</span>
                  <Input
                    type="number"
                    placeholder="Max"
                    value={filters.opportunities.max}
                    onChange={e => setFilters(f => ({ ...f, opportunities: { ...f.opportunities, max: e.target.value } }))}
                    className="w-20 bg-slate-800 border-slate-700 text-slate-200 text-sm h-8"
                  />
                  <Button variant="ghost" size="icon" className="ml-2 text-slate-500 hover:text-white" onClick={() => setFilters(f => ({ ...f, opportunities: { min: "", max: "" } }))} disabled={!filters.opportunities.min && !filters.opportunities.max}>×</Button>
                </div>
              </div>
            </PopoverContent>
          </Popover>
          {/* Manual Refresh Button */}
          <Button 
            variant="outline" 
            className="flex gap-2 items-center bg-slate-900 text-slate-200 border-slate-700 px-4 py-1.5 h-9 text-sm font-medium hover:bg-slate-800"
            onClick={() => fetchContacts(false)}
            disabled={contactsLoading || isAutoRefreshing}
          >
            <div className={`w-4 h-4 ${isAutoRefreshing ? 'animate-spin' : ''}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            Refresh
          </Button>
          {/* Customize Columns Button (existing) */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex gap-2 items-center bg-slate-900 text-slate-200 border-slate-700 px-4 py-1.5 h-9 text-sm font-medium">
                <Filter className="w-4 h-4" />
                Customize Columns
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80 bg-slate-900 border border-slate-700 p-0 mt-2 shadow-2xl rounded-lg">
              <div className="p-2 border-b border-slate-800">
                <Input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search columns..."
                  className="h-9 text-sm bg-slate-800/80 border border-slate-700 text-slate-200 placeholder:text-slate-400 focus:ring-0 focus:border-blue-500 rounded-md"
                  autoFocus
                />
              </div>
              <div className="max-h-72 overflow-y-auto py-1">
                {/* Hide All */}
                <DropdownMenuItem
                  onClick={e => { e.preventDefault(); handleToggleHideAll(); }}
                  className="flex items-center gap-2 px-3 py-1.5 text-slate-200 text-[15px] font-normal rounded-none focus:bg-slate-800 cursor-pointer group"
                >
                  <Checkbox
                    checked={visibleColumns.length === requiredColumns.length && requiredColumns.every(col => visibleColumns.includes(col))}
                    tabIndex={-1}
                    className="mr-2 border-slate-600 bg-transparent data-[state=checked]:bg-slate-900 data-[state=checked]:border-blue-500"
                  />
                  <span className="flex-1">Hide All</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-800 my-1" />
                {/* Required columns */}
                {requiredColumns.map((col) => (
                  <div key={col} className="flex items-center gap-2 px-3 py-1.5 text-slate-400 text-[15px] font-normal rounded-none opacity-60 cursor-not-allowed select-none">
                    <Checkbox checked tabIndex={-1} disabled className="mr-2 border-slate-700 bg-transparent" />
                    <span className="flex-1">{col} <span className="ml-1 text-xs">(required)</span></span>
                  </div>
                ))}
                {/* Optional columns */}
                {optionalColumns.map((col) => (
                  <DropdownMenuItem
                    key={col}
                    onClick={e => { e.preventDefault(); handleToggleColumn(col); }}
                    className="flex items-center gap-2 px-3 py-1.5 text-slate-200 text-[15px] font-normal rounded-none focus:bg-slate-800 cursor-pointer group"
                  >
                    <Checkbox
                      checked={visibleColumns.includes(col)}
                      tabIndex={-1}
                      className="mr-2 border-slate-600 bg-transparent  data-[state=checked]:border-blue-500"
                    />
                    <span className="flex-1">{col}</span>
                  </DropdownMenuItem>
                ))}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Polling Status Indicator - Removed since background sync is disabled */}

      {/* Active Filters Display */}
      {(Object.entries(filters).some(([key, value]) => {
        if (key === 'opportunities') {
          return value.min || value.max;
        }
        return Array.isArray(value) ? value.length > 0 : value;
      }) || (selectedUser && selectedUser.trim() !== "")) && (
          <div className="flex flex-wrap gap-2 px-4 py-2 border-b border-slate-800">
            {/* Selected User Filter */}
            {selectedUser && selectedUser.trim() !== "" && (
              <div className="flex items-center gap-1 px-2 py-1 bg-blue-900/50 border border-blue-700 rounded text-blue-300 text-xs">
                <span>User: {selectedUser}</span>
                <button
                  onClick={() => {
                    // This will be handled by the parent component
                    // For now, we'll just show the filter
                  }}
                  className="ml-1 text-blue-400 hover:text-blue-200"
                  title="Clear user filter (use the user dropdown above)"
                >
                  ×
                </button>
              </div>
            )}
            {filters.contactName && (
              <div className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>Contact Name: {filters.contactName}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, contactName: "" }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            )}
            {filters.aiStatus.length > 0 && filters.aiStatus.map(status => (
              <div key={status} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>AI Status: {status}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, aiStatus: f.aiStatus.filter(s => s !== status) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.aiSummary.length > 0 && filters.aiSummary.map(summary => (
              <div key={summary} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>AI Summary: {summary}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, aiSummary: f.aiSummary.filter(s => s !== summary) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.aiQuality.length > 0 && filters.aiQuality.map(quality => (
              <div key={quality} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>AI Quality: {quality}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, aiQuality: f.aiQuality.filter(q => q !== quality) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.aiSales.length > 0 && filters.aiSales.map(sales => (
              <div key={sales} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>AI Sales: {sales}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, aiSales: f.aiSales.filter(s => s !== sales) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.crmTasks.length > 0 && filters.crmTasks.map(task => (
              <div key={task} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>CRM Tasks: {task}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, crmTasks: f.crmTasks.filter(t => t !== task) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.category.length > 0 && filters.category.map(cat => (
              <div key={cat} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>Category: {cat}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, category: f.category.filter(c => c !== cat) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.channel.length > 0 && filters.channel.map(chan => (
              <div key={chan} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>Channel: {chan}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, channel: f.channel.filter(c => c !== chan) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.assignedTo.length > 0 && filters.assignedTo.map(assignee => (
              <div key={assignee} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>Assigned To: {assignee}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, assignedTo: f.assignedTo.filter(a => a !== assignee) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.touchSummary.length > 0 && filters.touchSummary.map(summary => (
              <div key={summary} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>Touch Summary: {summary}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, touchSummary: f.touchSummary.filter(s => s !== summary) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {filters.engagementSummary.length > 0 && filters.engagementSummary.map(engagement => (
              <div key={engagement} className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>Engagement: {engagement}</span>
                <button
                  onClick={() => setFilters(f => ({ ...f, engagementSummary: f.engagementSummary.filter(e => e !== engagement) }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {(filters.opportunities.min || filters.opportunities.max) && (
              <div className="flex items-center gap-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200 text-xs">
                <span>
                  Opportunities: {filters.opportunities.min || '0'} - {filters.opportunities.max || '∞'}
                </span>
                <button
                  onClick={() => setFilters(f => ({ ...f, opportunities: { min: "", max: "" } }))}
                  className="ml-1 text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            )}
            <div className="ml-auto">
              <button
                onClick={() => setFilters({
                  contactName: "",
                  aiStatus: [],
                  aiSummary: [],
                  aiQuality: [],
                  aiSales: [],
                  crmTasks: [],
                  category: [],
                  channel: [],
                  assignedTo: [],
                  touchSummary: [],
                  engagementSummary: [],
                  opportunities: { min: "", max: "" },
                })}
                className="flex items-center gap-1 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-slate-200 text-xs hover:bg-slate-600 transition-colors"
              >
                <span>×</span>
                <span>Clear Filters</span>
              </button>
            </div>
          </div>
        )}

      {loading ? (
        <div className="flex items-center justify-center p-8">
          <div className="text-slate-400">Loading contacts...</div>
        </div>
      ) : (
        <Table className="w-full min-w-[1600px] text-xs">
          <TableHeader>
            <TableRow className="border-b border-slate-800 h-10">
              {allColumns
                .filter(col => visibleColumns.includes(col))
                .sort((a, b) => {
                  // Ensure Contact Name is first, Actions is second, rest in original order
                  if (a === "Contact Name") return -1;
                  if (b === "Contact Name") return 1;
                  if (a === "Actions") return -1;
                  if (b === "Actions") return 1;
                  return 0;
                })
                .map((col) => (
                  <TableHead key={col} className="text-slate-400 whitespace-nowrap px-3 py-2 font-medium">
                    {col}
                  </TableHead>
                ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {contactsLoading ? (
              <TableRow><TableCell colSpan={columns.length}><div className="text-center text-slate-400 py-8">Loading contacts...</div></TableCell></TableRow>
            ) : paginatedRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <div className="text-center text-slate-400 py-8">
                    <div>
                      {selectedUser && selectedUser.trim() !== "" 
                        ? `No contacts found assigned to "${selectedUser}".` 
                        : "No contacts found."}
                    </div>
                    <div className="text-slate-500 text-sm mt-2">
                      Debug info: contactsData.length={contactsData.length}, 
                      transformedContacts.length={transformedContacts.length}, 
                      paginatedRows.length={paginatedRows.length}
                      {selectedUser && selectedUser.trim() !== "" && `, userFilter="${selectedUser}"`}
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              paginatedRows.map((row, i) => (
                <TableRow key={i} className="border-b border-slate-800 hover:bg-slate-800/50 h-10">
                  {/* Render only visible columns, mapping col name to cell */}
                  {allColumns
                    .filter(col => visibleColumns.includes(col))
                    .sort((a, b) => {
                      // Ensure Contact Name is first, Actions is second, rest in original order
                      if (a === "Contact Name") return -1;
                      if (b === "Contact Name") return 1;
                      if (a === "Actions") return -1;
                      if (b === "Actions") return 1;
                      return 0;
                    })
                    .map((col) => {
                      switch (col) {
                        case "Contact Name":
                          return <TableCell key={col} className="text-white font-semibold whitespace-nowrap px-3 py-2">{row.name}</TableCell>;
                        case "AI Status":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {row.aiStatus?.html ? (
                              <div 
                                className="inline-flex items-center gap-2 px-2 py-0.5 rounded-md border font-medium tracking-tight h-7 text-[11px]"
                                style={{ borderWidth: 1 }}
                                dangerouslySetInnerHTML={{ __html: row.aiStatus.html }}
                              />
                            ) : (
                              (() => { 
                                const aiStatusLabel = row.aiStatus?.label ?? ''; 
                                const p = getChipProps('aiStatus', aiStatusLabel); 
                                return (
                                  <span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}>
                                    <span className={p.iconColor}>{p.icon}</span>{aiStatusLabel}
                                  </span>
                                ); 
                              })()
                            )}
                          </TableCell>;
                        case "AI Summary":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="inline-flex items-center gap-2 px-2 py-0.5 rounded-md border border-blue-500 text-blue-300 font-medium tracking-tight h-7 text-[11px] hover:bg-blue-500/20 hover:text-blue-200"
                              onClick={() => handleOpenAiSummaryDialog(row)}
                            >
                              <Eye className="w-3 h-3" />
                              Read
                            </Button>
                          </TableCell>;
                        case "AI Quality Grade":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {(() => { 
                              const aiQualityLabel = row.aiQuality?.label ?? ''; 
                              const p = getChipProps('aiQuality', aiQualityLabel); 
                              return (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px] hover:bg-slate-700/50 cursor-pointer`}
                                  style={{ borderWidth: 1 }}
                                  onClick={() => handleOpenAiQualityGradeModal(contactsData.find(c => c.id === row.id))}
                                >
                                  <span className={p.iconColor}>{p.icon}</span>
                                  {aiQualityLabel}
                                </Button>
                              ); 
                            })()}
                          </TableCell>;
                        case "AI Sales Grade":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {(() => { 
                              const aiSalesLabel = row.aiSales?.label ?? ''; 
                              const p = getChipProps('aiSales', aiSalesLabel); 
                              return (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px] hover:bg-slate-700/50 cursor-pointer`}
                                  style={{ borderWidth: 1 }}
                                  onClick={() => handleOpenAiSalesGradeModal(contactsData.find(c => c.id === row.id))}
                                >
                                  <span className={p.iconColor}>{p.icon}</span>
                                  {aiSalesLabel}
                                </Button>
                              ); 
                            })()}
                          </TableCell>;
                        case "CRM Tasks":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {row.detailsLoading ? (
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin"></div>
                                <span className="text-slate-400 text-xs">Loading tasks...</span>
                              </div>
                            ) : Array.isArray(row.tasks) && row.tasks.length > 0 ? (
                              <div className="flex flex-col gap-1">
                                {row.tasks.slice(0, 3).map((task: any, idx: number) => (
                                  <div
                                    key={idx}
                                    className={`flex items-center justify-between px-2 py-1 rounded text-xs ${task.completed
                                        ? 'bg-green-900/50 text-green-300 border border-green-700'
                                        : task.is_overdue
                                          ? 'bg-red-900/50 text-red-300 border border-red-700'
                                          : 'bg-blue-900/50 text-blue-300 border border-blue-700'
                                      }`}
                                  >
                                    <span className="truncate max-w-[120px]">
                                      {task.title}
                                    </span>
                                    <Popover>
                                      <PopoverTrigger asChild>
                                        <Info className="w-3 h-3 text-slate-400 hover:text-slate-200 cursor-help flex-shrink-0 ml-1" />
                                      </PopoverTrigger>
                                      <PopoverContent className="w-80 p-3 bg-slate-800 border-slate-700 text-slate-200">
                                        <div className="space-y-2">
                                          <div className="font-medium text-white">{task.title}</div>
                                          {task.location_name && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Location:</span> {task.location_name}
                                            </div>
                                          )}
                                          {task.due_date && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Due:</span> {format(new Date(task.due_date), "MMMM d, yyyy")}
                                            </div>
                                          )}
                                          {task.description && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Description:</span> {task.description}
                                            </div>
                                          )}
                                          <div className="text-sm">
                                            <span className="text-slate-400">Status:</span> {task.completed ? 'Completed' : task.is_overdue ? 'Overdue' : 'Pending'}
                                          </div>
                                        </div>
                                      </PopoverContent>
                                    </Popover>
                                  </div>
                                ))}
                                {row.tasks.length > 3 && (
                                  <div className="text-xs text-slate-400">
                                    +{row.tasks.length - 3} more
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-500 text-xs">No tasks</span>
                            )}
                          </TableCell>;
                        case "Conversations":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {row.detailsLoading ? (
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin"></div>
                                <span className="text-slate-400 text-xs">Loading conversations...</span>
                              </div>
                            ) : Array.isArray(row.conversations) && row.conversations.length > 0 ? (
                              <div className="flex flex-col gap-1">
                                {row.conversations.slice(0, 3).map((conversation: any, idx: number) => (
                                  <div
                                    key={idx}
                                    className="flex items-center justify-between px-2 py-1 rounded text-xs bg-purple-900/50 text-purple-300 border border-purple-700"
                                  >
                                    <span className="truncate max-w-[120px]">
                                      {conversation.subject || conversation.conversation_id || 'Conversation'}
                                    </span>
                                    <Popover>
                                      <PopoverTrigger asChild>
                                        <Info className="w-3 h-3 text-slate-400 hover:text-slate-200 cursor-help flex-shrink-0 ml-1" />
                                      </PopoverTrigger>
                                      <PopoverContent className="w-80 p-3 bg-slate-800 border-slate-700 text-slate-200">
                                        <div className="space-y-2">
                                          <div className="font-medium text-white">
                                            {conversation.subject || 'Conversation'}
                                          </div>
                                          {conversation.location_name && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Location:</span> {conversation.location_name}
                                            </div>
                                          )}
                                          {conversation.conversation_id && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">ID:</span> {conversation.conversation_id}
                                            </div>
                                          )}
                                          {conversation.date_created && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Created:</span> {format(new Date(conversation.date_created), "MMMM d, yyyy")}
                                            </div>
                                          )}
                                          {conversation.last_message_date && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Last Message:</span> {format(new Date(conversation.last_message_date), "MMMM d, yyyy")}
                                            </div>
                                          )}
                                          {conversation.message_count && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Messages:</span> {conversation.message_count}
                                            </div>
                                          )}
                                          {conversation.last_message_type && (
                                            <div className="text-sm">
                                              <span className="text-slate-400">Last Message Type:</span>{" "}
                                              {lastMessageTypeLabels[conversation.last_message_type] || conversation.last_message_type}
                                            </div>
                                          )}
                                        </div>
                                      </PopoverContent>
                                    </Popover>
                                  </div>
                                ))}
                                {row.conversations.length > 3 && (
                                  <div className="text-xs text-slate-400">
                                    +{row.conversations.length - 3} more
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-500 text-xs">No conversations</span>
                            )}
                          </TableCell>;
                        case "Category":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const category = row.category ?? ''; const p = getChipProps('category', category); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{category}</span>); })()}</TableCell>;
                        case "Channel":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const channel = row.channel ?? ''; const p = getChipProps('channel', channel); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{channel}</span>); })()}</TableCell>;
                        case "Created By":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2"></TableCell>;
                        case "Attribution":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2"></TableCell>;
                        case "Assigned To":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2 text-slate-200">{row.assignedTo}</TableCell>;
                        case "Speed to Lead":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2"></TableCell>;
                        case "Touch Summary":
                          // Filter for outbound touches only - this would need backend support for proper filtering
                          // For now, we'll show the current data but this should be modified to show only outbound touches
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            <div className="flex flex-row flex-wrap gap-1 items-center">
                              {parseTouchSummary(row.touchSummary ?? '').map((chip, index) => (
                                <span
                                  key={index}
                                  className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${chip.border} ${chip.textColor} font-medium tracking-tight h-7 text-[11px] flex-shrink-0`}
                                  style={{ borderWidth: 1 }}
                                >
                                  <span className={chip.iconColor}>{chip.icon}</span>
                                  {chip.text}
                                </span>
                              ))}
                            </div>
                          </TableCell>;
                        case "Engagement Summary":
                          const formatEngagementType = (type: string) => {
                            if (type === "No Engagement") return "No Engagement";
                            return type.replace(/^TYPE_/, '').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
                          };
                          
                          return <TableCell key={col} className="px-3 py-2">
                            <div className="flex gap-1 flex-nowrap">
                              {Array.isArray(row.engagementSummary) && row.engagementSummary.length > 0
                                ? row.engagementSummary.slice(0, 3).map((e, idx) => (
                                  <span key={idx} className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${e.color || 'border-slate-500 text-slate-300'} font-medium tracking-tight h-7 text-[11px] whitespace-nowrap flex-shrink-0`} style={{ borderWidth: 1 }}>
                                    <span>{e.icon || '📄'}</span>
                                    {e.type === "No Engagement" ? "No Engagement" : `${e.count}x ${formatEngagementType(e.type)}`}
                                  </span>
                                ))
                                : <span className="text-slate-500 text-xs">No engagement</span>}
                              {Array.isArray(row.engagementSummary) && row.engagementSummary.length > 3 && (
                                <Popover>
                                  <PopoverTrigger asChild>
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-md border border-blue-600 text-blue-300 font-medium text-xs cursor-pointer hover:bg-blue-900/20 whitespace-nowrap flex-shrink-0">
                                      {row.engagementSummary.length - 3} more
                                    </span>
                                  </PopoverTrigger>
                                  <PopoverContent className="w-80 p-3 bg-slate-800 border-slate-700 text-slate-200">
                                    <div className="space-y-2">
                                      <div className="font-medium text-white">All Engagement</div>
                                      <div className="flex flex-wrap gap-1">
                                        {row.engagementSummary.map((e, idx) => (
                                          <span key={idx} className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${e.color || 'border-slate-500 text-slate-300'} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}>
                                            <span>{e.icon || '📄'}</span>
                                            {e.type === "No Engagement" ? "No Engagement" : `${e.count}x ${formatEngagementType(e.type)}`}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  </PopoverContent>
                                </Popover>
                              )}
                            </div>
                          </TableCell>;
                        case "Last Touch Date":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {row.lastTouchDate ? (
                              <div className="flex items-center gap-2">
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-slate-600 text-slate-300 font-medium tracking-tight h-7 text-[11px] bg-slate-800/50">
                                  <Calendar className="w-3 h-3" />
                                  {format(new Date(row.lastTouchDate), "MMM d, yyyy")}
                                </span>
                                <Popover>
                                  <PopoverTrigger asChild>
                                    <Info className="w-3 h-3 text-slate-400 hover:text-slate-200 cursor-help flex-shrink-0" />
                                  </PopoverTrigger>
                                  <PopoverContent className="w-64 p-3 bg-slate-800 border-slate-700 text-slate-200">
                                    <div className="space-y-2">
                                      <div className="font-medium text-white">Last Touch Date</div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Date:</span> {format(new Date(row.lastTouchDate), "MMMM d, yyyy")}
                                      </div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Time:</span> {format(new Date(row.lastTouchDate), "h:mm a")}
                                      </div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Full:</span> {format(new Date(row.lastTouchDate), "EEEE, MMMM d, yyyy 'at' h:mm a")}
                                      </div>
                                    </div>
                                  </PopoverContent>
                                </Popover>
                              </div>
                            ) : (
                              <span className="text-slate-500 text-xs">No touch date</span>
                            )}
                          </TableCell>;
                        case "Last Message":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            {row.lastMessage ? (
                              <div className="flex items-center gap-2">
                                <div className="flex items-center gap-1 flex-nowrap">
                                  {/* Message Direction */}
                                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-xs font-medium whitespace-nowrap ${
                                    (row.lastMessage as any).direction === 'outbound' 
                                      ? 'border-teal-500 text-teal-300' 
                                      : 'border-orange-500 text-orange-300'
                                  }`}>
                                    {(row.lastMessage as any).direction === 'outbound' ? '↗' : '↙'} {(row.lastMessage as any).direction === 'outbound' ? 'Outbound' : 'Inbound'}
                                  </span>
                                  
                                  {/* Message Type */}
                                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-xs font-medium whitespace-nowrap ${
                                    row.lastMessage.type?.includes('SMS') ? 'border-green-500 text-green-300' :
                                    row.lastMessage.type?.includes('EMAIL') ? 'border-blue-500 text-blue-300' :
                                    row.lastMessage.type?.includes('CALL') ? 'border-purple-500 text-purple-300' :
                                    row.lastMessage.type?.includes('CHAT') ? 'border-orange-500 text-orange-300' :
                                    row.lastMessage.type?.includes('VOICEMAIL') ? 'border-pink-500 text-pink-300' :
                                    'border-slate-600 text-slate-300'
                                  }`}>
                                    {row.lastMessage.type?.includes('SMS') ? '💬' : 
                                     row.lastMessage.type?.includes('EMAIL') ? '✉️' : 
                                     row.lastMessage.type?.includes('CALL') ? '📞' : 
                                     row.lastMessage.type?.includes('CHAT') ? '💭' : 
                                     row.lastMessage.type?.includes('VOICEMAIL') ? '🎙️' : 
                                     '📄'} {row.lastMessage.typeLabel || row.lastMessage.type?.replace('TYPE_', '')}
                                  </span>
                                  
                                  {/* Message Source */}
                                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-xs font-medium whitespace-nowrap ${
                                    (row.lastMessage as any).source === 'API' ? 'border-yellow-500 text-yellow-300' :
                                    (row.lastMessage as any).source === 'Automated' ? 'border-purple-500 text-purple-300' :
                                    (row.lastMessage as any).source === 'Manual' ? 'border-blue-500 text-blue-300' :
                                    'border-slate-600 text-slate-300'
                                  }`}>
                                    {(row.lastMessage as any).source === 'API' ? '&lt;&gt;' : 
                                     (row.lastMessage as any).source === 'Automated' ? '▶️' : 
                                     (row.lastMessage as any).source === 'Manual' ? '👤' : 
                                     '📋'} {(row.lastMessage as any).source || 'Unknown'}
                                  </span>
                                  
                                  {row.lastMessage.unread_count > 0 && (
                                    <span className="inline-flex items-center justify-center w-4 h-4 text-xs bg-red-500 text-white rounded-full flex-shrink-0">
                                      {row.lastMessage.unread_count}
                                    </span>
                                  )}
                                </div>
                                <Popover>
                                  <PopoverTrigger asChild>
                                    <Info className="w-3 h-3 text-slate-400 hover:text-slate-200 cursor-help flex-shrink-0" />
                                  </PopoverTrigger>
                                  <PopoverContent className="w-80 p-3 bg-slate-800 border-slate-700 text-slate-200">
                                    <div className="space-y-2">
                                      <div className="font-medium text-white">Last Message Details</div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Message:</span> {row.lastMessage.body}
                                      </div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Direction:</span> {(row.lastMessage as any).direction === 'outbound' ? 'Outbound' : 'Inbound'}
                                      </div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Type:</span> {row.lastMessage.typeLabel || row.lastMessage.type?.replace('TYPE_', '')}
                                      </div>
                                      <div className="text-sm">
                                        <span className="text-slate-400">Source:</span> {(row.lastMessage as any).source || 'Unknown'}
                                      </div>
                                      {(row.lastMessage as any).date_added && (
                                        <div className="text-sm">
                                          <span className="text-slate-400">Date:</span> {format(new Date((row.lastMessage as any).date_added), "MMMM d, yyyy 'at' h:mm a")}
                                        </div>
                                      )}
                                      {row.lastMessage.unread_count > 0 && (
                                        <div className="text-sm">
                                          <span className="text-slate-400">Unread:</span> {row.lastMessage.unread_count} messages
                                        </div>
                                      )}
                                    </div>
                                  </PopoverContent>
                                </Popover>
                              </div>
                            ) : (
                              <span className="text-slate-500 text-xs">No messages</span>
                            )}
                          </TableCell>;
                        case "Total Pipeline Value":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2 text-slate-300">{row.totalPipelineValue}</TableCell>;
                        case "Opportunities":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2 text-slate-300">{row.opportunities}</TableCell>;
                        case "Contact Tags":
                          return <TableCell key={col} className="px-3 py-2">
                            <div className="flex gap-1 flex-nowrap">
                              {row.contactTags.slice(0, 3).map((tag: any) => (
                                <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded-md border border-slate-600 text-slate-300 font-medium text-xs whitespace-nowrap flex-shrink-0">
                                  {tag}
                                </span>
                              ))}
                              {row.contactTags.length > 3 && (
                                <Popover>
                                  <PopoverTrigger asChild>
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-md border border-blue-600 text-blue-300 font-medium text-xs cursor-pointer hover:bg-blue-900/20 whitespace-nowrap flex-shrink-0">
                                      {row.contactTags.length - 3} more
                                    </span>
                                  </PopoverTrigger>
                                  <PopoverContent className="w-80 p-3 bg-slate-800 border-slate-700 text-slate-200">
                                    <div className="space-y-2">
                                      <div className="font-medium text-white">All Tags</div>
                                      <div className="flex flex-wrap gap-1">
                                        {row.contactTags.map((tag: any) => (
                                          <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded-md border border-slate-600 text-slate-300 font-medium text-xs">
                                            {tag}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  </PopoverContent>
                                </Popover>
                              )}
                            </div>
                          </TableCell>;
                        case "View Calls":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2"><button className="text-blue-400 hover:underline flex items-center gap-1 font-medium bg-transparent border-none cursor-pointer" onClick={() => setLocation(`/call-details?contact_id=${(row as any).id}&contact=${encodeURIComponent(row.name)}&date=${encodeURIComponent(row.dateCreated)}&tags=${encodeURIComponent(Array.isArray(row.contactTags) ? row.contactTags.join(',') : '')}`)}>View <ArrowUpRight className="w-4 h-4" /></button></TableCell>;
                        case "Date Created":
                          // Format as 'July 8, 2025 03:45:12 PM'
                          let dateObj = row.dateCreated;
                          if (typeof dateObj === 'string') {
                            dateObj = new Date(dateObj);
                          }
                          let formattedDate = '';
                          if (dateObj instanceof Date && !isNaN(dateObj.getTime())) {
                            formattedDate = format(dateObj, "MMMM d, yyyy hh:mm:ss a");
                          } else {
                            formattedDate = row.dateCreated;
                          }
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2 text-slate-300">{formattedDate}</TableCell>;
                        case "Actions":
                          return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                            <div className="flex items-center space-x-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                className={`text-slate-400 hover:text-white p-1 h-6 w-6 ${aiAnalysisLoading[row.id] ? 'opacity-50 cursor-not-allowed' : ''}`}
                                onClick={() => handleRunAiAnalysis(row)}
                                disabled={aiAnalysisLoading[row.id]}
                                title="Run AI Analysis"
                              >
                                {aiAnalysisLoading[row.id] ? (
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500"></div>
                                ) : (
                                  <Zap className="w-3 h-3" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className={`text-slate-400 hover:text-white p-1 h-6 w-6 ${syncDataLoading[row.id] ? 'opacity-50 cursor-not-allowed' : ''}`}
                                onClick={() => handleSyncContactData(row)}
                                disabled={syncDataLoading[row.id]}
                                title="Sync Data from GHL"
                              >
                                {syncDataLoading[row.id] ? (
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-green-500"></div>
                                ) : (
                                  <Activity className="w-3 h-3" />
                                )}
                              </Button>
                            </div>
                          </TableCell>;
                        default:
                          return null;
                      }
                    })}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}
      {/* Pagination Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-slate-800 bg-slate-900 text-slate-400 text-xs">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            className="bg-slate-900 border border-slate-700 rounded px-1 py-0.5 text-slate-200 text-xs h-7"
            value={rowsPerPage}
            onChange={e => {
              setRowsPerPage(Number(e.target.value));
              setPage(1);
            }}
          >
            {[10, 25, 50, 100].map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
        <div>
          Showing {(page - 1) * rowsPerPage + 1}-{Math.min(page * rowsPerPage, totalRows)} of {totalRows} contacts
        </div>
        <div className="flex gap-2 items-center">
          <Button
            variant="outline"
            className="border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs"
            disabled={page === 1 || contactsLoading}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span>Page {page} of {totalPages}</span>
          <Button
            variant="outline"
            className="border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs"
            disabled={page === totalPages || !hasMore || contactsLoading}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      </div>

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

      {/* AI Quality Grade Modal */}
      <AIQualityGradeModal
        open={aiQualityGradeModal.open}
        onOpenChange={(open) => setAiQualityGradeModal(prev => ({ ...prev, open }))}
        contactName={aiQualityGradeModal.contactName}
        aiQualityGrade={aiQualityGradeModal.aiQualityGrade}
        aiReasoning={aiQualityGradeModal.aiReasoning}
        aiStatus={aiQualityGradeModal.aiStatus}
        aiSummary={aiQualityGradeModal.aiSummary}
      />

      {/* AI Sales Grade Modal */}
      <Dialog open={aiSalesGradeModal.open} onOpenChange={(open) => setAiSalesGradeModal(prev => ({ ...prev, open }))}>
        <DialogContent className="max-w-4xl max-h-[90vh] bg-slate-900 border-slate-800 text-slate-50 overflow-hidden">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-green-400" />
              AI Sales Grade Analysis
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 overflow-y-auto max-h-[calc(90vh-120px)] pr-2">
            {/* Contact Name */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">{aiSalesGradeModal.contactName}</h3>
            </div>

            {/* AI Sales Grade */}
            <div>
              <h4 className="text-md font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Target className="w-4 h-4 text-green-400" />
                Sales Grade: {aiSalesGradeModal.aiSalesGrade}
              </h4>
            </div>

            {/* AI Sales Grade Reasoning */}
            <div>
              <h4 className="text-md font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" />
                Sales Grade Analysis
              </h4>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div 
                  className="text-slate-200 leading-relaxed ai-sales-reasoning-html"
                  dangerouslySetInnerHTML={{ __html: aiSalesGradeModal.aiSalesReasoning }}
                  style={{
                    lineHeight: '1.6',
                  }}
                />
              </div>
            </div>

            {/* AI Analysis Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h5 className="text-sm font-medium text-slate-400 mb-2">AI Status</h5>
                <div 
                  className="text-white font-semibold"
                  dangerouslySetInnerHTML={{ __html: aiSalesGradeModal.aiStatus || '<span style="color: #6b7280;">No status available</span>' }}
                />
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h5 className="text-sm font-medium text-slate-400 mb-2">Current Sales Grade</h5>
                <p className="text-white font-semibold">{aiSalesGradeModal.aiSalesGrade}</p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
} 