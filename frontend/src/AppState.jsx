import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getJson, postFile, postJson } from "./api.js";

// One model of state for the whole app: which dataset is active, and whether analysis results exist for it.
const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);

export function AppProvider({ children }) {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(null);
  const [actionError, setActionError] = useState(null);

  const refresh = useCallback(() => getJson("/app/status").then(setStatus).catch((e) => setActionError(e.message)), []);
  useEffect(() => { refresh(); }, [refresh]);

  const analyzing = status?.data_state === "Analyzing";
  const restoring = Boolean(status?.dataset?.restoring);
  useEffect(() => {
    if (!analyzing && !restoring) return undefined;
    const timer = setInterval(refresh, 2000);
    return () => clearInterval(timer);
  }, [analyzing, restoring, refresh]);

  const value = useMemo(() => {
    async function act(label, fn) {
      setBusy(label); setActionError(null);
      try { await fn(); } catch (error) { setActionError(error.message); } finally { setBusy(null); refresh(); }
    }
    return {
      status, busy, actionError, analyzing, refresh,
      dataset: status?.dataset ?? { kind: null },
      job: status?.job ?? null,
      steps: status?.steps ?? [],
      resultsFor: status?.results_for ?? null,       // "demo" when analysis outputs exist for the active dataset
      resultsVersion: status?.results_version ?? 0,  // changes when any analysis output is rewritten
      upload: (file) => act("upload", () => postFile("/app/upload", file)),
      loadDemo: () => act("load", () => postJson("/app/load-demo")),
      run: () => act("run", () => postJson("/app/run")),
    };
  }, [status, busy, actionError, analyzing, refresh]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
