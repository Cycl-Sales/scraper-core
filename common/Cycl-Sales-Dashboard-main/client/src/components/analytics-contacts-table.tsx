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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowDownLeft, ArrowUpRight, CheckSquare, ClipboardList, Code2, Filter, MessageCircle, Play, Plug, Search, User, Voicemail, Phone, Mail, MessageSquare, Ban, Info, Calendar } from "lucide-react";
import { useState } from "react";
import { useLocation } from "wouter";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select";
import { format } from "date-fns";

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

function randomPick(arr: any[]) { return arr[Math.floor(Math.random() * arr.length)]; }
const aiStatusOptions = [
  { label: "Valid Lead", color: "bg-blue-900 text-blue-300", icon: "👤" },
  { label: "Wants to Stay - Retention Path", color: "bg-green-900 text-green-300", icon: "🟢" },
  { label: "Unqualified", color: "bg-slate-800 text-slate-400", icon: "👤" },
  { label: "Not Contacted", color: "bg-slate-800 text-slate-400", icon: "👤" }
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
const touchSummaryOptions = ["No Touches", "1 Touch", "2 Touches", "3 Touches"];
const engagementTypes = [
  { type: "Call", icon: <Phone className="w-4 h-4" />, color: "border-green-400 text-green-300" },
  { type: "SMS", icon: <MessageCircle className="w-4 h-4" />, color: "border-yellow-400 text-yellow-300" },
  { type: "Email", icon: <Mail className="w-4 h-4" />, color: "border-blue-400 text-blue-300" },
  { type: "Chat", icon: <MessageSquare className="w-4 h-4" />, color: "border-purple-400 text-purple-300" },
];
function randomEngagementSummary() {
  // 20% chance of no engagement
  if (Math.random() < 0.2) return [{ type: "No Engagement", count: 0, icon: <Ban className="w-4 h-4" />, color: "border-slate-500 text-slate-400" }];
  // Otherwise, pick 1-3 random types, each with a random count 1-3
  const count = Math.floor(Math.random() * 3) + 1;
  const picked: any[] = [];
  const used = new Set();
  while (picked.length < count) {
    const idx = Math.floor(Math.random() * engagementTypes.length);
    if (!used.has(idx)) {
      used.add(idx);
      picked.push({
        type: engagementTypes[idx].type,
        count: Math.floor(Math.random() * 3) + 1,
        icon: engagementTypes[idx].icon,
        color: engagementTypes[idx].color,
      });
    }
  }
  return picked;
}
const totalPipelineValueOptions = ["$0.00", "$100.00", "$250.50", "$500.00", ""];
const contactTagOptions = [
  'preforeclosure', 'ga', 'nj', 'ca', 'mn', 'tx', 'ct', 'in', 'mo', 'mi', 'co', 'buybox', 'senior', 'possible divorce', 'added to sms', 'list a', 'list b', 'sms checked', 're add swire', 're assign sms', 'valid lead', 'contact created', 'imessage yes', 'ai off', 'textable-no', 'first manual sms sent', 'contact verified', 'signalwire phone empty', 'preforeclosure sms campaign', 'preforeclosure email campaign', 'preforeclosure sms long term'
];
function randomTags(): string[] {
  const count = Math.floor(Math.random() * 6) + 3;
  const tags: string[] = [];
  while (tags.length < count) {
    const tag = randomPick(contactTagOptions);
    if (!tags.includes(tag)) tags.push(tag);
  }
  return tags;
}
function randomDate() {
  const now = new Date();
  const past = new Date(now.getTime() - Math.floor(Math.random() * 1000000000));
  return past.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ' + past.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
const names = [
  "Katherine Marie Middleton", "Rickey J Wolf", "Johnnie S Selvey Lee", "Sandra L Carrasco", "Joal Noel Lorick", "Mark W Miller", "Marita A Belotti", "Charlange Denise Weimer", "Douglas William Trudeau", "Branden Jacob Conrad", "Anthony Joseph Bontemps", "Linda Y Webb", "Jorge E Caceres", "Teresa Odette Woodworth", "Randall A Felts", "Anastasia Jeannette Kwak", "Janine Marie Mccullom", "Gertrude L Cabarrus", "Melissa C Comrie", "Mark William Hughes", "Gaston Gregory Galvan", "Barry T Peck", "Lauren A Mancini Averitt"
];
const mockRows = Array.from({ length: 22 }, (_, i) => {
  const aiStatus = randomPick(aiStatusOptions);
  const aiSummary = randomPick(aiSummaryOptions);
  const aiQuality = randomPick(aiQualityOptions);
  const aiSales = randomPick(aiSalesOptions);
  const crmTasks = randomPick(crmTasksOptions);
  const category = randomPick(categoryOptions);
  const channel = randomPick(channelOptions);
  const assignedTo = randomPick(assignedToOptions);
  const touchSummary = randomPick(touchSummaryOptions);
  const engagementSummary = randomEngagementSummary();
  const totalPipelineValue = randomPick(totalPipelineValueOptions);
  const lastMessageTypes = [
    { type: "Outbound", color: "text-blue-400", icon: <ArrowUpRight className="w-4 h-4" /> },
    { type: "Inbound", color: "text-orange-400", icon: <ArrowDownLeft className="w-4 h-4" /> },
    { type: "SMS", color: "text-teal-300", icon: <MessageCircle className="w-4 h-4" /> },
    { type: "API", color: "text-yellow-300", icon: <Code2 className="w-4 h-4" /> },
    { type: "VM Drop", color: "text-green-400", icon: <Voicemail className="w-4 h-4" /> },
    { type: "Automated", color: "text-pink-400", icon: <Play className="w-4 h-4" /> },
    { type: "Failed", color: "text-red-400", icon: <Play className="w-4 h-4" /> }
  ];
  const lastMessage = Array.from({ length: Math.floor(Math.random() * 3) + 1 }, () => randomPick(lastMessageTypes));
  return {
    name: names[i % names.length],
    aiStatus,
    aiSummary,
    aiQuality,
    aiSales,
    crmTasks,
    category,
    channel,
    createdBy: "",
    attribution: "",
    assignedTo,
    speedToLead: "",
    touchSummary,
    engagementSummary,
    lastTouchDate: "",
    lastMessage,
    totalPipelineValue,
    opportunities: String(Math.floor(Math.random() * 6)),
    contactTags: randomTags(),
    viewCalls: true,
    dateCreated: randomDate()
  };
});

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
  "Date Created"
];

function getChipProps(type: string, value: string) {
  // Returns { border, text, iconColor, icon, bg } for each chip type/value
  switch (type) {
    case 'aiStatus':
      if (value === 'Valid Lead') return { border: 'border-blue-500', text: 'text-blue-300', iconColor: 'text-blue-300', icon: <User className="w-4 h-4" /> };
      if (value === 'Wants to Stay - Retention Path') return { border: 'border-green-500', text: 'text-green-300', iconColor: 'text-green-300', icon: <User className="w-4 h-4" /> };
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
      return { border: 'border-slate-600', text: 'text-slate-400', iconColor: 'text-slate-400', icon: <span className="text-lg">&#10005;</span> };
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
  contacts?: any[];
  loading?: boolean;
}

export default function AnalyticsContactsTable({ contacts = [], loading = false }: AnalyticsContactsTableProps) {
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const allColumns = columns;
  const requiredColumn = "Contact Name";
  const optionalColumns = allColumns.filter((col) => col !== requiredColumn);
  const [visibleColumns, setVisibleColumns] = useState<string[]>(allColumns);

  const handleToggleColumn = (col: string) => {
    if (col === requiredColumn) return;
    setVisibleColumns((prev) =>
      prev.includes(col)
        ? prev.filter((c) => c !== col)
        : [...prev, col]
    );
  }; 
  const handleToggleHideAll = () => {
    if (visibleColumns.length === 1 && visibleColumns[0] === requiredColumn) {
      setVisibleColumns([...allColumns]);
    } else {
      setVisibleColumns([requiredColumn]);
    }
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
  const transformedContacts = contacts.map((contact: any) => {
    // Map AI status
    const aiStatusMap: { [key: string]: any } = {
      'valid_lead': { label: 'Valid Lead', color: 'bg-blue-900 text-blue-300', icon: '👤' },
      'retention_path': { label: 'Wants to Stay - Retention Path', color: 'bg-green-900 text-green-300', icon: '🟢' },
      'unqualified': { label: 'Unqualified', color: 'bg-slate-800 text-slate-400', icon: '👤' },
      'not_contacted': { label: 'Not Contacted', color: 'bg-slate-800 text-slate-400', icon: '👤' }
    };
    
    // Map AI quality grades
    const aiQualityMap: { [key: string]: any } = {
      'grade_a': { label: 'Lead Grade A', color: 'bg-green-900 text-green-300' },
      'grade_b': { label: 'Lead Grade B', color: 'bg-blue-900 text-blue-300' },
      'grade_c': { label: 'Lead Grade C', color: 'bg-yellow-900 text-yellow-300' },
      'no_grade': { label: 'No Grade', color: 'bg-slate-800 text-slate-400' }
    };
    
    // Map AI sales grades
    const aiSalesMap: { [key: string]: any } = {
      'grade_a': { label: 'Sales Grade A', color: 'bg-green-900 text-green-300' },
      'grade_b': { label: 'Sales Grade B', color: 'bg-blue-900 text-blue-300' },
      'grade_c': { label: 'Sales Grade C', color: 'bg-yellow-900 text-yellow-300' },
      'grade_d': { label: 'Sales Grade D', color: 'bg-orange-900 text-orange-300' },
      'no_grade': { label: 'No Grade', color: 'bg-slate-800 text-slate-400' }
    };
    
    // Map CRM tasks
    const crmTasksMap: { [key: string]: any } = {
      'overdue': { label: '1 Overdue', color: 'bg-red-900 text-red-400' },
      'upcoming': { label: '2 Upcoming', color: 'bg-yellow-900 text-yellow-300' },
      'no_tasks': { label: 'No Tasks', color: 'bg-slate-800 text-slate-400' },
      'empty': { label: '', color: '' }
    };
    
    return {
      name: contact.name || '',
      aiStatus: aiStatusMap[contact.ai_status] || aiStatusMap.not_contacted,
      aiSummary: contact.ai_summary || 'Read',
      aiQuality: aiQualityMap[contact.ai_quality_grade] || aiQualityMap.no_grade,
      aiSales: aiSalesMap[contact.ai_sales_grade] || aiSalesMap.no_grade,
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
      // Get last message from conversations instead of old last_message field
      lastMessage: (() => {
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
      // Add tasks data from API
      tasks: Array.isArray(contact.tasks) ? contact.tasks : [],
      tasksCount: contact.tasks_count || 0,
      // Add conversations data from API
      conversations: Array.isArray(contact.conversations) ? contact.conversations : [],
      conversationsCount: contact.conversations_count || 0
    };
  });

  // Filtering logic for all columns
  const filteredRows = transformedContacts.filter(row => {
    if (filters.contactName && !row.name.toLowerCase().includes(filters.contactName.toLowerCase())) return false;
    if (filters.aiStatus.length && !filters.aiStatus.includes(row.aiStatus.label)) return false;
    if (filters.aiSummary.length && !filters.aiSummary.includes(row.aiSummary)) return false;
    if (filters.aiQuality.length && !filters.aiQuality.includes(row.aiQuality.label)) return false;
    if (filters.aiSales.length && !filters.aiSales.includes(row.aiSales.label)) return false;
    if (filters.crmTasks.length && !filters.crmTasks.includes(row.crmTasks.label)) return false;
    if (filters.category.length && !filters.category.includes(row.category)) return false;
    if (filters.channel.length && !filters.channel.includes(row.channel)) return false;
    if (filters.assignedTo.length && !filters.assignedTo.includes(row.assignedTo)) return false;
    if (filters.touchSummary.length && !filters.touchSummary.includes(row.touchSummary)) return false;
    if (filters.engagementSummary.length) {
      // engagementSummary is an array of objects, match if any type in row.engagementSummary matches a selected filter
      const types = Array.isArray(row.engagementSummary) ? row.engagementSummary.map(e => e.type) : [];
      if (!filters.engagementSummary.some(type => types.includes(type))) return false;
    }
    if (filters.opportunities.min && Number(row.opportunities) < Number(filters.opportunities.min)) return false;
    if (filters.opportunities.max && Number(row.opportunities) > Number(filters.opportunities.max)) return false;
    return true;
  });

  // Pagination logic using filteredRows
  const totalRows = filteredRows.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  const paginatedRows = filteredRows.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  const [, setLocation] = useLocation();

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900 p-0">
      {/* Header with title, filter, and customize columns button */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <span className="text-lg font-semibold text-white">Contacts</span>
        <div className="flex gap-2 items-center">
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
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
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
                    checked={visibleColumns.length === 1 && visibleColumns[0] === requiredColumn}
                    tabIndex={-1}
                    className="mr-2 border-slate-600 bg-transparent data-[state=checked]:bg-slate-900 data-[state=checked]:border-blue-500"
                  />
                  <span className="flex-1">Hide All</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-800 my-1" />
                {/* Required column */}
                <div className="flex items-center gap-2 px-3 py-1.5 text-slate-400 text-[15px] font-normal rounded-none opacity-60 cursor-not-allowed select-none">
                  <Checkbox checked tabIndex={-1} disabled className="mr-2 border-slate-700 bg-transparent" />
                  <span className="flex-1">{requiredColumn} <span className="ml-1 text-xs">(required)</span></span>
                </div>
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

      {/* Active Filters Display */}
      {Object.entries(filters).some(([key, value]) => {
        if (key === 'opportunities') {
          return value.min || value.max;
        }
        return Array.isArray(value) ? value.length > 0 : value;
      }) && (
          <div className="flex flex-wrap gap-2 px-4 py-2 border-b border-slate-800">
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
              {allColumns.filter(col => visibleColumns.includes(col)).map((col) => (
                <TableHead key={col} className="text-slate-400 whitespace-nowrap px-3 py-2 font-medium">
                  {col}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedRows.map((row, i) => (
            <TableRow key={i} className="border-b border-slate-800 hover:bg-slate-800/50 h-10">
              {/* Render only visible columns, mapping col name to cell */}
              {allColumns.filter(col => visibleColumns.includes(col)).map((col) => {
                switch (col) {
                  case "Contact Name":
                    return <TableCell key={col} className="text-white font-semibold whitespace-nowrap px-3 py-2">{row.name}</TableCell>;
                  case "AI Status":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const aiStatusLabel = row.aiStatus?.label ?? ''; const p = getChipProps('aiStatus', aiStatusLabel); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{aiStatusLabel}</span>); })()}</TableCell>;
                  case "AI Summary":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const aiSummary = row.aiSummary ?? ''; const p = getChipProps('aiSummary', "Read"); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{aiSummary}</span>); })()}</TableCell>;
                  case "AI Quality Grade":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const aiQualityLabel = row.aiQuality?.label ?? ''; const p = getChipProps('aiQuality', aiQualityLabel); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{aiQualityLabel}</span>); })()}</TableCell>;
                  case "AI Sales Grade":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const aiSalesLabel = row.aiSales?.label ?? ''; const p = getChipProps('aiSales', aiSalesLabel); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{aiSalesLabel}</span>); })()}</TableCell>;
                  case "CRM Tasks":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">
                      {Array.isArray(row.tasks) && row.tasks.length > 0 ? (
                        <div className="flex flex-col gap-1">
                          {row.tasks.slice(0, 3).map((task: any, idx: number) => (
                            <div 
                              key={idx} 
                              className={`flex items-center justify-between px-2 py-1 rounded text-xs ${
                                task.completed 
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
                      {Array.isArray(row.conversations) && row.conversations.length > 0 ? (
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
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{(() => { const p = getChipProps('touchSummary', (row.touchSummary ?? '') + ''); return (<span className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${p.border} ${p.text} font-medium tracking-tight h-7 text-[11px]`} style={{ borderWidth: 1 }}><span className={p.iconColor}>{p.icon}</span>{row.touchSummary}</span>); })()}</TableCell>;
                  case "Engagement Summary":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{
                      Array.isArray(row.engagementSummary)
                        ? row.engagementSummary.map((e, idx) => (
                          <span key={idx} className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-md border ${e.color} font-medium tracking-tight h-7 text-[11px] mr-1 mb-1`} style={{ borderWidth: 1 }}>
                            <span>{e.icon}</span>
                            {e.type === "No Engagement" ? "No Engagement" : `${e.count}x ${e.type}`}
                          </span>
                        ))
                        : null
                    }</TableCell>;
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
                          <div className="flex-1 min-w-0">
                            <div className="text-xs text-slate-200 truncate max-w-[200px]" title={row.lastMessage.body}>
                              {row.lastMessage.body}
                            </div>
                            <div className="flex items-center gap-1 mt-1">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-xs font-medium ${
                                row.lastMessage.type?.includes('SMS') ? 'border-blue-500 text-blue-300' :
                                row.lastMessage.type?.includes('EMAIL') ? 'border-green-500 text-green-300' :
                                row.lastMessage.type?.includes('CALL') ? 'border-purple-500 text-purple-300' :
                                row.lastMessage.type?.includes('CHAT') ? 'border-orange-500 text-orange-300' :
                                'border-slate-600 text-slate-300'
                              }`}>
                                {row.lastMessage.typeLabel || row.lastMessage.type}
                              </span>
                              {row.lastMessage.unread_count > 0 && (
                                <span className="inline-flex items-center justify-center w-4 h-4 text-xs bg-red-500 text-white rounded-full">
                                  {row.lastMessage.unread_count}
                                </span>
                              )}
                            </div>
                          </div>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Info className="w-3 h-3 text-slate-400 hover:text-slate-200 cursor-help flex-shrink-0" />
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-3 bg-slate-800 border-slate-700 text-slate-200">
                              <div className="space-y-2">
                                <div className="font-medium text-white">Last Message</div>
                                <div className="text-sm">
                                  <span className="text-slate-400">Message:</span> {row.lastMessage.body}
                                </div>
                                <div className="text-sm">
                                  <span className="text-slate-400">Type:</span> {row.lastMessage.typeLabel || row.lastMessage.type}
                                </div>
                                {row.lastMessage.date && (
                                  <div className="text-sm">
                                    <span className="text-slate-400">Date:</span> {format(new Date(row.lastMessage.date), "MMMM d, yyyy 'at' h:mm a")}
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
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2">{row.contactTags.map((tag: any) => <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded-md border border-slate-600 text-slate-300 font-medium text-xs mr-1 mb-1">{tag}</span>)}</TableCell>;
                  case "View Calls":
                    return <TableCell key={col} className="whitespace-nowrap px-3 py-2"><button className="text-blue-400 hover:underline flex items-center gap-1 font-medium bg-transparent border-none cursor-pointer" onClick={() => setLocation(`/call-details?contact=${encodeURIComponent(row.name)}&date=${encodeURIComponent(row.dateCreated)}&tags=${encodeURIComponent(Array.isArray(row.contactTags) ? row.contactTags.join(',') : '')}`)}>View <ArrowUpRight className="w-4 h-4" /></button></TableCell>;
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
                  default:
                    return null;
                }
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      )}
      {/* Footer: rows per page, count, pagination */}
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
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span>Page {page} of {totalPages}</span>
          <Button
            variant="outline"
            className="border-slate-700 text-slate-300 px-2 py-0.5 h-7 text-xs"
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
} 