import { useRef, useState } from 'react'
import { previewUrl } from '../api/client'
import type { ClipRange } from '../types'

interface ClipSelectorProps {
	sourceId: string
	duration: number
	title: string | null
	clips: ClipRange[]
	onClipsChange: (clips: ClipRange[]) => void
	onContinue: () => void
}

function formatTime(seconds: number): string {
	const mins = Math.floor(seconds / 60)
	const secs = Math.floor(seconds % 60)
	return `${mins}:${secs.toString().padStart(2, '0')}`
}

export function ClipSelector({
	sourceId,
	duration,
	title,
	clips,
	onClipsChange,
	onContinue,
}: ClipSelectorProps) {
	const videoRef = useRef<HTMLVideoElement>(null)
	const [markIn, setMarkIn] = useState<number | null>(null)
	const [currentTime, setCurrentTime] = useState(0)

	function handleMarkIn() {
		setMarkIn(currentTime)
	}

	function handleMarkOut() {
		if (markIn === null || currentTime <= markIn) {
			return
		}
		onClipsChange([...clips, { start: markIn, end: currentTime }])
		setMarkIn(null)
	}

	function handleRemove(index: number) {
		onClipsChange(clips.filter((_, clipIndex) => clipIndex !== index))
	}

	return (
		<section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
			<h2 className="text-lg font-semibold">2. Select clips</h2>
			{title && <p className="mt-1 text-sm text-slate-400">{title}</p>}
			<p className="mt-1 text-sm text-slate-500">
				Duration: {formatTime(duration)} · scrub the video, mark in/out, add ranges
			</p>
			<video
				ref={videoRef}
				src={previewUrl(sourceId)}
				controls
				className="mt-4 w-full rounded-lg bg-black"
				onTimeUpdate={() => {
					if (videoRef.current) {
						setCurrentTime(videoRef.current.currentTime)
					}
				}}
			/>
			<div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
				<span className="rounded bg-slate-800 px-2 py-1">
					Current: {formatTime(currentTime)}
				</span>
				{markIn !== null && (
					<span className="rounded bg-sky-900 px-2 py-1 text-sky-200">
						In: {formatTime(markIn)}
					</span>
				)}
				<button
					type="button"
					onClick={handleMarkIn}
					className="rounded-lg border border-slate-600 px-3 py-1 hover:bg-slate-800"
				>
					Mark in
				</button>
				<button
					type="button"
					onClick={handleMarkOut}
					disabled={markIn === null}
					className="rounded-lg border border-slate-600 px-3 py-1 hover:bg-slate-800 disabled:opacity-40"
				>
					Mark out &amp; add
				</button>
			</div>
			{clips.length > 0 && (
				<ul className="mt-4 space-y-2">
					{clips.map((clip, index) => (
						<li
							key={`${clip.start}-${clip.end}-${index}`}
							className="flex items-center justify-between rounded-lg bg-slate-800 px-3 py-2 text-sm"
						>
							<span>
								Clip {index + 1}: {formatTime(clip.start)} → {formatTime(clip.end)}
							</span>
							<button
								type="button"
								onClick={() => handleRemove(index)}
								className="text-red-400 hover:text-red-300"
							>
								Remove
							</button>
						</li>
					))}
				</ul>
			)}
			<button
				type="button"
				onClick={onContinue}
				disabled={clips.length === 0}
				className="mt-4 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
			>
				Continue to transitions
			</button>
		</section>
	)
}
