import { useEffect, useState } from "react";

const UNREACHABLE = "Cannot reach the ReviewLens server. Start it with: python3 -m src.server (port 8001).";

async function parse(response) {
  let data = null;
  try { data = await response.json(); } catch { /* body was not JSON */ }
  if (!response.ok) throw new Error(data?.error || `Request failed (${response.status}).`);
  if (data === null) throw new Error("The server sent an unreadable response.");
  return data;
}

function send(url, options) {
  return fetch(url, options).then(parse, (error) => {
    if (error.name === "AbortError") throw error;
    throw new Error(UNREACHABLE);
  });
}

export const getJson = (url, options) => send(url, options);
export const postJson = (url, body) => send(url, body === undefined ? { method: "POST" } : {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});
export const postFile = (url, file) => send(url, { method: "POST", headers: { "X-Filename": encodeURIComponent(file.name) }, body: file });

/** GET a url; refetch when url or deps change. Aborts the old request. Pass url=null to skip. */
export function useApi(url, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: Boolean(url) });
  useEffect(() => {
    if (!url) { setState({ data: null, error: null, loading: false }); return undefined; }
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    getJson(url, { signal: controller.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => { if (error.name !== "AbortError") setState({ data: null, error: error.message, loading: false }); });
    return () => controller.abort();
  }, [url, ...deps]); // eslint-disable-line react-hooks/exhaustive-deps
  return state;
}

export const fmt = (n) => (n === null || n === undefined ? "n/a" : Number(n).toLocaleString());

const entity = document.createElement("textarea");
/** Review text from the dataset keeps raw HTML (<br />, &#34;). Show it as plain text. */
export function plain(text) {
  entity.innerHTML = String(text ?? "").replace(/<[^>]*>/g, " ");
  return entity.value.replace(/\s+/g, " ").trim();
}
