import { useState } from 'react'
import { createJob, downloadUrl, pollJobUntilDone } from '../api/client'
import type { ClipRange, TransitionType } from '../types'
import { ApiError } from '../types'

interface ExportPanelProps {
	sourceId: string
	clips: ClipRange[]
	transition: TransitionType
	transitionDuration: number
}

export function ExportPanel({
	sourceId,
	clips,
	transition,
	transitionDuration,
}: ExportPanelProps) {
	const [jobId, setJobId] = useState<string | null>(null)
	const [progress, setProgress] = useState(0)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [done, setDone] = useState(false)

	async function handleExport() {
		setLoading(true)
		setError(null)
		setDone(false)
		setProgress(0)
		try {
			const created = await createJob({
				source_id: sourceId,
				clips,
				transition,
				transition_duration: transition === 'cut' ? 0 : transitionDuration,
			})
			setJobId(created.job_id)
			await pollJobUntilDone(created.job_id, setProgress)
			setDone(true)
		} catch (err) {
			const message = err instanceof ApiError ? err.message : 'export failed'
			setError(message)
		} finally {
			setLoading(false)
		}
	}

	return (
		<section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
			<h2 className="text-lg font-semibold">4. Export</h2>
			<p className="mt-1 text-sm text-slate-400">
				{clips.length} clip{clips.length === 1 ? '' : 's'} · {transition} transition
			</p>
			<button
				type="button"
				onClick={handleExport}
				disabled={loading || done}
				className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
			>
				{loading ? 'Rendering…' : done ? 'Complete' : 'Start export'}
			</button>
			{(loading || done) && (
				<div className="mt-4">
					<div className="h-2 overflow-hidden rounded-full bg-slate-800">
						<div
							className="h-full bg-emerald-500 transition-all"
							style={{ width: `${progress}%` }}
						/>
					</div>
					<p className="mt-2 text-sm text-slate-400">{progress}%</p>
				</div>
			)}
			{done && jobId && (
				<a
					href={downloadUrl(jobId)}
					download="result.mp4"
					className="mt-4 inline-block rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500"
				>
					Download result
				</a>
			)}
			{error && <p className="mt-3 text-sm text-red-400">{error}</p>}
		</section>
	)
}
