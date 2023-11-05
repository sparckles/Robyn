import { Button } from '@/components/documentation/Button'
import { Heading } from '@/components/documentation/Heading'

const guides = [
  {
    href: '/documentation/api_reference',
    name: 'Installation',
    description: 'Start using Robyn in your project.',
  },
  {
    href: '/documentation/api_reference/getting_started',
    name: 'Getting Started',
    description: 'Start with creating basic routes in Robyn.',
  },
  {
    href: '/documentation/api_reference/request_object',
    name: 'The Request Object',
    description: 'Learn about the Request Object in Robyn.',
  },
  {
    href: '/documentation/api_reference/robyn_env',
    name: 'The Robyn Env file',
    description: 'Learn about the Robyn variables',
  },
  {
    href: '/documentation/api_reference/middlewares',
    name: 'Middlewares, Events and Websockets',
    description: 'Learn about Middlewares, Events and Websockets in Robyn.',
  },
  {
    href: '/documentation/api_reference/authentication',
    name: 'Authentication',
    description: 'Learn about Authentication in Robyn.',
  },
  {
    href: '/documentation/api_reference/const_requests',
    name: 'Const Requests and Multi Core Scaling',
    description: 'Learn about Const Requests and Multi Core Scaling in Robyn.',
  },
  {
    href: '/documentation/api_reference/cors',
    name: 'CORS',
    description: 'CORS',
  },
  {
    href: '/documentation/api_reference/templating',
    name: 'Templating',
    description: 'Learn about Templating in Robyn.',
  },
  {
    href: '/documentation/api_reference/file-uploads',
    name: 'File Uploads',
    description:
      'Learn how to upload and download files to your server using Robyn.',
  },
  {
    href: '/documentation/api_reference/websockets',
    name: 'Websockets',
    description: 'Learn how to use Websockets in Robyn.',
  },
  {
    href: '/documentation/api_reference/views',
    name: 'Code Organisation',
    description: 'Learn about Views and SubRouters in Robyn.',
  },

  {
    href: '/documentation/api_reference/exceptions',
    name: 'Exceptions',
    description: 'Learn how to handle exceptions in Robyn.',
  },
  {
    href: '/documentation/api_reference/advanced_features',
    name: 'Advanced Features',
    description: 'Learn about advanced features in Robyn.',
  },
]

export function ApiDocs() {
  return (
    <div className="my-16 xl:max-w-none">
      <Heading level={2} id="api_docs">
        <h3 className="text-white">Api Docs</h3>
      </Heading>
      <div className="not-prose mt-4 grid grid-cols-1 gap-8 border-t border-white/5 pt-10 sm:grid-cols-2 xl:grid-cols-4">
        {guides.map((guide) => (
          <div key={guide.href}>
            <h3 className="text-sm font-semibold text-white">{guide.name}</h3>
            <p className="mt-1 text-sm text-zinc-400">{guide.description}</p>
            <p className="mt-4">
              <Button href={guide.href} variant="text" arrow="right">
                Read more
              </Button>
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
