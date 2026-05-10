export interface FavoriteSchool {
  id: number;
  school_id: number;
  school_name: string;
  province: string | null;
  city: string | null;
  created_at: string;
}

export interface FavoriteSchoolStatus {
  school_id: number;
  is_favorited: boolean;
}
