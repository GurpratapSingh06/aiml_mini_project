import React from "react";
import Link from "next/link";
import { Shield, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-[#102747] text-[#E9EFF6] border-t border-[#24558A]/30 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white">VEDANTA</span>
              <span className="text-xs text-[#27A6A1] font-mono">v0.1.0</span>
            </div>
            <p className="text-xs text-[#E9EFF6]/70 max-w-md">
              Verified Educational Data And Networked Technology Assistant.
              An institutional knowledge intelligence platform built for MIT Academy of Engineering, Pune.
              Zero hallucinations: all answers are verifiable and grounded in primary source documents and live websites.
            </p>
            <div className="flex items-center space-x-2 text-xs text-[#27A6A1]">
              <Shield className="w-3.5 h-3.5" />
              <span>Evidence-Backed • Deterministic Math • Local-First Architecture</span>
            </div>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white mb-3">
              Institutional Sources
            </h3>
            <ul className="space-y-2 text-xs text-[#E9EFF6]/80">
              <li>
                <a
                  href="https://mitaoe.ac.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white flex items-center space-x-1"
                >
                  <span>MITAOE Official Portal</span>
                  <ExternalLink className="w-3 h-3 text-[#27A6A1]" />
                </a>
              </li>
              <li>
                <Link href="/documents" className="hover:text-white">
                  Academic Calendars & Circulars
                </Link>
              </li>
              <li>
                <Link href="/documents" className="hover:text-white">
                  Fee Structure & FRA Reports
                </Link>
              </li>
              <li>
                <Link href="/analytics" className="hover:text-white">
                  Verified Placement Statistics
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white mb-3">
              Platform Engineering
            </h3>
            <ul className="space-y-2 text-xs text-[#E9EFF6]/80">
              <li>
                <Link href="/health" className="hover:text-white">
                  System Health & Indexes
                </Link>
              </li>
              <li>
                <Link href="/crawler" className="hover:text-white">
                  Incremental Crawl Manager
                </Link>
              </li>
              <li>
                <Link href="/settings" className="hover:text-white">
                  Retrieval Tuning & Config
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-[#24558A]/30 flex flex-col sm:flex-row items-center justify-between text-xs text-[#E9EFF6]/50">
          <p>© {new Date().getFullYear()} MIT Academy of Engineering, Pune. All rights reserved.</p>
          <p className="mt-2 sm:mt-0 font-mono">MITAOE Knowledge Intelligence Platform</p>
        </div>
      </div>
    </footer>
  );
}
