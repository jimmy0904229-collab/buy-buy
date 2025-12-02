import React, { useState, useMemo, useEffect } from 'react'

function PriceCard({ item, shippingCost, applyTax, taxThreshold, taxRate }) {
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
        {item.discount_text && (
          <div className="absolute top-2 left-2 z-10">
            <span className="bg-red-600 text-red-50 text-xs font-semibold px-2 py-1 rounded">{item.discount_text}</span>
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
            <div className="text-sm text-gray-400">Your Final</div>
            <div className="text-xl font-extrabold text-emerald-400">
              NT$ {
                (() => {
                  const base = Number(item.price_twd || 0)
                  const ship = Number(shippingCost || 0)
                  const tax = (applyTax && base >= Number(taxThreshold || 0)) ? Math.round((base + ship) * (taxRate || 0.17)) : 0
                  return base + ship + tax
                })()
              }
            </div>
            <div className="text-xs text-gray-400">Shipping: NT$ {Number(shippingCost || 0)}{applyTax? ` · Tax ${Math.round((taxRate||0.17)*100)}%` : ''}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [q, setQ] = useState('Barbour Spey')
  const [results, setResults] = useState([])
  const [sortOption, setSortOption] = useState(() => localStorage.getItem('sortOption') || 'recommended')
  const [storeFilter, setStoreFilter] = useState(() => localStorage.getItem('storeFilter') || 'All Stores')
  const [shippingCost, setShippingCost] = useState(() => Number(localStorage.getItem('shippingCost') || 800))
  const [applyTax, setApplyTax] = useState(() => (localStorage.getItem('applyTax') || 'true') === 'true')
  const [taxThreshold, setTaxThreshold] = useState(() => Number(localStorage.getItem('taxThreshold') || 0))
  const TAX_RATE = 0.17
  const [originCountry, setOriginCountry] = useState(() => localStorage.getItem('originCountry') || 'US')
  const [weightLbs, setWeightLbs] = useState(() => Number(localStorage.getItem('weightLbs') || 1))

  // Estimated per-lb rates in TWD (reference: BuyandShip pricing page). These are estimates
  // to help quick calculations; users should consult the official page for exact fees.
  const ORIGIN_RATES = {
    US: 150,
    GB: 200,
    JP: 100,
    HK: 60,
    AU: 220,
    EU: 210,
  }
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

  // persist settings to localStorage when they change
  useEffect(() => {
    try {
      localStorage.setItem('sortOption', sortOption)
      localStorage.setItem('storeFilter', storeFilter)
      localStorage.setItem('shippingCost', String(shippingCost))
      localStorage.setItem('applyTax', String(applyTax))
      localStorage.setItem('taxThreshold', String(taxThreshold))
      localStorage.setItem('originCountry', originCountry)
      localStorage.setItem('weightLbs', String(weightLbs))
    } catch (e) {
      // ignore storage errors (e.g., private mode)
    }
  }, [sortOption, storeFilter, shippingCost, applyTax, taxThreshold, originCountry, weightLbs])

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

        {/* Control bar: sort + store filter + shipping/tax controls */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
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
          <div className="mt-3 md:mt-0 flex items-center gap-2">
            <a className="text-sm text-emerald-300 underline" href="https://www.buyandship.com.tw/" target="_blank" rel="noreferrer">運費參考 BuyandShip</a>
            <label className="text-sm text-gray-300 ml-4 mr-2">Origin</label>
            <select value={originCountry} onChange={e => { setOriginCountry(e.target.value); const rate = ORIGIN_RATES[e.target.value] || 0; setShippingCost(Math.round((weightLbs||0) * rate)); }} className="p-2 bg-gray-800 border border-gray-700 rounded">
              <option value="US">United States</option>
              <option value="GB">United Kingdom</option>
              <option value="JP">Japan</option>
              <option value="HK">Hong Kong</option>
              <option value="AU">Australia</option>
              <option value="EU">Europe</option>
            </select>

            <label className="text-sm text-gray-300 ml-4 mr-2">Weight (lbs)</label>
            <input type="number" min="0" step="0.1" value={weightLbs} onChange={e => { const v = Number(e.target.value); setWeightLbs(v); const rate = ORIGIN_RATES[originCountry] || 0; setShippingCost(Math.round(v * rate)); }} className="w-20 p-2 bg-gray-800 border border-gray-700 rounded text-gray-100" />

            <label className="text-sm text-gray-300 ml-4 mr-2">Shipping NT$</label>
            <input type="number" value={shippingCost} onChange={e => setShippingCost(Number(e.target.value))} className="w-24 p-2 bg-gray-800 border border-gray-700 rounded text-gray-100" />
            <label className="text-sm text-gray-300 ml-4 mr-2">Apply Tax</label>
            <input type="checkbox" checked={applyTax} onChange={e => setApplyTax(e.target.checked)} className="align-middle" />
            <label className="text-sm text-gray-300 ml-4 mr-2">Tax Threshold NT$</label>
            <input type="number" value={taxThreshold} onChange={e => setTaxThreshold(Number(e.target.value))} className="w-24 p-2 bg-gray-800 border border-gray-700 rounded text-gray-100" />
          </div>
        </div>

        <div>
          {error && <div className="text-red-400 mb-4">{error}</div>}
          {results.length === 0 && !loading && !error && <div className="text-gray-400 mb-4">No results yet — try searching.</div>}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {displayedList.map((r, idx) => (
              r.url ? (
                <a key={idx} href={r.url} target="_blank" rel="noreferrer" className="block">
                  <PriceCard item={r} shippingCost={shippingCost} applyTax={applyTax} taxThreshold={taxThreshold} taxRate={TAX_RATE} />
                </a>
              ) : (
                <div key={idx}>
                  <PriceCard item={r} shippingCost={shippingCost} applyTax={applyTax} taxThreshold={taxThreshold} taxRate={TAX_RATE} />
                </div>
              )
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
