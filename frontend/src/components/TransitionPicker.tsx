import type { TransitionType } from '../types'

interface TransitionPickerProps {
	transition: TransitionType
	transitionDuration: number
	onTransitionChange: (transition: TransitionType) => void
	onDurationChange: (seconds: number) => void
	onContinue: () => void
}

const OPTIONS: { value: TransitionType; label: string }[] = [
	{ value: 'cut', label: 'Cut' },
	{ value: 'fade', label: 'Fade' },
	{ value: 'slide', label: 'Slide' },
]

export function TransitionPicker({
	transition,
	transitionDuration,
	onTransitionChange,
	onDurationChange,
	onContinue,
}: TransitionPickerProps) {
	const needsDuration = transition !== 'cut'

	return (
		<section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
			<h2 className="text-lg font-semibold">3. Transitions</h2>
			<p className="mt-1 text-sm text-slate-400">
				Choose how clips merge. Fade and slide need a duration in seconds.
			</p>
			<div className="mt-4 flex flex-wrap gap-2">
				{OPTIONS.map((option) => (
					<button
						key={option.value}
						type="button"
						onClick={() => onTransitionChange(option.value)}
						className={`rounded-lg px-4 py-2 text-sm font-medium ${
							transition === option.value
								? 'bg-sky-600 text-white'
								: 'border border-slate-600 hover:bg-slate-800'
						}`}
					>
						{option.label}
					</button>
				))}
			</div>
			{needsDuration && (
				<label className="mt-4 block text-sm">
					<span className="text-slate-400">Transition duration (seconds)</span>
					<input
						type="number"
						min={0.1}
						step={0.1}
						value={transitionDuration}
						onChange={(event) => onDurationChange(Number(event.target.value))}
						className="mt-1 w-32 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-sky-500"
					/>
				</label>
			)}
			<button
				type="button"
				onClick={onContinue}
				disabled={needsDuration && transitionDuration <= 0}
				className="mt-4 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
			>
				Continue to export
			</button>
		</section>
	)
}
