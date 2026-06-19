import { useState } from 'react'
import { createSource, pollSourceUntilReady } from '../api/client'
import { ApiError } from '../types'

interface UrlInputProps {
	onReady: (sourceId: string, duration: number, title: string | null) => void
}

export function UrlInput({ onReady }: UrlInputProps) {
	const [url, setUrl] = useState('')
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)

	async function handleSubmit(event: React.FormEvent) {
		event.preventDefault()
		const trimmed = url.trim()
		if (!trimmed) {
			return
		}
		setLoading(true)
		setError(null)
		try {
			const created = await createSource(trimmed)
			const ready = await pollSourceUntilReady(created.source_id)
			if (ready.duration === null) {
				throw new ApiError(500, 'source has no duration')
			}
			onReady(created.source_id, ready.duration, ready.title)
		} catch (err) {
			const message = err instanceof ApiError ? err.message : 'failed to load source'
			setError(message)
		} finally {
			setLoading(false)
		}
	}

	return (
		<section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
			<h2 className="text-lg font-semibold">1. YouTube URL</h2>
			<p className="mt-1 text-sm text-slate-400">
				Paste a watch or youtu.be link. The source downloads before editing.
			</p>
			<form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={handleSubmit}>
				<label className="sr-only" htmlFor="youtube-url">
					YouTube URL
				</label>
				<input
					id="youtube-url"
					type="url"
					required
					value={url}
					onChange={(event) => setUrl(event.target.value)}
					placeholder="https://www.youtube.com/watch?v=..."
					className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
					disabled={loading}
				/>
				<button
					type="submit"
					disabled={loading}
					className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
				>
					{loading ? 'Downloading…' : 'Load video'}
				</button>
			</form>
			{error && <p className="mt-3 text-sm text-red-400">{error}</p>}
		</section>
	)
}
