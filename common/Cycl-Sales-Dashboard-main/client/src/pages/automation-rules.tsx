import TopNavigation from "@/components/top-navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Clock, Edit, Mail, Pause, Phone, Play, Plus, Trash2, Users, Zap, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link } from "wouter";

export default function AutomationRules() {
  const [rules] = useState([
    {
      id: 1,
      name: "New Lead Welcome Sequence",
      trigger: "Contact Created",
      action: "Send Email",
      status: "active",
      lastRun: "2 hours ago",
      executions: 47
    },
    {
      id: 2,
      name: "Follow-up Missed Calls",
      trigger: "Missed Call",
      action: "Create Task",
      status: "active",
      lastRun: "15 minutes ago",
      executions: 23
    },
    {
      id: 3,
      name: "Lead Score Update",
      trigger: "Contact Updated",
      action: "Update Field",
      status: "paused",
      lastRun: "1 day ago",
      executions: 156
    }
  ]);

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
            <h1 className="text-3xl font-bold text-white mb-2">Automation Rules</h1>
            <p className="text-slate-400">Create and manage automated workflows for your CRM</p>
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Create Rule
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Rules List */}
          <div className="lg:col-span-3">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Zap className="w-5 h-5" />
                  Active Rules
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {rules.map((rule) => (
                    <div key={rule.id} className="border border-slate-700 rounded-lg p-4 hover:bg-slate-800/50 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-white">{rule.name}</h3>
                          <Badge variant={rule.status === 'active' ? 'default' : 'secondary'} 
                                 className={rule.status === 'active' ? 'bg-green-600' : 'bg-slate-600'}>
                            {rule.status === 'active' ? <Play className="w-3 h-3 mr-1" /> : <Pause className="w-3 h-3 mr-1" />}
                            {rule.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-red-400">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">Trigger</p>
                          <p className="text-white">{rule.trigger}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Action</p>
                          <p className="text-white">{rule.action}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Last Run</p>
                          <p className="text-white">{rule.lastRun}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Executions</p>
                          <p className="text-white">{rule.executions}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Templates */}
            <Card className="bg-slate-900 border-slate-800 mt-6">
              <CardHeader>
                <CardTitle className="text-white">Quick Templates</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border border-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-3 mb-2">
                      <Mail className="w-5 h-5 text-blue-400" />
                      <h4 className="font-semibold text-white">Email Follow-up</h4>
                    </div>
                    <p className="text-sm text-slate-400">Send automated email when a contact is added</p>
                  </div>
                  
                  <div className="border border-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-3 mb-2">
                      <Phone className="w-5 h-5 text-green-400" />
                      <h4 className="font-semibold text-white">Call Reminder</h4>
                    </div>
                    <p className="text-sm text-slate-400">Create task for missed call follow-up</p>
                  </div>
                  
                  <div className="border border-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-3 mb-2">
                      <Users className="w-5 h-5 text-purple-400" />
                      <h4 className="font-semibold text-white">Lead Assignment</h4>
                    </div>
                    <p className="text-sm text-slate-400">Auto-assign leads based on criteria</p>
                  </div>
                  
                  <div className="border border-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-3 mb-2">
                      <Clock className="w-5 h-5 text-orange-400" />
                      <h4 className="font-semibold text-white">Schedule Follow-up</h4>
                    </div>
                    <p className="text-sm text-slate-400">Schedule tasks based on contact activity</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Statistics */}
          <div className="space-y-6">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">3</div>
                  <p className="text-sm text-slate-400">Active Rules</p>
                </div>
                <Separator className="bg-slate-700" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">226</div>
                  <p className="text-sm text-slate-400">Total Executions</p>
                </div>
                <Separator className="bg-slate-700" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">97%</div>
                  <p className="text-sm text-slate-400">Success Rate</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm">
                  <p className="text-white">Welcome email sent</p>
                  <p className="text-slate-400">2 minutes ago</p>
                </div>
                <Separator className="bg-slate-700" />
                <div className="text-sm">
                  <p className="text-white">Task created for missed call</p>
                  <p className="text-slate-400">15 minutes ago</p>
                </div>
                <Separator className="bg-slate-700" />
                <div className="text-sm">
                  <p className="text-white">Lead score updated</p>
                  <p className="text-slate-400">1 hour ago</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}