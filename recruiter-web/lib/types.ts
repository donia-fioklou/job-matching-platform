export interface Candidate {
  id: number;
  name: string;
  job_title: string | null;
  city: string | null;
  email: string | null;
  phone: string | null;
  score: number;
}

export interface MatchResponse {
  total_matched: number;
  candidates: Candidate[];
}
