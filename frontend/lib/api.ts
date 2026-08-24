export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Student = { id: number; source_row: number; name: string; gender: string; grade: number; Math: number; Science: number; English: number; total: number; status: "Active" | "Debarred" };
export type PerformanceMetrics = { csv_parse: number; validation_and_normalization: number; exact_deduplication: number; fuzzy_duplicate_review: number; total_cleaning: number };
export type Report = { input_rows: number; accepted_rows: number; rejected_rows: number; exact_duplicates_removed: number; totals_recalculated: number; unknown_gender_normalized: number; rules: string[]; rejected: { row: number; reason: string }[]; possible_duplicate_review: { name: string; source_row: number; possible_match: string; possible_source_row: number; similarity: string }[]; performance_ms: PerformanceMetrics };

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "The request failed.");
  }
  return response.json() as Promise<T>;
}
