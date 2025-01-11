import { useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import clsx from 'clsx'
import { AnimatePresence, motion, useIsPresent } from 'framer-motion'

import { Button } from '@/components/documentation/Button'
import { useIsInsideMobileNavigation } from '@/components/documentation/MobileNavigation'
import { useSectionStore } from '@/components/documentation/SectionProvider'
import { Tag } from '@/components/documentation/Tag'
import LanguageSelector from '@/components/documentation/LanguageSelector'
import { remToPx } from '@/lib/remToPx'

function useInitialValue(value, condition = true) {
  let initialValue = useRef(value).current
  return condition ? initialValue : value
}

function TopLevelNavItem({ href, children }) {
  return (
    <li className="md:hidden">
      <Link
        href={href}
        className="block py-1 text-sm text-zinc-400 transition hover:text-white"
      >
        {children}
      </Link>
    </li>
  )
}

function NavLink({ href, tag, active, isAnchorLink = false, children }) {
  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={clsx(
        'flex justify-between gap-2 py-1 pr-3 text-sm transition',
        isAnchorLink ? 'pl-7' : 'pl-4',
        active ? 'text-white' : 'text-zinc-400 hover:text-white'
      )}
    >
      <span className="truncate">{children}</span>
      {tag && (
        <Tag variant="small" color="zinc">
          {tag}
        </Tag>
      )}
    </Link>
  )
}

function VisibleSectionHighlight({ group, pathname }) {
  let [sections, visibleSections] = useInitialValue(
    [
      useSectionStore((s) => s.sections),
      useSectionStore((s) => s.visibleSections),
    ],
    useIsInsideMobileNavigation()
  )

  let isPresent = useIsPresent()
  let firstVisibleSectionIndex = Math.max(
    0,
    [{ id: '_top' }, ...sections].findIndex(
      (section) => section.id === visibleSections[0]
    )
  )
  let itemHeight = remToPx(2)
  let height = isPresent
    ? Math.max(1, visibleSections.length) * itemHeight
    : itemHeight
  let top =
    group.links.findIndex((link) => link.href === pathname) * itemHeight +
    firstVisibleSectionIndex * itemHeight

  return (
    <motion.div
      layout
      initial={{ opacity: 0 }}
      animate={{ opacity: 1, transition: { delay: 0.2 } }}
      exit={{ opacity: 0 }}
      className="bg-white/2.5 absolute inset-x-0 top-0 will-change-transform"
      style={{ borderRadius: 8, height, top }}
    />
  )
}

function ActivePageMarker({ group, pathname }) {
  let itemHeight = remToPx(2)
  let offset = remToPx(0.25)
  let activePageIndex = group.links.findIndex((link) => link.href === pathname)
  let top = offset + activePageIndex * itemHeight

  return (
    <motion.div
      layout
      className="absolute left-2 h-6 w-px bg-orange-500"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1, transition: { delay: 0.2 } }}
      exit={{ opacity: 0 }}
      style={{ top }}
    />
  )
}

function NavigationGroup({ group, className }) {
  // If this is the mobile navigation then we always render the initial
  // state, so that the state does not change during the close animation.
  // The state will still update when we re-open (re-render) the navigation.
  let isInsideMobileNavigation = useIsInsideMobileNavigation()
  let [router, sections] = useInitialValue(
    [useRouter(), useSectionStore((s) => s.sections)],
    isInsideMobileNavigation
  )

  let isActiveGroup =
    group.links.findIndex((link) => link.href === router.pathname) !== -1

  return (
    <li className={clsx('relative mt-6', className)}>
      <motion.h2 layout="position" className="text-xs font-semibold text-white">
        {group.title}
      </motion.h2>
      <div className="relative mt-3 pl-2">
        <AnimatePresence initial={!isInsideMobileNavigation}>
          {isActiveGroup && (
            <VisibleSectionHighlight group={group} pathname={router.pathname} />
          )}
        </AnimatePresence>
        <motion.div
          layout
          className="absolute inset-y-0 left-2 w-px bg-white/5"
        />
        <AnimatePresence initial={false}>
          {isActiveGroup && (
            <ActivePageMarker group={group} pathname={router.pathname} />
          )}
        </AnimatePresence>
        <ul role="list" className="border-l border-transparent">
          {group.links.map((link) => (
            <motion.li key={link.href} layout="position" className="relative">
              <NavLink href={link.href} active={link.href === router.pathname}>
                {link.title}
              </NavLink>
              <AnimatePresence mode="popLayout" initial={false}>
                {link.href === router.pathname && sections.length > 0 && (
                  <motion.ul
                    role="list"
                    initial={{ opacity: 0 }}
                    animate={{
                      opacity: 1,
                      transition: { delay: 0.1 },
                    }}
                    exit={{
                      opacity: 0,
                      transition: { duration: 0.15 },
                    }}
                  >
                    {sections.map((section) => (
                      <li key={section.id}>
                        <NavLink
                          href={`${link.href}#${section.id}`}
                          tag={section.tag}
                          isAnchorLink
                        >
                          {section.title}
                        </NavLink>
                      </li>
                    ))}
                  </motion.ul>
                )}
              </AnimatePresence>
            </motion.li>
          ))}
        </ul>
      </div>
    </li>
  )
}

export const navigation = [
  {
    title: 'Documentation',
    links: [{ title: 'Introduction', href: '/documentation' }],
  },

  {
    title: 'Example Application',
    links: [
      { title: 'Getting Started', href: '/documentation/en/example_app' },
      {
        title: 'Modeling Routes',
        href: '/documentation/en/example_app/modeling_routes',
      },

      {
        title: 'Authentication and Authorization',
        href: '/documentation/en/example_app/authentication',
      },
      {
        title: 'Middlewares',
        href: '/documentation/en/example_app/authentication-middlewares',
      },
      {
        title: 'Real Time Notifications',
        href: '/documentation/en/example_app/real_time_notifications',
      },
      {
        title: 'Monitoring and Logging',
        href: '/documentation/en/example_app/monitoring_and_logging',
      },
      { title: 'Deployment', href: '/documentation/en/example_app/deployment' },
      {
        title: 'OpenAPI Documentation',
        href: '/documentation/en/example_app/openapi',
      },
      { title: 'Templates', href: '/documentation/en/example_app/templates' },
      {
        title: 'SubRouters',
        href: '/documentation/en/example_app/subrouters',
      },
    ],
  },
  {
    title: 'API Reference',
    links: [
      {
        href: '/documentation/en/api_reference/',
        title: 'Installation',
      },
      {
        href: '/documentation/en/api_reference/getting_started',
        title: 'Getting Started',
      },
      {
        href: '/documentation/en/api_reference/request_object',
        title: 'The Request Object',
      },
      {
        href: '/documentation/en/api_reference/robyn_env',
        title: 'The Robyn Env file',
      },
      {
        href: '/documentation/en/api_reference/middlewares',
        title: 'Middlewares, Events and Websockets',
      },
      {
        href: '/documentation/en/api_reference/authentication',
        title: 'Authentication',
      },
      {
        href: '/documentation/en/api_reference/const_requests',
        title: 'Const Requests and Multi Core Scaling',
      },
      {
        href: '/documentation/en/api_reference/cors',
        title: 'CORS',
      },
      {
        href: '/documentation/en/api_reference/templating',
        title: 'Templating',
      },
      {
        title: 'Redirection',
        href: '/documentation/en/api_reference/redirection',
      },
      {
        href: '/documentation/en/api_reference/file-uploads',
        title: 'File Uploads',
      },
      {
        href: '/documentation/en/api_reference/form_data',
        title: 'Form Data',
      },
      {
        href: '/documentation/en/api_reference/websockets',
        title: 'Websockets',
      },
      {
        href: '/documentation/en/api_reference/exceptions',
        title: 'Exceptions',
      },
      {
        href: '/documentation/en/api_reference/scaling',
        title: 'Scaling the Application',
      },
      {
        href: '/documentation/en/api_reference/advanced_features',
        title: 'Advanced Features',
      },
      {
        href: '/documentation/en/api_reference/multiprocess_execution',
        title: 'Multiprocess Execution',
      },
      {
        href: '/documentation/en/api_reference/using_rust_directly',
        title: 'Direct Rust Usage',
      },
      {
        href: '/documentation/en/api_reference/graphql-support',
        title: 'GraphQL Support',
      },
      {
        href: '/documentation/en/api_reference/openapi',
        title: 'OpenAPI Documentation',
      },
      {
        href: '/documentation/en/api_reference/dependency_injection',
        title: 'Dependency Injection',
      }
    ],
  },
  {
    title: 'Community Resources',
    links: [
      {
        href: '/documentation/en/community-resources#talks',
        title: 'Talks',
      },
      {
        href: '/documentation/en/community-resources#blogs',
        title: 'Blogs',
      },
    ],
  },
  {
    title: 'Architecture',
    links: [
      {
        href: '/documentation/en/architecture',
        title: 'Architecture',
      },
    ],
  },
  {
    title: 'Framework Comparison',
    links: [
      {
        href: '/documentation/en/framework_performance_comparison',
        title: 'Performance Comparison',
      },
    ],
  },
  {
    title: 'Hosting',
    links: [
      {
        href: '/documentation/en/hosting#railway',
        title: 'Railway',
      },
      {
        href: '/documentation/en/hosting#exposing-ports',
        title: 'Exposing Ports',
      },
    ],
  },
  {
    title: 'Plugins',
    links: [
      {
        href: '/documentation/en/plugins',
        title: 'Plugins',
      },
    ],
  },
  {
    title: 'Future Roadmap',
    links: [
      {
        href: '/documentation/en/api_reference/future-roadmap',
        title: 'Upcoming Features',
      },
    ],
  },
]

export function Navigation(props) {
  const router = useRouter()
  const currentLanguage = router.locale || 'en'

  // Function to transform links based on current language
  const getLocalizedHref = (href) => {
    // If it's the root documentation page
    if (href === '/documentation') {
      return `/documentation/${currentLanguage}`
    }
    // For all other links, replace /en/ with current language
    return href.replace('/documentation/en/', `/documentation/${currentLanguage}/`)
  }

  // Create localized navigation
  const localizedNavigation = navigation.map(group => ({
    ...group,
    links: group.links.map(link => ({
      ...link,
      href: getLocalizedHref(link.href)
    }))
  }))

  return (
    <nav {...props}>
      <div className="flex items-center justify-between px-4 py-2">
        <LanguageSelector />
      </div>
      <ul role="list">
        <TopLevelNavItem href="/">API</TopLevelNavItem>
        <TopLevelNavItem href="#">Documentation</TopLevelNavItem>
        <TopLevelNavItem href="#">Support</TopLevelNavItem>
        {localizedNavigation.map((group, groupIndex) => (
          <NavigationGroup
            key={group.title}
            group={group}
            className={groupIndex === 0 && 'md:mt-0'}
          />
        ))}
      </ul>
    </nav>
  )
}
