import { useEffect } from 'react'

let testimonials = [
  {
    body: "Robyn has revolutionized the way I develop web solutions. Its seamless integration of Python's async capabilities with a Rust runtime not only ensures reliability and scalability but also provides quick project setup, a delightful user experience, and robust plugin support. With its exceptional speed and multithreaded efficiency, Robyn's real-time communication through WebSockets and dynamic URL routing has empowered me to create highly performant and interactive applications while maintaining full control over navigation and workflows. A game-changer for modern web development!",
    author: {
      name: 'Kunal Kushwaha',
      handle: 'kunalstwt',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1661046102756323329/4fmGAMnN_400x400.jpg',
      title: 'DevRel manager at Civo',
    },
  },

  {
    body: "Having worked with a company building a Rust based open source search engine for over a year, I strongly believe in the notion that rewriting software with Rust can significantly improve software performance. Sanskar's idea to recreate Flask with Rust, was just incredible. Having used Robyn myself, it is refreshing to see such a performant Python framework and just the amazing developer ecosystem around it. Yes it still new and being developed, but I can say this with confidence that given the underlying Rust-based multithreaded run time will provide immense performance for running high throughout applications. I am glad to be one of the early sponsors and adopters for Robyn!",
    author: {
      name: 'Shivay Lamba',
      handle: 'howdevelop',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1589996761086500865/IBdsm4RZ_400x400.jpg',
      title: 'Developer Experience Engineer at MeiliSearch',
    },
  },
  {
    body: "I'm impressed with Robyn. It's a fast asynchronous web framework for the Python ecosystem that's built on top of Rust. The syntax is similar to other popular web frameworks, so it's easy to learn and be productive with. I've been using it to build web applications and services, and I'm really happy with the results. I'm also impressed with the Robyn community. They are very supportive and the developers are very responsive to feedback",
    author: {
      name: 'Carlos A. Marcano Vargas',
      handle: 'carlos_marcv',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1418988844347793410/SHKOyqB3_400x400.jpg',
      title: 'Technical Writer',
    },
  },
  // More testimonials...
  {
    body: 'Great to see a Community Driven Open Source project, achieve new heights! Robyn is built by the community for the community',
    author: {
      name: 'Eddie Jaoude',
      handle: 'eddiejaoude',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1640177590601416704/_Gs3eest_400x400.jpg',
      title: 'Creator of EddieHub',
    },
  },
  // More testimonials...
  {
    body: 'I used to be a Batman fan, but having met Robyn I now think the sidekick has become the hero. Free, OSS, straight forward and powerful, what is not to love?',
    author: {
      name: 'GrahamTheDev',
      handle: 'GrahamTheDev',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1674010320057032706/NKa0EtQ8_400x400.jpg',
      title: 'The Accessibility First DevRel ',
    },
  },
  {
    body: 'Having used both, Flask and Django for writing web applications in Python in the past, Robyn looks like their combined successor in terms of ergonomics and features available. Its reliance on a Rust runtime for performance and security is the cherry on the cake!',
    author: {
      name: 'Daniel Bodky',
      handle: 'd_bodky',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1665625007299391489/tsPgVWW2_400x400.jpg',
      title: 'Consultant, Trainer, Speaker @NETWAYS',
    },
  },
  // More testimonials...
  {
    body: 'Robyn has made a big difference in my projects. Its flexible structure allows my work to adapt smoothly to my needs, even when I face complex challenges. The community-driven and open-source nature of Robyn makes it a welcoming place for developers like me. Plus, its simple yet powerful API has greatly streamlined my development process, reducing my wor oad. I highly recommend it!',
    author: {
      name: 'Julia Furst Morgado',
      handle: 'juliafmorgado',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1140975948096868352/HJN-bkyS_400x400.jpg',
      title: 'Global technologist @Veeam',
    },
  },
  // More testimonials...
  {
    body: 'Robyn opens a new chapter in the Python web frameworks scene: the Rust powered one, where performance and safety are not the sole protagonists.',
    author: {
      name: 'Giovanni Barillari',
      handle: 'gi0baro',
      imageUrl:
        'https://pbs.twimg.com/profile_images/492996183439052800/zVEX94M__400x400.jpeg',
      title: 'Author of Granian and Emmett',
    },
  },
  // More testimonials...
  {
    body: "I collaborate with Robyn's team and I must say, Sanskar does an excellent job maintaining the community. The project as a whole is immensely beneficial, both for collaboration and its practical uses. The tool is impressive, easy to use and the entire community is very welcoming to first-time contributors",
    author: {
      name: 'Jyoti Bisht',
      handle: 'joeyousss',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1712848642271264768/1X_ygyTq_400x400.jpg',
      title: 'Open Source Developer',
    },
  },
  // More testimonials...
  {
    body: "Robyn is a breath of fresh air in web development. Merging Python's simplicity with Rust's speed, it offers a seamless experience for developers. Its features are precisely what today's web projects need. I'm particularly impressed with its community focus; it's evident that everyone's voice matters in shaping Robyn's journey. In a sea of web frameworks, Robyn stands out not just for its tech but also for its heart.",
    author: {
      name: 'Francesco Ciulla',
      handle: 'FrancescoCiull4',
      imageUrl:
        'https://pbs.twimg.com/profile_images/1617044903636123650/pYUcGGOu_400x400.jpg',
      title: 'DevRel at daily.dev',
    },
  },
  // More testimonials...
]

//shuflle testimonials

function classNames(...classes) {
  return classes.filter(Boolean).join(' ')
}

const chunk = (arr, size) =>
  Array.from({ length: Math.ceil(arr.length / size) }, (v, i) =>
    arr.slice(i * size, i * size + size)
  )

export default function Testimonials() {
  let chunkedTestimonials = [];
  
  // Separate testimonials into groups of 3, 4, and 3
  const firstGroup = chunk(testimonials.slice(0, 3), 3);
  const secondGroup = chunk(testimonials.slice(3, 7), 4);
  const thirdGroup = chunk(testimonials.slice(7), 3);
  
  // Concatenate the groups in the desired order
  chunkedTestimonials = firstGroup.concat(secondGroup, thirdGroup);
  return (
    <div className="relative isolate  pb-32 pt-24 sm:pt-32">
      <div
        className="absolute inset-x-0 top-1/2 -z-10 -translate-y-1/2 transform-gpu overflow-hidden opacity-30 blur-3xl"
        aria-hidden="true"
      >
        <div
          className="ml-[max(50%,38rem)] aspect-[1313/771] w-[82.0625rem] flex-none origin-top-right rotate-[30deg] bg-yellow-400 xl:mr-[calc(50%-12rem)]"
          style={{
            clipPath:
              'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
          }}
        />
      </div>
      <div
        className="absolute inset-x-0 top-0 -z-10 flex transform-gpu overflow-hidden pt-32 opacity-25 blur-3xl sm:pt-40 xl:justify-end"
        aria-hidden="true"
      >
        <div
          className="ml-[-22rem] aspect-[1313/771] w-[82.0625rem] flex-none origin-top-right rotate-[30deg]  xl:ml-0 xl:mr-[calc(50%-12rem)]"
          style={{
            clipPath:
              'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
          }}
        />
      </div>
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="text-lg font-semibold leading-8 tracking-tight text-yellow-400">
            Testimonials
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Some amazing people have said nice things about us.
          </p>
        </div>
        <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 grid-rows-1 gap-8 text-sm leading-6 text-gray-900 sm:mt-20 sm:grid-cols-1 xl:mx-0 xl:max-w-none xl:grid-flow-col xl:grid-cols-3">
          {chunkedTestimonials.map((columnGroup, columnGroupIdx) => (
            <div key={columnGroupIdx} className="space-y-8  ">
              {columnGroup.map((testimonial) => (
                <figure
                  key={testimonial.author.handle}
                  className="rounded-2xl bg-white/5 p-6 shadow-lg ring-1 ring-gray-900/5 duration-200 hover:bg-white/10"
                >
                  <blockquote className="text-white">
                    <p>{`“${testimonial.body}”`}</p>
                  </blockquote>
                  <figcaption className="mt-6 flex items-center gap-x-4">
                    <img
                      className="h-10 w-10 rounded-full bg-gray-50"
                      src={testimonial.author.imageUrl}
                      alt=""
                    />
                    <div>
                      <div className="font-semibold text-white">
                        {testimonial.author.name}
                      </div>
                      <div className="text-yellow-400">{`@${testimonial.author.handle}`}</div>
                      <div className="font-normal text-white">
                        {testimonial.author.title}
                      </div>
                    </div>
                  </figcaption>
                </figure>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
