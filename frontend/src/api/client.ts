import type {
	CreateJobPayload,
	JobCreated,
	JobDetail,
	SourceCreated,
	SourceDetail,
} from '../types'
import { ApiError } from '../types'

const DEFAULT_POLL_MS = 1500

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => {
		setTimeout(resolve, ms)
	})
}

async function parseError(response: Response): Promise<string> {
	try {
		const body = await response.json()
		if (typeof body.detail === 'string') {
			return body.detail
		}
		if (Array.isArray(body.detail) && body.detail.length > 0) {
			return body.detail.map((item: { msg: string }) => item.msg).join('; ')
		}
	} catch {
		return response.statusText
	}
	return response.statusText
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(path, init)
	if (!response.ok) {
		const message = await parseError(response)
		throw new ApiError(response.status, message)
	}
	return response.json() as Promise<T>
}

export function previewUrl(sourceId: string): string {
	return `/api/sources/${sourceId}/preview`
}

export function downloadUrl(jobId: string): string {
	return `/api/jobs/${jobId}/download`
}

export async function createSource(url: string): Promise<SourceCreated> {
	return request<SourceCreated>('/api/sources', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ url }),
	})
}

export async function getSource(sourceId: string): Promise<SourceDetail> {
	return request<SourceDetail>(`/api/sources/${sourceId}`)
}

export async function pollSourceUntilReady(
	sourceId: string,
	pollMs = DEFAULT_POLL_MS,
): Promise<SourceDetail> {
	for (;;) {
		const source = await getSource(sourceId)
		if (source.status === 'ready') {
			return source
		}
		if (source.status === 'error') {
			throw new ApiError(500, source.error ?? 'source download failed')
		}
		await sleep(pollMs)
	}
}

export async function createJob(payload: CreateJobPayload): Promise<JobCreated> {
	return request<JobCreated>('/api/jobs', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload),
	})
}

export async function getJob(jobId: string): Promise<JobDetail> {
	return request<JobDetail>(`/api/jobs/${jobId}`)
}

export async function pollJobUntilDone(
	jobId: string,
	onProgress?: (progress: number) => void,
	pollMs = DEFAULT_POLL_MS,
): Promise<JobDetail> {
	for (;;) {
		const job = await getJob(jobId)
		onProgress?.(job.progress)
		if (job.status === 'done') {
			return job
		}
		if (job.status === 'error') {
			throw new ApiError(500, job.error ?? 'render failed')
		}
		await sleep(pollMs)
	}
}
