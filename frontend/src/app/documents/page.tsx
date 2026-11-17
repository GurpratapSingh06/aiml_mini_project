"use client";

import React, { useState } from "react";
import {
  FileText,
  Search,
  Filter,
  CheckCircle,
  ExternalLink,
  Eye,
  Calendar,
  Layers,
} from "lucide-react";

interface DocItem {
  id: string;
  title: string;
  category: string;
  source_url: string;
  academic_year: string;
  page_count: number;
  is_scanned: boolean;
  ocr_confidence: number | null;
  status: string;
  summary: string;
}

const initialDocuments: DocItem[] = [
  {
    id: "doc-01",
    title: "MITAOE Mandatory Disclosure 2026-27 (AICTE & DTE Statutory Compliance)",
    category: "Statutory Disclosure",
    source_url: "https://mitaoe.ac.in/assets/images/pdf/Mandatory-Disclosure-2026-27.pdf",
    academic_year: "2026-27",
    page_count: 1829,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "Comprehensive 1,829-page institutional disclosure covering governance, faculty rosters, programs, infrastructure, and NBA accreditation.",
  },
  {
    id: "doc-02",
    title: "Institutional Academic Calendar 2026-27 Term 1 (UG & Honors)",
    category: "Academic Calendar",
    source_url: "https://mitaoe.ac.in/2026-2027-Term-I-UG-Calendar.html",
    academic_year: "2026-27",
    page_count: 4,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "Term commencement (July 2026), instructional duration, continuous in-semester evaluation, mid-term, and end-semester examination dates.",
  },
  {
    id: "doc-03",
    title: "MITAOE Information Brochure Academic Year 2026-27",
    category: "Brochure",
    source_url: "https://mitaoe.ac.in/assets/images/pdf/Information-Brochure-2026-27.pdf",
    academic_year: "2026-27",
    page_count: 36,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "Curriculum structure, department profiles, seat matrix, eligibility criteria, and academic policies for the 2026-27 intake.",
  },
  {
    id: "doc-04",
    title: "MITAOE Examination Time Table AY 2026-2027",
    category: "Examination",
    source_url: "https://mitaoe.ac.in/academic-year-2026-2027.php",
    academic_year: "2026-27",
    page_count: 8,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "In-Semester Evaluation and End-Semester Assessment timetable for B.Tech programs across engineering disciplines.",
  },
  {
    id: "doc-05",
    title: "Academic Calendar 2025-2026 Term I (Archived)",
    category: "Academic Calendar",
    source_url: "https://mitaoe.ac.in/assets/images/pdf/Academic-Calendar-2025-2026-Term-I.pdf",
    academic_year: "2025-26",
    page_count: 4,
    is_scanned: true,
    ocr_confidence: 0.96,
    status: "indexed",
    summary: "Historical instructional schedule and examination dates preceding the active 2026-27 academic year.",
  },
  {
    id: "doc-06",
    title: "Academic Calendar 2024-25 Term I (SY to B.Tech) (Archived)",
    category: "Academic Calendar",
    source_url: "https://mitaoe.ac.in/assets/images/pdf/Academic-Calendar-2024-25.pdf",
    academic_year: "2024-25",
    page_count: 4,
    is_scanned: true,
    ocr_confidence: 0.93,
    status: "indexed",
    summary: "Historical academic term schedule for 2024-25 archived in institutional repository.",
  },
];

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [activePreview, setActivePreview] = useState<DocItem | null>(null);

  const categories = ["All", "Statutory Disclosure", "Academic Calendar", "Brochure", "Examination", "Accreditation"];

  const filteredDocs = initialDocuments.filter((doc) => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          doc.summary.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "All" || doc.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Title & Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#102747]">
            Institutional Document Library
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Verified institutional PDF repository with page-level OCR indexing and deterministic table extraction.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter documents..."
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:border-[#24558A] w-full sm:w-64"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-xs bg-white text-gray-700 focus:outline-none"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Documents Grid / Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredDocs.map((doc) => (
          <div
            key={doc.id}
            className="bg-white rounded-xl border border-gray-200/90 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold bg-[#E9EFF6] text-[#24558A] px-2.5 py-0.5 rounded-full">
                  {doc.category}
                </span>
                <span className="text-xs font-mono text-gray-500 flex items-center space-x-1">
                  <Calendar className="w-3 h-3 text-gray-400" />
                  <span>{doc.academic_year}</span>
                </span>
              </div>

              <h3 className="font-semibold text-sm text-[#102747] leading-snug line-clamp-2">
                {doc.title}
              </h3>

              <p className="text-xs text-gray-600 line-clamp-3">
                {doc.summary}
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-gray-100">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="flex items-center space-x-1">
                  <Layers className="w-3.5 h-3.5 text-gray-400" />
                  <span>{doc.page_count} pages</span>
                </span>

                {doc.is_scanned ? (
                  <span className="inline-flex items-center space-x-1 text-purple-700 bg-purple-50 px-2 py-0.5 rounded font-mono text-[11px]">
                    <span>OCR {(doc.ocr_confidence! * 100).toFixed(0)}%</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px]">
                    <CheckCircle className="w-3 h-3 text-emerald-600" />
                    <span>Digital PDF</span>
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between pt-1">
                <button
                  onClick={() => setActivePreview(doc)}
                  className="text-xs font-semibold text-[#24558A] hover:text-[#102747] flex items-center space-x-1"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Details</span>
                </button>

                <a
                  href={doc.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-500 hover:text-[#102747] flex items-center space-x-1"
                >
                  <span>Source URL</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Preview Modal */}
      {activePreview && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-[#24558A]" />
                <h3 className="font-bold text-base text-[#102747] line-clamp-1">
                  {activePreview.title}
                </h3>
              </div>
              <button
                onClick={() => setActivePreview(null)}
                className="text-gray-400 hover:text-gray-600 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-gray-700">
              <div className="grid grid-cols-2 gap-2 bg-gray-50 p-3 rounded-lg font-mono">
                <div>
                  <span className="text-gray-400">Academic Year: </span>
                  <span className="font-semibold text-gray-900">{activePreview.academic_year}</span>
                </div>
                <div>
                  <span className="text-gray-400">Document Type: </span>
                  <span className="font-semibold text-gray-900">{activePreview.category}</span>
                </div>
                <div>
                  <span className="text-gray-400">Total Pages: </span>
                  <span className="font-semibold text-gray-900">{activePreview.page_count}</span>
                </div>
                <div>
                  <span className="text-gray-400">Processing Mode: </span>
                  <span className="font-semibold text-gray-900">
                    {activePreview.is_scanned ? "Scanned (Tesseract OCR Engine)" : "Digital PyMuPDF Parser"}
                  </span>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Knowledge Abstract</h4>
                <p className="leading-relaxed bg-white border border-gray-100 p-3 rounded">
                  {activePreview.summary}
                </p>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <a
                  href={activePreview.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-[#24558A] text-white px-4 py-2 rounded-lg font-semibold hover:bg-[#102747] flex items-center space-x-1.5 transition-colors"
                >
                  <span>Open Institutional PDF</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
