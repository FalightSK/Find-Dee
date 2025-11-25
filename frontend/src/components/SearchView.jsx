import { useState } from 'react'
import { Search, FileText, X } from 'lucide-react'

const FILTERS = ['All', 'PDF', 'Images', 'Urgent']

export default function SearchView() {
    const [query, setQuery] = useState('')
    const [activeFilter, setActiveFilter] = useState('All')
    const [results, setResults] = useState([])

    const handleSearch = (e) => {
        e.preventDefault()
        if (query) {
            setResults([
                { id: 1, name: `Result for "${query}" 1.pdf`, type: 'pdf', tag: 'Finance' },
                { id: 2, name: `Result for "${query}" 2.jpg`, type: 'image', tag: 'Meeting' },
            ])
        }
    }

    return (
        <div className="space-y-6 pt-2">
            {/* Search Bar */}
            <div className="relative">
                <form onSubmit={handleSearch}>
                    <input
                        type="text"
                        placeholder="Search documents..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 bg-gray-100 rounded-xl text-gray-700 placeholder-gray-400 focus:ring-2 focus:ring-line-green focus:outline-none transition-all"
                    />
                    <Search className="absolute left-4 top-3.5 text-gray-400" size={20} />
                </form>
            </div>

            {/* Filters */}
            <div className="flex space-x-2 overflow-x-auto pb-2 scrollbar-hide">
                {FILTERS.map((filter) => (
                    <button
                        key={filter}
                        onClick={() => setActiveFilter(filter)}
                        className={`px-4 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${activeFilter === filter
                                ? 'bg-line-green text-white'
                                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            }`}
                    >
                        {filter}
                    </button>
                ))}
            </div>

            {/* Results */}
            <div>
                {results.length > 0 ? (
                    <div className="space-y-3">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">Results</h3>
                        {results.map((file) => (
                            <div key={file.id} className="bg-white p-3 rounded-xl border border-gray-100 flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <div className="bg-gray-50 p-2 rounded-lg text-gray-500">
                                        <FileText size={18} />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-gray-900 text-sm">{file.name}</h4>
                                        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded mt-1 inline-block">
                                            {file.tag}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-3">
                            <Search size={24} className="text-gray-300" />
                        </div>
                        <p className="text-gray-400 text-sm">
                            Search for your files
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
