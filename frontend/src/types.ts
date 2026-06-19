export type SourceStatus = 'downloading' | 'ready' | 'error'

export type JobStatus = 'queued' | 'processing' | 'done' | 'error'

export type TransitionType = 'cut' | 'fade' | 'slide'

export interface ClipRange {
	start: number
	end: number
}

export interface SourceCreated {
	source_id: string
	status: SourceStatus
}

export interface SourceDetail {
	status: SourceStatus
	duration: number | null
	title: string | null
	error: string | null
}

export interface JobCreated {
	job_id: string
	status: JobStatus
}

export interface JobDetail {
	status: JobStatus
	progress: number
	error: string | null
}

export interface CreateJobPayload {
	source_id: string
	clips: ClipRange[]
	transition: TransitionType
	transition_duration: number
}

export type EditorStep = 'url' | 'clips' | 'transition' | 'export'

export interface ApiErrorBody {
	detail: string | Array<{ msg: string }>
}

export class ApiError extends Error {
	readonly status: number

	constructor(status: number, message: string) {
		super(message)
		this.status = status
	}
}
