import { forwardRef } from 'react'
import Link from 'next/link'
import clsx from 'clsx'
import { motion, useScroll, useTransform } from 'framer-motion'

import { Button } from '@/components/documentation/Button'
import {
  MobileNavigation,
  useIsInsideMobileNavigation,
} from '@/components/documentation/MobileNavigation'
import { useMobileNavigationStore } from '@/components/documentation/MobileNavigation'
import { MobileSearch, Search } from '@/components/documentation/Search'

function TopLevelNavItem({ href, children }) {
  return (
    <li>
      <Link
        href={href}
        className="text-sm leading-5 text-zinc-400 transition hover:text-white"
      >
        {children}
      </Link>
    </li>
  )
}

export const BottomNavbar = forwardRef(function Header({ className }, ref) {
  let { isOpen: mobileNavIsOpen } = useMobileNavigationStore()
  let isInsideMobileNavigation = useIsInsideMobileNavigation()

  let { scrollY } = useScroll()
  let bgOpacityLight = useTransform(scrollY, [0, 72], [0.5, 0.9])
  let bgOpacityDark = useTransform(scrollY, [0, 72], [0.2, 0.8])

  return (
    <>
      <motion.div
        ref={ref}
        className={clsx(
          className,
          'fixed inset-x-0 bottom-0 z-50 flex h-14 items-center justify-between gap-12 px-4 transition sm:px-6 lg:left-72 lg:z-30 lg:px-8 xl:left-80'
        )}
        style={{
          '--bg-opacity-light': bgOpacityLight,
          '--bg-opacity-dark': bgOpacityDark,
        }}
      >
        <div className="flex items-center gap-5 lg:hidden">
          <MobileNavigation />
        </div>
        <div className="flex items-center gap-5">
          <div className="lg:bg-white/15 hidden lg:block lg:h-5 lg:w-px" />
          <div className="flex gap-4"></div>
        </div>
      </motion.div>
    </>
  )
})
