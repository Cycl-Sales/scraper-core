import type { DashboardMetrics, Contact, Opportunity } from "@shared/schema";

// Mock dashboard metrics
export const mockDashboardMetrics: DashboardMetrics = {
  id: 1,
  totalContacts: 1247,
  totalOpportunities: 89,
  totalRevenue: 1250000.00,
  conversionRate: 12.5,
  averageDealSize: 14044.94,
  dateCalculated: new Date(),
  locationId: "demo-location"
};

// Mock contacts data
export const mockContacts: Contact[] = [
  {
    id: "contact_1",
    firstName: "John",
    lastName: "Smith",
    email: "john.smith@example.com",
    phone: "+1 (555) 123-4567",
    companyName: "Tech Solutions Inc",
    source: "Website",
    tags: ["Hot Lead", "Enterprise"],
    customFields: JSON.stringify({ industry: "Technology", budget: "50000-100000" }),
    dateCreated: new Date("2024-01-15"),
    dateUpdated: new Date("2024-01-20"),
    locationId: "demo-location"
  },
  {
    id: "contact_2",
    firstName: "Sarah",
    lastName: "Johnson",
    email: "sarah.johnson@acme.com",
    phone: "+1 (555) 234-5678",
    companyName: "Acme Corporation",
    source: "Referral",
    tags: ["Qualified", "Mid-Market"],
    customFields: JSON.stringify({ industry: "Manufacturing", budget: "25000-50000" }),
    dateCreated: new Date("2024-01-10"),
    dateUpdated: new Date("2024-01-18"),
    locationId: "demo-location"
  },
  {
    id: "contact_3",
    firstName: "Michael",
    lastName: "Brown",
    email: "michael.brown@innovate.com",
    phone: "+1 (555) 345-6789",
    companyName: "Innovate Labs",
    source: "Social Media",
    tags: ["Prospect", "Startup"],
    customFields: JSON.stringify({ industry: "Healthcare", budget: "10000-25000" }),
    dateCreated: new Date("2024-01-05"),
    dateUpdated: new Date("2024-01-15"),
    locationId: "demo-location"
  },
  {
    id: "contact_4",
    firstName: "Emily",
    lastName: "Davis",
    email: "emily.davis@global.com",
    phone: "+1 (555) 456-7890",
    companyName: "Global Enterprises",
    source: "Email Campaign",
    tags: ["Lead", "Enterprise"],
    customFields: JSON.stringify({ industry: "Finance", budget: "100000+" }),
    dateCreated: new Date("2024-01-12"),
    dateUpdated: new Date("2024-01-22"),
    locationId: "demo-location"
  },
  {
    id: "contact_5",
    firstName: "David",
    lastName: "Wilson",
    email: "david.wilson@startup.com",
    phone: "+1 (555) 567-8901",
    companyName: "StartupXYZ",
    source: "Website",
    tags: ["Hot Lead", "Startup"],
    customFields: JSON.stringify({ industry: "E-commerce", budget: "5000-10000" }),
    dateCreated: new Date("2024-01-08"),
    dateUpdated: new Date("2024-01-16"),
    locationId: "demo-location"
  }
];

// Mock opportunities data
export const mockOpportunities: Opportunity[] = [
  {
    id: "opp_1",
    name: "Enterprise CRM Implementation",
    pipelineId: "pipeline_1",
    pipelineStageId: "stage_3",
    assignedTo: "John Smith",
    monetaryValue: 75000.00,
    status: "Negotiation",
    source: "Website",
    contactId: "contact_1",
    dateCreated: new Date("2024-01-15"),
    dateUpdated: new Date("2024-01-20"),
    locationId: "demo-location"
  },
  {
    id: "opp_2",
    name: "Manufacturing Process Optimization",
    pipelineId: "pipeline_1",
    pipelineStageId: "stage_2",
    assignedTo: "Sarah Johnson",
    monetaryValue: 45000.00,
    status: "Proposal",
    source: "Referral",
    contactId: "contact_2",
    dateCreated: new Date("2024-01-10"),
    dateUpdated: new Date("2024-01-18"),
    locationId: "demo-location"
  },
  {
    id: "opp_3",
    name: "Healthcare Analytics Platform",
    pipelineId: "pipeline_1",
    pipelineStageId: "stage_1",
    assignedTo: "Michael Brown",
    monetaryValue: 25000.00,
    status: "Qualification",
    source: "Social Media",
    contactId: "contact_3",
    dateCreated: new Date("2024-01-05"),
    dateUpdated: new Date("2024-01-15"),
    locationId: "demo-location"
  },
  {
    id: "opp_4",
    name: "Financial Services Integration",
    pipelineId: "pipeline_1",
    pipelineStageId: "stage_4",
    assignedTo: "Emily Davis",
    monetaryValue: 150000.00,
    status: "Closed Won",
    source: "Email Campaign",
    contactId: "contact_4",
    dateCreated: new Date("2024-01-12"),
    dateUpdated: new Date("2024-01-22"),
    locationId: "demo-location"
  },
  {
    id: "opp_5",
    name: "E-commerce Platform Development",
    pipelineId: "pipeline_1",
    pipelineStageId: "stage_2",
    assignedTo: "David Wilson",
    monetaryValue: 15000.00,
    status: "Proposal",
    source: "Website",
    contactId: "contact_5",
    dateCreated: new Date("2024-01-08"),
    dateUpdated: new Date("2024-01-16"),
    locationId: "demo-location"
  }
];

// Mock chart data
export const mockCallData = [
  { location: "Website", volume: 45, date: new Date() },
  { location: "Social Media", volume: 32, date: new Date() },
  { location: "Referral", volume: 28, date: new Date() },
  { location: "Email", volume: 15, date: new Date() },
  { location: "Phone", volume: 12, date: new Date() },
  { location: "Other", volume: 8, date: new Date() },
];

export const mockEngagementData = [
  { userName: "Website Leads", percentage: "45.00", date: new Date() },
  { userName: "Social Media", percentage: "30.00", date: new Date() },
  { userName: "Referrals", percentage: "20.00", date: new Date() },
  { userName: "Others", percentage: "5.00", date: new Date() },
];

export const mockPipelineData = [
  { month: "Jan", value: "25000.00", date: new Date() },
  { month: "Feb", value: "32000.00", date: new Date() },
  { month: "Mar", value: "28000.00", date: new Date() },
  { month: "Apr", value: "40000.00", date: new Date() },
  { month: "May", value: "35000.00", date: new Date() },
  { month: "Jun", value: "42000.00", date: new Date() },
];

// Mock API service functions
export const mockAPI = {
  getDashboardMetrics: async (): Promise<DashboardMetrics> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockDashboardMetrics;
  },
  
  getContacts: async (): Promise<Contact[]> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockContacts;
  },
  
  getOpportunities: async (): Promise<Opportunity[]> => {
    await new Promise(resolve => setTimeout(resolve, 400));
    return mockOpportunities;
  },
  
  getCallData: async () => {
    await new Promise(resolve => setTimeout(resolve, 200));
    return mockCallData;
  },
  
  getEngagementData: async () => {
    await new Promise(resolve => setTimeout(resolve, 200));
    return mockEngagementData;
  },
  
  getPipelineData: async () => {
    await new Promise(resolve => setTimeout(resolve, 200));
    return mockPipelineData;
  }
}; 