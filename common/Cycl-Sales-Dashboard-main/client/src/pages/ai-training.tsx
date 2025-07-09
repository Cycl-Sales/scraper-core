import { useState } from "react";
import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Brain, Upload, FileText, Database, BarChart3, Play, Pause } from "lucide-react";

export default function AITraining() {
  const [trainingProgress, setTrainingProgress] = useState(67);
  const [datasets] = useState([
    {
      id: 1,
      name: "Email Conversations",
      type: "Text",
      size: "2.3 MB",
      records: 1247,
      status: "active",
      lastUpdated: "2 hours ago"
    },
    {
      id: 2,
      name: "Call Transcripts",
      type: "Speech",
      size: "15.7 MB", 
      records: 589,
      status: "training",
      lastUpdated: "1 day ago"
    },
    {
      id: 3,
      name: "Customer Feedback",
      type: "Text",
      size: "890 KB",
      records: 432,
      status: "pending",
      lastUpdated: "3 days ago"
    }
  ]);

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      
      <main className="p-8 max-w-full">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">AI Training Data</h1>
          <p className="text-slate-400">Manage training datasets and improve AI model performance</p>
        </div>

        <Tabs defaultValue="datasets" className="space-y-6">
          <TabsList className="bg-slate-900 border-slate-800">
            <TabsTrigger value="datasets" className="data-[state=active]:bg-slate-800">Training Datasets</TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:bg-slate-800">Model Performance</TabsTrigger>
            <TabsTrigger value="upload" className="data-[state=active]:bg-slate-800">Upload Data</TabsTrigger>
          </TabsList>

          <TabsContent value="datasets" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Datasets List */}
              <div className="lg:col-span-3">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                      <Database className="w-5 h-5" />
                      Training Datasets
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {datasets.map((dataset) => (
                        <div key={dataset.id} className="border border-slate-700 rounded-lg p-4 hover:bg-slate-800/50 transition-colors">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <FileText className="w-5 h-5 text-blue-400" />
                              <h3 className="font-semibold text-white">{dataset.name}</h3>
                              <Badge variant={dataset.status === 'active' ? 'default' : dataset.status === 'training' ? 'secondary' : 'outline'} 
                                     className={
                                       dataset.status === 'active' ? 'bg-green-600' : 
                                       dataset.status === 'training' ? 'bg-blue-600' : 'bg-slate-600'
                                     }>
                                {dataset.status}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                                {dataset.status === 'training' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                              </Button>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">Type</p>
                              <p className="text-white">{dataset.type}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Size</p>
                              <p className="text-white">{dataset.size}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Records</p>
                              <p className="text-white">{dataset.records.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Last Updated</p>
                              <p className="text-white">{dataset.lastUpdated}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Training Status */}
              <div className="space-y-6">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                      <Brain className="w-5 h-5" />
                      Training Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-300">Current Training</span>
                        <span className="text-white">{trainingProgress}%</span>
                      </div>
                      <Progress value={trainingProgress} className="h-2" />
                    </div>
                    <Separator className="bg-slate-700" />
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">2,268</div>
                      <p className="text-sm text-slate-400">Total Records</p>
                    </div>
                    <Separator className="bg-slate-700" />
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">18.9 MB</div>
                      <p className="text-sm text-slate-400">Total Data Size</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle className="text-white">Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Button className="w-full bg-blue-600 hover:bg-blue-700">
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Dataset
                    </Button>
                    <Button variant="outline" className="w-full border-slate-700 hover:bg-slate-800">
                      Start Training
                    </Button>
                    <Button variant="outline" className="w-full border-slate-700 hover:bg-slate-800">
                      Export Model
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white">Accuracy Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-400">94.2%</div>
                    <p className="text-sm text-slate-400">Current Model</p>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white">Response Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-400">1.2s</div>
                    <p className="text-sm text-slate-400">Average</p>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white">Confidence</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-400">87%</div>
                    <p className="text-sm text-slate-400">Average</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="upload" className="space-y-6">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Upload Training Data</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="dataset-name" className="text-slate-300">Dataset Name</Label>
                  <Input
                    id="dataset-name"
                    placeholder="Enter dataset name..."
                    className="bg-slate-800 border-slate-700"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="description" className="text-slate-300">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe your training data..."
                    className="bg-slate-800 border-slate-700"
                  />
                </div>

                <div className="border-2 border-dashed border-slate-700 rounded-lg p-8 text-center hover:border-slate-600 transition-colors cursor-pointer">
                  <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-slate-300 mb-2">Drag and drop your files here</p>
                  <p className="text-sm text-slate-400 mb-4">Supports CSV, JSON, TXT files (max 50MB)</p>
                  <Button variant="outline" className="border-slate-700 hover:bg-slate-800">
                    Choose Files
                  </Button>
                </div>

                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  Upload Dataset
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}