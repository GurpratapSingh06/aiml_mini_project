import React from "react";

export function Logo({ className = "w-8 h-8" }: { className?: string }) {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <svg
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Abstract connected V-shaped knowledge network */}
        <path
          d="M6 8 L20 32 L34 8"
          stroke="#102747"
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M12 8 L20 24 L28 8"
          stroke="#27A6A1"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Knowledge nodes */}
        <circle cx="6" cy="8" r="3" fill="#24558A" />
        <circle cx="34" cy="8" r="3" fill="#24558A" />
        <circle cx="20" cy="32" r="3.5" fill="#27A6A1" />
        <circle cx="12" cy="8" r="2.5" fill="#102747" />
        <circle cx="28" cy="8" r="2.5" fill="#102747" />
        <circle cx="20" cy="24" r="2.5" fill="#24558A" />
      </svg>
    </div>
  );
}
