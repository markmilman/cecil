import { describe, it, expect } from 'vitest';
import { ApiClient, ApiClientError } from './apiClient';

/**
 * Test suite for ApiClient
 */
describe('ApiClient', () => {
  it('creates an instance with default configuration', () => {
    const client = new ApiClient();
    expect(client).toBeInstanceOf(ApiClient);
  });

  it('creates an instance with custom port', () => {
    const client = new ApiClient({ port: 9000 });
    expect(client).toBeInstanceOf(ApiClient);
  });

  it('creates an instance with custom base URL', () => {
    const client = new ApiClient({ baseURL: 'http://localhost:3000' });
    expect(client).toBeInstanceOf(ApiClient);
  });

  it('exposes the underlying axios client', () => {
    const client = new ApiClient();
    const axiosInstance = client.getClient();
    expect(axiosInstance).toBeDefined();
  });
});

/**
 * Test suite for ApiClientError
 */
describe('ApiClientError', () => {
  it('creates an error with message only', () => {
    const error = new ApiClientError('Test error');
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe('Test error');
    expect(error.name).toBe('ApiClientError');
  });

  it('creates an error with status code', () => {
    const error = new ApiClientError('Server error', 500);
    expect(error.statusCode).toBe(500);
  });

  it('creates an error with error response', () => {
    const errorResponse = {
      error: 'BadRequest',
      message: 'Invalid input',
      details: { field: 'email' },
    };
    const error = new ApiClientError('Invalid input', 400, errorResponse);
    expect(error.errorResponse).toEqual(errorResponse);
  });
});
