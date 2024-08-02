import { motion } from 'framer-motion'

import { Footer } from '@/components/Footer'
import { BottomNavbar } from '@/components/documentation/BottomNavbar'
import { Navigation } from '@/components/documentation/Navigation'
import { Prose } from '@/components/documentation/Prose'
import { SectionProvider } from '@/components/documentation/SectionProvider'
import { useState, useEffect } from 'react'
import { Container } from '../Container'

export function Layout({ children, sections = [] }) {
  const [showSideBar, setShowSideBar] = useState(true)
  const [margin, setMargin] = useState('lg:ml-72 xl:ml-80')

  useEffect(() => {
    if (showSideBar) {
      setMargin('lg:ml-72 xl:ml-80')
    } else {
      setMargin('lg:ml-8 xl:ml-8')
    }
  }, [showSideBar])

  return (
    <SectionProvider sections={sections}>
      <div className={margin}>
        <motion.header
          layoutScroll
          className="contents lg:pointer-events-none lg:fixed lg:inset-0 lg:z-40 lg:flex"
        >
          <div className="contents lg:pointer-events-auto lg:block lg:w-72 lg:overflow-y-auto lg:border-white/10 lg:px-6 lg:pb-8 xl:w-80">
            <BottomNavbar />

            {showSideBar && <Navigation className="lg:mt-8 lg:block" />}
          </div>
        </motion.header>
        <div className="relative px-4 sm:px-6 lg:px-8">
          <main className="py-16">
            <div
              className="bottom-4 left-4 z-40"
              style={{ position: 'fixed' }}
            >
              <div className="flex md:flex-1">
                <button className="border-1 group rounded-full bg-zinc-800/90 px-2 py-2 backdrop-blur transition hover:ring-white/20 ">

                  {showSideBar ? (
                    <LeftIcon
                      className="h-6 w-6 fill-zinc-700"
                      onClick={() => {
                        setShowSideBar(false)
                      }}
                    />
                  ) : (
                    <RightIcon
                      className="h-6 w-6 fill-zinc-700"
                      onClick={() => {
                        setShowSideBar(true)
                      }}
                    />
                  )}
                </button>
              </div>
            </div>

            <Prose>{children}</Prose>
          </main>
          <Footer />
        </div>
      </div>
    </SectionProvider>
  )
}

function LeftIcon(props) {
  return (
    <svg viewBox="0 -960 960 960" {...props}>
      <path d="M560-240 320-480l240-240 56 56-184 184 184 184-56 56Z" />
    </svg>
  )
}

function RightIcon(props) {
  return (
    <svg viewBox="0 -960 960 960" {...props}>
      <path d="M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z" />
    </svg>
  )
}
