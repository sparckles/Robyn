import axios from 'axios'
import { MDXProvider } from '@mdx-js/react'
import { serialize } from 'next-mdx-remote/serialize'
import { MDXRemote } from 'next-mdx-remote'

import {
  a as A,
  H2,
  Article,
} from '@/components/releases/mdx'

import * as releaseMdxComponents from '@/components/releases/mdx'

const ChangelogPage = ({ releases }) => {
  return (
    <>
      {releases.map((release) => (
        <MDXProvider key={release.id} components={releaseMdxComponents}>
          <Article
            key={release.id}
            date={new Date(release.publishedAt)}
            id={release.name}
          >
            <A
              href={`https://github.com/sparckles/robyn/releases/tag/${release.tag}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-yellow-500 transition-colors"
            >
            <H2 key={release.id} className="text-lg font-extrabold text-white">
              {release.name}
              </H2>
            </A>
            <MDXRemote
              key={release.id}
              {...release.body}
              components={releaseMdxComponents}
            />
          </Article>
        </MDXProvider>
      ))}
    </>
  )
}

export async function getStaticProps() {
  const response = await axios.get(
    'https://api.github.com/repos/sparckles/robyn/releases'
  )

  const releases = await Promise.all(
    response.data.map(async (release) => ({
      id: release.id,
      name: release.name,
      body: await serialize(release.body),
      publishedAt: release.published_at,
      tag: release.tag_name,
    }))
  )

  return {
    props: {
      releases,
    },
  }
}

export default ChangelogPage
