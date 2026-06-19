import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('../api/client', () => ({
	createSource: vi.fn(),
	pollSourceUntilReady: vi.fn(),
	getSource: vi.fn(),
	createJob: vi.fn(),
	pollJobUntilDone: vi.fn(),
	getJob: vi.fn(),
	previewUrl: (id: string) => `/api/sources/${id}/preview`,
	downloadUrl: (id: string) => `/api/jobs/${id}/download`,
}))

describe('App', () => {
	it('renders the first step with URL input', () => {
		render(<App />)
		expect(screen.getByRole('heading', { name: 'uplive' })).toBeInTheDocument()
		expect(screen.getByText('1. YouTube URL')).toBeInTheDocument()
		expect(screen.getByRole('button', { name: 'Load video' })).toBeInTheDocument()
	})
})
