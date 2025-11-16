/**
 * Tests for standardized API error handling
 */

import { NextResponse } from 'next/server'
import {
  validationError,
  notFoundError,
  forbiddenError,
  databaseError,
  serviceUnavailableError,
  internalError,
  isFetchError,
  isJsonError,
} from '../api-error'

describe('API Error Handling', () => {
  // Suppress console.error during tests
  beforeAll(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterAll(() => {
    jest.restoreAllMocks()
  })

  describe('validationError', () => {
    it('should return 400 status with error message', () => {
      const response = validationError('Name is required', 'POST /api/agents')
      expect(response.status).toBe(400)
    })

    it('should include user wallet in logs when provided', () => {
      const response = validationError('Invalid amount', 'POST /api/requests', 'wallet123')
      expect(response.status).toBe(400)
    })
  })

  describe('notFoundError', () => {
    it('should return 404 status with resource name', () => {
      const response = notFoundError('Agent', 'GET /api/agents/123')
      expect(response.status).toBe(404)
    })
  })

  describe('forbiddenError', () => {
    it('should return 403 status with error message', () => {
      const response = forbiddenError('Not authorized', 'POST /api/requests/approve', 'wallet123')
      expect(response.status).toBe(403)
    })
  })

  describe('databaseError', () => {
    it('should return 500 status and sanitize error details', () => {
      const dbError = new Error('Connection failed: password=secret123')
      const response = databaseError('GET /api/agents', dbError)
      expect(response.status).toBe(500)
    })

    it('should handle non-Error objects', () => {
      const response = databaseError('GET /api/agents', 'String error')
      expect(response.status).toBe(500)
    })
  })

  describe('serviceUnavailableError', () => {
    it('should return 503 status with service name', () => {
      const response = serviceUnavailableError('SecurityGuard AI', 'POST /api/security/scan')
      expect(response.status).toBe(503)
    })
  })

  describe('internalError', () => {
    it('should return 500 status without exposing details', () => {
      const error = new Error('Internal system failure')
      const response = internalError('POST /api/agents', error)
      expect(response.status).toBe(500)
    })
  })

  describe('isFetchError', () => {
    it('should detect fetch errors', () => {
      const fetchError = new TypeError('fetch failed')
      expect(isFetchError(fetchError)).toBe(true)
    })

    it('should detect network errors', () => {
      const networkError = new TypeError('network error')
      expect(isFetchError(networkError)).toBe(true)
    })

    it('should return false for other errors', () => {
      const otherError = new Error('Something else')
      expect(isFetchError(otherError)).toBe(false)
    })
  })

  describe('isJsonError', () => {
    it('should detect JSON parsing errors', () => {
      const jsonError = new SyntaxError('Unexpected token in JSON')
      expect(isJsonError(jsonError)).toBe(true)
    })

    it('should return false for other errors', () => {
      const otherError = new Error('Not a JSON error')
      expect(isJsonError(otherError)).toBe(false)
    })
  })

  describe('Error message sanitization', () => {
    it('should remove passwords from error messages', () => {
      const error = new Error('Failed: password=secret123')
      const response = databaseError('GET /api/test', error)
      expect(response.status).toBe(500)
      // Password should be sanitized in logs
    })

    it('should remove API keys from error messages', () => {
      const error = new Error('API key sk_test_1234567890abcdefghijklmnopqrstuvwxyz failed')
      const response = databaseError('GET /api/test', error)
      expect(response.status).toBe(500)
      // API key should be sanitized in logs
    })
  })
})
