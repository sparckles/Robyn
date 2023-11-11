import { mdxAnnotations } from 'mdx-annotations'
import recmaNextjsStaticProps from 'recma-nextjs-static-props'
import { recmaImportImages } from 'recma-import-images'

function recmaRemoveNamedExports() {
  return (tree) => {
    tree.body = tree.body.map((node) => {
      if (node.type === 'ExportNamedDeclaration') {
        return node.declaration
      }
      return node
    })
  }
}

export const recmaPlugins = [
  mdxAnnotations.recma,
  recmaRemoveNamedExports,
  recmaNextjsStaticProps,
  recmaImportImages,
]
