import { Switch, Route, Redirect } from "wouter";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Dashboard from "@/pages/dashboard";
import Contacts from "@/pages/contacts";
import Calls from "@/pages/calls";
import AIAssistant from "@/pages/ai-assistant";
import AutomationRules from "@/pages/automation-rules";
import ResponseTemplates from "@/pages/response-templates";
import AITraining from "@/pages/ai-training";
import NotFound from "@/pages/not-found";
import Overview from "@/pages/overview";
import Analytics from "@/pages/analytics";
import CallDetails from "@/pages/call-details";
import Settings from "@/pages/settings";
import Automations from "@/pages/automations";
import { ThemeProvider } from "./theme-context";

function Router() {
  return (
    <Switch>
      <Route path="/" component={() => <Redirect to="/overview" />} />
      <Route path="/overview" component={Overview} />
      <Route path="/dashboard" component={Dashboard} />
      <Route path="/contacts" component={Contacts} />
      <Route path="/calls" component={Calls} />
      <Route path="/analytics" component={Analytics} />
      <Route path="/ai-assistant" component={AIAssistant} />
      <Route path="/automation-rules" component={AutomationRules} />
      <Route path="/response-templates" component={ResponseTemplates} />
      <Route path="/ai-training" component={AITraining} />
      <Route path="/call-details" component={CallDetails} />
      <Route path="/settings" component={Settings} />
      <Route path="/automations" component={Automations} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ThemeProvider>
      <TooltipProvider>
        <div className="dark">
          <Toaster />
          <Router />
        </div>
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
