export interface CollectionPolicy {
  method: string;
  historical_sample_target: number;
  weekly_refresh_policy: string;
  language_scope: string[];
  supported_review_types: string[];
  known_limitations: string[];
}

export interface MetricDefinitions {
  steam_recommendation: string;
  model_sentiment: string;
  aspect_sentiment: string;
  topic_prevalence: string;
}

export interface MethodologyData {
  version: string;
  updated_at: string;
  collection_policy: CollectionPolicy;
  definitions: MetricDefinitions;
  data_retention: string;
}

export interface ModelCardItem {
  model_id: string;
  model_key: string;
  version: string;
  task: string;
  framework: string;
  supported_languages: string[];
  evaluation_metrics: Record<string, number>;
  limitations: string[];
  is_active: boolean;
}

export interface DatasetDocumentationItem {
  dataset_version: string;
  description: string;
  source: string;
  collection_window: { start: string; end: string };
  sampling_policy: string;
  splits: { train: number; val: number; test: number };
  license: string;
}

