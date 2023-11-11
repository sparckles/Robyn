import clsx from 'clsx'

const variantStyles = {
  medium: 'rounded-lg px-1.5 ring-1 ring-inset',
}

const colorStyles = {
  orange: {
    small: 'text-orange-400',
    medium: 'ring-orange-400/30 bg-orange-400/10 text-orange-400',
  },
  sky: {
    small: 'text-sky-500',
    medium: 'ring-sky-400/30 bg-sky-400/10 text-sky-400',
  },
  amber: {
    small: 'text-amber-500',
    medium: 'ring-amber-400/30 bg-amber-400/10 text-amber-400',
  },
  rose: {
    small: 'text-rose-500',
    medium: 'ring-rose-500/20 bg-rose-400/10 text-rose-400',
  },
  zinc: {
    small: 'text-zinc-500',
    medium: 'ring-zinc-500/20 bg-zinc-400/10 text-zinc-400',
  },
}

const valueColorMap = {
  get: 'orange',
  post: 'sky',
  put: 'amber',
  delete: 'rose',
}

export function Tag({
  children,
  variant = 'medium',
  color = valueColorMap[children.toLowerCase()] ?? 'orange',
}) {
  return (
    <span
      className={clsx(
        'font-mono text-[0.625rem] font-semibold leading-6',
        variantStyles[variant],
        colorStyles[color][variant]
      )}
    >
      {children}
    </span>
  )
}
