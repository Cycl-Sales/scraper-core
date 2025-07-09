import { z } from "zod";

// User interface
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  isActive: boolean;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
}

// GoHighLevel contacts interface
export interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  companyName: string;
  source: string;
  tags: string[];
  customFields: string;
  dateCreated: Date;
  dateUpdated: Date;
  locationId: string;
}

// GoHighLevel opportunities interface
export interface Opportunity {
  id: string;
  name: string;
  pipelineId: string;
  pipelineStageId: string;
  assignedTo: string;
  monetaryValue: number;
  status: string;
  source: string;
  contactId: string;
  dateCreated: Date;
  dateUpdated: Date;
  locationId: string;
}

// GoHighLevel calendar events interface
export interface CalendarEvent {
  id: string;
  title: string;
  calendarId: string;
  contactId: string;
  startTime: Date;
  endTime: Date;
  appointmentStatus: string;
  assignedUserId: string;
  locationId: string;
  dateCreated: Date;
}

// Dashboard metrics interface
export interface DashboardMetrics {
  id: number;
  totalContacts: number;
  totalOpportunities: number;
  totalRevenue: number;
  conversionRate: number;
  averageDealSize: number;
  dateCalculated: Date;
  locationId: string;
}

// Zod schemas for validation
export const userSchema = z.object({
  username: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(6),
});

export const contactSchema = z.object({
  firstName: z.string(),
  lastName: z.string(),
  email: z.string().email(),
  phone: z.string(),
  companyName: z.string(),
  source: z.string(),
  tags: z.array(z.string()),
  customFields: z.string(),
  locationId: z.string(),
});

export const opportunitySchema = z.object({
  name: z.string(),
  pipelineId: z.string(),
  pipelineStageId: z.string(),
  assignedTo: z.string(),
  monetaryValue: z.number(),
  status: z.string(),
  source: z.string(),
  contactId: z.string(),
  locationId: z.string(),
});

export const calendarEventSchema = z.object({
  title: z.string(),
  calendarId: z.string(),
  contactId: z.string(),
  startTime: z.date(),
  endTime: z.date(),
  appointmentStatus: z.string(),
  assignedUserId: z.string(),
  locationId: z.string(),
});

// Type exports
export type InsertUser = z.infer<typeof userSchema>;
export type InsertContact = z.infer<typeof contactSchema>;
export type InsertOpportunity = z.infer<typeof opportunitySchema>;
export type InsertCalendarEvent = z.infer<typeof calendarEventSchema>;
