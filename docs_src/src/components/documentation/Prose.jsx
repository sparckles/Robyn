import clsx from 'clsx'

export function Prose({ className, ...props }) {
  return (
    <article
      className={clsx(
        className,
        'prose text-white dark:prose-invert prose-headings:font-extrabold'
      )}
      {...props}
    />
  )
}
