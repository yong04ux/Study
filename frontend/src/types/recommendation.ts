export interface RecommendationRequest {
  user_id: string;
  province: string;
  subject_type: string;
  score: number;
  rank: number;
  preferred_provinces: string[];
  preferred_majors: string[];
}

export interface RecommendationScoreAnalysis {
  level: string;
  summary: string;
  suggestion: string;
}

export interface RecommendationChoiceItem {
  school_id?: number | null;
  major_id?: number | null;
  school_name: string;
  name?: string;
  major_name: string;
  province: string;
  city?: string | null;
  min_score: number;
  estimated_min_score?: number;
  min_rank?: number | null;
  estimated_min_rank?: number | null;
  is_985: boolean;
  is_211: boolean;
  is_double_first_class: boolean;
  tags?: string[];
  reason: string;
}

export interface RecommendationChoiceGroup {
  rush: RecommendationChoiceItem[];
  stable: RecommendationChoiceItem[];
  safe: RecommendationChoiceItem[];
}

export interface RecommendationResponse {
  score_analysis: RecommendationScoreAnalysis;
  recommended_choices: RecommendationChoiceGroup;
  study_plan: string | Record<string, unknown>;
  final_answer: string;
}
