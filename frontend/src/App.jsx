import { useState } from 'react'
import './App.css'
import axios from 'axios'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [company, setCompany] = useState('')
  const [quarter, setQuarter] = useState('')

  const handleSearch = async (e) => {
    e.preventDefault()
    const response = await axios.post(`https://needle-api.fly.dev/search`, {
    // const response = await axios.post(`http://localhost:8000/search`, {
      query: query,
      filters: {
        ...(company && { company }),
        ...(quarter && { quarter }),
      }
    })
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
        <select value={company} onChange={e => setCompany(e.target.value)}>
          <option value="">All Companies</option>
          <option value="Apple">Apple</option>
          <option value="Microsoft">Microsoft</option>
          <option value="Netflix">Netflix</option>
          <option value="NVIDIA">NVIDIA</option>
          <option value="Tesla">Tesla</option>
        </select>
        <select value={quarter} onChange={e => setQuarter(e.target.value)}>
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
        <button type="submit" className="mt-2 bg-blue-500 text-white rounded px-4 py-2">
          Search
        </button>
      </form>

      <div className='mt-4'>
        {results.map((result, idx) => (
          <div key={idx} className='border-b py-2'>
            <h3 className='font-semibold'>{result.metadata.company} (Q{result.metadata.quarter}Y{result.metadata.year})</h3>
            <p className='text-gray-700'>{result.metadata.snippet}</p>
            <a href={result.metadata.url} target="_blank" className='text-blue-600 underline'>
              View Transcript
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
