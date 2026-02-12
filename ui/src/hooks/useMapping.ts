/**
 * useMapping hook
 *
 * Manages state for the mapping editor: sample record, field actions,
 * validation, preview, and save operations. Calls apiClient methods
 * for backend communication.
 */

import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '@/lib/apiClient';
import { RedactionAction } from '@/types';

import type {
  MappingValidationResult,
  FieldPreviewEntry,
} from '@/types';

interface UseMappingState {
  sampleRecord: Record<string, string>;
  fields: Record<string, RedactionAction>;
  fieldOptions: Record<string, Record<string, string>>;
  defaultAction: RedactionAction;
  isLoading: boolean;
  error: string | null;
  validationResult: MappingValidationResult | null;
  previewResult: FieldPreviewEntry[];
  isSaving: boolean;
  savedMappingId: string | null;
}

interface UseMappingReturn extends UseMappingState {
  loadSampleRecord: (source: string) => Promise<void>;
  setFieldAction: (fieldName: string, action: RedactionAction) => void;
  setDefaultAction: (action: RedactionAction) => void;
  validate: () => Promise<void>;
  preview: () => Promise<void>;
  save: (name?: string) => Promise<void>;
  reset: () => void;
  dismissValidation: () => void;
  dismissPreview: () => void;
}

const INITIAL_STATE: UseMappingState = {
  sampleRecord: {},
  fields: {},
  fieldOptions: {},
  defaultAction: RedactionAction.REDACT,
  isLoading: false,
  error: null,
  validationResult: null,
  previewResult: [],
  isSaving: false,
  savedMappingId: null,
};

export function useMapping(source?: string): UseMappingReturn {
  const [state, setState] = useState<UseMappingState>(INITIAL_STATE);

  const loadSampleRecord = useCallback(async (src: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await apiClient.getSampleRecord(src);
      const initialFields: Record<string, RedactionAction> = {};
      for (const fieldName of Object.keys(response.record)) {
        initialFields[fieldName] = RedactionAction.REDACT;
      }
      setState((prev) => ({
        ...prev,
        isLoading: false,
        sampleRecord: response.record,
        fields: initialFields,
        fieldOptions: {},
        validationResult: null,
        previewResult: [],
        savedMappingId: null,
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load sample record from source',
      }));
    }
  }, []);

  useEffect(() => {
    if (source) {
      loadSampleRecord(source);
    }
  }, [source, loadSampleRecord]);

  const setFieldAction = useCallback((fieldName: string, action: RedactionAction) => {
    setState((prev) => ({
      ...prev,
      fields: { ...prev.fields, [fieldName]: action },
      validationResult: null,
      previewResult: [],
    }));
  }, []);

  const setDefaultAction = useCallback((action: RedactionAction) => {
    setState((prev) => {
      const updatedFields: Record<string, RedactionAction> = {};
      for (const fieldName of Object.keys(prev.fields)) {
        updatedFields[fieldName] = action;
      }
      return {
        ...prev,
        defaultAction: action,
        fields: updatedFields,
        validationResult: null,
        previewResult: [],
      };
    });
  }, []);

  const validate = useCallback(async () => {
    setState((prev) => ({ ...prev, error: null }));
    try {
      const fieldsPayload: Record<string, { action: RedactionAction; options: Record<string, string> }> = {};
      for (const [name, action] of Object.entries(state.fields)) {
        fieldsPayload[name] = {
          action,
          options: state.fieldOptions[name] || {},
        };
      }
      const result = await apiClient.validateMapping({
        mapping: {
          version: 1,
          default_action: state.defaultAction,
          fields: fieldsPayload,
        },
        sample_record: state.sampleRecord,
      });
      setState((prev) => ({ ...prev, validationResult: result }));
    } catch {
      setState((prev) => ({
        ...prev,
        error: 'Failed to validate mapping',
      }));
    }
  }, [state.fields, state.fieldOptions, state.defaultAction, state.sampleRecord]);

  const preview = useCallback(async () => {
    setState((prev) => ({ ...prev, error: null }));
    try {
      const fieldsPayload: Record<string, { action: RedactionAction; options: Record<string, string> }> = {};
      for (const [name, action] of Object.entries(state.fields)) {
        fieldsPayload[name] = {
          action,
          options: state.fieldOptions[name] || {},
        };
      }
      const result = await apiClient.previewMapping(fieldsPayload, state.sampleRecord);
      setState((prev) => ({ ...prev, previewResult: result.entries }));
    } catch {
      setState((prev) => ({
        ...prev,
        error: 'Failed to preview mapping',
      }));
    }
  }, [state.fields, state.fieldOptions, state.sampleRecord]);

  const save = useCallback(async (name?: string) => {
    setState((prev) => ({ ...prev, isSaving: true, error: null }));
    try {
      const fieldsPayload: Record<string, { action: RedactionAction; options: Record<string, string> }> = {};
      for (const [fieldName, action] of Object.entries(state.fields)) {
        fieldsPayload[fieldName] = {
          action,
          options: state.fieldOptions[fieldName] || {},
        };
      }
      const result = await apiClient.createMapping({
        version: 1,
        default_action: state.defaultAction,
        fields: fieldsPayload,
      }, name);
      setState((prev) => ({
        ...prev,
        isSaving: false,
        savedMappingId: result.mapping_id,
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        isSaving: false,
        error: 'Failed to save mapping',
      }));
    }
  }, [state.fields, state.fieldOptions, state.defaultAction]);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  const dismissValidation = useCallback(() => {
    setState((prev) => ({ ...prev, validationResult: null }));
  }, []);

  const dismissPreview = useCallback(() => {
    setState((prev) => ({ ...prev, previewResult: [] }));
  }, []);

  return {
    ...state,
    loadSampleRecord,
    setFieldAction,
    setDefaultAction,
    validate,
    preview,
    save,
    reset,
    dismissValidation,
    dismissPreview,
  };
}
