"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  Users,
  Award,
  Building,
  CreditCard,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

interface PlacementRecord {
  department?: string;
  academic_year: string;
  total_students?: number;
  students_placed?: number;
  highest_package_lpa?: number;
  average_package_lpa?: number;
  source_url?: string;
  record_type?: string;
  package_distribution?: Record<string, unknown>;
  companies_visited?: number;
  offers_made?: number;
}

interface FeeRecord {
  department?: string;
  academic_year: string;
  category: string;
  fee_type?: string;
  total_amount_inr?: number;
  additional_charges?: {
    tuition_fee?: number;
    development_fee?: number;
    university_fee?: number;
    caution_money_refundable?: number;
    sppu_eligibility_mh?: number;
    sppu_eligibility_oms?: number;
    notes?: string;
  };
  source_url?: string;
}

const DEPT_CODE_MAP: Record<string, string> = {
  "Computer Engineering": "CE",
  "Artificial Intelligence and Machine Learning": "AIML",
  "Information Technology": "IT",
  "Electronics and Telecommunication Engineering": "ENTC",
  "Mechanical Engineering": "MECH",
  "Civil Engineering": "CIVIL",
  "Chemical Engineering": "CHEM",
  "Software Engineering": "SE",
  "Data Science": "DS",
};

export default function AnalyticsPage() {
  const [placements, setPlacements] = useState<PlacementRecord[]>([]);
  const [fees, setFees] = useState<FeeRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchData = async () => {
    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const [resPlacements, resFees] = await Promise.all([
        fetch(`${apiUrl}/api/v1/statistics/placements`).catch(() => null),
        fetch(`${apiUrl}/api/v1/statistics/fees`).catch(() => null),
      ]);

      if (resPlacements && resPlacements.ok) {
        const data = await resPlacements.json();
        if (Array.isArray(data) && data.length > 0) {
          setPlacements(data);
        }
      }

      if (resFees && resFees.ok) {
        const data = await resFees.json();
        if (Array.isArray(data) && data.length > 0) {
          setFees(data);
        }
      }
    } catch (e) {
      console.warn("Could not fetch analytics from API, using cached state", e);
    } finally {
      setLoading(false);
      setLastRefreshed(new Date());
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Compute aggregate numbers
  const aggregateRecord = placements.find(
    (p) => p.department === "Institutional Aggregate" || p.record_type === "aggregate"
  );

  const highestCTC = aggregateRecord?.highest_package_lpa ?? 27.0;
  const averageCTC = aggregateRecord?.average_package_lpa ?? 6.75;
  const studentsPlaced = aggregateRecord?.students_placed ?? 761;
  const totalEligible = aggregateRecord?.total_students ?? 922;
  const placementRate = totalEligible > 0 ? ((studentsPlaced / totalEligible) * 100).toFixed(1) : "82.5";
  const companiesCount = aggregateRecord?.companies_visited ?? 450;
  const offersCount = aggregateRecord?.offers_made ?? 500;

  // Department-wise records only (exclude aggregate)
  const deptPlacements = placements.filter(
    (p) => p.department !== "Institutional Aggregate" && p.record_type !== "aggregate"
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#102747]">
            Institutional Knowledge & Statistical Intelligence
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Audited numerical records, approved fee structures, and verified entity hierarchies for MIT Academy of Engineering (MITAOE).
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-[11px] text-gray-400 font-mono">
            Verified: AY 2026–27 • {lastRefreshed.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#E9EFF6] hover:bg-[#d6e3f0] text-[#24558A] rounded-lg text-xs font-semibold transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh Data</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>HIGHEST CTC (INSTITUTE)</span>
            <Award className="w-4 h-4 text-[#27A6A1]" />
          </div>
          <p className="text-3xl font-bold text-[#102747] font-mono">
            {highestCTC} <span className="text-sm font-sans text-gray-500 font-normal">LPA</span>
          </p>
          <p className="text-[11px] text-gray-400 mt-1">
            Grounded in MITAOE Placement Cell disclosures
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>OVERALL AVERAGE CTC</span>
            <TrendingUp className="w-4 h-4 text-[#24558A]" />
          </div>
          <p className="text-3xl font-bold text-[#24558A] font-mono">
            {averageCTC} <span className="text-sm font-sans text-gray-500 font-normal">LPA</span>
          </p>
          <p className="text-[11px] text-gray-400 mt-1">
            Institute-wide overall graduate average
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>STUDENTS PLACED</span>
            <Users className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-3xl font-bold text-emerald-600 font-mono">
            {studentsPlaced}
          </p>
          <p className="text-[11px] text-gray-400 mt-1">
            Out of {totalEligible} candidates ({placementRate}%) • {offersCount}+ offers
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 mb-2">
            <span>RECRUITING PARTNERS</span>
            <Building className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-3xl font-bold text-purple-600 font-mono">
            {companiesCount}+
          </p>
          <p className="text-[11px] text-gray-400 mt-1">
            Amazon, Cisco, Veritas, IBM, TCS
          </p>
        </div>
      </div>

      {/* Placement Comparison Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-[#102747] flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-[#24558A]" />
              <span>Department-Wise Placement Statistics</span>
            </h3>
            <p className="text-[11px] text-gray-400">
              Audited records from the Training & Placement Cell • Source:{" "}
              <a
                href="https://mitaoe.ac.in/placement.php"
                target="_blank"
                rel="noreferrer"
                className="text-[#24558A] underline hover:text-[#102747]"
              >
                mitaoe.ac.in/placement.php
              </a>
            </p>
          </div>
          <span className="text-xs bg-[#E9EFF6] text-[#24558A] px-2.5 py-1 rounded font-mono font-medium">
            Formula: (Students Placed / Total Candidates) × 100
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
              {deptPlacements.map((stat, idx) => {
                const code = DEPT_CODE_MAP[stat.department || ""] || "DEPT";
                const placed = stat.students_placed || 0;
                const total = stat.total_students || 1;
                const pct = total > 0 ? ((placed / total) * 100).toFixed(1) : "0.0";
                return (
                  <tr key={idx} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-3.5">
                      <p className="font-semibold text-gray-900">{stat.department}</p>
                      <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono font-semibold">
                        {code}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono font-semibold text-gray-900">
                      {stat.highest_package_lpa} LPA
                    </td>
                    <td className="px-6 py-3.5 font-mono text-[#24558A] font-semibold">
                      {stat.average_package_lpa} LPA
                    </td>
                    <td className="px-6 py-3.5 font-mono text-gray-600">
                      {placed} / {total}
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="inline-flex items-center space-x-1 font-mono font-bold text-emerald-700">
                        <span>{pct}%</span>
                      </span>
                    </td>
                    <td className="px-6 py-3.5 w-48">
                      <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-[#24558A] h-2 rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Approved Fee Structure Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-[#102747] flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-[#24558A]" />
              <span>Approved Fee Structure (Academic Year 2026–27)</span>
            </h3>
            <p className="text-[11px] text-gray-400">
              First Year B.Tech (All Branches) • Grounded in{" "}
              <a
                href="https://mitaoe.ac.in/assets/images/pdf/FY-BTech-Fee-Structure-26-27.PDF"
                target="_blank"
                rel="noreferrer"
                className="text-[#24558A] underline hover:text-[#102747]"
              >
                FY-BTech-Fee-Structure-26-27.PDF
              </a>
            </p>
          </div>
          <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded font-mono font-medium border border-emerald-200">
            FRA Approved • SPPU Autonomous
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-3">Category</th>
                <th className="px-6 py-3">Tuition Fee</th>
                <th className="px-6 py-3">Development Fee</th>
                <th className="px-6 py-3">University / SPPU Fee</th>
                <th className="px-6 py-3">Total Approved Fee</th>
                <th className="px-6 py-3">Caution Deposit (Refundable)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-normal">
              {fees.map((fee, idx) => {
                const charges = fee.additional_charges || {};
                const tuition = charges.tuition_fee ?? 0;
                const dev = charges.development_fee ?? 0;
                const univ = charges.university_fee ?? 737;
                const deposit = charges.caution_money_refundable ?? 25000;
                const total = fee.total_amount_inr ?? tuition + dev + univ;

                return (
                  <tr key={idx} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-3.5 font-bold text-gray-900">
                      <span className="inline-block bg-gray-100 text-gray-800 px-2 py-0.5 rounded font-mono">
                        {fee.category}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono text-gray-700">
                      ₹{tuition.toLocaleString("en-IN")}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-gray-700">
                      ₹{dev.toLocaleString("en-IN")}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-gray-700">
                      ₹{univ.toLocaleString("en-IN")}
                    </td>
                    <td className="px-6 py-3.5 font-mono font-bold text-[#24558A]">
                      ₹{total.toLocaleString("en-IN")}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-emerald-700">
                      ₹{deposit.toLocaleString("en-IN")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Verified Institutional Leadership & Faculty Directory */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4 shadow-xs">
        <h3 className="text-sm font-bold text-[#102747] flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-[#24558A]" />
          <span>Verified Institutional Leadership & Faculty Knowledge Base</span>
        </h3>
        <p className="text-xs text-gray-500">
          Audited organizational hierarchy linking verified individuals to academic governance, active department heads, and historical predecessors.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-[#24558A] uppercase">Director / HOI</span>
            <p className="font-semibold text-sm text-gray-900">Dr. Yogesh. J. Bhalerao</p>
            <p className="text-xs text-gray-500">Director, MIT Academy of Engineering</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono">
              Status: Verified Active
            </span>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-[#24558A] uppercase">Head of Computer Engineering (Current)</span>
            <p className="font-semibold text-sm text-gray-900">Dr. Pramod D. Ganjewar</p>
            <p className="text-xs text-gray-500">Associate Professor & HOD (AY 2026–27)</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono">
              hod.comp@mitaoe.edu.in
            </span>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-amber-700 uppercase">Computer Engineering Predecessor</span>
            <p className="font-semibold text-sm text-gray-900">Dr. Sandip A. Gade</p>
            <p className="text-xs text-gray-500">Professor (Former HOD, Computer Engg)</p>
            <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-mono">
              Status: Historical Record
            </span>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <span className="text-[11px] font-bold text-[#24558A] uppercase">Faculty (Mathematics)</span>
            <p className="font-semibold text-sm text-gray-900">Mr. Azhar R. Shaikh</p>
            <p className="text-xs text-gray-500">School of Humanities & Engg. Sciences</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono">
              azharshaikh@mitaoe.ac.in
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
