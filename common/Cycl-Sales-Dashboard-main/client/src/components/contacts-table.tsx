import { useState, useEffect } from "react";
import { Search, Plus, Eye, Phone, Edit } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useContacts } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import type { Contact } from "@shared/schema";

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

  const filteredContacts = contacts?.filter((contact) => {
    const fullName = `${contact.firstName || ''} ${contact.lastName || ''}`.trim();
    const searchLower = searchTerm.toLowerCase();
    
    return fullName.toLowerCase().includes(searchLower) ||
           (contact.email && contact.email.toLowerCase().includes(searchLower)) ||
           (contact.phone && contact.phone.toLowerCase().includes(searchLower)) ||
           (contact.companyName && contact.companyName.toLowerCase().includes(searchLower)) ||
           (contact.source && contact.source.toLowerCase().includes(searchLower));
  }) || [];

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
                        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                          <Phone className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
