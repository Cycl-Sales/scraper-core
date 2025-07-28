import TopNavigation from "@/components/top-navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Calendar, Copy, Edit, Mail, MessageSquare, Phone, Plus, Tag, Trash2, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link } from "wouter";

export default function ResponseTemplates() {
  const [templates] = useState([
    {
      id: 1,
      name: "Welcome New Contact",
      category: "Email",
      content: "Hi {{first_name}},\n\nWelcome to our CRM system! We're excited to have you on board. Our team will be in touch shortly to discuss how we can help you achieve your goals.\n\nBest regards,\n{{agent_name}}",
      variables: ["first_name", "agent_name"],
      usage: 47
    },
    {
      id: 2,
      name: "Follow-up Call Script",
      category: "Call",
      content: "Hi {{first_name}}, this is {{agent_name}} from {{company_name}}. I'm calling to follow up on our previous conversation about {{topic}}. Do you have a few minutes to discuss your {{service_type}} needs?",
      variables: ["first_name", "agent_name", "company_name", "topic", "service_type"],
      usage: 23
    },
    {
      id: 3,
      name: "Meeting Confirmation",
      category: "Email",
      content: "Hi {{first_name}},\n\nThis is to confirm our meeting scheduled for {{meeting_date}} at {{meeting_time}}. We'll be discussing {{meeting_topic}}.\n\nThe meeting will be held at: {{location}}\n\nLooking forward to speaking with you.\n\n{{agent_name}}",
      variables: ["first_name", "meeting_date", "meeting_time", "meeting_topic", "location", "agent_name"],
      usage: 15
    }
  ]);

  const [selectedCategory, setSelectedCategory] = useState("all");

  const filteredTemplates = selectedCategory === "all" 
    ? templates 
    : templates.filter(template => template.category.toLowerCase() === selectedCategory);

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      
      <main className="p-8 max-w-full">
        <div className="mb-4">
          <Link href="/automations">
            <Button variant="ghost" className="flex items-center gap-2 text-slate-300 hover:text-white mb-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Automations
            </Button>
          </Link>
        </div>
        {/* Page Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Response Templates</h1>
            <p className="text-slate-400">Create and manage AI-powered response templates</p>
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Create Template
          </Button>
        </div>

        {/* Filters */}
        <div className="mb-6 flex gap-4 items-center">
          <Label className="text-slate-300">Filter by category:</Label>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-48 bg-slate-800 border-slate-700">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="email">Email</SelectItem>
              <SelectItem value="call">Call Scripts</SelectItem>
              <SelectItem value="sms">SMS</SelectItem>
              <SelectItem value="chat">Chat</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Templates List */}
          <div className="lg:col-span-2 space-y-6">
            {filteredTemplates.map((template) => (
              <Card key={template.id} className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {template.category === 'Email' && <Mail className="w-4 h-4 text-blue-400" />}
                        {template.category === 'Call' && <Phone className="w-4 h-4 text-green-400" />}
                        {template.category === 'Meeting' && <Calendar className="w-4 h-4 text-purple-400" />}
                      </div>
                      <CardTitle className="text-white">{template.name}</CardTitle>
                      <Badge variant="secondary" className="bg-slate-700 text-slate-300">
                        {template.category}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-slate-400 hover:text-red-400">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label className="text-slate-300 text-sm">Template Content</Label>
                      <div className="mt-2 p-3 bg-slate-800 rounded-lg border border-slate-700">
                        <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono">
                          {template.content}
                        </pre>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Tag className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-400">Variables:</span>
                        <div className="flex gap-1">
                          {template.variables.map((variable) => (
                            <Badge key={variable} variant="outline" className="text-xs border-slate-600 text-slate-300">
                              {variable}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="text-sm text-slate-400">
                        Used {template.usage} times
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <MessageSquare className="w-5 h-5" />
                  Templates Overview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{templates.length}</div>
                  <p className="text-sm text-slate-400">Total Templates</p>
                </div>
                <Separator className="bg-slate-700" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">85</div>
                  <p className="text-sm text-slate-400">Total Usage</p>
                </div>
                <Separator className="bg-slate-700" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">12</div>
                  <p className="text-sm text-slate-400">Active Variables</p>
                </div>
              </CardContent>
            </Card>

            {/* Template Categories */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Categories</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    <span className="text-slate-300">Email Templates</span>
                  </div>
                  <Badge variant="secondary" className="bg-slate-700">2</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-green-400" />
                    <span className="text-slate-300">Call Scripts</span>
                  </div>
                  <Badge variant="secondary" className="bg-slate-700">1</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-purple-400" />
                    <span className="text-slate-300">SMS Templates</span>
                  </div>
                  <Badge variant="secondary" className="bg-slate-700">0</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Common Variables */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Common Variables</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <code className="text-blue-400">{"{{first_name}}"}</code>
                    <span className="text-slate-400">Contact's first name</span>
                  </div>
                  <div className="flex justify-between">
                    <code className="text-blue-400">{"{{last_name}}"}</code>
                    <span className="text-slate-400">Contact's last name</span>
                  </div>
                  <div className="flex justify-between">
                    <code className="text-blue-400">{"{{company}}"}</code>
                    <span className="text-slate-400">Company name</span>
                  </div>
                  <div className="flex justify-between">
                    <code className="text-blue-400">{"{{agent_name}}"}</code>
                    <span className="text-slate-400">Agent's name</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}