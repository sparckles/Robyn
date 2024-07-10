import axios from 'axios'
import { MDXProvider } from '@mdx-js/react'
import { useEffect, useState } from 'react'
import Markdown from 'react-markdown' // package for rendering markdown as React components
import { Layout as ReleaseLayout } from '@/components/releases/Layout'
import { serialize } from 'next-mdx-remote/serialize'
import { MDXRemote } from 'next-mdx-remote'

import {
  a,
  wrapper,
  H2,
  img,
  Article,
  code,
  p,
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
            <H2 key={release.id} className="text-lg font-extrabold text-white">
              {release.name}
            </H2>
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
    }))
  )

  return {
    props: {
      releases,
    },
  }
}

export default ChangelogPage
