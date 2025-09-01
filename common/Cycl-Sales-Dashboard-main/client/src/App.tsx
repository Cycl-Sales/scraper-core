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
import SubAccountTest from "@/pages/sub-account-test";
import { ThemeProvider } from "./theme-context";
import { SubAccountProvider, useSubAccount } from "./contexts/SubAccountContext";
import SubAccountAuth from "./components/SubAccountAuth";
import SubAccountLayout from "./components/SubAccountLayout";

function Router() {
  const { isSubAccount, isAuthenticated, isLoading } = useSubAccount();

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  // Show authentication for sub-accounts
  if (isSubAccount && !isAuthenticated) {
    return <SubAccountAuth />;
  }

  // Sub-account routes (limited access)
  if (isSubAccount && isAuthenticated) {
    return (
      <SubAccountLayout>
        <Switch>
          <Route path="/analytics" component={Analytics} />
          <Route path="/automations" component={Automations} />
          <Route path="/call-details" component={CallDetails} />
          <Route path="/sub-account-test" component={SubAccountTest} />
          <Route path="/" component={() => <Redirect to="/analytics" />} />
          <Route component={NotFound} />
        </Switch>
      </SubAccountLayout>
    );
  }

  // Agency routes (full access)
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
      <Route path="/sub-account-test" component={SubAccountTest} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ThemeProvider>
      <SubAccountProvider>
        <TooltipProvider delayDuration={0} skipDelayDuration={0}>
          <div className="dark">
            <Toaster />
            <Router />
          </div>
        </TooltipProvider>
      </SubAccountProvider>
    </ThemeProvider>
  );
}

export default App;
