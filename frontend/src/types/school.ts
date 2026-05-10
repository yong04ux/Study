export interface SchoolListItem {
  id: number;
  school_name: string;
  province: string;
  city: string | null;
  school_type: string | null;
  school_level: string | null;
  is_985: boolean;
  is_211: boolean;
  is_double_first_class: boolean;
  is_favorited?: boolean;
}

export interface SchoolDetail extends SchoolListItem {
  school_code: string;
  description?: string | null;
}

export interface SchoolSearchParams {
  school_name?: string;
  province?: string;
  school_level?: string;
  is_985?: boolean;
  is_211?: boolean;
  page?: number;
  page_size?: number;
}

export interface SchoolSearchResponse {
  total: number;
  page: number;
  page_size: number;
  items: SchoolListItem[];
}

export interface SchoolScoreLineParams {
  province?: string;
  year?: number;
  subject_type?: string;
  major_name?: string;
}

export interface ScoreLine {
  major_name: string | null;
  year: number;
  province: string;
  subject_type: string;
  batch: string;
  min_score: number;
  min_rank: number | null;
  avg_score: number | null;
  max_score: number | null;
}

export type SchoolSummary = SchoolListItem;
export type SchoolScoreLine = ScoreLine;
