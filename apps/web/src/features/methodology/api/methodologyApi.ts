import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../../lib/api-client";
import {
  DatasetDocumentationItem,
  MethodologyData,
  ModelCardItem,
} from "../types/methodology";

export async function fetchMethodology(): Promise<MethodologyData> {
  return apiClient<MethodologyData>("/methodology");
}

export async function fetchModelCards(): Promise<ModelCardItem[]> {
  return apiClient<ModelCardItem[]>("/methodology/models");
}

export async function fetchDatasets(): Promise<DatasetDocumentationItem[]> {
  return apiClient<DatasetDocumentationItem[]>("/methodology/datasets");
}

export function useMethodology() {
  return useQuery({
    queryKey: ["methodology"],
    queryFn: fetchMethodology,
    staleTime: 1000 * 60 * 10,
  });
}

export function useModelCards() {
  return useQuery({
    queryKey: ["modelCards"],
    queryFn: fetchModelCards,
    staleTime: 1000 * 60 * 10,
  });
}

export function useDatasets() {
  return useQuery({
    queryKey: ["datasets"],
    queryFn: fetchDatasets,
    staleTime: 1000 * 60 * 10,
  });
}

