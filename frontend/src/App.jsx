import { useState, useEffect } from 'react'
import './App.css'
import axios from 'axios'

function App() {
  const [query, setQuery] = useState('')
  const [companyTicker, setCompanyTicker] = useState('')
  const [quarter, setQuarter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [companiesList, setCompaniesList] = useState([])
  const [quartersList, setQuartersList] = useState([])
  const [answer, setAnswer] = useState('')
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
    setLoading(true)
    setError(null)
    setAnswer('')
    setSnippets([])
    try {
      const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/search`, {
        query: query,
        filters: {
          ...(companyTicker && { ticker: companyTicker }),
          ...(quarter && { quarter }),
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
      {/* <img
        src="/needle_logo_orig.png"
        alt="Needle Semantic Search logo"
        className="h-40 w-auto mx-auto mb-6"
      /> */}
      <h1 className="text-3xl font-bold text-grey-800">🔍 Needle Semantic Search</h1>
        <p className="text-gray-500">
          Instantly query&nbsp;&amp;&nbsp;summarise Fortune&nbsp;75 earnings-call transcripts.
        </p>

        {/* inline “info” dropdown */}
        <details className="mt-2 inline-block">
          <summary className="cursor-pointer text-blue-600 text-sm inline-flex items-center gap-1 select-none">
            <span className="inline-block w-4 h-4 rounded-full border border-current flex items-center justify-center text-[10px] leading-none">i</span>
            <span>What’s in the index?</span>
          </summary>
          <div className="mt-2 text-gray-500 text-sm max-w-md mx-auto">
            Needle indexes ~6-7 years of quarterly earnings transcripts from the top&nbsp;75 publicly-traded companies.
            Results combine semantic search with an LLM-generated answer plus supporting excerpts.
          </div>
        </details>
      </div>
      <form className='max-w-2xl mx-auto' onSubmit={handleSearch}>
        <div className="flex justify-center flex-wrap gap-2 mb-4">
          {[
            'What did Apple say about AI strategy?',
            'Who mentioned supply‑chain risk in 2024?',
            'How are margins trending for Tesla?'
          ].map((sample) => (
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
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full px-5 py-3 rounded-xl border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500"
          placeholder="What did Apple say about AI strategy?"
        />
        <div className='flex gap-4 justify-center my-4'>
          {/* Company filter */}
          <select 
            className="border rounded-lg shadow-sm px-4 py-2 bg-white"
              value={companyTicker}
              onChange={e => setCompanyTicker(e.target.value)}
          >
            <option value="">All Companies</option>
            {companiesList.map(({name, ticker}) => (
              <option key={ticker} value={ticker}>
                {`${name} (${ticker.toUpperCase()})`}
              </option>
            ))}
          </select>

          {/* Quarters */}
          <select className='border rounded-lg shadow-sm px-4 py-2 bg-white' value={quarter} onChange={e => setQuarter(e.target.value)}>
            <option value="">All Quarters</option>
            {quartersList.map((q) => (
              <option key={q} value={q}>{q}</option>
            ))}
          </select>

        </div>
        <button type="submit" className="mt-2 mb-6 bg-blue-600 hover:bg-blue-600/90 text-white rounded-lg shadow px-6 py-3">
          Search Transcripts
        </button>
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
                {snippets.map((s, idx) => (
                  <li key={idx} className="flex flex-col space-y-1">
                    <blockquote className='text-grey-800 leading-snug italic'>
                      "{s.text}"
                    </blockquote>
                    <span className="text-sm text-gray-500">
                      {formatSpeakers(s.participants)}{formatSpeakers(s.participants) && ' • '}
                      {s.company.toUpperCase()} {s.quarter.toUpperCase()} {s.year}
                    </span>
                    <span className="text-gray-700">{s.snippet}</span>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-indigo-600 mt-1"
                    >
                      View Transcript →
                    </a>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

export default App
