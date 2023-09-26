import { createContext, useContext } from 'react'

let FeedContext = createContext({ isFeed: false })

export function FeedProvider({ children }) {
  return (
    <FeedContext.Provider value={{ isFeed: true }}>
      {children}
    </FeedContext.Provider>
  )
}

export function useFeed() {
  return useContext(FeedContext)
}
