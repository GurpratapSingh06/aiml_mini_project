"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "./Logo";
import {
  Search,
  FileText,
  Activity,
  Globe,
  BarChart3,
  Settings as SettingsIcon,
  ShieldCheck,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/search", label: "Search & Q&A", icon: Search },
    { href: "/documents", label: "Document Library", icon: FileText },
    { href: "/crawler", label: "Crawl Engine", icon: Globe },
    { href: "/analytics", label: "Knowledge Analytics", icon: BarChart3 },
    { href: "/health", label: "System Health", icon: Activity },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#102747] text-white shadow-md border-b border-[#24558A]/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="bg-white p-1 rounded-lg shadow-sm">
              <Logo className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-lg tracking-wider text-white">
                  VEDANTA
                </span>
                <span className="text-[10px] uppercase tracking-widest bg-[#27A6A1] text-white px-1.5 py-0.5 rounded font-semibold">
                  MITAOE
                </span>
              </div>
              <p className="text-[11px] text-[#E9EFF6]/70 leading-none">
                Discover Knowledge. Trust Every Answer.
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[#24558A] text-white shadow-inner"
                      : "text-[#E9EFF6]/80 hover:bg-[#24558A]/50 hover:text-white"
                  }`}
                >
                  <Icon className="w-4 h-4 text-[#27A6A1]" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Institutional Trust Indicator */}
          <div className="hidden lg:flex items-center space-x-2 text-xs text-[#27A6A1] bg-[#102747]/80 border border-[#27A6A1]/40 px-2.5 py-1.5 rounded-full">
            <ShieldCheck className="w-4 h-4" />
            <span className="font-medium text-[#E9EFF6]">Evidence-Backed Intelligence</span>
          </div>
        </div>
      </div>
    </header>
  );
}
