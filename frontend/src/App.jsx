import React, { useState } from 'react'

function PriceCard({ item }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden shadow-md w-full max-w-xl">
      <div className="flex">
        <img src={item.image} alt={item.retailer} className="w-40 h-40 object-cover" />
        <div className="p-4 flex-1">
          <div className="flex justify-between items-start">
            <h3 className="text-lg font-semibold">{item.retailer}</h3>
            {item.is_lowest && (
              <span className="bg-emerald-500 text-emerald-900 text-xs font-semibold px-2 py-1 rounded">Lowest Price</span>
            )}
          </div>
          <p className="text-sm text-gray-300 mt-2">Original: {item.original_price} {item.currency}</p>
          <p className="mt-4 text-gray-200">Shipping (TWD): {item.shipping_twd}</p>
          <p className="mt-1 text-gray-200">Tax (TWD): {item.tax_twd}</p>
          <div className="mt-4">
            <div className="text-sm text-gray-400">Final Landed Cost</div>
            <div className="text-2xl font-extrabold text-emerald-400">NT$ {item.final_price_twd}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [q, setQ] = useState('Barbour Spey')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  async function doSearch(e) {
    e && e.preventDefault()
    setLoading(true)
    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q }),
      })
      const data = await res.json()
      setResults(data.results || [])
    } catch (err) {
      console.error(err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

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

        <div className="space-y-4">
          {results.length === 0 && !loading && <div className="text-gray-400">No results yet — try searching.</div>}
          {results.map((r, idx) => (
            <PriceCard key={idx} item={r} />
          ))}
        </div>
      </div>
    </div>
  )
}
