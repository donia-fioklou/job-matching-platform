import { Candidate } from "@/lib/types";

interface Props {
  candidate: Candidate;
  rank: number;
}

export function CandidateCard({ candidate, rank }: Props) {
  const scorePercent = Math.round(candidate.score * 100);
  const scoreColor =
    scorePercent >= 70
      ? "bg-emerald-500"
      : scorePercent >= 45
      ? "bg-amber-400"
      : "bg-slate-400";

  const initials = candidate.name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex gap-4 hover:shadow-md transition-shadow">
      {/* Rank + avatar */}
      <div className="flex flex-col items-center gap-2 min-w-[44px]">
        <span className="text-xs font-semibold text-slate-400">#{rank}</span>
        <div className="w-11 h-11 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm select-none">
          {initials}
        </div>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-slate-800 truncate">{candidate.name}</p>
        {candidate.job_title && (
          <p className="text-sm text-slate-500 truncate">{candidate.job_title}</p>
        )}
        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-slate-500">
          {candidate.city && (
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21c-4-4-7-7.5-7-11a7 7 0 0114 0c0 3.5-3 7-7 11z" />
                <circle cx="12" cy="10" r="2" />
              </svg>
              {candidate.city}
            </span>
          )}
          {candidate.email && (
            <a href={`mailto:${candidate.email}`} className="flex items-center gap-1 hover:text-indigo-600 transition-colors">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path strokeLinecap="round" d="M2 7l10 7 10-7" />
              </svg>
              {candidate.email}
            </a>
          )}
          {candidate.phone && (
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h2l2 5-2 2a14 14 0 006 6l2-2 5 2v2a2 2 0 01-2 2A18 18 0 013 5z" />
              </svg>
              {candidate.phone}
            </span>
          )}
        </div>
      </div>

      {/* Score */}
      <div className="flex flex-col items-center justify-center min-w-[56px]">
        <div className={`${scoreColor} text-white text-sm font-bold rounded-full w-12 h-12 flex items-center justify-center`}>
          {scorePercent}%
        </div>
        <p className="text-xs text-slate-400 mt-1">match</p>
      </div>
    </div>
  );
}
