import { useRouter } from 'next/router'
import { Menu } from '@headlessui/react'
import { motion } from 'framer-motion'

const languages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
]

function LanguageSelector() {
  const router = useRouter()
  const { pathname, asPath, query } = router
  const currentLanguage = asPath.includes('/zh') ? 'zh' : 'en'

  const changeLanguage = (locale) => {
    const currentPath = asPath.split('?')[0]
    
    if (currentPath === '/documentation' || currentPath === '/documentation/') {
      router.push(`/documentation/${locale}`)
      return
    }

    const newPath = currentPath.replace(
      /\/documentation\/(en|zh)/,
      `/documentation/${locale}`
    )
    
    router.push(newPath)
  }

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center gap-2 rounded-lg bg-zinc-800/40 px-3 py-2 text-sm text-white hover:bg-zinc-800 transition-colors duration-200">
        {languages.find(l => l.code === currentLanguage)?.name}
        <svg
          width="8"
          height="5"
          className="ml-1 stroke-current"
          fill="none"
          viewBox="0 0 8 5"
        >
          <path d="M1 1L4 4L7 1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </Menu.Button>
      <Menu.Items as={motion.div}
        initial={{ y: -10 }}
        animate={{ y: 0 }}
        exit={{ y: -10 }}
        className="absolute left-0 mt-1 w-40 origin-top-left rounded-lg bg-[#27272A] ring-1 ring-zinc-700 shadow-xl z-50"
      >
        {languages.map((language) => (
          <Menu.Item key={language.code}>
            {({ active }) => (
              <button
                onClick={() => changeLanguage(language.code)}
                className={`${
                  active ? 'bg-zinc-700/50' : ''
                } ${
                  currentLanguage === language.code ? 'bg-orange-500/10 text-orange-500' : 'text-zinc-100'
                } group flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm transition-colors duration-200`}
              >
                {language.name}
              </button>
            )}
          </Menu.Item>
        ))}
      </Menu.Items>
    </Menu>
  )
}

export default LanguageSelector 