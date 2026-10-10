// The five learned writing patterns, in model order, with their theme colour (defined in styles.css).
export const PATTERNS = [
  { name: "Balanced Evaluative Review", color: "var(--pattern-1)" },
  { name: "Extended Analytical Review", color: "var(--pattern-2)" },
  { name: "Concise General Opinion", color: "var(--pattern-3)" },
  { name: "Long-Term Usage Experience", color: "var(--pattern-4)" },
  { name: "Personal Experience and Recommendation", color: "var(--pattern-5)" },
];
export const colorOf = (pattern) => PATTERNS.find((p) => p.name === pattern)?.color ?? "var(--text-3)";
