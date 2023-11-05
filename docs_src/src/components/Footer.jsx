import Link from 'next/link'

import { Container } from '@/components/Container'
import { GitHubIcon } from './SocialIcons'

function NavLink({ href, children, ...props }) {
  return (
    <Link {...props} href={href} className="transition hover:text-yellow-400">
      {children}
    </Link>
  )
}

export function GithubButton() {
  return (
    <button
      type="button"
      aria-label="Toggle dark mode"
      className="group rounded-full border-2 border-yellow-500 bg-zinc-800/90 px-3 py-2 shadow-lg shadow-zinc-800/5 ring-1 ring-white/10  backdrop-blur transition hover:ring-white/20"
    >
      <GitHubIcon className="block h-6 w-6 fill-zinc-700 stroke-zinc-500 transition group-hover:stroke-zinc-400" />
    </button>
  )
}

export function Footer() {
  return (
    <>
      <Container className="bottom-2 w-[90%] z-40" style={{ position: 'fixed' }}>
        <div className="flex justify-end md:flex-1 ]">
          <div className="pointer-events-auto ">
            <Link target="_blank" href="https://github.com/sparckles/robyn">
              <GithubButton />
            </Link>
          </div>
        </div>
      </Container>

      <footer className="mt-32">
        <Container.Outer>
          <div className="border-t  border-zinc-700/40 pb-16 pt-10">
            <Container.Inner>
              <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
                <div className="flex flex-wrap justify-center gap-x-6 gap-y-1 text-sm font-medium text-zinc-200">
                  <NavLink href="/">Home</NavLink>
                  <NavLink href="/documentation">Documentation</NavLink>
                  <NavLink href="/releases">Releases</NavLink>
                  <NavLink href="/community">Community</NavLink>
                  <NavLink href="https://discord.gg/rkERZ5eNU8" target="_blank">
                    Discord
                  </NavLink>
                </div>
                <p className="text-sm text-zinc-500">
                  &copy; {new Date().getFullYear()} Sparckles OSS. All rights
                  reserved.
                </p>
              </div>
            </Container.Inner>
          </div>
        </Container.Outer>
      </footer>
    </>
  )
}
