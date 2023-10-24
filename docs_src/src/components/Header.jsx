import { Fragment, useEffect, useRef } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { Popover, Transition } from '@headlessui/react'
import clsx from 'clsx'

import { Container } from '@/components/Container'
import robynLogo from '@/images/robyn_logo.jpg'
import { MobileSearch, Search } from '@/components/documentation/Search'

function CloseIcon(props) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path
        d="m17.25 6.75-10.5 10.5M6.75 6.75l10.5 10.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ChevronDownIcon(props) {
  return (
    <svg viewBox="0 0 8 6" aria-hidden="true" {...props}>
      <path
        d="M1.75 1.75 4 4.25l2.25-2.5"
        fill="none"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function MobileNavItem({ href, children }) {
  return (
    <li>
      <Popover.Button as={Link} href={href} className="block py-2">
        {children}
      </Popover.Button>
    </li>
  )
}

function MobileNavigation(props) {
  return (
    <Popover {...props}>
      <Popover.Button className="group flex items-center rounded-full bg-zinc-800/90 px-4 py-2 text-sm font-medium text-zinc-200 shadow-lg shadow-zinc-800/5 ring-1  ring-white/10 backdrop-blur hover:ring-white/20">
        Menu
        <ChevronDownIcon className="ml-3 h-auto w-2 stroke-zinc-500 group-hover:stroke-zinc-400" />
      </Popover.Button>
      <Transition.Root>
        <Transition.Child
          as={Fragment}
          enter="duration-150 ease-out"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="duration-150 ease-in"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Popover.Overlay className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm" />
        </Transition.Child>
        <Transition.Child
          as={Fragment}
          enter="duration-150 ease-out"
          enterFrom="opacity-0 scale-95"
          enterTo="opacity-100 scale-100"
          leave="duration-150 ease-in"
          leaveFrom="opacity-100 scale-100"
          leaveTo="opacity-0 scale-95"
        >
          <Popover.Panel
            focus
            className="fixed inset-x-4 top-8 z-50 origin-top rounded-3xl bg-zinc-900 p-8 ring-1 ring-zinc-800"
          >
            <div className="flex flex-row-reverse items-center justify-between">
              <Popover.Button aria-label="Close menu" className="-m-1 p-1">
                <CloseIcon className="h-6 w-6 text-zinc-400" />
              </Popover.Button>
              <h2 className="text-sm font-medium text-zinc-400">Navigation</h2>
            </div>
            <nav className="mt-6">
              <ul className="-my-2 divide-y divide-zinc-100/5 text-base text-zinc-300">
                <MobileNavItem href="/documentation">
                  Documentation
                </MobileNavItem>
                <MobileNavItem href="/releases">Releases</MobileNavItem>
                <MobileNavItem href="/community">Community</MobileNavItem>
                <MobileNavItem href="https://github.com/sparckles/robyn">
                  GitHub
                </MobileNavItem>
              </ul>
            </nav>
          </Popover.Panel>
        </Transition.Child>
      </Transition.Root>
    </Popover>
  )
}

function NavItem({ href, children, ...props }) {
  let isActive = useRouter().pathname === href

  return (
    <li>
      <Link
        href={href}
        className={clsx(
          'relative block px-3 py-2 transition',
          isActive ? 'text-yellow-500' : 'hover:text-yellow-500'
        )}
        {...props}
      >
        {children}
        {isActive && (
          <span className="absolute inset-x-1 -bottom-px h-px bg-gradient-to-r from-orange-800/0 via-yellow-800/40 to-yellow-500/0 " />
        )}
      </Link>
    </li>
  )
}

function DesktopNavigation(props) {
  return (
    <nav {...props}>
      <ul className="flex rounded-full bg-zinc-800/90 px-3 text-sm  font-medium text-zinc-200 shadow-lg  shadow-zinc-800/5 ring-1 ring-white/10 backdrop-blur">
        <NavItem href="/documentation">Documentation</NavItem>
        <NavItem href="/releases">Releases</NavItem>
        <NavItem href="/community">Community</NavItem>
        <NavItem href="https://discord.gg/rkERZ5eNU8" target="_blank">
          Discord
        </NavItem>
      </ul>
    </nav>
  )
}

function clamp(number, a, b) {
  let min = Math.min(a, b)
  let max = Math.max(a, b)
  return Math.min(Math.max(number, min), max)
}

function Avatar({ large = false, className, ...props }) {
  return (
    <Link
      href="/"
      aria-label="Home"
      className={clsx(className, 'pointer-events-auto')}
      {...props}
    >
      <Image
        src={robynLogo}
        alt=""
        sizes={large ? '4rem' : '2.25rem'}
        className={clsx(
          'rounded-md bg-zinc-800 object-cover',
          large ? 'h-16 w-16' : 'h-9 w-9'
        )}
        priority
      />
    </Link>
  )
}

export function Header() {
  let isHomePage = useRouter().pathname === '/'

  let headerRef = useRef()
  let avatarRef = useRef()
  let isInitial = useRef(true)

  useEffect(() => {
    let downDelay = avatarRef.current?.offsetTop ?? 0
    let upDelay = 64

    function setProperty(property, value) {
      document.documentElement.style.setProperty(property, value)
    }

    function removeProperty(property) {
      document.documentElement.style.removeProperty(property)
    }

    function updateHeaderStyles() {
      let { top, height } = headerRef.current.getBoundingClientRect()
      let scrollY = clamp(
        window.scrollY,
        0,
        document.body.scrollHeight - window.innerHeight
      )

      if (isInitial.current) {
        setProperty('--header-position', 'sticky')
      }

      setProperty('--content-offset', `${downDelay}px`)

      if (isInitial.current || scrollY < downDelay) {
        setProperty('--header-height', `${downDelay + height}px`)
        setProperty('--header-mb', `${-downDelay}px`)
      } else if (top + height < -upDelay) {
        let offset = Math.max(height, scrollY - upDelay)
        setProperty('--header-height', `${offset}px`)
        setProperty('--header-mb', `${height - offset}px`)
      } else if (top === 0) {
        setProperty('--header-height', `${scrollY + height}px`)
        setProperty('--header-mb', `${-scrollY}px`)
      }

      if (top === 0 && scrollY > 0 && scrollY >= downDelay) {
        setProperty('--header-inner-position', 'fixed')
        removeProperty('--header-top')
        removeProperty('--avatar-top')
      } else {
        removeProperty('--header-inner-position')
        setProperty('--header-top', '0px')
        setProperty('--avatar-top', '0px')
      }
    }

    function updateStyles() {
      updateHeaderStyles()
      isInitial.current = false
    }

    updateStyles()
    window.addEventListener('scroll', updateStyles, { passive: true })
    window.addEventListener('resize', updateStyles)

    return () => {
      window.removeEventListener('scroll', updateStyles)
      window.removeEventListener('resize', updateStyles)
    }
  }, [isHomePage])

  return (
    <>
      <header
        className="pointer-events-none relative z-50 flex flex-col"
        style={{
          height: 'var(--header-height)',
          marginBottom: 'var(--header-mb)',
        }}
      >
        <div
          ref={headerRef}
          className="top-0 z-10 h-16 pt-6"
          style={{ position: 'var(--header-position)' }}
        >
          <Container
            className="top-[var(--header-top,theme(spacing.6))] w-full"
            style={{ position: 'var(--header-inner-position)' }}
          >
            <div className="relative flex gap-4">
              <div className="flex flex-1">{<Avatar />}</div>
              <div className="flex flex-1 justify-end md:justify-center">
                <MobileNavigation className="pointer-events-auto md:hidden" />
                <DesktopNavigation className="pointer-events-auto hidden md:block" />
              </div>
              <div className="flex justify-end md:flex-1">
                <div className="pointer-events-auto">
                  <Search />
                  <MobileSearch />
                </div>
              </div>
            </div>
          </Container>
        </div>
      </header>
      {isHomePage && <div style={{ height: 'var(--content-offset)' }} />}
    </>
  )
}
