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
  /** ForgeFlow is Claude-only: design is always from Claude. Optional for request body. */
  model_type?: string
  parameters?: Record<string, number>
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

// ---------------------------------------------------------------------------
// Intake pipeline
// ---------------------------------------------------------------------------

export type IntakeStatus =
  | 'raw_collected'
  | 'enriching'
  | 'brief_drafted'
  | 'brief_approved'
  | 'rejected'
  | 'cad_queued'

export type TriggerMode = 'etsy_url' | 'erank_paste' | 'manual'

export interface IntakeImageResponse {
  id: string
  intake_id: string
  image_index: number | null
  source_url: string | null
  local_path: string
  file_size_bytes: number | null
  vision_analysis_json: Record<string, unknown> | null
  created_at: string
}

export interface IntakeListItem {
  id: string
  status: IntakeStatus
  trigger_mode: TriggerMode
  raw_title: string | null
  source_url: string | null
  source_keyword: string | null
  confidence_score: number | null
  image_count: number
  enrichment_attempt_count: number
  created_at: string
  updated_at: string
}

export interface IntakeResponse {
  id: string
  status: IntakeStatus
  trigger_mode: TriggerMode
  source_url: string | null
  source_keyword: string | null
  raw_title: string | null
  raw_description: string | null
  raw_tags: string[] | null
  raw_price_usd: number | null
  raw_review_count: number | null
  raw_rating: number | null
  image_count: number
  visual_summary_json: Record<string, unknown> | null
  text_extraction_json: Record<string, unknown> | null
  draft_brief_json: Record<string, unknown> | null
  approved_brief_json: Record<string, unknown> | null
  confidence_score: number | null
  confidence_detail_json: {
    per_field: Record<string, number>
    low_confidence_fields: string[]
    warning_level: 'red' | 'yellow' | 'green'
  } | null
  enrichment_attempt_count: number
  reviewer_notes: string | null
  approved_by: string | null
  approved_at: string | null
  rejection_reason: string | null
  product_id: number | null
  cad_model_id: number | null
  created_at: string
  updated_at: string
  images: IntakeImageResponse[]
}

export interface IntakeSubmitRequest {
  trigger_mode: TriggerMode
  source_url?: string | null
  source_keyword?: string | null
  raw_title?: string | null
}

export interface IntakeSubmitResponse {
  intake_id: string
  status: IntakeStatus
}

export interface IntakeApproveResponse {
  product_id: number
  cad_model_id: number
}
