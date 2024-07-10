import { useEffect, useRef, useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import clsx from 'clsx'

import { useFeed } from '@/components/releases/FeedProvider'
import { FormattedDate } from '@/components/releases/FormattedDate'

export const a = Link

export const wrapper = function Wrapper({ children }) {
  return children
}

export function H2(props) {
  let { isFeed } = useFeed()

  if (isFeed) {
    return null
  }

  return (
    <h2 className="text-2xs/4 typography  font-bold text-white/50" {...props} />
  )
}

export const p = function Paragraph({ children }) {
  return <p className="text-2xs/4 typography text-white">{children}</p>
}

export const img = function Img(props) {
  return (
    <div className="relative mt-8 overflow-hidden rounded-xl bg-gray-900 [&+*]:mt-8">
      <Image
        alt=""
        sizes="(min-width: 1280px) 36rem, (min-width: 1024px) 45vw, (min-width: 640px) 32rem, 95vw"
        {...props}
      />
      <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-inset  ring-white/10" />
    </div>
  )
}

function ContentWrapper({ className, children }) {
  return (
    <div className="mx-auto max-w-7xl px-6 lg:flex lg:px-8">
      <div className="ml-10 lg:flex lg:w-full lg:justify-center ">
        <div
          className={clsx(
            'mx-auto max-w-lg break-words text-gray-300 lg:mx-0 lg:w-0 lg:max-w-xl lg:flex-auto ',
            className
          )}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

function ArticleHeader({ id, date }) {
  return (
    <header className="relative mb-10 ">
      <div className="pointer-events-none absolute left-[max(-0.5rem,calc(50%-18.625rem))] top-0 z-50 flex h-4 items-center justify-end gap-x-2 ">
        <div className="h-[0.0625rem] w-3.5 bg-gray-400 " />
      </div>
      <ContentWrapper>
        <div className="flex flex-wrap">
          <Link href={`#${id}`} className="inline-flex">
            <FormattedDate
              date={date}
              className="text-2xs/4 font-medium text-white/50"
            />
          </Link>
        </div>
      </ContentWrapper>
    </header>
  )
}

export function Article({ id, title, date, children }) {
  let { isFeed } = useFeed()
  let heightRef = useRef(null)
  let [heightAdjustment, setHeightAdjustment] = useState(0)

  useEffect(() => {
    let observer = new window.ResizeObserver(() => {
      let { height } = heightRef.current.getBoundingClientRect()
      let nextMultipleOf8 = 8 * Math.ceil(height / 8)
      setHeightAdjustment(nextMultipleOf8 - height)
    })

    observer.observe(heightRef.current)

    return () => {
      observer.disconnect()
    }
  }, [])

  if (isFeed) {
    return (
      <article class="text-white">
        <script
          type="text/metadata"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({ id, title, date }),
          }}
        />
        {children}
      </article>
    )
  }

  return (
    <article
      id={id}
      className="scroll-mt-16"
      style={{ paddingBottom: `${heightAdjustment}px` }}
    >
      <div ref={heightRef}>
        <ArticleHeader id={id} date={date} />
        <ContentWrapper className="typography">{children}</ContentWrapper>
      </div>
    </article>
  )
}

export const article = Article
export const h2 = H2

export const ul = function UnorderedList({ children }) {
  return <ul className="list-inside list-disc">{children}</ul>
}

export const code = function Code({ highlightedCode, ...props }) {
  if (highlightedCode) {
    return (
      <code {...props} dangerouslySetInnerHTML={{ __html: highlightedCode }} />
    )
  }

  return <code {...props} />
}

export const pre = function Pre({ children }) {
  return <pre className="overflow-x-scroll">{children}</pre>
}
