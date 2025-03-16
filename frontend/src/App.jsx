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
    try {
      const response = await axios.post(`https://needle-api.fly.dev/search`, {
        query: query,
        filters: {
          ...(company && { company }),
          ...(quarter && { quarter }),
        }
      })
      setResults(response.data.results)
    } catch (err) {
      console.error("Search error:", err)
      setError('Unable to retrieve search results. Please try again later.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='max-w-x1 mx-auto mt-10'>
      <div className='text-center my-8'>
        <h1 className="text-3xl font-bold text-grey-800">🔍 Needle Semantic Search</h1>
        <p className="text-gray-500 mt-2">Find exactly what you're looking for from earnings calls in seconds.</p>
      </div>
      <form className='max-w-2xl mx-auto' onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full px-4 py-3 border text-lg border-gray-300 rounded-lg shadow-sm"
          placeholder="Ask about Apple's latest earnings..."
        />
        <div className='flex gap-4 justify-center my-4'>
          {/* Company filter */}
          <select className='border px-3 py-2 rounded-lg' value={company} onChange={e => setCompany(e.target.value)}>
            <option value="">All Companies</option>
            <option value="Apple">Apple</option>
            <option value="Microsoft">Microsoft</option>
            <option value="Netflix">Netflix</option>
            <option value="NVIDIA">NVIDIA</option>
            <option value="Tesla">Tesla</option>
          </select>

          {/* Quarters */}
          <select className='border px-3 py-2 rounded-lg shadow-sm' value={quarter} onChange={e => setQuarter(e.target.value)}>
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

      {/* Loading indicator */}
      {loading && <div className='mt-4 animate-pulse text-gray-600'>Loading results...</div>}

      {/* Error handling */}
      {error && <div className='mt-4 text-red-500'>An error occurred: {error}</div>}

      {/* Results Cards */}
      <div className='mt-4 grid gap-4'>
        {results.map((result, idx) => (
          <div key={idx} className='max-w-xl mx-auto my-4 border rounded-xl p-4 shadow hover:shadow-md transition-shadow'>
            <div className='flex justify-between items-center'>
              <h3 className='text-xl font-semibold text-gray-800'>
                {result.metadata.company} - <span className='text-gray-5000'>Q{result.metadata.quarter}Y{result.metadata.year}</span>
              </h3>
              <p className='text-gray-700 mt-2'>{result.metadata.snippet}</p>
              <a href={result.metadata.url} target="_blank" className='text-blue-600 underline'>
                View Transcript →        
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
