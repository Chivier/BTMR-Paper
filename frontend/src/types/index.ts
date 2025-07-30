// API Types matching the backend models

export interface PaperProcessRequest {
  input_source: string;
  input_type: 'arxiv' | 'url' | 'md' | 'pdf';
  output_format: 'html' | 'pdf';
  language: 'en' | 'zh';
  fetch_format?: string;
  save_json?: boolean;
  model?: string;
  openai_base_url?: string;
}

export interface Figure {
  url: string;
  caption: string;
  figure_type?: string;
}

export interface Subsection {
  title: string;
  content: string;
  figures: Figure[];
}

export interface Contribution {
  title: string;
  content: string;
}

export interface Background {
  title: string;
  content: string;
  subsections: Subsection[];
}

export interface Method {
  description?: string;
  key_points: string[];
  subsections: Subsection[];
  figures: Figure[];
}

export interface Results {
  evaluation?: string;
  baseline?: string;
  datasets?: string;
  experimental_setup?: string;
  subsections: Subsection[];
  figures: Figure[];
  tables: Figure[];
}

export interface ExtractedData {
  title: string;
  authors: string[] | string;
  abstract: string;
  background: Background[];
  contributions: Contribution[];
  method?: Method;
  results?: Results;
  processing_metadata?: Record<string, any>;
}

export interface ProcessingProgress {
  paper_id: string;
  status: 'pending' | 'fetching' | 'extracting' | 'generating' | 'completed' | 'failed';
  progress: number;
  message: string;
  timestamp: string;
  error?: string;
}

export interface PaperMetadata {
  paper_id: string;
  title: string;
  authors: string[] | string;
  arxiv_url?: string;
  format_used: string;
  output_format: 'html' | 'pdf';
  language: 'en' | 'zh';
  processing_time: number;
  created_at: string;
  file_size?: number;
  status: 'pending' | 'fetching' | 'extracting' | 'generating' | 'completed' | 'failed';
  error_message?: string;
  retry_count: number;
  last_failed_at?: string;
}

export interface PaperResponse {
  metadata: PaperMetadata;
  extracted_data: ExtractedData;
  output_path: string;
  json_path?: string;
  images_path?: string;
}

export interface PaperListResponse {
  papers: PaperMetadata[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface FileUploadResponse {
  filename: string;
  file_path: string;
  file_size: number;
  content_type: string;
  upload_id: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  dependencies: Record<string, string>;
}

export interface Statistics {
  total_papers: number;
  total_processing_time: number;
  average_processing_time: number;
  format_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  active_processes: number;
}

// Frontend-specific types

export interface ProcessingJob {
  id: string;
  request: PaperProcessRequest;
  progress: ProcessingProgress;
  startTime: Date;
  websocket?: WebSocket;
}

export interface AppState {
  currentJob?: ProcessingJob;
  recentPapers: PaperMetadata[];
  selectedPaper?: PaperMetadata;
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
}

export interface SearchFilters {
  query?: string;
  format?: 'html' | 'pdf' | 'all';
  language?: 'en' | 'zh' | 'all';
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export interface PaginationState {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

// Component Props Types

export interface PaperCardProps {
  paper: PaperMetadata;
  onSelect?: (paper: PaperMetadata) => void;
  onDelete?: (paperId: string) => void;
  showActions?: boolean;
}

export interface ProgressBarProps {
  progress: number;
  status: ProcessingProgress['status'];
  message?: string;
  className?: string;
}

export interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  accept?: string[];
  maxSize?: number;
  disabled?: boolean;
}

export interface PaperViewerProps {
  paper: PaperResponse;
  format: 'html' | 'pdf' | 'json';
}

export interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  loading?: boolean;
}

// Error Types

export interface ApiError {
  error: string;
  detail?: string;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

// WebSocket Message Types

export interface WebSocketMessage {
  type: 'progress' | 'error' | 'complete' | 'ping' | 'pong';
  data?: any;
}

// Utility Types

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export type SortField = 'created_at' | 'title' | 'processing_time' | 'authors';
export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

// Form Types

export interface ProcessPaperForm {
  inputSource: string;
  inputType: PaperProcessRequest['input_type'];
  outputFormat: PaperProcessRequest['output_format'];
  language: PaperProcessRequest['language'];
  fetchFormat: string;
  saveJson: boolean;
  customModel?: string;
  customApiBase?: string;
}

export interface UploadedFile {
  file: File;
  uploadId?: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

// Configuration Types

export interface ConfigurationRequest {
  openai_api_key?: string;
  openai_api_base?: string;
  default_model?: string;
  translate_model?: string;
  max_paper_length?: number;
  max_image_size_mb?: number;
  request_timeout?: number;
  default_output_format?: string;
  default_language?: string;
  image_quality?: number;
  max_image_dimension?: number;
  log_level?: string;
}

export interface ConfigurationResponse {
  openai_api_key: string;
  openai_api_base: string;
  default_model: string;
  translate_model: string;
  max_paper_length: number;
  max_image_size_mb: number;
  request_timeout: number;
  default_output_format: string;
  default_language: string;
  image_quality: number;
  max_image_dimension: number;
  log_level: string;
  colors: Record<string, string>;
}

export interface ConfigurationValidation {
  valid: boolean;
  issues: string[];
  warnings: string[];
  config_file_exists: boolean;
  env_file_exists: boolean;
}

export interface AvailableModel {
  id: string;
  name: string;
  description: string;
  recommended: boolean;
}

export interface AvailableModelsResponse {
  models: AvailableModel[];
  custom_note: string;
  error?: string;
  last_updated?: string;
}

export interface ConfigurationForm {
  apiSettings: {
    openai_api_key: string;
    openai_api_base: string;
    default_model: string;
    translate_model: string;
  };
  processingSettings: {
    max_paper_length: number;
    max_image_size_mb: number;
    request_timeout: number;
    default_output_format: string;
    default_language: string;
  };
  imageSettings: {
    image_quality: number;
    max_image_dimension: number;
  };
  systemSettings: {
    log_level: string;
  };
}
