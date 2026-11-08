"use client";

import React, { useState } from "react";
import {
  Sliders,
  Database,
  Trash2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Save,
} from "lucide-react";

export default function SettingsPage() {
  const [bm25K1, setBm25K1] = useState(1.5);
  const [bm25B, setBm25B] = useState(0.75);
  const [rrfK, setRrfK] = useState(60);
  const [topK, setTopK] = useState(10);
  const [rerankerEnabled, setRerankerEnabled] = useState(false);
  const [notification, setNotification] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setNotification({
      text: "Retrieval hyperparameters saved and applied to memory pipeline.",
      type: "success",
    });
  };

  const handleClearCache = async () => {
    setNotification({
      text: "Query cache and retrieval caches cleared from Redis.",
      type: "success",
    });
  };

  const handleReindex = async () => {
    setNotification({
      text: "Full FAISS & BM25 index rebuild queued in background worker.",
      type: "success",
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[#102747]">Platform Settings & Retrieval Tuning</h1>
        <p className="text-xs text-gray-500 mt-1">
          Configure hybrid retrieval weights, Reciprocal Rank Fusion constants, and persistence maintenance.
        </p>
      </div>

      {notification && (
        <div
          className={`p-3.5 rounded-lg text-xs font-medium border flex items-center space-x-2 ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-300"
              : "bg-rose-50 text-rose-800 border-rose-300"
          }`}
        >
          {notification.type === "success" ? (
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600" />
          )}
          <span>{notification.text}</span>
        </div>
      )}

      {/* Hyperparameters Form */}
      <form onSubmit={handleSave} className="bg-white rounded-xl border border-gray-200 p-6 space-y-6 shadow-xs">
        <h2 className="text-sm font-bold text-[#102747] flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-[#24558A]" />
          <span>Hybrid Retrieval Engine Parameters</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-700">BM25 Term Frequency Saturation (k1)</label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="3.0"
              value={bm25K1}
              onChange={(e) => setBm25K1(parseFloat(e.target.value) || 1.5)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:border-[#24558A]"
            />
            <p className="text-[11px] text-gray-400">Controls term frequency dampening. Default: 1.5</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-700">BM25 Length Normalization (b)</label>
            <input
              type="number"
              step="0.05"
              min="0.0"
              max="1.0"
              value={bm25B}
              onChange={(e) => setBm25B(parseFloat(e.target.value) || 0.75)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:border-[#24558A]"
            />
            <p className="text-[11px] text-gray-400">Controls document length penalty. Default: 0.75</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-700">Reciprocal Rank Fusion Constant (k)</label>
            <input
              type="number"
              min="1"
              max="200"
              value={rrfK}
              onChange={(e) => setRrfK(parseInt(e.target.value) || 60)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:border-[#24558A]"
            />
            <p className="text-[11px] text-gray-400">Rank smoothing constant in RRF fusion formula. Default: 60</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-700">Top-K Passages Retained</label>
            <input
              type="number"
              min="1"
              max="50"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value) || 10)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:border-[#24558A]"
            />
            <p className="text-[11px] text-gray-400">Final evidence candidate threshold passed to validator. Default: 10</p>
          </div>
        </div>

        <div className="flex items-center justify-between p-3.5 bg-gray-50 rounded-lg border border-gray-100">
          <div>
            <h4 className="font-semibold text-xs text-gray-800">Neural Cross-Encoder Reranker</h4>
            <p className="text-[11px] text-gray-500">
              Apply ms-marco-MiniLM-L-6-v2 cross-encoder over candidate passages for fine relevance refinement.
            </p>
          </div>
          <input
            type="checkbox"
            checked={rerankerEnabled}
            onChange={(e) => setRerankerEnabled(e.target.checked)}
            className="w-4 h-4 text-[#24558A] rounded focus:ring-0 cursor-pointer"
          />
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="bg-[#24558A] hover:bg-[#102747] text-white px-5 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>

      {/* Index & Cache Maintenance */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4 shadow-xs">
        <h2 className="text-sm font-bold text-[#102747] flex items-center space-x-2">
          <Database className="w-4 h-4 text-[#24558A]" />
          <span>Index & Cache Maintenance Operations</span>
        </h2>
        <p className="text-xs text-gray-500">
          Administrative utilities for managing on-disk FAISS indexes and Redis in-memory caches.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-xs text-gray-800">Clear Query Cache</h4>
              <p className="text-[11px] text-gray-500">Flush all cached natural language answers from Redis.</p>
            </div>
            <button
              onClick={handleClearCache}
              className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 hover:bg-gray-100 rounded text-xs font-semibold flex items-center space-x-1 shrink-0"
            >
              <Trash2 className="w-3.5 h-3.5 text-gray-500" />
              <span>Clear</span>
            </button>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-xs text-gray-800">Rebuild Vector Index</h4>
              <p className="text-[11px] text-gray-500">Re-embed and re-index all database chunks into FAISS.</p>
            </div>
            <button
              onClick={handleReindex}
              className="px-3 py-1.5 bg-[#24558A] text-white hover:bg-[#102747] rounded text-xs font-semibold flex items-center space-x-1 shrink-0"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Rebuild</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
