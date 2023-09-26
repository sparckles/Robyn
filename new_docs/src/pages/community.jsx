import Head from 'next/head'
import Image from 'next/image'
import sparcklesLogo from '@/images/sparckles-logo.png'
import { useEffect, useState } from 'react'

function Contributors() {
  const [contributors, setContributors] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchContributors = async () => {
      try {
        const response = await fetch(
          `https://api.github.com/repos/sparckles/robyn/contributors`
        )
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        setContributors(data)
      } catch (error) {
        setError(error.toString())
      }
    }

    fetchContributors()
  }, [])

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  return (
    <div className="flex flex-wrap bg-transparent">
      {contributors.map((contributor) => (
        <div key={contributor.id} className="m-2 flex flex-col items-center">
          <a
            href={contributor.html_url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 text-white hover:text-white hover:underline"
          >
            <img
              src={contributor.avatar_url}
              alt={contributor.login}
              className="h-12 w-12 rounded-full"
            />
          </a>
        </div>
      ))}
    </div>
  )
}
export default function Community() {
  return (
    <>
      <Head>
        <meta
          name="description"
          content="The Robyn Community is a group of people who are passionate about the Robyn project."
        />
      </Head>
      <main className="relative isolate">
        {/* Background */}
        <div
          className="absolute inset-x-0 top-4 -z-10 flex transform-gpu justify-center overflow-hidden blur-3xl"
          aria-hidden="true"
        >
          <div
            className="aspect-[1108/632] w-[69.25rem] flex-none bg-gradient-to-r from-orange-800 to-yellow-500 opacity-40"
            style={{
              clipPath:
                'polygon(73.6% 51.7%, 91.7% 11.8%, 100% 46.4%, 97.4% 82.2%, 92.5% 84.9%, 75.7% 64%, 55.3% 47.5%, 46.5% 49.4%, 45% 62.9%, 50.3% 87.2%, 21.3% 64.1%, 0.1% 100%, 5.4% 51.1%, 21.4% 63.9%, 58.9% 0.2%, 73.6% 51.7%)',
            }}
          />
        </div>

        {/* Header section */}
        <div className="px-6 pt-14 lg:px-8">
          <div className="mx-auto max-w-2xl pt-24 text-center sm:pt-40">
            <h2 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              Robyn Community
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Robyn is a community project and is housed under the sparckles
              orgranisation.
            </p>
          </div>
        </div>

        {/* Content section */}

        <div className="relative isolate -z-10 mt-4 sm:mt-12">
          <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
            <div className="mx-auto flex max-w-2xl flex-col gap-16  px-6 py-16 sm:rounded-3xl sm:p-8 lg:mx-0 lg:max-w-none lg:flex-row lg:items-center lg:py-20 xl:gap-x-20 xl:px-20">
              <div className="w-full flex-auto">
                <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                  Our Amazing Contributors
                </h2>
                <Contributors />
              </div>
            </div>
          </div>
        </div>

        {/* Values section */}
        <div className="mx-auto mt-32 max-w-7xl px-6 sm:mt-40 lg:px-8">
          <div className="mx-auto max-w-2xl lg:mx-0">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Join us on our journey
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Join us on our journey to spark new ideas, ignite the spirit of
              open-source development, and break down the walls that limit
              innovation and progress. Together, we can create a brighter future
              for the Python ecosystem and the global software community.
            </p>

            <div className="mt-10 flex">
              <a
                href="https://discord.com/invite/rkERZ5eNU8"
                target="_blank"
                rel="noreferrer"
                className="text-sm font-semibold leading-6 text-indigo-400"
              >
                Join our community! <span aria-hidden="true">&rarr;</span>
              </a>
            </div>
          </div>
        </div>

        {/* Team section */}
        <div className="mx-auto mt-32 max-w-7xl px-6 sm:mt-40 lg:px-8">
          <div className="mx-auto max-w-2xl lg:mx-0">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Our team
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Robyn is housed under an open source orgranisation called
              Sparckles. We are a group of developers passionate about the open
              source community. Come join us and help us empower the Python web
              ecosystem.
            </p>
          </div>
        </div>

        {/* CTA section */}
        <div className="relative isolate -z-10 mt-32 sm:mt-40">
          <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
            <div className="mx-10 flex max-w-2xl flex-col gap-16 bg-white/5 px-6 py-16 ring-1 ring-white/10 sm:rounded-3xl sm:p-8 md:mx-auto lg:mx-0 lg:max-w-none lg:flex-row lg:items-center lg:py-20 xl:gap-x-20 xl:px-20">
              <Image
                className="h-96 w-full flex-none rounded-2xl object-cover shadow-xl  lg:aspect-square lg:h-auto lg:max-w-sm"
                src={sparcklesLogo}
                alt="sparckles logo"
              />
              <div className="w-full flex-auto">
                <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                  Sparckles
                </h2>
                <p className="mt-6 text-lg leading-8 text-gray-300">
                  Sparckles is an innovative open-source organization dedicated
                  to enhancing the Python ecosystem by developing cutting-edge
                  tools, fostering a vibrant community, and providing robust
                  infrastructure solutions.
                </p>
                <div className="mt-10 flex">
                  <a
                    href="https://github.com/sparckles"
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-semibold leading-6 text-indigo-400"
                  >
                    Visit our homepage <span aria-hidden="true">&rarr;</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div
            className="absolute inset-x-0 -top-16 -z-10 flex transform-gpu justify-center overflow-hidden blur-3xl"
            aria-hidden="true"
          >
            <div
              className="aspect-[1318/752] w-[82.375rem] flex-none bg-gradient-to-r from-orange-800 to-yellow-500 opacity-20"
              style={{
                clipPath:
                  'polygon(73.6% 51.7%, 91.7% 11.8%, 100% 46.4%, 97.4% 82.2%, 92.5% 84.9%, 75.7% 64%, 55.3% 47.5%, 46.5% 49.4%, 45% 62.9%, 50.3% 87.2%, 21.3% 64.1%, 0.1% 100%, 5.4% 51.1%, 21.4% 63.9%, 58.9% 0.2%, 73.6% 51.7%)',
              }}
            />
          </div>
        </div>

        {/* sponsors */}
        <div className="py-24 sm:py-32">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl lg:max-w-none">
              <div className="text-center">
                <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                  Sponsors
                </h2>
                <p className="mt-4 text-lg leading-8 text-gray-300">
                  Thanks to our sponsors for supporting us!
                </p>
              </div>
              <dl className="mx-10 mt-16 grid max-w-screen-xl grid-cols-1 gap-0.5 overflow-hidden rounded-2xl text-center sm:mx-10 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex flex-col justify-center justify-items-center bg-white/5 p-8">
                  <a
                    href="https://www.digitalocean.com/?refcode=3f2b9fd4968d&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <dd className=" text-3xl font-semibold tracking-tight text-white">
                      <img
                        src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/SVG/DO_Logo_vertical_blue.svg"
                        alt="Digital Ocean"
                        className="aspect-square  "
                      />
                    </dd>
                  </a>
                </div>
                <div className="flex flex-col justify-center   bg-white/5 p-8">
                  <dt className="text-sm font-semibold leading-6 text-gray-300"></dt>
                  <a
                    href="https://github.com/appwrite"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <dd className=" text-3xl font-semibold tracking-tight text-white">
                      <img
                        src="https://pbs.twimg.com/profile_images/1569586501335359494/4rq0Hb99_400x400.jpg"
                        alt="AppWrite"
                        className="rounded-full"
                      />
                    </dd>
                  </a>
                </div>
                <div className="flex flex-col justify-center justify-items-center  bg-white/5 p-8">
                  <dt className="text-sm font-semibold leading-6 text-gray-300">
                    {/* Community Contributors */}
                  </dt>
                  <a
                    href="https://github.com/shivaylamba"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <dd className=" text-3xl font-semibold tracking-tight text-white">
                      <img
                        src="https://avatars.githubusercontent.com/u/19529592?v=4"
                        alt="Shivay Lamba"
                        className="rounded-full "
                      />
                    </dd>
                  </a>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
