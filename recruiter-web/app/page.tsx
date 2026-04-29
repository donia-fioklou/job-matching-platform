"use client";


import { useState } from "react";
import { Candidate, MatchResponse } from "@/lib/types";
import { CandidateCard } from "@/components/CandidateCard";

export default function Home() {
  const [description, setDescription] = useState("");
  // Valeurs fixes imposées
  const topK = 3;
  const minScore = 0.3;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<MatchResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_description: description.trim(),
          top_k: topK,
          min_score: minScore,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? "Erreur serveur");
      }

      const data: MatchResponse = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0" />
          </svg>
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-800">JobMatch — Recruteurs</h1>
          <p className="text-xs text-slate-400">Trouvez les meilleurs profils pour votre poste</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 flex flex-col gap-8">
        <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-1">Description du poste</h2>
          <p className="text-sm text-slate-500 mb-4">
            Collez ou rédigez la description du poste. L&apos;IA recherche les candidats dont le CV correspond le mieux.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex : Nous recherchons un développeur React expérimenté, maîtrisant TypeScript, Node.js et les bases de données PostgreSQL. Expérience 3+ ans requise..."
              rows={8}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
              required
            />

            <div className="flex flex-wrap gap-4 items-end">
              <button
                type="submit"
                disabled={loading || !description.trim()}
                className="ml-auto flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm px-6 py-2.5 rounded-xl transition-colors"
              >
                {loading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Analyse en cours…
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
                    </svg>
                    Trouver des profils
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {result && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800">
                {result.total_matched} profil{result.total_matched !== 1 ? "s" : ""} trouvé{result.total_matched !== 1 ? "s" : ""}
              </h2>
              <p className="text-xs text-slate-400">Classés par pertinence décroissante</p>
            </div>

            {result.candidates.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
                <p className="text-slate-500 text-sm">Aucun candidat ne correspond à ces critères.</p>
                <p className="text-slate-400 text-xs mt-1">Réduisez le score minimum ou reformulez la description.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {result.candidates.map((c: Candidate, i: number) => (
                  <CandidateCard key={c.id} candidate={c} rank={i + 1} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
