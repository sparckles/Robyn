import { forwardRef } from 'react'
import Link from 'next/link'
import clsx from 'clsx'
import { motion, useScroll, useTransform } from 'framer-motion'

import { MobileNavigation } from '@/components/documentation/MobileNavigation'
import { useMobileNavigationStore } from '@/components/documentation/MobileNavigation'
import { MobileSearch, Search } from '@/components/documentation/Search'

export const BottomNavbar = forwardRef(function Header({ className }, ref) {
  let { scrollY } = useScroll()
  let bgOpacityLight = useTransform(scrollY, [0, 72], [0.5, 0.9])
  let bgOpacityDark = useTransform(scrollY, [0, 72], [0.2, 0.8])

  return (
    <>
      <motion.div
        ref={ref}
        className={clsx(
          className,
          'fixed inset-x-0 bottom-0 z-50 flex h-14 max-w-fit items-center justify-between gap-12 px-4 transition sm:px-6 lg:left-72 lg:z-30 lg:px-8 xl:left-80'
        )}
        style={{
          '--bg-opacity-light': bgOpacityLight,
          '--bg-opacity-dark': bgOpacityDark,
        }}
      >
        <div className="flex items-center gap-5 lg:hidden">
          <MobileNavigation />
        </div>
      </motion.div>
    </>
  )
})
