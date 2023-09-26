import { useId } from 'react'

import { Button } from '@/components/Button'

export function SignUpForm() {
  let id = useId()

  return (
    <form className="relative isolate mt-8 flex items-center pr-1">
      <label htmlFor={id} className="sr-only">
        Email address
      </label>
      <input
        required
        type="email"
        autoComplete="email"
        name="email"
        id={id}
        placeholder="Email address"
        className="peer w-0 flex-auto bg-transparent px-4 py-2.5 text-base text-white placeholder:text-gray-500 focus:outline-none sm:text-[0.8125rem]/6"
      />
      <Button type="submit" arrow>
        Get updates
      </Button>
      <div className="peer-focus:ring-sky-300/15 absolute inset-0 -z-10 rounded-lg transition peer-focus:ring-4" />
      <div className="bg-white/2.5 ring-white/15 absolute inset-0 -z-10 rounded-lg ring-1 transition peer-focus:ring-sky-300" />
    </form>
  )
}
