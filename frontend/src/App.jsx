import { useState, useEffect, useRef } from 'react'
import './App.css'
import axios from 'axios'

import { getCachedResult, setCachedResult } from './cache'

function App() {
  const [query, setQuery] = useState('')
  const [companyTicker, setCompanyTicker] = useState('')
  const [quarter, setQuarter] = useState('')
  const [section, setSection] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [companiesList, setCompaniesList] = useState([])
  const [quartersList, setQuartersList] = useState([])
  const [answer, setAnswer] = useState('')
  const [cacheCleared, setCacheCleared] = useState(false)
  const [showInfoBox, setShowInfoBox] = useState(false)
  const infoBoxRef = useRef(null)

  // --- demo sample queries ---------------------------
  const SAMPLE_QUERIES = [
    'Which CEOs talked about layoffs or workforce reductions in 2023?',
    'Who mentioned generative AI opportunities in Q1 2024?',
    'How did Microsoft describe cloud growth drivers in Q1 2024?',
    'Which companies cited foreign-exchange headwinds in 2022?',
    'Who discussed returning cash to shareholders via dividends in 2023?',
    'Who referenced inventory write-downs due to weak consumer demand in 2022?',
    'How did Visa describe cross-border payment growth drivers in Q1 2024?',
    'Who mentioned raising prices to offset inflation in 2022?'
  ]

  // Pick 4 random queries once per mount
  const [displayQueries] = useState(() => {
    const shuffled = [...SAMPLE_QUERIES].sort(() => 0.5 - Math.random())
    return shuffled.slice(0, 4)
  })
  // ----------------------------------------------------

  const [snippets, setSnippets] = useState([])

  const SkeletonCard = () => (
    <div className="border border-gray-200 rounded-2xl bg-white shadow-sm p-6 animate-pulse">
      <div className="h-6 bg-gray-300 rounded w-1/3 mb-4"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-300 rounded"></div>
        <div className="h-4 bg-gray-300 rounded w-5/6"></div>
        <div className="h-4 bg-gray-300 rounded w-2/3"></div>
      </div>
    </div>
  )

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (infoBoxRef.current && !infoBoxRef.current.contains(event.target)) {
        setShowInfoBox(false)
      }
    }
    if (showInfoBox) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showInfoBox])

  useEffect(() => {
    axios
      .get(`${import.meta.env.VITE_BACKEND_URL}/metadata`)
      .then((res) => {
        const raw = res.data.companies || {}
        const parsed = Object.entries(raw).map(([name, ticker]) => ({ name, ticker}))
        console.log(raw, parsed)
        setCompaniesList(parsed)
        setQuartersList(res.data.quarters || [])
      })
      .catch((err) => console.error('Metadata fetch error:', err))
  }, [])

  const formatSpeakers = (participants = {}) => {
      const names = Object.entries(participants)
        .filter(([, role]) => role === 'executive' || role === 'analyst')
        .map(([name]) => name)
      return names.length ? `Speakers: ${names.join(', ')}` : ''
    }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (query.trim() === '') return
    setLoading(true)
    setError(null)
    setAnswer('')
    setSnippets([])
    try {
      const queryKey = JSON.stringify({ query, companyTicker, quarter, section})
      const cached = getCachedResult(queryKey)

      if (cached) {
        setAnswer(cached.answer)
        setSnippets(cached.snippets)
        return
      }

      const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/search`, {
        query: query,
        filters: {
          ...(companyTicker && { company: companyTicker }),
          ...(quarter && { quarter }),
          ...(section && { section }),
        }
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: false,
      })
      if (!response.data.answer) {
        setError('No results found. Please try another query.')
      } else {
        setAnswer(response.data.answer)
        setSnippets(response.data.snippets || [])
        setCachedResult(queryKey, {
          answer: response.data.answer,
          snippets: response.data.snippets || [],
        })
      }
    } catch (err) {
      console.error("Search error:", err)
      setError('Unable to retrieve search results. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='max-w-2xl mx-auto py-10 px-4 sm:px-6 lg:px-8'>
      <div className="flex flex-col items-center space-y-3 my-8">
      <h1 className="text-3xl font-bold text-grey-800">🪡 Needle Semantic Search 🪡</h1>
        <p className="text-gray-500">
          Instantly query&nbsp;&amp;&nbsp;summarise Fortune&nbsp;75 earnings-call transcripts.
        </p>

        <div className="relative mt-2">
          <button
            onClick={() => setShowInfoBox(!showInfoBox)}
            className="cursor-pointer text-blue-600 text-sm inline-flex items-center gap-1 select-none focus:outline-none"
          >
            <span className="inline-block w-4 h-4 rounded-full border border-current flex items-center justify-center text-[10px] leading-none">i</span>
            <span>What’s in the index?</span>
          </button>
          {showInfoBox && (
            <div
              ref={infoBoxRef}
              className="absolute top-8 left-1/2 -translate-x-1/2 z-10 w-[300px] bg-white text-gray-700 text-sm border border-gray-300 rounded-lg shadow-lg p-4 cursor-pointer"
              onClick={() => setShowInfoBox(false)}
            >
              Needle indexes ~6–7 years of quarterly earnings transcripts from the top&nbsp;75 publicly traded companies. Results combine semantic search with an LLM-generated answer and supporting excerpts.
            </div>
          )}
        </div>
      </div>
      <form className='max-w-2xl mx-auto' onSubmit={handleSearch}>
        <div className="flex justify-center flex-wrap gap-2 mb-4">
          {displayQueries.map((sample) => (
            <button
              key={sample}
              type="button"
              onClick={() => setQuery(sample)}
              className="bg-gray-200 hover:bg-gray-300 text-sm px-3 py-1 rounded-full"
            >
              {sample}
            </button>
          ))}
        </div>
        <div className="text-center w-full text-sm mb-2">
          <button
            type="button"
            onClick={() => {
              localStorage.removeItem('needleQueryCache')
              setCacheCleared(true)
              setTimeout(() => setCacheCleared(false), 2500)
            }}
            className="text-gray-400 hover:text-gray-600 underline focus:outline-none"
            title="Clear cached results"
          >
            Clear Local Cache
          </button>
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full px-5 py-3 rounded-xl border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500"
          placeholder="What did Apple say about AI strategy?"
        />
        <div className="flex flex-col sm:flex-row justify-center gap-4 my-4">
          {/* Company filter */}
          <select
            className="border rounded-lg shadow-sm px-4 py-2 bg-white max-w-[280px] sm:max-w-[320px] truncate text-sm"
            value={companyTicker}
            onChange={(e) => setCompanyTicker(e.target.value)}
          >
            <option value="">All Companies</option>
            {companiesList.map(({ name, ticker }) => (
              <option key={ticker} value={ticker}>
                {`${name} (${ticker.toUpperCase()})`}
              </option>
            ))}
          </select>

          {/* Section filter */}
          <select
            className="border rounded-lg shadow-sm px-4 py-2 bg-white min-w-[180px] text-sm"
            value={section}
            onChange={(e) => setSection(e.target.value)}
          >
            <option value="">All Sections</option>
            <option value="prepared_remarks">Prepared Remarks</option>
            <option value="qa">Q&amp;A</option>
          </select>
        </div>
        {/*
          Grey-out Search button when query is empty.
        */}
        {(() => {
          const isQueryEmpty = !query.trim()
          return (
            <button
              type="submit"
              disabled={isQueryEmpty}
              className={`mt-2 mb-6 rounded-lg shadow px-6 py-3 text-white ${
                isQueryEmpty
                  ? 'bg-blue-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-600/90'
              }`}
            >
              Search Transcripts
            </button>
          )
        })()}
      </form>

      {/* No results */}
      {!error && !answer && !loading && (
        <div className="text-center text-gray-500 my-8">
          No results yet. Try a query to get insights.
        </div>
      )}

      {/* Loading indicator */}
      {loading && <SkeletonCard />}

      {/* Error handling */}
      {error && <div className='mt-4 text-red-500'>An error occurred: {error}</div>}

      {answer && (
        <div className="mt-4 border border-gray-200 rounded-2xl bg-white shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Answer</h2>
          <p className="text-gray-700 mb-4">{answer}</p>

          {snippets.length > 0 && (
            <details>
              <summary className="cursor-pointer text-indigo-600 font-medium">
                Show supporting excerpts ({snippets.length})
              </summary>
              <ul className="mt-4 space-y-3 pl-4 text-left">
                {snippets.map((s, idx) => {
                  const highlightUrl = `${s.url}#:~:text=${encodeURIComponent(
                    s.text.replace(/[“”"]/g, '').split(/\s+/).slice(0, 8).join(' ')
                  )}`

                  return (
                    <li
                      key={idx}
                      onClick={() => window.open(highlightUrl, '_blank', 'noopener')}
                      className="flex flex-col space-y-1 p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                      title="Open full transcript in a new tab"
                    >
                      <blockquote className='text-grey-800 leading-snug italic'>
                        "{s.text}"
                      </blockquote>
                      <div className="flex items-center flex-wrap gap-2 text-sm text-gray-500">
                        {/* Speakers / company / quarter / year */}
                        <span>
                          {formatSpeakers(s.participants)}
                          {formatSpeakers(s.participants) && ' • '}
                          {s.company.toUpperCase()} {s.quarter.toUpperCase()} {s.year}
                        </span>
                        {/* Section pill */}
                        {s.section && (
                          <span
                            className={
                              'px-2 py-[2px] rounded-full font-medium ' +
                              (s.section === 'qa'
                                ? 'bg-indigo-100 text-indigo-700'
                                : 'bg-emerald-100 text-emerald-700')
                            }
                          >
                            {s.section === 'qa' ? 'Q&A' : 'Prepared Remarks'}
                          </span>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </details>
          )}
        </div>
      )}
      {cacheCleared && (
        <div className="fixed bottom-4 right-4 z-50 bg-green-600 text-white text-sm px-4 py-2 rounded shadow-lg transition-opacity duration-300">
          Client-side cache cleared
        </div>
      )}
    </div>
  )
}

export default App
