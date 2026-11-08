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

const mockDocuments: DocItem[] = [
  {
    id: "doc-01",
    title: "MITAOE Placement Statistics & Recruitment Highlights 2023-24",
    category: "Placement Report",
    source_url: "https://mitaoe.ac.in/placements/placement-report-2023-24.pdf",
    academic_year: "2023-24",
    page_count: 14,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "Comprehensive department-wise breakdown of student placement packages, median CTC, and recruiting partners.",
  },
  {
    id: "doc-02",
    title: "FRA Approved Fee Structure for B.Tech Programs 2024-25",
    category: "Fee Structure",
    source_url: "https://mitaoe.ac.in/admissions/fee-structure-2024-25.pdf",
    academic_year: "2024-25",
    page_count: 4,
    is_scanned: true,
    ocr_confidence: 0.94,
    status: "indexed",
    summary: "Official Fees Regulating Authority approval for tuition fees, development fees, and category scholarship provisions.",
  },
  {
    id: "doc-03",
    title: "Academic Calendar & Examination Schedule Semester I & II",
    category: "Academic Calendar",
    source_url: "https://mitaoe.ac.in/academics/academic-calendar-2024-25.pdf",
    academic_year: "2024-25",
    page_count: 6,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "Term commencement dates, mid-semester assessment schedules, project submission windows, and holiday schedule.",
  },
  {
    id: "doc-04",
    title: "NAAC Self-Study Report (SSR) Institutional Profile",
    category: "Accreditation",
    source_url: "https://mitaoe.ac.in/iqac/naac-ssr-cycle2.pdf",
    academic_year: "2022-23",
    page_count: 182,
    is_scanned: false,
    ocr_confidence: null,
    status: "indexed",
    summary: "Institutional accreditation documentation covering teaching-learning quality, governance, research output, and infrastructure.",
  },
  {
    id: "doc-05",
    title: "Office Order: Academic Council & Anti-Ragging Committee",
    category: "Circular",
    source_url: "https://mitaoe.ac.in/circulars/office-order-committees-2024.pdf",
    academic_year: "2024-25",
    page_count: 2,
    is_scanned: true,
    ocr_confidence: 0.91,
    status: "indexed",
    summary: "Official notifications detailing constituted academic committee members, ombudsperson, and disciplinary protocols.",
  },
];

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [activePreview, setActivePreview] = useState<DocItem | null>(null);

  const categories = ["All", "Placement Report", "Fee Structure", "Academic Calendar", "Accreditation", "Circular"];

  const filteredDocs = mockDocuments.filter((doc) => {
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
