import TopNavigation from "@/components/top-navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { CYCLSALES_APP_ID } from "@/lib/constants";
import { Eye, EyeOff, Info, Plus, Redo2, Save, Trash2, Undo2, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";

// Add this type for template options
interface TemplateOption {
  id: number;
  name: string;
  parent_template_id?: number;
  is_default?: boolean;
  automation_group?: string;
  is_custom?: boolean;
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
  
  // Parse location_id from query string
  const locationId = (() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      return params.get('location_id') || '';
    }
    return '';
  })();

  // State for locations
  const [locations, setLocations] = useState<{ id: string, name: string }[]>([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [singleLocationName, setSingleLocationName] = useState('');
  const [locationsLoaded, setLocationsLoaded] = useState(false);

  // OpenAI API Key state
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [showOpenaiApiKey, setShowOpenaiApiKey] = useState(false);
  const [openaiApiKeyLoading, setOpenaiApiKeyLoading] = useState(false);
  const [openaiApiKeyError, setOpenaiApiKeyError] = useState<string | null>(null);
  const [hasOpenaiApiKey, setHasOpenaiApiKey] = useState(false);
  const [maskedOpenaiApiKey, setMaskedOpenaiApiKey] = useState<string | null>(null);

  // Initialize selectedLocation from URL or localStorage
  useEffect(() => {
    if (locationId) {
      // URL has location_id, use it and cache it
      setSelectedLocation(locationId);
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('automations_selected_location', locationId);
      }
    } else {
      // No URL location_id, try to get from localStorage
      if (typeof window !== 'undefined' && window.localStorage) {
        const cachedLocation = window.localStorage.getItem('automations_selected_location');
        if (cachedLocation) {
          setSelectedLocation(cachedLocation);
        } else {
        }
      }
    }
  }, [locationId]);

  // Cleanup localStorage when navigating away from the page
  useEffect(() => {
    // Set a flag to indicate we're on the automations page
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem('automations_page_active', 'true');
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Mark that the page was hidden
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.setItem('automations_page_was_hidden', 'true');
        }
      } else if (document.visibilityState === 'visible') {
        // Page became visible again
        if (typeof window !== 'undefined' && window.localStorage) {
          const wasHidden = window.localStorage.getItem('automations_page_was_hidden');
          const isStillOnAutomationsPage = window.location.pathname === '/automations';
          
          if (wasHidden === 'true' && !isStillOnAutomationsPage) {
            // Page was hidden and we're no longer on the automations page
            // This means we navigated away - clear the cached location
            window.localStorage.removeItem('automations_selected_location');
          }
          
          // Clear the hidden flag
          window.localStorage.removeItem('automations_page_was_hidden');
        }
      }
    };

    // Add event listener for visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Add event listener for beforeunload to clear cache when leaving the page
    const handleBeforeUnload = () => {
      // Clear the cached location when leaving the page
      if (typeof window !== 'undefined' && window.localStorage) { 
        window.localStorage.removeItem('automations_selected_location');
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup function
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
      
      // Clear the active flag and cached location when component unmounts
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem('automations_page_active');
        window.localStorage.removeItem('automations_page_was_hidden');
        window.localStorage.removeItem('automations_selected_location');
      }
    };
  }, []);

  // Update localStorage when selectedLocation changes
  useEffect(() => {
    if (selectedLocation && typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem('automations_selected_location', selectedLocation);
    }
  }, [selectedLocation]);

  // Handle location selection change
  const handleLocationChange = (locationId: string) => {
    setSelectedLocation(locationId);
    // Clear single location name when changing location
    setSingleLocationName('');
  };

  useEffect(() => {
    // Determine which location to use (URL param takes precedence)
    const effectiveLocationId = locationId || selectedLocation;
    
    if (!effectiveLocationId) {
      // No location selected: fetch all locations for dropdown
      fetch(`/api/installed-locations?appId=${CYCLSALES_APP_ID}`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data.locations)) {
            setLocations(data.locations.map((loc: any) => ({ id: loc.location_id, name: loc.location })));
            setLocationsLoaded(true);
          }
        });
    } else {
      // Location selected: fetch just that location's name for display
      fetch(`/api/installed-locations?appId=${CYCLSALES_APP_ID}`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data.locations)) {
            const found = data.locations.find((loc: any) => loc.location_id === effectiveLocationId);
            setSingleLocationName(found ? found.location : effectiveLocationId);
            
            // Also set locations for dropdown if not already loaded
            if (!locationsLoaded) {
              setLocations(data.locations.map((loc: any) => ({ id: loc.location_id, name: loc.location })));
              setLocationsLoaded(true);
            }
          }
        });
    }
  }, [locationId, selectedLocation, locationsLoaded]);
  // Repeat similar for salesRules, statuses, valueExamples, taskRules, etc.
  // In the UI, render and update using the nested state only

  // State for toggles, checkboxes, and inputs
  const [templateName, setTemplateName] = useState("Generic Default");
  const [isDefaultConfig, setIsDefaultConfig] = useState(false);
  const [businessContext, setBusinessContext] = useState("This company acquires residential properties that are in pre-foreclosure or facing auction. The goal is to either reinstate the mortgage with funding or purchase the property. Once acquired, the company temporarily holds the property, assigns the ...");
  const [saveContactStatus, setSaveContactStatus] = useState({
    addTag: true,
    updateField: true,
  });
  
  const [useNotesForScoring, setUseNotesForScoring] = useState(true);
  const [updateScoreField, setUpdateScoreField] = useState(true);
  const [addScoreTag, setAddScoreTag] = useState(false);
  const [useCallSummaryFields, setUseCallSummaryFields] = useState(true);
  const [updateStatusSummary, setUpdateStatusSummary] = useState(true);
  const [createSummaryNote, setCreateSummaryNote] = useState(true);
  const [deleteOldSummary, setDeleteOldSummary] = useState(true);
  const [updateValueField, setUpdateValueField] = useState(true);
  const [useValueOverride, setUseValueOverride] = useState(true);
  const [autoCompleteTasks, setAutoCompleteTasks] = useState(true);
  const [autoRescheduleTasks, setAutoRescheduleTasks] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const [templateOptions, setTemplateOptions] = useState<TemplateOption[]>([]);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const isInitialRender = useRef(true);

  // Load automation template and OpenAI API key when location is selected
  useEffect(() => {
    const effectId = Date.now();
    
    // Skip the first render to prevent empty API calls
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }
    
    // Only make API call if selectedLocation has a meaningful value
    if (selectedLocation && selectedLocation !== '' && selectedLocation !== 'all' && selectedLocation.length > 0) {

      const requestBody = { 
        location_id: selectedLocation,
        appId: CYCLSALES_APP_ID
      };
      
      // Double-check that we have valid data before making the request
      if (!requestBody.location_id || requestBody.location_id.trim() === '') {
        return;
      }
      
      fetch('/api/automation_template/get', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })
        .then(res => {
          return res.json();
        })
        .then(data => {
          
          // Extract the actual template data from the JSON-RPC response
          const templateData = data.result || data;
          
          if (templateData && !data.error) {
            setTemplateName(getDisplayName(templateData.name || ''));
            setBusinessContext(templateData.business_context || '');
            setIsDefaultConfig(!!templateData.is_default);
            
            // Update all the settings arrays
            setCallTranscriptSettings(templateData.call_transcript_setting_ids || []);
            setCallSummarySettings(templateData.call_summary_setting_ids || []);
            setAiSalesScoringSettings(templateData.ai_sales_scoring_setting_ids || []);
            setRunContactAutomationsSettings(templateData.run_contact_automations_setting_ids || []);
            setContactStatusSettings(templateData.contact_status_setting_ids || []);
            setAiContactScoringSettings(templateData.ai_contact_scoring_setting_ids || []);
            setFullContactSummarySettings(templateData.full_contact_summary_setting_ids || []);
            setContactValueSettings(templateData.contact_value_setting_ids || []);
            setTaskGenerationSettings(templateData.task_generation_setting_ids || []);
            
            // Update template ID if this template exists in the options
            if (templateData.id) {
              setTemplateId(templateData.id);
            }
          } else {
            // If no template found, set default values
            setTemplateName('Generic Default');
            setBusinessContext('This company acquires residential properties that are in pre-foreclosure or facing auction. The goal is to either reinstate the mortgage with funding or purchase the property. Once acquired, the company temporarily holds the property, assigns the ...');
            setIsDefaultConfig(true);
          }
        })
        .catch(error => {
          console.error('Error loading automation template for location:', error);
        });

      // Load OpenAI API key for this location
      setOpenaiApiKeyLoading(true);
      setOpenaiApiKeyError(null);
      setHasOpenaiApiKey(false);
      setMaskedOpenaiApiKey(null);
      setOpenaiApiKey('');

      fetch(`/api/location-openai-key/${selectedLocation}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
        .then(res => res.json())
        .then(data => {
          if (data.has_api_key) {
            setHasOpenaiApiKey(true);
            setMaskedOpenaiApiKey(data.masked_api_key || '••••••');
          } else {
            setHasOpenaiApiKey(false);
            setMaskedOpenaiApiKey(null);
          }
        })
        .catch(error => {
          console.error('Error loading OpenAI API key:', error);
          setOpenaiApiKeyError('Failed to load API key');
        })
        .finally(() => setOpenaiApiKeyLoading(false));
    } 
  }, [selectedLocation]);

  useEffect(() => {
    // Fetch template options from backend
    fetch('/api/automation_template/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        appId: CYCLSALES_APP_ID
      })
    })
      .then(res => res.json())
      .then(data => {
        const templates = data.result?.templates || data.templates || [];
        setTemplateOptions(templates);
        
        // If we have a selected location, try to find its template
        if (selectedLocation && selectedLocation !== 'all' && selectedLocation !== '') {
          // Find template for this location
          const locationTemplate = templates.find((t: TemplateOption) => 
            t.name && t.name.includes(selectedLocation) || 
            t.automation_group === selectedLocation
          );
          if (locationTemplate) {
            setTemplateId(locationTemplate.id);
            setTemplateName(getDisplayName(locationTemplate.name));
          } else if (templates.length > 0) {
            // Fallback to first template
            setTemplateId(templates[0].id);
            setTemplateName(getDisplayName(templates[0].name));
          }
        } else if (templates.length > 0) {
          // Default to first template
          setTemplateId(templates[0].id);
          setTemplateName(getDisplayName(templates[0].name));
        }
      });
  }, [selectedLocation]);

  // Fetch automation template data for selected templateId
  useEffect(() => {
    if (templateId === null || !Number.isInteger(templateId) || templateId <= 0) return;
    
    // Only load template by ID if we're not already loading by location
    if (selectedLocation && selectedLocation !== 'all' && selectedLocation !== '') {

      return;
    }
    
    fetch('/api/automation_template/get_by_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        id: templateId,
        appId: CYCLSALES_APP_ID
      }),
    })
      .then(res => res.json())
      .then(data => {
        // Extract the actual template data from the JSON-RPC response
        const templateData = data.result || data;
        
        if (templateData && !data.error) {
          setTemplateName(getDisplayName(templateData.name || ''));
          setBusinessContext(templateData.business_context || '');
          setIsDefaultConfig(!!templateData.is_default);
          setCallTranscriptSettings(templateData.call_transcript_setting_ids || []);
          setCallSummarySettings(templateData.call_summary_setting_ids || []);
          setAiSalesScoringSettings(templateData.ai_sales_scoring_setting_ids || []);
          setRunContactAutomationsSettings(templateData.run_contact_automations_setting_ids || []);
          setContactStatusSettings(templateData.contact_status_setting_ids || []);
          setAiContactScoringSettings(templateData.ai_contact_scoring_setting_ids || []);
          setFullContactSummarySettings(templateData.full_contact_summary_setting_ids || []);
          setContactValueSettings(templateData.contact_value_setting_ids || []);
          setTaskGenerationSettings(templateData.task_generation_setting_ids || []);
        }
      });
  }, [templateId, selectedLocation]);

  // Update dropdown change handler to never set templateId to null/undefined
  const handleTemplateChange = (val: string) => {
    const selected = templateOptions.find(t => String(t.id) === val);
    if (selected && Number.isInteger(selected.id) && selected.id > 0) {
      setTemplateId(selected.id);
      setTemplateName(getDisplayName(selected.name));
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
    
    // Validate that a location is selected
    if (!selectedLocation || selectedLocation === '' || selectedLocation === 'all') {
      setSaveStatus('❌ Please select a location before saving the template.');
      return;
    }
    
    // Check if we're editing a default template
    const currentTemplate = templateOptions.find(t => t.id === templateId);
    const isEditingDefaultTemplate = currentTemplate?.is_default;
    
    // Sync local state variables with template settings
    const updatedContactStatusSettings = contactStatusSettings.map(setting => ({
      ...setting,
      add_status_tag: saveContactStatus.addTag,
      update_status_field: saveContactStatus.updateField,
    }));
    
    const updatedAiContactScoringSettings = aiContactScoringSettings.map(setting => ({
      ...setting,
      use_notes_for_context: useNotesForScoring,
      update_score_field: updateScoreField,
      add_score_tag: addScoreTag,
    }));
    
    const updatedFullContactSummarySettings = fullContactSummarySettings.map(setting => ({
      ...setting,
      use_call_summary_fields: useCallSummaryFields,
      update_status_summary: updateStatusSummary,
      create_summary_note: createSummaryNote,
      delete_old_summary: deleteOldSummary,
    }));
    
    const updatedContactValueSettings = contactValueSettings.map(setting => ({
      ...setting,
      update_value_field: updateValueField,
      use_value_override: useValueOverride,
    }));
    
    const updatedTaskGenerationSettings = taskGenerationSettings.map(setting => ({
      ...setting,
      auto_complete_tasks: autoCompleteTasks,
      auto_reschedule_tasks: autoRescheduleTasks,
    }));
    
    // Debug the data being sent
    const requestData: any = {
      location_id: selectedLocation,
      appId: CYCLSALES_APP_ID,
      business_context: businessContext,
      is_default: isDefaultConfig,
      call_transcript_setting_ids: callTranscriptSettings,
      call_summary_setting_ids: callSummarySettings,
      ai_sales_scoring_setting_ids: aiSalesScoringSettings,
      run_contact_automations_setting_ids: runContactAutomationsSettings,
      contact_status_setting_ids: updatedContactStatusSettings,
      ai_contact_scoring_setting_ids: updatedAiContactScoringSettings,
      full_contact_summary_setting_ids: updatedFullContactSummarySettings,
      contact_value_setting_ids: updatedContactValueSettings,
      task_generation_setting_ids: updatedTaskGenerationSettings,
    };
    
    // Only include the name if we're not editing a default template
    // This allows the backend to create the proper location-specific name
    if (!isEditingDefaultTemplate) {
      requestData.name = templateName;
    }
    
    // Show saving status
    setSaveStatus('Saving...');
    
    fetch('/api/automation_template/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    })
      .then(res => res.json())
      .then(data => {
        if (data && !data.error) {
          // Check if this is a new template (has parent_template_id)
          if (data.parent_template_id) {
            setSaveStatus('✅ Custom template created successfully! Your changes are saved to a new location-specific template.');
            // Update the template ID to the new one
            if (data.id) {
              setTemplateId(data.id);
            }
            // Update the template name to show it's custom
            if (data.name) {
              setTemplateName(getDisplayName(data.name));
            }
          } else {
            setSaveStatus('✅ Template updated successfully!');
          }
          
          // Refresh the template options to include the new template
          fetch('/api/automation_template/list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              appId: CYCLSALES_APP_ID
            })
          })
            .then(res => res.json())
            .then(listData => {
              const templates = listData.result?.templates || listData.templates || [];
              setTemplateOptions(templates);
              
              // Update the current template if it was created/updated
              if (data.id) {
                const updatedTemplate = templates.find((t: TemplateOption) => t.id === data.id);
                if (updatedTemplate) {
                  setTemplateId(updatedTemplate.id);
                  setTemplateName(getDisplayName(updatedTemplate.name));
                }
              }
            });
        } else {
          setSaveStatus('❌ Error saving template: ' + (data.error || 'Unknown error'));
        }
      })
      .catch((error) => { 
        setSaveStatus('❌ Error saving template: ' + error.message);
      });
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

  // Function to clean up template name for display
  const getDisplayName = (templateName: string) => {
    // Remove location ID from template name if it exists
    // Pattern: "Location Name (location_id) - Automation Template"
    const match = templateName.match(/^(.+?)\s+\([^)]+\)\s+-\s+Automation\s+Template$/);
    if (match) {
      return match[1]; // Just return the location name
    }
    
    // For templates without location ID, remove "- Automation Template" suffix
    const simpleMatch = templateName.match(/^(.+?)\s+-\s+Automation\s+Template$/);
    if (simpleMatch) {
      return simpleMatch[1]; // Just return the location name
    }
    
    return templateName;
  };

  // Function to save OpenAI API key
  const saveOpenaiApiKey = async () => {
    if (!selectedLocation || selectedLocation === '' || selectedLocation === 'all') {
      setOpenaiApiKeyError('Please select a location first');
      return;
    }

    if (!openaiApiKey || openaiApiKey.trim() === '') {
      setOpenaiApiKeyError('Please enter an API key');
      return;
    }

    setOpenaiApiKeyLoading(true);
    setOpenaiApiKeyError(null);

    try {
      const response = await fetch(`/api/location-openai-key/${selectedLocation}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ openai_api_key: openaiApiKey }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setHasOpenaiApiKey(true);
        // Mask using first and last parts without exposing full key
        const mk = openaiApiKey.length > 11 ? `${openaiApiKey.slice(0,7)}...${openaiApiKey.slice(-4)}` : '••••••';
        setMaskedOpenaiApiKey(mk);
        setOpenaiApiKey('');
      } else {
        setOpenaiApiKeyError(data.error || 'Failed to save API key');
      }
    } catch (error) {
      setOpenaiApiKeyError('Network error while saving API key');
    } finally {
      setOpenaiApiKeyLoading(false);
    }
  };

  // Function to clear OpenAI API key
  const clearOpenaiApiKey = async () => {
    if (!selectedLocation || selectedLocation === '' || selectedLocation === 'all') return;
    setOpenaiApiKeyLoading(true);
    setOpenaiApiKeyError(null);
    try {
      const response = await fetch(`/api/location-openai-key/${selectedLocation}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ openai_api_key: '' }),
      });
      const data = await response.json();
      if (response.ok && data.success) {
        setHasOpenaiApiKey(false);
        setMaskedOpenaiApiKey(null);
        setOpenaiApiKey('');
      } else {
        setOpenaiApiKeyError(data.error || 'Failed to clear API key');
      }
    } catch (e) {
      setOpenaiApiKeyError('Network error while clearing API key');
    } finally {
      setOpenaiApiKeyLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-50 overflow-x-hidden">
      <TopNavigation />
      <main className="p-8 max-w-full">
        {/* Template Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Select value={templateId ? String(templateId) : ''} onValueChange={handleTemplateChange}>
                <SelectTrigger className="w-80 bg-slate-800 border-slate-700 text-slate-200 text-sm font-medium">
                  <SelectValue placeholder="Select Template" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700 text-slate-200 text-sm w-80">
                  {templateOptions.map(option => (
                    <SelectItem key={option.id} value={String(option.id)}>
                      <div className="flex items-center gap-2 w-full">
                        <span className="truncate">{getDisplayName(option.name)}</span>
                        {option.parent_template_id && (
                          <span className="text-xs text-blue-400 bg-blue-900 px-1 rounded">Custom</span>
                        )}
                        {option.is_default && (
                          <span className="text-xs text-green-400 bg-green-900 px-1 rounded">Default</span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {/* Show current template type indicator */}
              {templateOptions.find(t => t.id === templateId)?.parent_template_id && (
                <span className="text-xs text-blue-400 bg-blue-900 px-2 py-1 rounded font-medium">Custom Template</span>
              )}
              {templateOptions.find(t => t.id === templateId)?.is_default && (
                <span className="text-xs text-green-400 bg-green-900 px-2 py-1 rounded font-medium">Default Template</span>
              )}
            </div>
            <Button variant="ghost" size="icon"><Undo2 /></Button>
            <Button variant="ghost" size="icon"><Redo2 /></Button>
            <Button 
              className={`${!selectedLocation || selectedLocation === '' || selectedLocation === 'all' ? 'bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`} 
              onClick={handleSave}
              disabled={!selectedLocation || selectedLocation === '' || selectedLocation === 'all'}
            >
              <Save className="w-4 h-4 mr-2" />Save
            </Button>
            {saveStatus && <div className="mt-2 text-sm text-green-400">{saveStatus}</div>}
          </div>
          
          {/* Location Indicator */}
          {selectedLocation && selectedLocation !== 'all' && (
            <div className="flex items-center gap-2 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <div className="text-sm">
                <span className="text-blue-300">Editing:</span>
                <span className="text-blue-100 font-medium ml-1">
                  {singleLocationName || selectedLocation}
                </span>
                {singleLocationName && singleLocationName !== selectedLocation && (
                  <span className="text-blue-400 text-xs ml-1">(ID: {selectedLocation})</span>
                )}
              </div>
            </div>
          )}
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
                <Select value={selectedLocation} onValueChange={handleLocationChange}>
                  <SelectTrigger className="w-64 bg-slate-800 border-slate-700">
                    <SelectValue placeholder="Select a location" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {locations.map(loc => (
                      <SelectItem key={loc.id} value={loc.id}>{loc.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
            {/* OpenAI API Key */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle>OpenAI API Key</CardTitle>
                <CardDescription>Enter your OpenAI API key to enable AI-powered features like call analysis, contact scoring, and automated summaries.</CardDescription>
              </CardHeader>
              <CardContent>
                {hasOpenaiApiKey && (
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm text-slate-300">Current key: <span className="font-mono text-slate-200">{maskedOpenaiApiKey}</span></div>
                    <Button variant="ghost" size="sm" onClick={clearOpenaiApiKey} disabled={openaiApiKeyLoading} className="text-red-300 hover:text-red-200">
                      <XCircle className="w-4 h-4 mr-1" /> Clear Key
                    </Button>
                  </div>
                )}
                <div className="relative">
                  <Input
                    type={showOpenaiApiKey ? "text" : "password"}
                    value={openaiApiKey}
                    onChange={(e) => setOpenaiApiKey(e.target.value)}
                    placeholder={hasOpenaiApiKey ? "Enter new key to replace existing" : "sk-..."}
                    className="bg-slate-800 border-slate-700 pr-10"
                    disabled={openaiApiKeyLoading}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full px-3 hover:bg-slate-800"
                    onClick={() => setShowOpenaiApiKey(!showOpenaiApiKey)}
                    disabled={openaiApiKeyLoading}
                  >
                    {showOpenaiApiKey ? (
                      <EyeOff className="h-4 w-4 text-slate-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-slate-400" />
                    )}
                  </Button>
                </div>
                {openaiApiKeyError && (
                  <p className="text-xs text-red-400 mt-2">{openaiApiKeyError}</p>
                )}
                <p className="text-xs text-slate-400 mt-2">
                  Your API key is stored with your location and used by backend services for AI features.
                </p>
                <div className="flex justify-end mt-4">
                  <Button
                    onClick={saveOpenaiApiKey}
                    disabled={openaiApiKeyLoading || !openaiApiKey.trim() || !selectedLocation || selectedLocation === '' || selectedLocation === 'all'}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {openaiApiKeyLoading ? 'Saving...' : hasOpenaiApiKey ? 'Replace API Key' : 'Save API Key'}
                  </Button>
                </div>
              </CardContent>
            </Card>
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
                    <input type="checkbox" checked={callTranscriptSettings[0]?.add_user_data || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], add_user_data: e.target.checked }])} />
                    <span>Automatically add user data <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callTranscriptSettings[0]?.update_contact_name || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], update_contact_name: e.target.checked }])} />
                    <span>Automatically update contact name <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callTranscriptSettings[0]?.improve_speaker_accuracy || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], improve_speaker_accuracy: e.target.checked }])} />
                    <span>Improve transcript speaker accuracy <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callTranscriptSettings[0]?.improve_word_accuracy || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], improve_word_accuracy: e.target.checked }])} />
                    <span>Improve transcript word accuracy <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callTranscriptSettings[0]?.assign_speaker_labels || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], assign_speaker_labels: e.target.checked }])} />
                    <span>Assign transcript speaker labels <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">If you want to save transcript results...</Label>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callTranscriptSettings[0]?.save_full_transcript || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], save_full_transcript: e.target.checked }])} />
                    <span>Save the full transcript to the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_call_transcript&#125;&#125;</code> ("Multi Line") custom field <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callTranscriptSettings[0]?.save_transcript_url || false} onChange={e => setCallTranscriptSettings([{ ...callTranscriptSettings[0], save_transcript_url: e.target.checked }])} />
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
                    <input type="checkbox" checked={callSummarySettings[0]?.add_url_to_note || false} onChange={e => setCallSummarySettings([{ ...callSummarySettings[0], add_url_to_note: e.target.checked }])} />
                    <span>Add the custom transcript page URL to the note/field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callSummarySettings[0]?.update_summary_field || false} onChange={e => setCallSummarySettings([{ ...callSummarySettings[0], update_summary_field: e.target.checked }])} />
                    <span>Update the <code className="bg-slate-800 px-1 rounded">&#123;&#123;contact.last_call_summary&#125;&#125;</code> ("Multi Line") custom field</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={callSummarySettings[0]?.create_contact_note || false} onChange={e => setCallSummarySettings([{ ...callSummarySettings[0], create_contact_note: e.target.checked }])} />
                    <span>Create a new contact note</span>
                  </div>
                </div>
                <Separator />
                <Label className="font-semibold text-slate-300">Extract these details...</Label>
                <div className="space-y-2">
                  {callSummarySettings[0]?.extract_detail_ids?.map((detail, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Input value={detail.question} onChange={e => handleChangeExtractDetail(idx, e.target.value)} className="bg-slate-800 border-slate-700" />
                      <Button variant="ghost" size="icon" onClick={() => handleRemoveExtractDetail(idx)}><Trash2 className="w-4 h-4 text-slate-400" /></Button>
                    </div>
                  )) || []}
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
                <Input 
                  value={aiSalesScoringSettings[0]?.framework || "CONSULTATIVE SALES FRAMEWORK – BUSINESS ACQUISITIONS"} 
                  onChange={e => setAiSalesScoringSettings([{ ...aiSalesScoringSettings[0], framework: e.target.value }])}
                  className="bg-slate-800 border-slate-700" 
                />
                <Label className="font-semibold text-slate-300">Rules & Examples</Label>
                <div className="space-y-2">
                  {/* salesRules state is removed, so this section will not render dynamic rules */}
                  <Textarea 
                    value={aiSalesScoringSettings[0]?.rule_ids?.[0]?.rule_text || "An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven't signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven't shown strong urgency. They may say they're interested but haven't taken action or confirmed they're ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I'll think about it' with no clear follow-through. They're in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} 
                    onChange={e => {
                      const updatedRules = [...(aiSalesScoringSettings[0]?.rule_ids || [])];
                      if (updatedRules.length > 0) {
                        updatedRules[0] = { ...updatedRules[0], rule_text: e.target.value };
                      } else {
                        updatedRules.push({ id: Date.now(), rule_text: e.target.value });
                      }
                      setAiSalesScoringSettings([{ ...aiSalesScoringSettings[0], rule_ids: updatedRules }]);
                    }}
                    className="bg-slate-800 border-slate-700 min-h-[120px]" 
                  />
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
                    <input type="checkbox" checked={runContactAutomationsSettings[0]?.disable_for_tag || false} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], disable_for_tag: e.target.checked }])} />
                    <span>Disable evaluation for contacts with tag <Info className="inline w-4 h-4 text-slate-400" /></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomationsSettings[0]?.after_inactivity || false} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], after_inactivity: e.target.checked }])} />
                    <span>After hours of inactivity</span>
                    <Input type="number" value={runContactAutomationsSettings[0]?.inactivity_hours || 10} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], inactivity_hours: Number(e.target.value) }])} className="w-20 bg-slate-800 border-slate-700 ml-2" />
                    <span>Hours</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomationsSettings[0]?.after_min_duration || false} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], after_min_duration: e.target.checked }])} />
                    <span>After minimum call duration</span>
                    <Input type="number" value={runContactAutomationsSettings[0]?.min_duration_seconds || 20} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], min_duration_seconds: Number(e.target.value) }])} className="w-20 bg-slate-800 border-slate-700 ml-2" />
                    <span>Seconds</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={runContactAutomationsSettings[0]?.after_message_count || false} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], after_message_count: e.target.checked }])} />
                    <span>After count of messages</span>
                    <Input type="number" value={runContactAutomationsSettings[0]?.message_count || 2} onChange={e => setRunContactAutomationsSettings([{ ...runContactAutomationsSettings[0], message_count: Number(e.target.value) }])} className="w-20 bg-slate-800 border-slate-700 ml-2" />
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
                  <Textarea 
                    value={contactStatusSettings[0]?.status_option_ids?.[0]?.description || "An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven't signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven't shown strong urgency. They may say they're interested but haven't taken action or confirmed they're ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I'll think about it' with no clear follow-through. They're in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} 
                    onChange={e => {
                      const updatedOptions = [...(contactStatusSettings[0]?.status_option_ids || [])];
                      if (updatedOptions.length > 0) {
                        updatedOptions[0] = { ...updatedOptions[0], description: e.target.value };
                      } else {
                        updatedOptions.push({ id: Date.now(), name: 'Default', description: e.target.value, icon: 'user', color: 'blue' });
                      }
                      setContactStatusSettings([{ ...contactStatusSettings[0], status_option_ids: updatedOptions }]);
                    }}
                    className="bg-slate-800 border-slate-700 min-h-[120px]" 
                  />
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
                  <Textarea 
                    value={aiContactScoringSettings[0]?.examples_rules || "An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven't signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven't shown strong urgency. They may say they're interested but haven't taken action or confirmed they're ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I'll think about it' with no clear follow-through. They're in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} 
                    onChange={e => setAiContactScoringSettings([{ ...aiContactScoringSettings[0], examples_rules: e.target.value }])}
                    className="bg-slate-800 border-slate-700 min-h-[120px]" 
                  />
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
                  <Textarea 
                    value={contactValueSettings[0]?.value_example_ids?.[0]?.example_text || "An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven't signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven't shown strong urgency. They may say they're interested but haven't taken action or confirmed they're ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I'll think about it' with no clear follow-through. They're in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} 
                    onChange={e => {
                      const updatedExamples = [...(contactValueSettings[0]?.value_example_ids || [])];
                      if (updatedExamples.length > 0) {
                        updatedExamples[0] = { ...updatedExamples[0], example_text: e.target.value };
                      } else {
                        updatedExamples.push({ id: Date.now(), example_text: e.target.value });
                      }
                      setContactValueSettings([{ ...contactValueSettings[0], value_example_ids: updatedExamples }]);
                    }}
                    className="bg-slate-800 border-slate-700 min-h-[120px]" 
                  />
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
                  <Textarea 
                    value={taskGenerationSettings[0]?.task_rule_ids?.[0]?.rule_text || "An A-grade contact is fully committed — they have signed the agreement or scheduled a notary, respond quickly, follow instructions, and clearly want to stop the foreclosure or proceed with a sale. They show urgency and cooperation without needing to be chased.\n\nA B-grade contact is interested but slightly delayed — they may have received the agreement but haven't signed yet, are responsive but waiting on a spouse, or seem open but are processing the decision. They ask questions and show intent, but still require active follow-up.\n\nA C-grade contact is lukewarm — they respond inconsistently, give short or unclear answers, and haven't shown strong urgency. They may say they're interested but haven't taken action or confirmed they're ready to move forward.\n\nA D-grade contact is non-committal — they reply slowly, avoid key questions, deflect with vague excuses, or say things like 'I'll think about it' with no clear follow-through. They're in foreclosure but not showing interest in help yet.\n\nAn F-grade contact does not engage at all — they ignore calls and texts, respond negatively, or have clearly said they are not interested or no longer need assistance."} 
                    onChange={e => {
                      const updatedRules = [...(taskGenerationSettings[0]?.task_rule_ids || [])];
                      if (updatedRules.length > 0) {
                        updatedRules[0] = { ...updatedRules[0], rule_text: e.target.value };
                      } else {
                        updatedRules.push({ id: Date.now(), rule_text: e.target.value });
                      }
                      setTaskGenerationSettings([{ ...taskGenerationSettings[0], task_rule_ids: updatedRules }]);
                    }}
                    className="bg-slate-800 border-slate-700 min-h-[120px]" 
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
} 