export type DecimalValue = string | number;
export interface Page<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}
export interface Question {
  id: number;
  owner: number;
  text: string;
  subject: string;
  options: string[];
  correct_option: number;
  points: DecimalValue;
  image_url: string | null;
  created_at: string;
}
export interface Snapshot {
  position: number;
  text: string;
  options: string[];
  correct_option: number;
  selected: number | null;
  points: DecimalValue;
}
export interface Result {
  id: string;
  quiz: number;
  quiz_title: string;
  student: number;
  student_name: string;
  number: number;
  status: string;
  started_at: string;
  deadline: string;
  finished_at: string | null;
  correct: number;
  incorrect: number;
  unanswered: number;
  earned: DecimalValue;
  maximum: DecimalValue;
  percentage: DecimalValue;
  elapsed_seconds: number;
  questions?: Snapshot[];
}
export interface Student {
  id: number;
  full_name: string;
  telegram_username: string;
  is_active: boolean;
  registered_at: string;
  participation_count: number;
  average_percentage: DecimalValue | null;
  last_activity: string | null;
  attempts?: Result[];
}
export interface Group {
  id: number;
  name: string;
  students: number[];
}
export interface ImportRow {
  source_row:number;
  text: string;
  options: string[];
  correct_option: number;
  points: string;
  image_base64: string | null;
}
export interface ImportPreview {
  total_rows?:number;image_count?:number;invalid_rows?:number;
  id: string;
  count: number;
  rows: ImportRow[];
  errors: { row: number; message: string }[];
}
export interface ExportJob {
  id: string;
  status: string;
  error: string;
  created_at: string;
  finished_at: string | null;
}
export interface RankingRow {
  student_id: number;
  rank: number;
  name: string;
  percentage: DecimalValue;
  quizzes: number;
  elapsed_seconds: number;
}
export interface StudentSummary {
  student_id: number;
  student__full_name: string;
  attempts: number;
  percentage: DecimalValue;
  last_activity: string | null;
}
export interface TeacherSummary {
  quiz__owner_id: number;
  quiz__owner__full_name: string;
  quiz__owner__username: string;
  quizzes: number;
  attempts: number;
  students: number;
  percentage: DecimalValue;
}
export type ReportRow = Partial<
  Result & RankingRow & StudentSummary & TeacherSummary
>;
export interface Dashboard {
  quizzes: number;
  published: number;
  participants: number;
  completed: number;
  average: DecimalValue;
  teachers: number | null;
  active_teachers: number | null;
  students: number | null;
  attempts: number;
  activity: { date: string; attempts: number }[];
  recent_quizzes: {
    id: number;
    title: string;
    subject: string;
    status: string;
  }[];
  status_distribution: { status: string; count: number }[];
  most_active: { quiz_id: number; quiz__title: string; count: number }[];
  recent_attempts: Result[];
}
export interface CommandResponse {
  code?: string;
  temporary_password?: string;
  id?: string | number;
  status?: string;
}
export interface CsrfToken {
  csrfToken: string;
}
