"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Search,
  AlertTriangle,
  ExternalLink,
  FileText,
  ChevronDown,
  ChevronUp,
  Clock,
  Sparkles,
  Info,
  CheckCircle2,
  HelpCircle,
  Terminal,
  Activity,
  Brain,
  Database,
  Globe,
  Download,
  FileSearch,
  ScanSearch,
  ShieldCheck,
  Save,
  History,
  RotateCcw,
  Check,
} from "lucide-react";

// ---- Interfaces ----------------------------------------------------

interface Citation {
  source_url: string;
  source_title: string | null;
  page_number: number | null;
  passage: string | null;
  academic_year: string | null;
  retrieval_score?: number;
  retrieval_rank?: number;
  score?: number;
}

interface ChunkDiagnostic {
  chunk_id: string;
  score: number;
  rank: number;
  retrieval_method: string;
  bm25_score: number;
  semantic_score: number;
  source_url: string;
}

interface DiagnosticsData {
  normalized_query?: string;
  expanded_query?: string;
  intent?: string;
  departments?: string[];
  retrieval_candidates?: number;
  top_chunks?: ChunkDiagnostic[];
}

interface SearchResponse {
  query_id?: string;
  query?: string;
  answer: string;
  answer_confidence?: number;
  confidence?: number;
  verification_status: string;
  is_answerable: boolean;
  citations?: Citation[];
  evidence?: Citation[];
  retrieval_latency_ms?: number;
  total_latency_ms?: number;
  latency_ms?: number;
  cache_hit: boolean;
  limitations: string | null;
  suggested_queries?: string[];
  diagnostics?: DiagnosticsData | null;
}

interface HistoryItem {
  id: string;
  query: string;
  intent: string;
  answer: string;
  confidence: number;
  verification_status: string;
  total_latency_ms: number;
  cache_hit: boolean;
  created_at: string | null;
}

interface ResearchStageConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const RESEARCH_STAGES: ResearchStageConfig[] = [
  { id: "analyzing_question", name: "ANALYZING QUESTION", description: "Understanding intent and extracting institutional entities...", icon: Brain },
  { id: "searching_local_knowledge", name: "SEARCHING LOCAL KNOWLEDGE", description: "Querying index, knowledge graph, and statistical records...", icon: Database },
  { id: "discovering_sources", name: "DISCOVERING OFFICIAL SOURCES", description: "Identifying authoritative mitaoe.ac.in pages...", icon: Globe },
  { id: "fetching_pages", name: "FETCHING RELEVANT PAGES", description: "Retrieving official institutional HTML and documents...", icon: Download },
  { id: "extracting_information", name: "EXTRACTING INFORMATION", description: "Extracting tables, faculty profiles, and text passages...", icon: FileSearch },
  { id: "analyzing_evidence", name: "ANALYZING EVIDENCE", description: "Cross-checking faculty, designations, and academic years...", icon: ScanSearch },
  { id: "verifying_information", name: "VERIFYING INFORMATION", description: "Evaluating authenticity, consistency, and statutory dates...", icon: ShieldCheck },
  { id: "generating_answer", name: "GENERATING ANSWER", description: "Synthesizing evidence-backed, factual response...", icon: Sparkles },
  { id: "saving_to_history", name: "SAVING TO LOCAL HISTORY", description: "Persisting verified research to local memory...", icon: Save },
  { id: "completed", name: "COMPLETED", description: "Research complete with verifiable citations.", icon: CheckCircle2 },
];

// ---- Markdown Formatter Helper -------------------------------------

function renderInlineMarkdown(text: string): React.ReactNode {
  // Matches **bold**
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-gray-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

function FormattedMarkdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Table detection: line starts and ends with '|'
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }
      if (tableLines.length >= 2 && tableLines[1].includes("---")) {
        const headers = tableLines[0].split("|").slice(1, -1).map((c) => c.trim());
        const rows = tableLines.slice(2).map((r) => r.split("|").slice(1, -1).map((c) => c.trim()));

        elements.push(
          <div key={`table-${i}`} className="my-4 overflow-x-auto rounded-lg border border-gray-200 shadow-xs">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[#E9EFF6] text-[#102747] font-semibold border-b border-gray-200">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="py-2.5 px-3 border-r last:border-r-0 border-gray-200">
                      {renderInlineMarkdown(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {rows.map((row, rIdx) => (
                  <tr key={rIdx} className={rIdx % 2 === 0 ? "bg-white" : "bg-gray-50/60"}>
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="py-2 px-3 border-r last:border-r-0 border-gray-100 text-gray-800">
                        {renderInlineMarkdown(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h3 key={i} className="text-base font-bold text-[#102747] mt-3 mb-1">
          {renderInlineMarkdown(trimmed.slice(4))}
        </h3>
      );
    } else if (trimmed.startsWith("## ")) {
      elements.push(
        <h2 key={i} className="text-lg font-bold text-[#102747] mt-4 mb-2 border-b pb-1">
          {renderInlineMarkdown(trimmed.slice(3))}
        </h2>
      );
    } else if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
      elements.push(
        <li key={i} className="ml-5 list-disc text-sm text-gray-800 my-0.5 leading-relaxed">
          {renderInlineMarkdown(trimmed.slice(2))}
        </li>
      );
    } else if (trimmed === "") {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(
        <p key={i} className="text-sm text-gray-800 leading-relaxed my-1">
          {renderInlineMarkdown(rawLine)}
        </p>
      );
    }

    i++;
  }

  return <div className="space-y-1">{elements}</div>;
}

// ---- Initial Default Suggestions -----------------------------------
const INITIAL_SUGGESTIONS = [
  "Who is Azher Shaikh?",
  "Who is the HOD of CE?",
  "What is the average placement package?",
  "Compare CE and IT placement statistics",
  "What is the institute fee structure?",
  "Show the latest academic calendar",
];

// ---- Main Component ------------------------------------------------

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [expandedPassages, setExpandedPassages] = useState<{ [key: number]: boolean }>({});
  const [academicYearFilter, setAcademicYearFilter] = useState<string>("all");
  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(false);
  const [suggestions, setSuggestions] = useState<string[]>(INITIAL_SUGGESTIONS);

  // Streaming Live Research State
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [stageStatuses, setStageStatuses] = useState<{ [key: string]: "running" | "completed" | "skipped" | "failed" }>({});
  const [liveMessage, setLiveMessage] = useState<string>("");
  const [discoveredSources, setDiscoveredSources] = useState<number>(0);
  const [activeSourceUrl, setActiveSourceUrl] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number>(0);

  // History Memory State
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Typewriter effect state
  const [typedAnswer, setTypedAnswer] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);

  useEffect(() => {
    if (!result?.answer) {
      setTypedAnswer("");
      setIsTyping(false);
      return;
    }

    const fullText = result.answer;
    setTypedAnswer("");
    setIsTyping(true);

    // Stream word chunks smoothly with typewriter effect
    const words = fullText.split(/(\s+)/);
    let i = 0;
    let current = "";
    const interval = setInterval(() => {
      if (i < words.length) {
        current += words[i];
        i++;
        setTypedAnswer(current);
      } else {
        setTypedAnswer(fullText);
        setIsTyping(false);
        clearInterval(interval);
      }
    }, 15);

    return () => clearInterval(interval);
  }, [result?.answer]);

  // Load history
  const fetchHistory = useCallback(async () => {
    try {
      setLoadingHistory(true);
      const res = await fetch("/api/v1/search/history?limit=6");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.debug("Failed to fetch history:", e);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Execute Streaming Search
  const executeSearch = useCallback(
    async (searchQuery: string) => {
      if (!searchQuery.trim()) return;

      setLoading(true);
      setResult(null);
      setCurrentStage("analyzing_question");
      setCompletedStages([]);
      setStageStatuses({});
      setLiveMessage("Initiating VEDANTA Autonomous Research Engine...");
      setDiscoveredSources(0);
      setActiveSourceUrl(null);
      setElapsedMs(0);

      const tStart = Date.now();
      const timer = setInterval(() => {
        setElapsedMs(Date.now() - tStart);
      }, 60);

      try {
        const res = await fetch("/api/v1/search/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: searchQuery,
            top_k: 8,
            include_evidence: true,
            academic_year: academicYearFilter === "all" ? null : academicYearFilter,
          }),
        });

        if (!res.ok) {
          throw new Error(`Server returned HTTP ${res.status}`);
        }

        if (!res.body) {
          throw new Error("No response body available for streaming");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("data: ")) {
              try {
                const evt = JSON.parse(trimmed.slice(6));
                if (evt.stage) {
                  setCurrentStage(evt.stage);
                  const st = evt.status || "completed";
                  setStageStatuses((prev) => ({ ...prev, [evt.stage]: st }));
                  if (st === "completed") {
                    setCompletedStages((prev) => (prev.includes(evt.stage) ? prev : [...prev, evt.stage]));
                  }
                }
                if (evt.message) {
                  setLiveMessage(evt.message);
                }
                if (evt.discovered_source_count !== undefined) {
                  setDiscoveredSources(evt.discovered_source_count);
                }
                if (evt.source_url) {
                  setActiveSourceUrl(evt.source_url);
                }
                if (evt.status === "completed" && evt.data) {
                  setResult(evt.data);
                  if (evt.data.suggested_queries && Array.isArray(evt.data.suggested_queries) && evt.data.suggested_queries.length > 0) {
                    setSuggestions(evt.data.suggested_queries);
                  }
                  setCurrentStage("completed");
                  setCompletedStages((prev) => (prev.includes("completed") ? prev : [...prev, "completed"]));
                  fetchHistory();
                }
              } catch (e) {
                console.warn("SSE json parse error:", e);
              }
            }
          }
        }
      } catch (err: unknown) {
        console.error("Streaming search error, falling back:", err);
        // Fallback to standard search if stream aborted
        try {
          const res = await fetch("/api/v1/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: searchQuery,
              top_k: 8,
              include_evidence: true,
              academic_year: academicYearFilter === "all" ? null : academicYearFilter,
            }),
          });
          if (res.ok) {
            const data = await res.json();
            setResult(data);
            if (data.suggested_queries && Array.isArray(data.suggested_queries) && data.suggested_queries.length > 0) {
              setSuggestions(data.suggested_queries);
            }
            setCurrentStage("completed");
            fetchHistory();
          } else {
            throw new Error(`Fallback HTTP ${res.status}`);
          }
        } catch {
          setResult({
            answer:
              "Unable to retrieve verified evidence from the VEDANTA knowledge base. Please check backend connectivity or refine your query.",
            confidence: 0.0,
            verification_status: "insufficient_evidence",
            is_answerable: false,
            citations: [],
            total_latency_ms: 0,
            cache_hit: false,
            limitations: `Search error: ${(err as Error).message}`,
            suggested_queries: [
              "Who is the HOD of Computer Engineering?",
              "What is the current academic year at MITAOE?",
              "Show the academic calendar for 2026-27",
            ],
          });
        }
      } finally {
        clearInterval(timer);
        setLoading(false);
      }
    },
    [academicYearFilter, fetchHistory]
  );

  useEffect(() => {
    if (initialQuery) {
      executeSearch(initialQuery);
    }
  }, [initialQuery, executeSearch]);

  const togglePassage = (idx: number) => {
    setExpandedPassages((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "verified":
        return (
          <span className="inline-flex items-center space-x-1.5 bg-emerald-50 text-emerald-700 border border-emerald-300 text-xs font-semibold px-2.5 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>VERIFIED</span>
          </span>
        );
      case "partially_verified":
        return (
          <span className="inline-flex items-center space-x-1.5 bg-blue-50 text-blue-700 border border-blue-300 text-xs font-semibold px-2.5 py-1 rounded-full">
            <Info className="w-3.5 h-3.5 text-blue-600" />
            <span>PARTIALLY VERIFIED</span>
          </span>
        );
      case "conflicting_sources":
        return (
          <span className="inline-flex items-center space-x-1.5 bg-purple-50 text-purple-700 border border-purple-300 text-xs font-semibold px-2.5 py-1 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 text-purple-600" />
            <span>CONFLICTING SOURCES</span>
          </span>
        );
      case "outdated_source":
        return (
          <span className="inline-flex items-center space-x-1.5 bg-amber-50 text-amber-700 border border-amber-300 text-xs font-semibold px-2.5 py-1 rounded-full">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            <span>OUTDATED SOURCE</span>
          </span>
        );
      case "insufficient_evidence":
        return (
          <span className="inline-flex items-center space-x-1.5 bg-rose-50 text-rose-700 border border-rose-300 text-xs font-semibold px-2.5 py-1 rounded-full">
            <HelpCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>INSUFFICIENT EVIDENCE</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 bg-gray-50 text-gray-700 border border-gray-300 text-xs font-semibold px-2.5 py-1 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 text-gray-600" />
            <span>UNCERTAIN</span>
          </span>
        );
    }
  };

  const citationsList = result?.citations || result?.evidence || [];
  const confidenceScore = result ? (result.confidence !== undefined ? result.confidence : result.answer_confidence || 0) : 0;
  const latencyDisplay = result?.total_latency_ms || result?.latency_ms || elapsedMs;

  // Active stage index
  const activeStageIdx = RESEARCH_STAGES.findIndex((s) => s.id === currentStage);
  const progressPercent =
    currentStage === "completed"
      ? 100
      : activeStageIdx >= 0
      ? Math.round(((activeStageIdx + 1) / RESEARCH_STAGES.length) * 100)
      : loading
      ? 15
      : 0;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Search Input Box */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            executeSearch(query);
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask any question about MITAOE (faculty, HODs, 2026-27 calendar, fees, placements)..."
              className="w-full pl-11 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm text-[#102747] focus:outline-none focus:border-[#24558A]"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={academicYearFilter}
              onChange={(e) => setAcademicYearFilter(e.target.value)}
              className="px-3 py-2.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-gray-50 focus:outline-none"
            >
              <option value="all">All Academic Years</option>
              <option value="2026-27">AY 2026–27 (Current)</option>
              <option value="2025-26">AY 2025–26</option>
              <option value="2024-25">AY 2024–25</option>
              <option value="2023-24">AY 2023–24</option>
            </select>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-[#24558A] hover:bg-[#102747] text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 flex items-center space-x-1.5 shrink-0 shadow-xs"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Researching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Quick Suggestion Pills */}
        <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-400 font-medium flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-[#27A6A1]" />
            <span>Suggested:</span>
          </span>
          {suggestions.map((sq, i) => (
            <button
              key={`${sq}-${i}`}
              type="button"
              disabled={loading}
              onClick={() => {
                setQuery(sq);
                executeSearch(sq);
              }}
              className="px-2.5 py-1 bg-gray-50 hover:bg-[#E9EFF6] text-gray-700 hover:text-[#102747] rounded-md border border-gray-200 transition-colors text-left disabled:opacity-50"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Final Answer Card (Loading skeleton, Verified answer, Error, Insufficient evidence, Dev Diagnostics) */}
      {loading && !result && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-xs p-6 space-y-3 animate-pulse">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex items-center space-x-2">
              <div className="w-24 h-5 bg-gray-200 rounded" />
              <div className="w-20 h-4 bg-gray-100 rounded" />
            </div>
            <div className="w-16 h-4 bg-gray-100 rounded" />
          </div>
          <div className="space-y-2 pt-2">
            <div className="w-1/3 h-4 bg-gray-200 rounded" />
            <div className="w-full h-4 bg-gray-100 rounded" />
            <div className="w-5/6 h-4 bg-gray-100 rounded" />
          </div>
          <p className="text-xs text-gray-400 font-mono pt-1 flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-[#24558A] animate-ping" />
            <span>VEDANTA research engine synthesizing answer...</span>
          </p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Answer Card */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Header / Meta bar */}
            <div className="bg-[#E9EFF6]/50 px-6 py-3.5 border-b border-gray-200 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-3">
                {getStatusBadge(result.verification_status)}
                <span className="text-xs text-gray-600 font-mono font-medium">
                  Confidence: {(confidenceScore * 100).toFixed(0)}%
                </span>
                {result.cache_hit && (
                  <span className="text-[11px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-mono font-medium">
                    ⚡ In-Memory Cached
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-4 text-xs text-gray-500 font-mono">
                <span className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{latencyDisplay} ms</span>
                </span>
                <span>{citationsList.length} sources cited</span>
                {result.diagnostics && (
                  <button
                    onClick={() => setShowDiagnostics(!showDiagnostics)}
                    className="flex items-center space-x-1 text-[#24558A] hover:underline font-sans font-semibold cursor-pointer"
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    <span>{showDiagnostics ? "Hide Diagnostics" : "Dev Diagnostics"}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Answer Body */}
            <div className="p-6 space-y-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Ground Truth Verified Institutional Answer
              </h2>

              {/* Formatted Markdown with Real-Time Typewriter Streaming Effect */}
              <div className="prose prose-sm max-w-none text-gray-900 leading-relaxed font-normal text-base relative">
                <FormattedMarkdown content={typedAnswer || result.answer} />
                {isTyping && (
                  <span className="inline-block w-2 h-4 ml-1 bg-[#24558A] animate-pulse align-middle" title="Typing response..." />
                )}
              </div>

              {result.limitations && (
                <div className="p-3 bg-amber-50/70 border-l-4 border-amber-400 text-xs text-amber-900 rounded-r">
                  <span className="font-semibold">Verification Note: </span>
                  {result.limitations}
                </div>
              )}
            </div>
          </div>

          {/* Developer Search Diagnostics Panel */}
          {showDiagnostics && result.diagnostics && (
            <div className="bg-slate-900 text-slate-100 p-5 rounded-xl border border-slate-700 font-mono text-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-slate-200 flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <span>Developer Search Diagnostics (Hybrid BM25 + FAISS + RRF)</span>
                </span>
                <span className="text-slate-400 text-[11px]">
                  Candidates: {result.diagnostics.retrieval_candidates || 0}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                <div>
                  <span className="text-slate-400">Intent:</span>{" "}
                  <span className="text-yellow-400">{result.diagnostics.intent}</span>
                </div>
                <div>
                  <span className="text-slate-400">Departments:</span>{" "}
                  <span className="text-cyan-400">
                    {(result.diagnostics.departments || []).join(", ") || "None"}
                  </span>
                </div>
                <div className="col-span-full">
                  <span className="text-slate-400">Expanded Query:</span>{" "}
                  <span className="text-slate-200">{result.diagnostics.expanded_query}</span>
                </div>
              </div>

              {result.diagnostics.top_chunks && result.diagnostics.top_chunks.length > 0 && (
                <div className="space-y-2 pt-2">
                  <span className="text-slate-400 font-semibold">Top Retrieved Chunks Breakdown:</span>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-[11px]">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-1 px-2">Rank</th>
                          <th className="py-1 px-2">Method</th>
                          <th className="py-1 px-2">RRF Score</th>
                          <th className="py-1 px-2">BM25</th>
                          <th className="py-1 px-2">Semantic</th>
                          <th className="py-1 px-2">Source URL</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.diagnostics.top_chunks.map((chk, i) => (
                          <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                            <td className="py-1 px-2 font-bold text-emerald-400">#{chk.rank}</td>
                            <td className="py-1 px-2 text-cyan-300">{chk.retrieval_method}</td>
                            <td className="py-1 px-2 text-amber-300">{chk.score}</td>
                            <td className="py-1 px-2">{chk.bm25_score}</td>
                            <td className="py-1 px-2">{chk.semantic_score}</td>
                            <td className="py-1 px-2 truncate max-w-xs text-slate-400" title={chk.source_url}>
                              {chk.source_url}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 4. Live Research Status Indicator (Active during search or recently completed) */}
      {(loading || currentStage) && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden transition-all">
          {/* Header Bar */}
          <div className="bg-linear-to-r from-[#102747] to-[#24558A] px-5 py-3 text-white flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-2.5">
              <div className="relative">
                <Brain className="w-5 h-5 text-[#27A6A1]" />
                {loading && (
                  <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#27A6A1] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
                  </span>
                )}
              </div>
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-100">
                  VEDANTA Autonomous Research Engine
                </h3>
                <p className="text-[11px] text-slate-300">
                  {loading ? "Multi-Stage Dynamic Institutional Discovery" : "Evidence Verification Complete"}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="bg-white/10 px-2.5 py-1 rounded-md text-emerald-300 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>{elapsedMs} ms</span>
              </span>
              <span className="bg-white/10 px-2.5 py-1 rounded-md text-cyan-300">
                {discoveredSources} Sources Discovered
              </span>
              <span className="bg-[#27A6A1]/30 text-emerald-200 px-2 py-0.5 rounded text-[11px] font-bold">
                {progressPercent}%
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-100 h-1.5 overflow-hidden">
            <div
              className="bg-linear-to-r from-[#24558A] via-[#27A6A1] to-emerald-500 h-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Live Stage Message & Active Indicator */}
          <div className="p-4 bg-[#E9EFF6]/30 border-b border-gray-100 flex items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              {loading ? (
                <div className="w-4 h-4 border-2 border-[#24558A] border-t-transparent rounded-full animate-spin shrink-0" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              )}
              <span className="text-xs font-medium text-[#102747]">
                {liveMessage || "Processing inquiry through multi-source institutional pipeline..."}
              </span>
            </div>

            {activeSourceUrl && (
              <span className="text-[11px] font-mono text-gray-500 truncate max-w-xs" title={activeSourceUrl}>
                Target: {activeSourceUrl}
              </span>
            )}
          </div>

          {/* 10-Stage Pipeline Visualizer */}
          <div className="p-4 grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
            {RESEARCH_STAGES.map((stg, sIdx) => {
              const StageIcon = stg.icon;
              const status = stageStatuses[stg.id];
              const isCompleted = status === "completed" || completedStages.includes(stg.id);
              const isSkipped = status === "skipped";
              const isFailed = status === "failed";
              const isActive = (currentStage === stg.id && loading) || status === "running";

              return (
                <div
                  key={stg.id}
                  className={`p-2.5 rounded-lg border transition-all flex flex-col justify-between space-y-1 ${
                    isFailed
                      ? "bg-rose-50 border-rose-300 text-rose-900"
                      : isActive
                      ? "bg-amber-50/80 border-amber-300 text-amber-900 shadow-xs ring-1 ring-amber-300"
                      : isSkipped
                      ? "bg-slate-50/70 border-slate-200 text-slate-400"
                      : isCompleted
                      ? "bg-emerald-50/60 border-emerald-200 text-emerald-900"
                      : "bg-gray-50/50 border-gray-100 text-gray-400"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold opacity-70">
                      STEP {sIdx + 1}
                    </span>
                    {isFailed ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                    ) : isSkipped ? (
                      <span className="text-[9px] font-mono font-bold bg-slate-200/80 text-slate-600 px-1 py-0.5 rounded">
                        SKIPPED
                      </span>
                    ) : isCompleted ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : isActive ? (
                      <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-gray-200" />
                    )}
                  </div>

                  <div className="flex items-center space-x-1.5 pt-0.5">
                    <StageIcon className={`w-3.5 h-3.5 shrink-0 ${isFailed ? "text-rose-600" : isActive ? "text-amber-600" : isSkipped ? "text-slate-400" : isCompleted ? "text-emerald-600" : "text-gray-400"}`} />
                    <span className="font-semibold text-[11px] truncate leading-tight">
                      {stg.name}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. Institutional Research Memory / Local History */}
      {history.length > 0 && !loading && (
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 flex items-center space-x-1.5">
              <History className="w-4 h-4 text-[#24558A]" />
              <span>Institutional Research Memory (PostgreSQL Cache)</span>
            </h4>
            <button
              onClick={fetchHistory}
              disabled={loadingHistory}
              className="text-[11px] text-gray-400 hover:text-[#24558A] flex items-center space-x-1 transition-colors"
              title="Refresh History"
            >
              <RotateCcw className={`w-3 h-3 ${loadingHistory ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {history.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  setQuery(item.query);
                  executeSearch(item.query);
                }}
                className="p-3 bg-gray-50 hover:bg-[#E9EFF6]/60 border border-gray-200/80 rounded-lg cursor-pointer transition-all hover:border-[#24558A] group space-y-1.5"
              >
                <div className="flex items-center justify-between gap-1 text-[11px]">
                  <span className="font-bold text-[#102747] group-hover:text-[#24558A] truncate max-w-[180px]">
                    {item.query}
                  </span>
                  <span className="font-mono text-gray-400 shrink-0 text-[10px]">
                    {item.total_latency_ms} ms
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-gray-500">
                  <span className="uppercase font-semibold tracking-wider text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                    {item.verification_status}
                  </span>
                  {item.cache_hit && (
                    <span className="text-blue-600 font-mono">⚡ cached</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Remaining Existing Sections (Primary Evidence Sources & Related Inquiries) */}
      {result && (
        <div className="space-y-6">
          {/* Citations & Evidence Section */}
          <div className="space-y-4">
            <h3 className="text-base font-bold text-[#102747] flex items-center space-x-2">
              <FileText className="w-5 h-5 text-[#24558A]" />
              <span>Primary Evidence Sources ({citationsList.length})</span>
            </h3>

            <div className="grid grid-cols-1 gap-4">
              {citationsList.map((citation, idx) => {
                const isExpanded = expandedPassages[idx];
                const rankNum = citation.retrieval_rank || idx + 1;
                return (
                  <div
                    key={idx}
                    className="bg-white p-5 rounded-xl border border-gray-200 hover:border-[#27A6A1] shadow-xs transition-all space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="w-6 h-6 rounded-full bg-[#E9EFF6] text-[#24558A] text-xs font-bold flex items-center justify-center shrink-0">
                          {rankNum}
                        </span>
                        <h4 className="font-semibold text-sm text-[#102747] line-clamp-1">
                          {citation.source_title || citation.source_url}
                        </h4>
                      </div>

                      <div className="flex items-center space-x-2 shrink-0">
                        {citation.page_number && (
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded font-mono font-medium">
                            Page {citation.page_number}
                          </span>
                        )}
                        {citation.academic_year && (
                          <span className="text-xs bg-[#E9EFF6] text-[#24558A] px-2 py-0.5 rounded font-medium">
                            AY {citation.academic_year}
                          </span>
                        )}
                        <a
                          href={citation.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-[#24558A] hover:text-[#102747] rounded hover:bg-gray-100"
                          title="Open original URL"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </div>

                    {/* Source Passage */}
                    {citation.passage && (
                      <div className="bg-gray-50/80 p-3 rounded-lg border border-gray-100 text-xs text-gray-700 leading-relaxed">
                        <p className={isExpanded ? "" : "line-clamp-2"}>
                          &quot;{citation.passage}&quot;
                        </p>
                        {citation.passage.length > 140 && (
                          <button
                            onClick={() => togglePassage(idx)}
                            className="mt-1 text-[11px] font-semibold text-[#24558A] hover:underline flex items-center space-x-0.5 cursor-pointer"
                          >
                            <span>{isExpanded ? "Show less" : "Show full passage"}</span>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Related Inquiries */}
          {result.suggested_queries && result.suggested_queries.length > 0 && (
            <div className="bg-white p-5 rounded-xl border border-gray-200 space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#27A6A1]" />
                <span>Related Institutional Questions</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.suggested_queries.map((sq, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuery(sq);
                      executeSearch(sq);
                    }}
                    className="text-xs bg-gray-50 hover:bg-[#E9EFF6] text-[#102747] px-3 py-1.5 rounded-lg border border-gray-200 transition-colors text-left cursor-pointer"
                  >
                    {sq}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-sm text-gray-500">
          Loading VEDANTA Search...
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
