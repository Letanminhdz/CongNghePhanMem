import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MedicinesService, BookmarksService, SearchHistoryService } from '../client';
import { useUser } from '../context/UserContext';

const colorMap = {
  blue: 'bg-blue-50 text-blue-600',
  emerald: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  purple: 'bg-purple-50 text-purple-600',
  red: 'bg-red-50 text-red-600',
};

const MedicineSearch = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [query, setQuery] = useState('');
  const [savedMap, setSavedMap] = useState({});
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 9;
  const searchTimeoutRef = useRef(null);

  const fetchMedicines = async (searchQuery = '') => {
    setLoading(true);
    try {
      const response = await MedicinesService.searchMedicinesApiV1MedicinesSearchGet({ q: searchQuery, limit: 100, skip: 0 });
      setResults(response.items || []);
      setCurrentPage(1);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchBookmarks = async () => {
    if (!user) return;
    try {
      const data = await BookmarksService.getBookmarksApiV1BookmarksGet({ limit: 100, skip: 0 });
      const map = {};
      data.items.forEach(b => {
        if (b.item_type.toLowerCase() === 'medicine') {
          map[b.item_neo4j_id] = b.id;
        }
      });
      setSavedMap(map);
    } catch (err) {
      console.error('Failed to fetch bookmarks', err);
    }
  };

  useEffect(() => {
    fetchMedicines();
    if (user) {
      fetchBookmarks();
    }
  }, [user]);

  useEffect(() => {
    if (query.trim() === '') {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await MedicinesService.searchMedicinesApiV1MedicinesSearchGet({ q: query.trim(), limit: 5, skip: 0 });
        setSuggestions(res.items || []);
        setShowSuggestions(true);
      } catch (err) {
        console.error('Failed to fetch medicine suggestions', err);
      }
    }, 300);
  }, [query]);

  const handleSearch = async (searchQuery = query) => {
    setQuery(searchQuery);
    setShowSuggestions(false);
    fetchMedicines(searchQuery);
    if (user && searchQuery.trim() !== '') {
      try {
        await SearchHistoryService.addSearchHistoryApiV1SearchHistoryPost({
          requestBody: { query_text: searchQuery.trim(), item_type: 'medicine' }
        });
      } catch (err) {
        console.error('Failed to save search history', err);
      }
    }
  };

  const toggleSave = async (id) => {
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      if (savedMap[id]) {
        await BookmarksService.deleteBookmarkApiV1BookmarksIdDelete({ id: savedMap[id] });
        setSavedMap(prev => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      } else {
        const res = await BookmarksService.createBookmarkApiV1BookmarksPost({
          requestBody: { item_type: 'medicine', item_neo4j_id: id }
        });
        setSavedMap(prev => ({ ...prev, [id]: res.id }));
      }
    } catch (err) {
      console.error('Failed to toggle bookmark', err);
    }
  };

  return (
    <>
      <div className="mb-8 space-y-4">
        <div className="relative w-full shadow-sm z-20">
          <iconify-icon icon="lucide:search" class="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground text-xl"></iconify-icon>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            onFocus={() => {
              if (suggestions.length > 0) setShowSuggestions(true);
            }}
            onBlur={() => {
              setTimeout(() => setShowSuggestions(false), 200);
            }}
            placeholder="Search by medicine name, active ingredient, or condition..."
            className="w-full pl-12 pr-28 py-4 bg-card border border-border rounded-2xl text-base focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-30 w-full mt-2 bg-card border border-border rounded-xl shadow-lg max-h-60 overflow-auto">
              {suggestions.map((med) => (
                <button
                  key={med.name}
                  className="w-full text-left px-5 py-3 text-sm hover:bg-secondary transition-colors border-b border-border last:border-0 flex flex-col"
                  onMouseDown={() => handleSearch(med.name)}
                >
                  <span className="font-semibold text-foreground">{med.name}</span>
                  {med.generic_name && <span className="text-xs text-muted-foreground mt-0.5">{med.generic_name}</span>}
                </button>
              ))}
            </div>
          )}
          <button onClick={() => handleSearch()} disabled={loading} className="absolute right-3 top-1/2 -translate-y-1/2 bg-primary text-primary-foreground px-4 py-2 rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors z-10">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12">
        {results.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE).map((med, idx) => {
          const id = med.name || idx.toString();
          const colorKey = Object.keys(colorMap)[idx % Object.keys(colorMap).length];
          return (
            <div key={id} className="bg-card rounded-2xl border border-border p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col relative group">
              <button
                onClick={() => toggleSave(id)}
                className={`absolute top-4 right-4 transition-colors ${savedMap[id] ? 'text-primary' : 'text-muted-foreground hover:text-primary'}`}
              >
                <iconify-icon icon={savedMap[id] ? "lucide:bookmark-check" : "lucide:bookmark"} class="text-xl"></iconify-icon>
              </button>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorMap[colorKey]}`}>
                  <iconify-icon icon="lucide:pill" class="text-2xl"></iconify-icon>
                </div>
                <div>
                  <h3 className="font-heading font-semibold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-1">{med.name}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-1">{med.generic_name || 'Medicine'}</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-4 flex-1">{med.dosage || 'No dosage information available.'}</p>
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-1 rounded bg-secondary text-[10px] font-medium text-foreground">API Data</span>
              </div>
              <button
                onClick={() => navigate(user ? `/app/medicines/${encodeURIComponent(med.name)}` : `/medicines/${encodeURIComponent(med.name)}`)}
                className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-secondary hover:text-primary transition-colors mt-auto"
              >
                View Details
              </button>
            </div>
          )
        })}
      </div>

      {results.length > ITEMS_PER_PAGE && (
        <div className="flex items-center justify-center gap-2 mt-auto pb-8">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="w-10 h-10 rounded-full border border-border flex items-center justify-center text-muted-foreground hover:bg-secondary transition-colors disabled:opacity-50"
          >
            <iconify-icon icon="lucide:chevron-left"></iconify-icon>
          </button>

          {Array.from({ length: Math.ceil(results.length / ITEMS_PER_PAGE) }).map((_, i) => (
            <button
              key={i + 1}
              onClick={() => setCurrentPage(i + 1)}
              className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${currentPage === i + 1 ? 'bg-primary text-primary-foreground shadow-sm' : 'border border-border text-foreground hover:bg-secondary transition-colors'}`}
            >
              {i + 1}
            </button>
          ))}

          <button
            onClick={() => setCurrentPage(prev => Math.min(Math.ceil(results.length / ITEMS_PER_PAGE), prev + 1))}
            disabled={currentPage === Math.ceil(results.length / ITEMS_PER_PAGE)}
            className="w-10 h-10 rounded-full border border-border flex items-center justify-center text-muted-foreground hover:bg-secondary transition-colors disabled:opacity-50"
          >
            <iconify-icon icon="lucide:chevron-right"></iconify-icon>
          </button>
        </div>
      )}
    </>
  );
};

export default MedicineSearch;
