export type ProductStatus =
  | 'research_only'
  | 'scored'
  | 'cad_generated'
  | 'manufacturing_simulated'
  | 'listing_generated'
  | 'prototype_candidate'
  | 'archived'

export interface ResearchDataSummary {
  id: number
  listed_price: number | null
  review_count: number | null
  rating: number | null
  estimated_sales: number | null
  competitor_count: number | null
}

export interface OpportunityScoreSummary {
  id: number
  total_score: number
  demand_score: number
  competition_score: number
  manufacturing_score: number
  margin_score: number
  differentiation_score: number
  scored_at: string
}

export interface Product {
  id: number
  name: string
  slug: string
  category: string
  source: string
  source_keyword: string | null
  source_notes: string | null
  status: ProductStatus
  created_at: string
  updated_at: string
  research_data: ResearchDataSummary[]
  latest_opportunity_score: OpportunityScoreSummary | null
}

export interface ProductListItem {
  id: number
  name: string
  slug: string
  category: string
  source: string
  status: ProductStatus
  created_at: string
  updated_at: string
  opportunity_score: number | null
  estimated_price: number | null
  competition_level: string | null
  manufacturing_difficulty: string | null
  profit_margin_estimate: number | null
}

export interface PipelineStageCounts {
  research_only: number
  scored: number
  cad_generated: number
  manufacturing_simulated: number
  listing_generated: number
  prototype_candidate: number
  archived: number
}

export interface TopOpportunitySummary {
  id: number
  name: string
  slug: string
  total_score: number
  category: string
}

export interface RecentActivityItem {
  id: number
  name: string
  slug: string
  type: string
  at: string
}

export interface DashboardSummary {
  total_products: number
  average_opportunity_score: number | null
  average_estimated_margin: number | null
  average_estimated_print_time_minutes: number | null
  pipeline_stage_counts: PipelineStageCounts
  top_opportunities: TopOpportunitySummary[]
  top_opportunity: TopOpportunitySummary | null
  fastest_to_manufacture: TopOpportunitySummary | null
  highest_margin: TopOpportunitySummary | null
  most_differentiable: TopOpportunitySummary | null
  recent_imports: RecentActivityItem[]
  recent_cad_generations: RecentActivityItem[]
  recent_listing_generations: RecentActivityItem[]
}

export interface ProductCreate {
  name: string
  category: string
  source?: string
  source_keyword?: string | null
  source_notes?: string | null
  status?: ProductStatus
}

export interface ProductUpdate {
  name?: string
  category?: string
  source?: string
  source_keyword?: string | null
  source_notes?: string | null
  status?: ProductStatus
}

export interface ResearchDataCreate {
  source_type?: string
  keyword?: string | null
  listed_price?: number | null
  review_count?: number | null
  rating?: number | null
  estimated_sales?: number | null
  competitor_count?: number | null
  listing_count?: number | null
  listing_age_days?: number | null
  notes?: string | null
}

export interface ResearchDataResponse {
  id: number
  product_id: number
  source_type: string
  keyword: string | null
  listed_price: number | null
  review_count: number | null
  rating: number | null
  estimated_sales: number | null
  competitor_count: number | null
  listing_count: number | null
  listing_age_days: number | null
  notes: string | null
  imported_at: string
}

export interface ImportRecordResponse {
  id: number
  file_name: string | null
  source_type: string
  record_count: number
  status: string
  notes: string | null
  imported_at: string
}

export interface ImportListItem {
  id: number
  file_name: string | null
  source_type: string
  record_count: number
  status: string
  imported_at: string
}

export interface CsvPreviewResponse {
  valid: boolean
  row_count: number
  errors: { row: number; message: string }[]
  preview: { name: string; category: string; source: string; listed_price: number | null; review_count: number | null; rating: number | null; estimated_sales: number | null; competitor_count: number | null }[]
}

export interface CadModelResponse {
  id: number
  product_id: number
  version: number
  model_type: string
  parameters_json: string | null
  scad_code: string | null
  scad_file_path: string | null
  stl_file_path: string | null
  generation_method: string
  created_at: string
}

export interface CadCreate {
  model_type: string
  parameters?: Record<string, number>
  /** When true, Claude suggests template + params from product/category (Etsy best-seller style). */
  use_ai?: boolean
}

export interface CadExportResult {
  success: boolean
  message: string
  stl_file_path?: string | null
}

export interface SimulationCreate {
  cad_model_id?: number | null
  material_type?: string
  layer_height?: number
  infill?: number
  nozzle_size?: number
}

export interface SimulationResponse {
  id: number
  product_id: number
  cad_model_id: number | null
  material_type: string
  layer_height: number
  infill: number
  nozzle_size: number
  estimated_print_time_minutes: number | null
  estimated_material_grams: number | null
  estimated_filament_cost: number | null
  supports_required: boolean
  recommended_orientation: string | null
  difficulty_score: number | null
  notes: string | null
  simulated_at: string
}

export interface SimulationResultWithWarnings {
  simulation: SimulationResponse
  warnings: string[]
}

export interface ListingResponse {
  id: number
  product_id: number
  version: number
  title: string | null
  short_pitch: string | null
  bullet_points_json: string | null
  description: string | null
  tags_json: string | null
  suggested_price: number | null
  photo_prompt: string | null
  why_it_could_sell: string | null
  differentiation_angle: string | null
  created_at: string
}

export interface ListingUpdate {
  title?: string | null
  short_pitch?: string | null
  bullet_points_json?: string | null
  description?: string | null
  tags_json?: string | null
  suggested_price?: number | null
  photo_prompt?: string | null
  why_it_could_sell?: string | null
  differentiation_angle?: string | null
}
