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
  const currentLanguage = router.locale || 'en'

  const changeLanguage = (locale) => {
    router.push({ pathname, query }, asPath, { locale })
  }

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-white hover:bg-white/10">
        {languages.find(l => l.code === currentLanguage)?.name}
        <svg
          width="6"
          height="3"
          className="ml-2 stroke-current"
          fill="none"
          viewBox="0 0 6 3"
        >
          <path d="M0 0L3 3L6 0" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </Menu.Button>
      <Menu.Items as={motion.div}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="absolute right-0 mt-2 w-40 origin-top-right rounded-lg bg-white/10 p-1 backdrop-blur-lg"
      >
        {languages.map((language) => (
          <Menu.Item key={language.code}>
            {({ active }) => (
              <button
                onClick={() => changeLanguage(language.code)}
                className={`${
                  active ? 'bg-white/10' : ''
                } ${
                  currentLanguage === language.code ? 'text-orange-500' : 'text-white'
                } group flex w-full items-center rounded-md px-2 py-2 text-sm`}
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