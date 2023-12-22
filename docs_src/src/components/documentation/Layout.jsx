import { motion } from 'framer-motion'

import { Footer } from '@/components/Footer'
import { BottomNavbar } from '@/components/documentation/BottomNavbar'
import { Navigation } from '@/components/documentation/Navigation'
import { Prose } from '@/components/documentation/Prose'
import { SectionProvider } from '@/components/documentation/SectionProvider'

export function Layout({ children, sections = [] }) {
  return (
    <SectionProvider sections={sections}>
      <div className="lg:ml-72 xl:ml-80">
        <motion.header
          layoutScroll
          className="contents lg:pointer-events-none lg:fixed lg:inset-0 lg:z-40 lg:flex"
        >
          <div className="contents lg:pointer-events-auto lg:block lg:w-72 lg:overflow-y-auto lg:border-white/10 lg:px-6 lg:pb-8 xl:w-80">
            <BottomNavbar />

            <Navigation className="hidden lg:mt-32 lg:block" />
          </div>
        </motion.header>
        <div className="relative px-4 sm:px-6 lg:px-8">
          <main className="py-16">
            <Prose>{children}</Prose>
          </main>
          <Footer />
        </div>
      </div>
    </SectionProvider>
  )
}
