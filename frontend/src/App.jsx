import { useState } from "react";
import ComplaintDiscovery from "./ComplaintDiscovery.jsx";
import ContradictionInvestigator from "./ContradictionInvestigator.jsx";
import SuspicionInvestigator from "./SuspicionInvestigator.jsx";
import InsightsPage from "./InsightsPage.jsx";
import CheckReview from "./CheckReview.jsx";
import Shell from "./Shell.jsx";
import Overview from "./Overview.jsx";
import { AppProvider } from "./AppState.jsx";

const PAGES = { complaints: ComplaintDiscovery, contradictions: ContradictionInvestigator, suspicion: SuspicionInvestigator, insights: InsightsPage };

export default function App() {
  const [nav, setNav] = useState({ view: "overview", focus: null });
  // go(view, focus): pages open already filtered to the thing a link points at.
  const go = (view, focus = null) => setNav({ view, focus });
  const Page = PAGES[nav.view];

  return (
    <AppProvider>
      <Shell view={nav.view} setView={go}>
        {nav.view === "overview" && <Overview go={go} />}
        {Page && <Page key={JSON.stringify(nav.focus)} focus={nav.focus} clearFocus={() => go(nav.view)} />}
        {nav.view === "check" && <CheckReview />}
      </Shell>
    </AppProvider>
  );
}
