import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Bot, Brain, MessageSquare, Settings, Zap, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link } from "wouter";

export default function AIAssistant() {
  const [assistantName, setAssistantName] = useState("AI Assistant");
  const [personality, setPersonality] = useState("professional");
  const [responseStyle, setResponseStyle] = useState("conversational");
  const [isEnabled, setIsEnabled] = useState(true);
  const [autoRespond, setAutoRespond] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful AI assistant for a CRM system. Be professional, helpful, and concise in your responses.");

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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">AI Assistant Configuration</h1>
          <p className="text-slate-400">Configure your AI assistant's behavior and capabilities</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Settings */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Bot className="w-5 h-5" />
                  Basic Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="assistant-name" className="text-slate-300">Assistant Name</Label>
                    <Input
                      id="assistant-name"
                      value={assistantName}
                      onChange={(e) => setAssistantName(e.target.value)}
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="personality" className="text-slate-300">Personality</Label>
                    <Select value={personality} onValueChange={setPersonality}>
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="friendly">Friendly</SelectItem>
                        <SelectItem value="casual">Casual</SelectItem>
                        <SelectItem value="formal">Formal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="response-style" className="text-slate-300">Response Style</Label>
                  <Select value={responseStyle} onValueChange={setResponseStyle}>
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="conversational">Conversational</SelectItem>
                      <SelectItem value="concise">Concise</SelectItem>
                      <SelectItem value="detailed">Detailed</SelectItem>
                      <SelectItem value="bullet-points">Bullet Points</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="system-prompt" className="text-slate-300">System Prompt</Label>
                  <Textarea
                    id="system-prompt"
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    className="bg-slate-800 border-slate-700 min-h-[100px]"
                    placeholder="Define how your AI assistant should behave..."
                  />
                </div>
              </CardContent>
            </Card>

            {/* Capabilities */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Brain className="w-5 h-5" />
                  AI Capabilities
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-slate-300">Contact Assistance</Label>
                    <p className="text-sm text-slate-500">Help with contact management and data entry</p>
                  </div>
                  <Switch checked={true} />
                </div>
                <Separator className="bg-slate-700" />
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-slate-300">Call Summarization</Label>
                    <p className="text-sm text-slate-500">Automatically summarize call notes and outcomes</p>
                  </div>
                  <Switch checked={true} />
                </div>
                <Separator className="bg-slate-700" />
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-slate-300">Lead Scoring</Label>
                    <p className="text-sm text-slate-500">AI-powered lead qualification and scoring</p>
                  </div>
                  <Switch checked={false} />
                </div>
                <Separator className="bg-slate-700" />
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-slate-300">Email Generation</Label>
                    <p className="text-sm text-slate-500">Generate email templates and responses</p>
                  </div>
                  <Switch checked={true} />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Status and Quick Actions */}
          <div className="space-y-6">
            {/* Status */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Settings className="w-5 h-5" />
                  Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label className="text-slate-300">AI Assistant Enabled</Label>
                  <Switch checked={isEnabled} onCheckedChange={setIsEnabled} />
                </div>
                <Separator className="bg-slate-700" />
                <div className="flex items-center justify-between">
                  <Label className="text-slate-300">Auto-Respond</Label>
                  <Switch checked={autoRespond} onCheckedChange={setAutoRespond} />
                </div>
                <Separator className="bg-slate-700" />
                <div className="space-y-2">
                  <Label className="text-slate-300">Response Delay</Label>
                  <Select defaultValue="instant">
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="instant">Instant</SelectItem>
                      <SelectItem value="1min">1 minute</SelectItem>
                      <SelectItem value="5min">5 minutes</SelectItem>
                      <SelectItem value="15min">15 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Zap className="w-5 h-5" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Test Assistant
                </Button>
                <Button variant="outline" className="w-full border-slate-700 hover:bg-slate-800">
                  Reset to Defaults
                </Button>
                <Button variant="outline" className="w-full border-slate-700 hover:bg-slate-800">
                  Export Configuration
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8 flex justify-end">
          <Button className="bg-blue-600 hover:bg-blue-700 px-8">
            Save Configuration
          </Button>
        </div>
      </main>
    </div>
  );
}