import React, { useState, useMemo } from 'react'

function PriceCard({ item }) {
  const placeholder = 'https://placehold.co/400x400?text=Product+Image'
  const src = item.image_url || item.image || placeholder

  const onImgError = (e) => {
    e.target.onerror = null
    e.target.src = placeholder
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden shadow-md">
      <div className="relative">
        {item.is_lowest && (
          <div className="absolute top-2 right-2 z-10">
            <span className="bg-emerald-500 text-emerald-900 text-xs font-semibold px-2 py-1 rounded">Lowest</span>
          </div>
        )}
        <img src={src} alt={item.retailer} onError={onImgError} className="w-full h-48 object-cover" />
      </div>
      <div className="p-4">
        <h3 className="text-lg font-semibold">{item.retailer}</h3>
        <div className="mt-2">
          <div className="text-2xl font-extrabold text-emerald-400">NT$ {item.price_twd}</div>
          <div className="text-sm text-gray-400">{item.original_price_string ? item.original_price_string : `${item.original_price} ${item.currency}`}</div>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            {item.sizes && item.sizes.length > 0 ? (
              <span className="px-2 py-1 bg-gray-700 rounded">Sizes: {item.sizes.slice(0,4).join(', ')}</span>
            ) : (
              <span className="px-2 py-1 bg-gray-700 rounded">Weight: {item.weight || 'N/A'}</span>
            )}
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Final</div>
            <div className="text-xl font-extrabold text-emerald-400">NT$ {item.final_price_twd}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [q, setQ] = useState('Barbour Spey')
  const [results, setResults] = useState([])
  const [sortOption, setSortOption] = useState('recommended')
  const [storeFilter, setStoreFilter] = useState('All Stores')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function doSearch(e) {
    e && e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q }),
      })
      if (!res.ok) {
        const text = await res.text()
        console.error('Search API error', res.status, text)
        setError(`Search failed: ${res.status}`)
        setResults([])
      } else {
        const data = await res.json()
        setResults(data.results || [])
      }
    } catch (err) {
      console.error(err)
      setError('Network error')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  // derived values: store options and the filtered/sorted list
  const storeOptions = useMemo(() => {
    const setStores = new Set((results || []).map(r => r.retailer || 'Unknown'))
    return ['All Stores', ...Array.from(setStores)]
  }, [results])

  const displayedList = useMemo(() => {
    let list = (results || []).slice()
    if (storeFilter && storeFilter !== 'All Stores') {
      list = list.filter(i => (i.retailer || '').toLowerCase() === (storeFilter || '').toLowerCase())
    }
    if (sortOption === 'low') {
      list.sort((a, b) => (a.price_twd || 0) - (b.price_twd || 0))
    } else if (sortOption === 'high') {
      list.sort((a, b) => (b.price_twd || 0) - (a.price_twd || 0))
    }
    return list
  }, [results, sortOption, storeFilter])

  return (
    <div className="min-h-screen p-8 bg-gray-900 text-gray-100">
      <div className="max-w-4xl mx-auto">
        <header className="mb-6">
          <h1 className="text-3xl font-bold">HypePrice Tracker</h1>
          <p className="text-gray-400 mt-1">Compare prices and compute landed cost to Taiwan</p>
        </header>

        <form onSubmit={doSearch} className="flex gap-2 mb-6">
          <input className="flex-1 p-3 rounded bg-gray-800 border border-gray-700" value={q} onChange={e => setQ(e.target.value)} />
          <button className="px-4 py-2 bg-emerald-500 text-emerald-900 rounded font-semibold" disabled={loading}>{loading? 'Searching...':'Search'}</button>
        </form>

        {/* Control bar: sort + store filter */}
        <div className="flex items-center gap-4 mb-6">
          <div>
            <label className="text-sm text-gray-300 mr-2">Sort</label>
            <select value={sortOption} onChange={e => setSortOption(e.target.value)} className="p-2 bg-gray-800 border border-gray-700 rounded">
              <option value="recommended">Recommended</option>
              <option value="low">Price: Low to High</option>
              <option value="high">Price: High to Low</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-300 mr-2">Store</label>
            <select value={storeFilter} onChange={e => setStoreFilter(e.target.value)} className="p-2 bg-gray-800 border border-gray-700 rounded">
              {/* options generated from results */}
              <option value="All Stores">All Stores</option>
              {Array.from(new Set(results.map(r => r.retailer || 'Unknown'))).map((s, i) => (
                <option key={i} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          {error && <div className="text-red-400 mb-4">{error}</div>}
          {results.length === 0 && !loading && !error && <div className="text-gray-400 mb-4">No results yet — try searching.</div>}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {displayedList.map((r, idx) => (
              <PriceCard key={idx} item={r} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
