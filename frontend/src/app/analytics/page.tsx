"use client";

import React from "react";
import {
  TrendingUp,
  Users,
  Award,
  Building,
} from "lucide-react";

interface PlacementStat {
  dept: string;
  code: string;
  highest: number;
  average: number;
  placed: number;
  total: number;
  percentage: number;
}

const mockStats: PlacementStat[] = [
  { dept: "Computer Engineering", code: "CE", highest: 24.5, average: 6.8, placed: 182, total: 206, percentage: 88.3 },
  { dept: "Computer Science & Engineering", code: "CSE", highest: 22.0, average: 6.5, placed: 124, total: 140, percentage: 88.5 },
  { dept: "Artificial Intelligence & ML", code: "AIML", highest: 21.0, average: 6.9, placed: 58, total: 66, percentage: 87.8 },
  { dept: "Information Technology", code: "IT", highest: 18.0, average: 6.2, placed: 110, total: 130, percentage: 84.6 },
  { dept: "Electronics & Telecomm.", code: "ENTC", highest: 16.5, average: 5.4, placed: 145, total: 180, percentage: 80.5 },
  { dept: "Mechanical Engineering", code: "MECH", highest: 12.0, average: 4.8, placed: 98, total: 135, percentage: 72.5 },
  { dept: "Civil Engineering", code: "CIVIL", highest: 9.5, average: 4.2, placed: 44, total: 65, percentage: 67.7 },
];

export default function AnalyticsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[#102747]">
          Institutional Statistical & Entity Analytics
        </h1>
        <p className="text-xs text-gray-500 mt-1">
          Deterministic numerical intelligence extracted from primary placement disclosures and audited annual reports.
        </p>
      </div>

      {/* Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-200">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>HIGHEST CTC (INSTITUTE)</span>
            <Award className="w-4 h-4 text-[#27A6A1]" />
          </div>
          <p className="text-3xl font-bold text-[#102747] font-mono">24.5 <span className="text-sm font-sans text-gray-500 font-normal">LPA</span></p>
          <p className="text-[11px] text-gray-400 mt-1">Computer Engineering (2023-24)</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>OVERALL AVG CTC</span>
            <TrendingUp className="w-4 h-4 text-[#24558A]" />
          </div>
          <p className="text-3xl font-bold text-[#24558A] font-mono">5.85 <span className="text-sm font-sans text-gray-500 font-normal">LPA</span></p>
          <p className="text-[11px] text-gray-400 mt-1">Across 7 B.Tech departments</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>STUDENTS PLACED</span>
            <Users className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-3xl font-bold text-emerald-600 font-mono">761</p>
          <p className="text-[11px] text-gray-400 mt-1">Out of 922 eligible candidates (82.5%)</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>RECRUITING PARTNERS</span>
            <Building className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-3xl font-bold text-purple-600 font-mono">140+</p>
          <p className="text-[11px] text-gray-400 mt-1">Amazon, Cisco, Veritas, BMC, TCS</p>
        </div>
      </div>

      {/* Placement Comparison Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-[#102747]">Department-Wise Placement Statistics</h3>
            <p className="text-[11px] text-gray-400">Grounded in Training & Placement Cell records • AY 2023-24</p>
          </div>
          <span className="text-xs bg-[#E9EFF6] text-[#24558A] px-2.5 py-1 rounded font-mono font-medium">
            Formula Provenance: (Placed / Eligible) × 100
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-3">Department</th>
                <th className="px-6 py-3">Highest CTC</th>
                <th className="px-6 py-3">Average CTC</th>
                <th className="px-6 py-3">Placed / Total</th>
                <th className="px-6 py-3">Placement %</th>
                <th className="px-6 py-3">Distribution Bar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-normal">
              {mockStats.map((stat, idx) => (
                <tr key={idx} className="hover:bg-gray-50/80 transition-colors">
                  <td className="px-6 py-3.5">
                    <p className="font-semibold text-gray-900">{stat.dept}</p>
                    <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono font-semibold">
                      {stat.code}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 font-mono font-semibold text-gray-900">
                    {stat.highest} LPA
                  </td>
                  <td className="px-6 py-3.5 font-mono text-[#24558A] font-semibold">
                    {stat.average} LPA
                  </td>
                  <td className="px-6 py-3.5 font-mono text-gray-600">
                    {stat.placed} / {stat.total}
                  </td>
                  <td className="px-6 py-3.5">
                    <span className="inline-flex items-center space-x-1 font-mono font-bold text-emerald-700">
                      <span>{stat.percentage}%</span>
                    </span>
                  </td>
                  <td className="px-6 py-3.5 w-48">
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-[#24558A] h-2 rounded-full"
                        style={{ width: `${stat.percentage}%` }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Institutional Entities Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h3 className="text-sm font-bold text-[#102747] flex items-center space-x-2">
          <Users className="w-4 h-4 text-[#24558A]" />
          <span>Extracted Institutional Entities & Relationships</span>
        </h3>
        <p className="text-xs text-gray-500">
          Audited organizational hierarchy linking verified individuals to academic roles and council responsibilities.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-[#24558A] uppercase">Director / Head of Institution</span>
            <p className="font-semibold text-sm text-gray-900">Dr. Mahesh Goudar</p>
            <p className="text-xs text-gray-500">Director, MIT Academy of Engineering</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono">
              Status: Verified Active
            </span>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-[#24558A] uppercase">Head of Computer Engineering</span>
            <p className="font-semibold text-sm text-gray-900">Dr. Sandip A. Gade</p>
            <p className="text-xs text-gray-500">School of Computer Engineering</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono">
              Status: Verified Active
            </span>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-[#24558A] uppercase">Dean (Academics)</span>
            <p className="font-semibold text-sm text-gray-900">Dr. Sunita S. Barve</p>
            <p className="text-xs text-gray-500">Dean Academics & Autonomous Curriculum</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono">
              Status: Verified Active
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
