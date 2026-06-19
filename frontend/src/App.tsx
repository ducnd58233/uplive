import { useState } from 'react'
import { ClipSelector } from './components/ClipSelector'
import { ExportPanel } from './components/ExportPanel'
import { TransitionPicker } from './components/TransitionPicker'
import { UrlInput } from './components/UrlInput'
import type { ClipRange, TransitionType } from './types'

type Step = 1 | 2 | 3 | 4

export default function App() {
	const [step, setStep] = useState<Step>(1)
	const [sourceId, setSourceId] = useState<string | null>(null)
	const [duration, setDuration] = useState(0)
	const [title, setTitle] = useState<string | null>(null)
	const [clips, setClips] = useState<ClipRange[]>([])
	const [transition, setTransition] = useState<TransitionType>('cut')
	const [transitionDuration, setTransitionDuration] = useState(0.5)

	function handleSourceReady(id: string, sourceDuration: number, sourceTitle: string | null) {
		setSourceId(id)
		setDuration(sourceDuration)
		setTitle(sourceTitle)
		setClips([])
		setStep(2)
	}

	return (
		<div className="mx-auto max-w-3xl px-4 py-10">
			<header className="mb-8">
				<h1 className="text-3xl font-bold tracking-tight">uplive</h1>
				<p className="mt-2 text-slate-400">
					Clip, merge, and export segments from a YouTube video.
				</p>
			</header>
			<ol className="mb-6 flex gap-2 text-xs text-slate-500">
				{([1, 2, 3, 4] as Step[]).map((item) => (
					<li
						key={item}
						className={`rounded px-2 py-1 ${step === item ? 'bg-sky-900 text-sky-200' : ''}`}
					>
						Step {item}
					</li>
				))}
			</ol>
			<div className="space-y-6">
				{step === 1 && <UrlInput onReady={handleSourceReady} />}
				{step >= 2 && sourceId && (
					<ClipSelector
						sourceId={sourceId}
						duration={duration}
						title={title}
						clips={clips}
						onClipsChange={setClips}
						onContinue={() => setStep(3)}
					/>
				)}
				{step >= 3 && (
					<TransitionPicker
						transition={transition}
						transitionDuration={transitionDuration}
						onTransitionChange={setTransition}
						onDurationChange={setTransitionDuration}
						onContinue={() => setStep(4)}
					/>
				)}
				{step >= 4 && sourceId && (
					<ExportPanel
						sourceId={sourceId}
						clips={clips}
						transition={transition}
						transitionDuration={transitionDuration}
					/>
				)}
			</div>
		</div>
	)
}
