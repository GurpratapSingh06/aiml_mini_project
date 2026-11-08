"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  ShieldCheck,
  FileText,
  BarChart2,
  Layers,
  ArrowRight,
  Building,
} from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const sampleQueries = [
    { text: "Who is the HOD of Computer Engineering?", label: "Faculty & HOD" },
    { text: "What are the latest Computer Engineering placement statistics?", label: "Placements" },
    { text: "What is the fee structure for 2024-25?", label: "Fee Structure" },
    { text: "Academic calendar for current semester", label: "Academics" },
    { text: "MITAOE NAAC grade and accreditation", label: "Accreditation" },
  ];

  return (
    <div className="flex flex-col items-center justify-center">
      {/* Hero Section */}
      <section className="w-full bg-gradient-to-b from-[#102747] via-[#102747] to-[#1A3A63] text-white py-20 px-4 sm:px-6 lg:px-8 border-b border-[#24558A]/30">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center space-x-2 bg-[#24558A]/50 border border-[#27A6A1]/40 px-3.5 py-1.5 rounded-full text-xs font-medium text-[#27A6A1]">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-[#E9EFF6]">Institutional Knowledge Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight">
            Discover Knowledge. <br className="hidden sm:inline" />
            <span className="text-[#27A6A1]">Trust Every Answer.</span>
          </h1>

          <p className="text-base sm:text-lg text-[#E9EFF6]/80 max-w-2xl mx-auto font-normal">
            Ground truth retrieval across MIT Academy of Engineering portals, official circulars,
            accreditation reports, placement documents, and fee disclosures.
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="max-w-2xl mx-auto mt-8 relative">
            <div className="relative flex items-center bg-white rounded-xl shadow-2xl overflow-hidden p-1.5 border-2 border-transparent focus-within:border-[#27A6A1] transition-all">
              <Search className="w-5 h-5 text-gray-400 ml-3" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask any institutional question (e.g. Who heads Computer Engineering?)"
                className="w-full px-4 py-3 text-sm text-[#102747] focus:outline-none placeholder-gray-400 font-medium"
              />
              <button
                type="submit"
                className="bg-[#24558A] hover:bg-[#102747] text-white px-6 py-3 rounded-lg text-sm font-semibold transition-colors flex items-center space-x-1.5 shrink-0"
              >
                <span>Query</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>

          {/* Sample Query Badges */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <span className="text-xs text-[#E9EFF6]/60 font-medium mr-1">Suggested:</span>
            {sampleQueries.map((item, idx) => (
              <button
                key={idx}
                onClick={() => router.push(`/search?q=${encodeURIComponent(item.text)}`)}
                className="text-xs bg-[#24558A]/40 hover:bg-[#24558A] text-[#E9EFF6] px-3 py-1.5 rounded-full border border-[#E9EFF6]/20 transition-all hover:border-[#27A6A1]"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Pillars */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 w-full">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl font-bold text-[#102747]">
            Architected for Verifiable Academic Accuracy
          </h2>
          <p className="text-sm text-gray-600 mt-2">
            VEDANTA is not a generic hallucinating chatbot. It is a deterministic institutional knowledge retrieval system.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-[#24558A]/10 text-[#24558A] flex items-center justify-center mb-4">
              <Layers className="w-5 h-5 text-[#24558A]" />
            </div>
            <h3 className="font-semibold text-base text-[#102747] mb-2">Hybrid Retrieval</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Reciprocal Rank Fusion uniting exact BM25 keyword matching with FAISS sentence-transformer semantic vectors.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-[#27A6A1]/10 text-[#27A6A1] flex items-center justify-center mb-4">
              <FileText className="w-5 h-5 text-[#27A6A1]" />
            </div>
            <h3 className="font-semibold text-base text-[#102747] mb-2">Page-Level Citations</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Every factual assertion links directly to primary sources: live website URLs and specific PDF page numbers.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-[#102747]/10 text-[#102747] flex items-center justify-center mb-4">
              <BarChart2 className="w-5 h-5 text-[#102747]" />
            </div>
            <h3 className="font-semibold text-base text-[#102747] mb-2">Deterministic Math</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Arithmetic calculations (averages, package changes, fee totals) are verified through Python logic, never AI guesses.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
            </div>
            <h3 className="font-semibold text-base text-[#102747] mb-2">Evidence Validation</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Identifies conflicting sources, distinguishes current from historical academic years, and reports lack of evidence honestly.
            </p>
          </div>
        </div>
      </section>

      {/* Institutional Entities Quick Access */}
      <section className="w-full bg-[#E9EFF6]/50 py-16 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-bold text-[#102747]">
                MITAOE Academic Departments & Intelligence Explorer
              </h2>
              <p className="text-xs text-gray-600 mt-1">
                Explore faculty, leadership, placement trends, and curricula across academic schools
              </p>
            </div>
            <Link
              href="/analytics"
              className="mt-3 sm:mt-0 text-xs font-semibold text-[#24558A] hover:text-[#102747] flex items-center space-x-1"
            >
              <span>View Full Analytics</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { name: "Computer Engineering", code: "CE", hod: "Dr. Sandip A. Gade" },
              { name: "Comp. Sci. & Engineering", code: "CSE", hod: "School of Computing" },
              { name: "AI & Machine Learning", code: "AIML", hod: "School of Computing" },
              { name: "Information Technology", code: "IT", hod: "School of Computing" },
              { name: "Electronics & Telecomm.", code: "ENTC", hod: "School of Electrical" },
              { name: "Mechanical Engineering", code: "MECH", hod: "School of Mechanical" },
              { name: "Civil Engineering", code: "CIVIL", hod: "School of Civil" },
              { name: "First Year Engineering", code: "FY", hod: "Dept. of Applied Sciences" },
            ].map((dept, idx) => (
              <Link
                key={idx}
                href={`/search?q=${encodeURIComponent(dept.name)}`}
                className="bg-white p-4 rounded-lg border border-gray-200 hover:border-[#27A6A1] shadow-xs hover:shadow-sm transition-all group"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#24558A] bg-[#E9EFF6] px-2 py-0.5 rounded">
                    {dept.code}
                  </span>
                  <Building className="w-3.5 h-3.5 text-gray-400 group-hover:text-[#27A6A1] transition-colors" />
                </div>
                <h4 className="font-semibold text-sm text-[#102747] group-hover:text-[#24558A] line-clamp-1">
                  {dept.name}
                </h4>
                <p className="text-[11px] text-gray-500 mt-1">{dept.hod}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
