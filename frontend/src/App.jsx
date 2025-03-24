import { useState } from 'react'
import './App.css'
import axios from 'axios'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [company, setCompany] = useState('')
  const [quarter, setQuarter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResults([])
    try {
      const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/search`, {
        query: query,
        filters: {
          ...(company && { company }),
          ...(quarter && { quarter }),
        }
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: false,
      })
      if (response.data === "") {
        setError('No results found. Please try another query.')
        setResults([])
      } else {
        setResults(response.data.results)
      }
    } catch (err) {
      console.error("Search error:", err)
      setError('Unable to retrieve search results. Please try again later.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='max-w-2xl mx-auto py-10 px-4 sm:px-6 lg:px-8'>
      <div className='text-center my-8'>
        <h1 className="text-3xl font-bold text-grey-800">🔍 Needle Semantic Search</h1>
        <p className="text-gray-500 mt-2">Find exactly what you're looking for from earnings calls in seconds.</p>
      </div>
      <form className='max-w-2xl mx-auto' onSubmit={handleSearch}>
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
              value={company}
              onChange={e => setCompany(e.target.value)}
          >
            <option value="">All Companies</option>
            <option value="Apple">Apple</option>
            <option value="Microsoft">Microsoft</option>
            <option value="Netflix">Netflix</option>
            <option value="NVIDIA">NVIDIA</option>
            <option value="Tesla">Tesla</option>
          </select>

          {/* Quarters */}
          <select className='border rounded-lg shadow-sm px-4 py-2 bg-white' value={quarter} onChange={e => setQuarter(e.target.value)}>
            <option value="">All Quarters</option>
            <option value="Q2 2025">Q2 2025</option>
            <option value="Q1 2025">Q1 2025</option>
            <option value="Q4 2024">Q4 2024</option>
            <option value="Q3 2024">Q3 2024</option>
            <option value="Q2 2024">Q2 2024</option>
            <option value="Q1 2024">Q1 2024</option>
            <option value="Q4 2023">Q4 2023</option>
            <option value="Q3 2023">Q3 2023</option>
            <option value="Q2 2023">Q2 2023</option>
            <option value="Q1 2023">Q1 2023</option>
            <option value="Q4 2022">Q4 2022</option>
            <option value="Q3 2022">Q3 2022</option>
            <option value="Q2 2022">Q2 2022</option>
            <option value="Q1 2022">Q1 2022</option>
            <option value="Q4 2021">Q4 2021</option>
            <option value="Q3 2021">Q3 2021</option>
            <option value="Q2 2021">Q2 2021</option>
            <option value="Q1 2021">Q1 2021</option>
            <option value="Q4 2020">Q4 2020</option>
            <option value="Q3 2020">Q3 2020</option>
            <option value="Q2 2020">Q2 2020</option>
            <option value="Q1 2020">Q1 2020</option>
          </select>

        </div>
        <button type="submit" className="mt-2 bg-blue-600 hover:bg-blue-600/90 text-white rounded-lg shadow px-6 py-3">
          Search Transcripts
        </button>
      </form>

      {/* No results */}
      {!error && !results.length && !loading && (
        <div className="text-center text-gray-500 my-8">
          No results yet. Try a query to get insights.
        </div>
      )}

      {/* Loading indicator */}
      {loading && <div className="my-6 text-center text-gray-500">Searching insights...</div>}

      {/* Error handling */}
      {error && <div className='mt-4 text-red-500'>An error occurred: {error}</div>}

      {/* Results Cards */}
      <div className='mt-4 grid gap-6'>
        {results.map((result, idx) => (
          <div 
            key={idx} 
            className='border border-grey-200 rounded-2xl bg-white shadow-sm p-6 hover:shadow-lg transition-shadow'
          >
            <div className='flex justify-between items-center mb-3'>
              <h2 className='text-xl font-semibold text-gray-800'>
                {result.company}{' '}
                <span className='font-medium text-gray-400'>
                  Q{result.quarter} {result.year}
                </span>
              </h2>
              <a
                href={result.url}
                target="_blank"
                rel='noopener noreferrer'
                className='text-sm font-medium text-indigo-600'
              >
                View Transcript →        
              </a>
            </div>
            <ul className='space-y-2 pl-4 text-left'>
              {result.summary.map((summary, idx) => (
                <li key={idx} className='flex items-start leading-snug'>
                  <span className='mt-2 mr-2 h-2 w-2 bg-indigo-500 rounded-full flex-shrink-0'></span>
                  <span className='text-gray-700 text-base'>{summary}</span>
                </li>
              ))}
          </ul>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
