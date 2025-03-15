import { useState } from 'react'
import './App.css'
import axios from 'axios'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])

  const handleSearch = async (e) => {
    e.preventDefault()
    const response = await axios.get(`http://localhost:8000/search?q=${query}`)
    setResults(response.data.results)
  }

  return (
    <div className='max-w-x1 mx-auto mt-10'>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder='Ask about earnings transcripts...'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className='border rounded px-4 py-2 w-full'
          />
          <button type="submit" className="mt-2 bg-blue-500 text-white rounded px-4 py-2">
            Search
          </button>
      </form>

      <div className='mt-4'>
        {results.map((result, idx) => (
          <div key={idx} className='border-b py-2'>
            <h3 className='font-semibold'>{result.metadata.company} (Q{result.metadata.quarter}Y{result.metadata.year})</h3>
            <p className='text-gray-700'>{result.metadata.snippet}</p>
            <a href={result.url} target="_blank" className='text-blue-600 underline'>
              View  Transcript
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
