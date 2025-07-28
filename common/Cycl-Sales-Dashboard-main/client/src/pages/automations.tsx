import TopNavigation from "@/components/top-navigation";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Info, Trash2, Plus, Undo2, Redo2, Save, ChevronDown } from "lucide-react";
import { useLocation } from "wouter";

// Add this type for template options
interface TemplateOption {
  id: number;
  name: string;
}

// Add explicit types for all settings state variables to fix linter errors
interface CallTranscriptSetting {
  id: number;
  enabled: boolean;
  add_user_data: boolean;
  update_contact_name: boolean;
  improve_speaker_accuracy: boolean;
  improve_word_accuracy: boolean;
  assign_speaker_labels: boolean;
  save_full_transcript: boolean;
  save_transcript_url: boolean;
}
interface ExtractDetail { id: number; question: string; }
interface CallSummarySetting {
  id: number;
  enabled: boolean;
  add_url_to_note: boolean;
  update_summary_field: boolean;
  create_contact_note: boolean;
  extract_detail_ids: ExtractDetail[];
}
interface SalesRule { id: number; rule_text: string; }
interface AiSalesScoringSetting {
  id: number;
  enabled: boolean;
  framework: string;
  rule_ids: SalesRule[];
}
interface RunContactAutomationsSetting {
  id: number;
  enabled: boolean;
  disable_for_tag: boolean;
  after_inactivity: boolean;
  inactivity_hours: number;
  after_min_duration: boolean;
  min_duration_seconds: number;
  after_message_count: boolean;
  message_count: number;
}
interface StatusOption {
  id: number;
  name: string;
  description: string;
  icon: string;
  color: string;
}
interface ContactStatusSetting {
  id: number;
  enabled: boolean;
  add_status_tag: boolean;
  update_status_field: boolean;
  status_option_ids: StatusOption[];
}
interface AiContactScoringSetting {
  id: number;
  enabled: boolean;
  use_notes_for_context: boolean;
  update_score_field: boolean;
  add_score_tag: boolean;
  examples_rules: string;
}
interface FullContactSummarySetting {
  id: number;
  enabled: boolean;
  use_call_summary_fields: boolean;
  update_status_summary: boolean;
  create_summary_note: boolean;
  delete_old_summary: boolean;
}
interface ValueExample { id: number; example_text: string; }
interface ContactValueSetting {
  id: number;
  enabled: boolean;
  update_value_field: boolean;
  use_value_override: boolean;
  value_example_ids: ValueExample[];
}
interface TaskRule { id: number; rule_text: string; }
interface TaskGenerationSetting {
  id: number;
  enabled: boolean;
  auto_complete_tasks: boolean;
  auto_reschedule_tasks: boolean;
  task_rule_ids: TaskRule[];
}

export default function Automations() {
  const [location] = useLocation();
  // Parse location_id from query string
  const locationId = (() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      return params.get('location_id') || '';
    }
    return '';
  })();
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem('selectedLocation', locationId || 'all');
  }
  // State for locations
  const [locations, setLocations] = useState<{ id: string, name: string }[]>([]);
  const [selectedLocation, setSelectedLocation] = useState(locationId || '');
  const [singleLocationName, setSingleLocationName] = useState('');

  useEffect(() => {
    if (!locationId) {
      // No location_id: fetch all locations for dropdown
      fetch("/api/installed-locations")
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data.locations)) {
            setLocations(data.locations.map((loc: any) => ({ id: loc.location_id, name: loc.location })));
          }
        });
    } else {
      // location_id present: fetch just that location's name for display
      fetch(`/api/installed-locations`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data.locations)) {
            const found = data.locations.find((loc: any) => loc.location_id === locationId);
            setSingleLocationName(found ? found.location : locationId);
          }
        });
    }
  }, [locationId]);
  // Repeat similar for salesRules, statuses, valueExamples, taskRules, etc.
  // In the UI, render and update using the nested state only

  // State for toggles, checkboxes, and inputs
  const [templateName, setTemplateName] = useState("Generic Default");
  const [isDefaultConfig, setIsDefaultConfig] = useState(false);
  const [businessContext, setBusinessContext] = useState("This company acquires residential properties that are in pre-foreclosure or facing auction. The goal is to either reinstate the mortgage with funding or purchase the property. Once acquired, the company temporarily holds the property, assigns the ...");
  const [enableTranscripts, setEnableTranscripts] = useState(true);
  const [transcriptOptions, setTranscriptOptions] = useState({
    addUserData: true,
    updateContactName: true,
    improveSpeaker: true,
    improveWord: true,
    assignLabels: true,
  });
  const [saveTranscript, setSaveTranscript] = useState({
    full: true,
    url: true,
  });
  const [callSummariesEnabled, setCallSummariesEnabled] = useState(true);
  const [saveCallSummary, setSaveCallSummary] = useState({
    addUrl: true,
    updateSummary: true,
    createNote: true,
  });
  const [aiSalesScoringEnabled, setAISalesScoringEnabled] = useState(true);
  const [runContactAutomationsEnabled, setRunContactAutomationsEnabled] = useState(true);
  const [runContactAutomations, setRunContactAutomations] = useState({
    disableTag: true,
    afterInactivity: true,
    afterMinDuration: true,
    afterMessageCount: true,
    inactivityHours: 10,
    minDuration: 20,
    messageCount: 2,
  });
  const [determineContactStatusEnabled, setDetermineContactStatusEnabled] = useState(true);
  const [saveContactStatus, setSaveContactStatus] = useState({
    addTag: true,
    updateField: true,
  });
  const [aiContactScoringEnabled, setAIContactScoringEnabled] = useState(true);
  const [useNotesForScoring, setUseNotesForScoring] = useState(true);
  const [updateScoreField, setUpdateScoreField] = useState(true);
  const [addScoreTag, setAddScoreTag] = useState(false);
  const [fullContactSummaryEnabled, setFullContactSummaryEnabled] = useState(true);
  const [useCallSummaryFields, setUseCallSummaryFields] = useState(true);
  const [updateStatusSummary, setUpdateStatusSummary] = useState(true);
  const [createSummaryNote, setCreateSummaryNote] = useState(true);
  const [deleteOldSummary, setDeleteOldSummary] = useState(true);
  const [determineContactValueEnabled, setDetermineContactValueEnabled] = useState(true);
  const [updateValueField, setUpdateValueField] = useState(true);
  const [useValueOverride, setUseValueOverride] = useState(true);
  const [taskGenerationEnabled, setTaskGenerationEnabled] = useState(true);
  const [autoCompleteTasks, setAutoCompleteTasks] = useState(true);
  const [autoRescheduleTasks, setAutoRescheduleTasks] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const [templateOptions, setTemplateOptions] = useState<TemplateOption[]>([]);
  const [templateId, setTemplateId] = useState<number | null>(null);

  useEffect(() => {
    // Fetch template options from backend
    fetch('/api/automation_template/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({})
    })
      .then(res => res.json())
      .then(data => {
        const templates = data.result?.templates || data.templates || [];
        setTemplateOptions(templates);
        if (templates.length > 0) {
          setTemplateId(templates[0].id);
          setTemplateName(templates[0].name);
        }
      });
  }, []);

  // Fetch automation template data for selected templateId
  useEffect(() => {
    console.log('templateId in useEffect:', templateId);
    if (templateId === null || !Number.isInteger(templateId) || templateId <= 0) return;
    fetch('/api/automation_template/get_by_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: templateId }),
    })
      .then(res => res.json())
      .then(data => {
        if (data && !data.error) {
          setTemplateName(data.name || '');
          setBusinessContext(data.business_context || '');
          setIsDefaultConfig(!!data.is_default);
          setCallTranscriptSettings(data.call_transcript_setting_ids || []);
          setCallSummarySettings(data.call_summary_setting_ids || []);
          setAiSalesScoringSettings(data.ai_sales_scoring_setting_ids || []);
          setRunContactAutomationsSettings(data.run_contact_automations_setting_ids || []);
          setContactStatusSettings(data.contact_status_setting_ids || []);
          setAiContactScoringSettings(data.ai_contact_scoring_setting_ids || []);
          setFullContactSummarySettings(data.full_contact_summary_setting_ids || []);
          setContactValueSettings(data.contact_value_setting_ids || []);
          setTaskGenerationSettings(data.task_generation_setting_ids || []);
        }
      });
  }, [templateId]);

  // Update dropdown change handler to never set templateId to null/undefined
  const handleTemplateChange = (val: string) => {
    const selected = templateOptions.find(t => String(t.id) === val);
    if (selected && Number.isInteger(selected.id) && selected.id > 0) {
      setTemplateId(selected.id);
      setTemplateName(selected.name);
    }
  };

  // Add state for all backend fields and nested relations
  const [callTranscriptSettings, setCallTranscriptSettings] = useState<CallTranscriptSetting[]>([]);
  const [callSummarySettings, setCallSummarySettings] = useState<CallSummarySetting[]>([]);
  const [aiSalesScoringSettings, setAiSalesScoringSettings] = useState<AiSalesScoringSetting[]>([]);
  const [runContactAutomationsSettings, setRunContactAutomationsSettings] = useState<RunContactAutomationsSetting[]>([]);
  const [contactStatusSettings, setContactStatusSettings] = useState<ContactStatusSetting[]>([]);
  const [aiContactScoringSettings, setAiContactScoringSettings] = useState<AiContactScoringSetting[]>([]);
  const [fullContactSummarySettings, setFullContactSummarySettings] = useState<FullContactSummarySetting[]>([]);
  const [contactValueSettings, setContactValueSettings] = useState<ContactValueSetting[]>([]);
  const [taskGenerationSettings, setTaskGenerationSettings] = useState<TaskGenerationSetting[]>([]);

  // In the fetch for /api/automation_template/get, map all fields and nested lists to state
  // useEffect(() => {
  //   if (!selectedLocation) return;
  //   fetch('/api/automation_template/get', {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ location_id: selectedLocation }),
  //   })
  //     .then(res => res.json())
  //     .then(data => {
  //       if (data && !data.error) {
  //         setTemplateName(data.name || '');
  //         setBusinessContext(data.business_context || '');
  //         setIsDefaultConfig(!!data.is_default);
  //         setCallTranscriptSettings(data.call_transcript_setting_ids || []);
  //         setCallSummarySettings(data.call_summary_setting_ids || []);
  //         setAiSalesScoringSettings(data.ai_sales_scoring_setting_ids || []);
  //         setRunContactAutomationsSettings(data.run_contact_automations_setting_ids || []);
  //         setContactStatusSettings(data.contact_status_setting_ids || []);
  //         setAiContactScoringSettings(data.ai_contact_scoring_setting_ids || []);
  //         setFullContactSummarySettings(data.full_contact_summary_setting_ids || []);
  //         setContactValueSettings(data.contact_value_setting_ids || []);
  //         setTaskGenerationSettings(data.task_generation_setting_ids || []);
  //       }
  //     });
  // }, [selectedLocation]);

  // Save handler
  const handleSave = () => {
    setSaveStatus(null);
    fetch('/api/automation_template/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location_id: selectedLocation,
        name: templateName,
        business_context: businessContext,
        is_default: isDefaultConfig,
        call_transcript_setting_ids: callTranscriptSettings,
        call_summary_setting_ids: callSummarySettings,
        ai_sales_scoring_setting_ids: aiSalesScoringSettings,
        run_contact_automations_setting_ids: runContactAutomationsSettings,
        contact_status_setting_ids: contactStatusSettings,
        ai_contact_scoring_setting_ids: aiContactScoringSettings,
        full_contact_summary_setting_ids: fullContactSummarySettings,
        contact_value_setting_ids: contactValueSettings,
        task_generation_setting_ids: taskGenerationSettings,
      }),
    })
      .then(res => res.json())
      .then(data => {
        if (data && !data.error) {
          setSaveStatus('Saved successfully!');
        } else {
          setSaveStatus('Error saving.');
        }
      })
      .catch(() => setSaveStatus('Error saving.'));
  };

  // Handlers for dynamic lists (add/remove)
  // Remove separate local state for extractDetails, salesRules, statuses, contactValueExamples, taskRules
  // Use only the nested state from the selected template for all dynamic lists
  // Example for Call Summaries & Extract Details:
  const summary = callSummarySettings[0] || { extract_detail_ids: [] };
  const handleAddExtractDetail = () => {
    const newDetails = [...(summary.extract_detail_ids || []), { id: Date.now(), question: '' }];
    setCallSummarySettings([{ ...summary, extract_detail_ids: newDetails }]);
  };
  const handleRemoveExtractDetail = (idx: number) => {
    const newDetails = [...(summary.extract_detail_ids || [])];
    newDetails.splice(idx, 1);
    setCallSummarySettings([{ ...summary, extract_detail_ids: newDetails }]);
  };
  const handleChangeExtractDetail = (idx: number, value: string) => {
    const newDetails = [...(summary.extract_detail_ids || [])];
    newDetails[idx] = { ...newDetails[idx], question: value };
    setCallSummarySettings([{ ...summary, extract_detail_ids: newDetails }]);
  };
  // Repeat similar for salesRules, statuses, valueExamples, taskRules, etc.
  // In the UI, render and update using the nested state only

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      <main className="p-8 max-w-full">
        {/* Template Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <Select value={templateId ? String(templateId) : ''} onValueChange={handleTemplateChange}>
              <SelectTrigger className="w-64 bg-slate-800 border-slate-700 text-slate-200 text-sm font-medium">
                <SelectValue placeholder="Select Template" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700 text-slate-200 text-sm">
                {templateOptions.map(option => (
                  <SelectItem key={option.id} value={String(option.id)}>{option.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="ghost" size="icon"><Undo2 /></Button>
            <Button variant="ghost" size="icon"><Redo2 /></Button>
            <Button className="bg-blue-600 hover:bg-blue-700" onClick={handleSave}><Save className="w-4 h-4 mr-2" />Save</Button>
            {saveStatus && <div className="mt-2 text-sm text-green-400">{saveStatus}</div>}
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column */}
          <div className="space-y-6 lg:col-span-4">
            {/* Select Locations */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle>Select Locations</CardTitle>
                <CardDescription>Select the locations you want to have included in this automation group.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!locationId ? (
                  <Select value={selectedLocation} onValueChange={v => setSelectedLocation(v)}>
                    <SelectTrigger className="w-64 bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      {locations.map(loc => (
                        <SelectItem key={loc.id} value={loc.id}>{loc.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input value={singleLocationName || locationId} readOnly className="w-64 bg-slate-800 border-slate-700 text-slate-400" />
                )}
                <div className="flex items-center gap-2">
                  <Switch checked={isDefaultConfig} onCheckedChange={setIsDefaultConfig} />
                  <Label className="text-slate-300">Make this the default configuration</Label>
                </div>
              </CardContent>
            </Card>
            {/* Business Context */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle>Business Context</CardTitle>
                <CardDescription>Use this text area to provide context for the AI to use in various tasks to help it better understand the business and provide more accurate results.</CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea value={businessContext} onChange={e => setBusinessContext(e.target.value)} className="bg-slate-800 border-slate-700 min-h-[100px]" />
              </CardContent>
            </Card>
          </div>
          {/* Right Column */}
          <div className="space-y-6 lg:col-span-8">
            {/* Call Transcripts & Analysis */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Call Transcripts & Analysis</CardTitle>
                  <CardDescription>Call transcripts are generated for every phone call, and used for many of the automations below. Transcripts with Speechmatics are less than half the cost of the native transcripts.</CardDescription>
                </div>
                <Switch checked={callTranscriptSettings[0]?.enabled || false} onCheckedChange={val => setCallTranscriptSettings([{ ...callTranscriptSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Render all transcript options as checkboxes, etc. */}
                <Label className="font-semibold text-slate-300">Default transcript improvements</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={transcriptOptions.addUserData} onChange={e => setTranscriptOptions(o => ({ ...o, addUserData: e.target.checked }))} />
                    <span>Automatically add user data <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={transcriptOptions.updateContactName} onChange={e => setTranscriptOptions(o => ({ ...o, updateContactName: e.target.checked }))} />
                    <span>Automatically update contact name <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={transcriptOptions.improveSpeaker} onChange={e => setTranscriptOptions(o => ({ ...o, improveSpeaker: e.target.checked }))} />
                    <span>Improve transcript speaker accuracy <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={transcriptOptions.improveWord} onChange={e => setTranscriptOptions(o => ({ ...o, improveWord: e.target.checked }))} />
                    <span>Improve transcript word accuracy <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={transcriptOptions.assignLabels} onChange={e => setTranscriptOptions(o => ({ ...o, assignLabels: e.target.checked }))} />
                    <span>Assign transcript speaker labels <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">If you want to save transcript results...</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveTranscript.full} onChange={e => setSaveTranscript(o => ({ ...o, full: e.target.checked }))} />
                    <span>Save the full transcript to the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_call_transcript&#125;&#125;</code> ("Multi Line") custom field <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveTranscript.url} onChange={e => setSaveTranscript(o => ({ ...o, url: e.target.checked }))} />
                    <span>Save the custom transcript page URL to the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_call_page_url&#125;&#125;</code> ("Single Line") custom field <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                </div>
              </CardContent>
            </Card>
            {/* Call Summaries */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Call Summaries</CardTitle>
                  <CardDescription>Call summaries are generated for each phone call, in accordance with your configuration below.</CardDescription>
                </div>
                <Switch checked={callSummarySettings[0]?.enabled || false} onCheckedChange={val => setCallSummarySettings([{ ...callSummarySettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">To save call summary...</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveCallSummary.addUrl} onChange={e => setSaveCallSummary(o => ({ ...o, addUrl: e.target.checked }))} />
                    <span>Add the custom transcript page URL to the note/field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveCallSummary.updateSummary} onChange={e => setSaveCallSummary(o => ({ ...o, updateSummary: e.target.checked }))} />
                    <span>Update the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_call_summary&#125;&#125;</code> ("Multi Line") custom field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveCallSummary.createNote} onChange={e => setSaveCallSummary(o => ({ ...o, createNote: e.target.checked }))} />
                    <span>Create a new contact note</span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">Extract these details...</Label>
                <div className="space-y-2">
                  {summary.extract_detail_ids.map((detail, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Input value={detail.question} onChange={e => handleChangeExtractDetail(idx, e.target.value)} className="bg-slate-800 border-slate-700" />
                      <Button variant="ghost" size="icon" onClick={() => handleRemoveExtractDetail(idx)}><Trash2 className="w-4 h-4 text-slate-400" /></Button>
                    </div>
                  ))}
                  <Button variant="ghost" className="flex items-center gap-2 text-blue-400" onClick={handleAddExtractDetail}><Plus className="w-4 h-4" />Add a detail</Button>
                </div>
              </CardContent>
            </Card>
            {/* AI Sales Scoring */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>AI Sales Scoring <span className="ml-2 px-2 py-0.5 bg-blue-900 text-blue-300 rounded text-xs font-semibold">Recommended</span></CardTitle>
                  <CardDescription>Use AI to analyze phone calls and conversations to provide a score based on your framework, rules, and examples.</CardDescription>
                </div>
                <Switch checked={aiSalesScoringSettings[0]?.enabled || false} onCheckedChange={val => setAiSalesScoringSettings([{ ...aiSalesScoringSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">Sales Framework</Label>
                <Input value="CONSULTATIVE SALES FRAMEWORK – FORECLOSURE ACQUISITIONS" className="bg-slate-800 border-slate-700" readOnly />
                <Label className="font-semibold text-slate-300">Rules & Examples</Label>
                <div className="space-y-2">
                  {/* salesRules state is removed, so this section will not render dynamic rules */}
                  <Textarea value={"An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven’t signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven’t shown strong urgency. They may say they’re interested but haven’t taken action or confirmed they’re ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I’ll think about it' with no clear follow-through. They’re in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} className="bg-slate-800 border-slate-700 min-h-[120px]" readOnly />
                </div>
              </CardContent>
            </Card>
            {/* Run Contact Automations */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Run Contact Automations <span className="ml-2 px-2 py-0.5 bg-blue-900 text-blue-300 rounded text-xs font-semibold">Recommended</span></CardTitle>
                  <CardDescription>IMPORTANT: This determines when the rest of the tasks below are run.</CardDescription>
                </div>
                <Switch checked={runContactAutomationsSettings[0]?.enabled || false} onCheckedChange={val => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">When to run...</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomations.disableTag} onChange={e => setRunContactAutomations(o => ({ ...o, disableTag: e.target.checked }))} />
                    <span>Disable evaluation for contacts with tag <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomations.afterInactivity} onChange={e => setRunContactAutomations(o => ({ ...o, afterInactivity: e.target.checked }))} />
                    <span>After hours of inactivity</span>
                    <Input type="number" value={runContactAutomations.inactivityHours} onChange={e => setRunContactAutomations(o => ({ ...o, inactivityHours: Number(e.target.value) }))} className="w-20 bg-slate-800 border-slate-700 ml-2" />
                    <span>Hours</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomations.afterMinDuration} onChange={e => setRunContactAutomations(o => ({ ...o, afterMinDuration: e.target.checked }))} />
                    <span>After minimum call duration</span>
                    <Input type="number" value={runContactAutomations.minDuration} onChange={e => setRunContactAutomations(o => ({ ...o, minDuration: Number(e.target.value) }))} className="w-20 bg-slate-800 border-slate-700 ml-2" />
                    <span>Seconds</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomations.afterMessageCount} onChange={e => setRunContactAutomations(o => ({ ...o, afterMessageCount: e.target.checked }))} />
                    <span>After count of messages</span>
                    <Input type="number" value={runContactAutomations.messageCount} onChange={e => setRunContactAutomations(o => ({ ...o, messageCount: Number(e.target.value) }))} className="w-20 bg-slate-800 border-slate-700 ml-2" />
                    <span>Messages</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            {/* Determine Contact Status */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Determine Contact Status <span className="ml-2 px-2 py-0.5 bg-blue-900 text-blue-300 rounded text-xs font-semibold">Recommended</span></CardTitle>
                  <CardDescription>Use AI analysis to automatically determine the contact status based on the conversation history.</CardDescription>
                </div>
                <Switch checked={contactStatusSettings[0]?.enabled || false} onCheckedChange={val => setContactStatusSettings([{ ...contactStatusSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">To save the result...</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveContactStatus.addTag} onChange={e => setSaveContactStatus(o => ({ ...o, addTag: e.target.checked }))} />
                    <span>Add the status name as a tag</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={saveContactStatus.updateField} onChange={e => setSaveContactStatus(o => ({ ...o, updateField: e.target.checked }))} />
                    <span>Update the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_status_result&#125;&#125;</code> custom field</span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">Choose from these statuses...</Label>
                <div className="space-y-4">
                  {/* statuses state is removed, so this section will not render dynamic statuses */}
                  <Textarea value={"An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven’t signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven’t shown strong urgency. They may say they’re interested but haven’t taken action or confirmed they’re ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I’ll think about it' with no clear follow-through. They’re in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} className="bg-slate-800 border-slate-700 min-h-[120px]" readOnly />
                </div>
              </CardContent>
            </Card>
            {/* AI Contact Scoring */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>AI Contact Scoring <span className="ml-2 px-2 py-0.5 bg-blue-900 text-blue-300 rounded text-xs font-semibold">Recommended</span></CardTitle>
                  <CardDescription>Use AI to analyze each contact and assign a quality grade (A, B, C, D, F) based on your own scoring system.</CardDescription>
                </div>
                <Switch checked={aiContactScoringSettings[0]?.enabled || false} onCheckedChange={val => setAiContactScoringSettings([{ ...aiContactScoringSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">Scoring Context</Label>
                <div className="flex items-center gap-2">
                  <input type="checkbox" checked={useNotesForScoring} onChange={e => setUseNotesForScoring(e.target.checked)} />
                  <span>Use the contact’s notes to add context <Info className="inline w-4 h-4 text-slate-400" /></span>
                </div>
                <Label className="font-semibold text-slate-300">Scoring Results</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={updateScoreField} onChange={e => setUpdateScoreField(e.target.checked)} />
                    <span>Update the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_score_grade&#125;&#125;</code> custom field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={addScoreTag} onChange={e => setAddScoreTag(e.target.checked)} />
                    <span>Add the score as a tag</span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">Examples & Rules</Label>
                <div className="space-y-2">
                  {/* contactValueExamples state is removed, so this section will not render dynamic value examples */}
                  <Textarea value={"An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven’t signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven’t shown strong urgency. They may say they’re interested but haven’t taken action or confirmed they’re ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I’ll think about it' with no clear follow-through. They’re in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} className="bg-slate-800 border-slate-700 min-h-[120px]" readOnly />
                </div>
              </CardContent>
            </Card>
            {/* Full Contact Summary */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Full Contact Summary <span className="ml-2 px-2 py-0.5 bg-blue-900 text-blue-300 rounded text-xs font-semibold">Recommended</span></CardTitle>
                  <CardDescription>Generate a full summary of the contact’s history, including previous calls, messages, notes, etc. to show in the contact notes or in the dashboard.</CardDescription>
                </div>
                <Switch checked={fullContactSummarySettings[0]?.enabled || false} onCheckedChange={val => setFullContactSummarySettings([{ ...fullContactSummarySettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">To create your summary...</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={useCallSummaryFields} onChange={e => setUseCallSummaryFields(e.target.checked)} />
                    <span>Use the fields values from Call Summaries to improve relevance <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={updateStatusSummary} onChange={e => setUpdateStatusSummary(e.target.checked)} />
                    <span>Update the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_status_summary&#125;&#125;</code> custom field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={createSummaryNote} onChange={e => setCreateSummaryNote(e.target.checked)} />
                    <span>Create a new contact note with the current summary</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={deleteOldSummary} onChange={e => setDeleteOldSummary(e.target.checked)} />
                    <span>Delete the old summary note</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            {/* Determine Contact Value */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Determine Contact Value</CardTitle>
                  <CardDescription>Automatically estimate the value of the contact based on the given context and examples. This number can be used to override the pipeline value of the contact in the dashboard.</CardDescription>
                </div>
                <Switch checked={contactValueSettings[0]?.enabled || false} onCheckedChange={val => setContactValueSettings([{ ...contactValueSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">If you’d like to determine contact’s value…</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={updateValueField} onChange={e => setUpdateValueField(e.target.checked)} />
                    <span>Update the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_value_estimate&#125;&#125;</code> ("Monetary") custom field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={useValueOverride} onChange={e => setUseValueOverride(e.target.checked)} />
                    <span>Use value as an override in the dashboard</span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">Infer value from these examples…</Label>
                <div className="space-y-2">
                  {/* contactValueExamples state is removed, so this section will not render dynamic value examples */}
                  <Textarea value={"An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven’t signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven’t shown strong urgency. They may say they’re interested but haven’t taken action or confirmed they’re ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I’ll think about it' with no clear follow-through. They’re in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} className="bg-slate-800 border-slate-700 min-h-[120px]" readOnly />
                </div>
              </CardContent>
            </Card>
            {/* Task Generation */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Task Generation</CardTitle>
                  <CardDescription>Use AI analysis to automatically manage and generate tasks based on conversation context.</CardDescription>
                </div>
                <Switch checked={taskGenerationSettings[0]?.enabled || false} onCheckedChange={val => setTaskGenerationSettings([{ ...taskGenerationSettings[0], enabled: val }])} />
              </CardHeader>
              <CardContent className="space-y-4">
                <Label className="font-semibold text-slate-300">Task Management Options</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={autoCompleteTasks} onChange={e => setAutoCompleteTasks(e.target.checked)} />
                    <span>Automatically complete tasks when resolved <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={autoRescheduleTasks} onChange={e => setAutoRescheduleTasks(e.target.checked)} />
                    <span>Automatically reschedule tasks when needed <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">Task Generation Rules</Label>
                <div className="space-y-2">
                  {/* taskRules state is removed, so this section will not render dynamic task rules */}
                  <Textarea value={"An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven’t signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven’t shown strong urgency. They may say they’re interested but haven’t taken action or confirmed they’re ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I’ll think about it' with no clear follow-through. They’re in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} className="bg-slate-800 border-slate-700 min-h-[120px]" readOnly />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
} 