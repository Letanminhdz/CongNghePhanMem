import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { DiseasesService, BookmarksService, SearchHistoryService } from '../client';

const diseases = [
  { id: 1, name: 'Hypertension', icon: 'lucide:heart-pulse', color: 'bg-blue-50 text-blue-600', risk: 'Moderate Risk', riskColor: 'bg-amber-100 text-amber-700 border-amber-200', desc: 'A condition in which the force of the blood against the artery walls is too high. Usually defined as blood pressure above 140/90.', symptoms: ['Headache', 'Shortness of breath'], category: 'Cardiovascular' },
  { id: 2, name: 'Asthma', icon: 'lucide:wind', color: 'bg-red-50 text-red-600', risk: 'High Risk', riskColor: 'bg-red-100 text-red-700 border-red-200', desc: 'A condition in which a person\'s airways become inflamed, narrow and swell, and produce extra mucus, which makes it difficult to breathe.', symptoms: ['Wheezing', 'Coughing'], category: 'Respiratory' },
  { id: 3, name: 'Common Cold', icon: 'lucide:thermometer', color: 'bg-green-50 text-green-600', risk: 'Low Risk', riskColor: 'bg-green-100 text-green-700 border-green-200', desc: 'A common viral infection of the nose and throat. In contrast to the flu, a common cold can be caused by many different types of viruses.', symptoms: ['Runny nose', 'Sore throat'], category: 'Infectious' },
  { id: 4, name: 'Migraine', icon: 'lucide:brain', color: 'bg-purple-50 text-purple-600', risk: 'Moderate Risk', riskColor: 'bg-amber-100 text-amber-700 border-amber-200', desc: 'A headache of varying intensity, often accompanied by nausea and sensitivity to light and sound.', symptoms: ['Throbbing pain', 'Aura'], category: 'Neurological' },
];

const categories = ['All Conditions', 'Cardiovascular', 'Respiratory', 'Neurological', 'Infectious'];

const DiseaseSearch = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 9;
  const searchTimeoutRef = useRef(null);

  const fetchDiseases = async (searchQuery = '') => {
    setLoading(true);
    try {
      const response = await DiseasesService.searchDiseasesApiV1DiseasesSearchGet({ q: searchQuery, limit: 100, skip: 0 });
      setResults(response.items || []);
      setCurrentPage(1);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiseases();
  }, []);

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
        const res = await DiseasesService.searchDiseasesApiV1DiseasesSearchGet({ q: query.trim(), limit: 5, skip: 0 });
        setSuggestions(res.items || []);
        setShowSuggestions(true);
      } catch (err) {
        console.error('Failed to fetch disease suggestions', err);
      }
    }, 300);
  }, [query]);

  const handleSearch = async (searchQuery = query) => {
    setQuery(searchQuery);
    setShowSuggestions(false);
    fetchDiseases(searchQuery);
    if (searchQuery.trim() !== '') {
      try {
        await SearchHistoryService.addSearchHistoryApiV1SearchHistoryPost({
          requestBody: { query_text: searchQuery.trim(), item_type: 'disease' }
        });
      } catch (err) {
        console.error('Failed to save search history', err);
      }
    }
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground mb-2">Disease Lookup</h1>
        <p className="text-muted-foreground mb-8">Search for medical conditions, symptoms, and treatment guidelines.</p>

        <div className="bg-card p-4 rounded-2xl shadow-sm border border-border flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full z-20">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted-foreground">
              <iconify-icon icon="lucide:search" class="text-xl"></iconify-icon>
            </div>
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
              className="w-full pl-12 pr-4 py-3.5 bg-background border border-input rounded-full text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow text-base"
              placeholder="Search by disease name or symptoms..."
            />
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-30 w-full mt-2 bg-card border border-border rounded-xl shadow-lg max-h-60 overflow-auto">
                {suggestions.map((dis) => (
                  <button
                    key={dis.name}
                    className="w-full text-left px-5 py-3 text-sm hover:bg-secondary transition-colors border-b border-border last:border-0 flex flex-col"
                    onMouseDown={() => handleSearch(dis.name)}
                  >
                    <span className="font-semibold text-foreground">{dis.name}</span>
                    {dis.category && <span className="text-xs text-muted-foreground mt-0.5">{dis.category}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-2 w-full md:w-auto">
            <button onClick={handleSearch} disabled={loading} className="flex-shrink-0 px-6 py-3 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors flex items-center disabled:opacity-50">
              <iconify-icon icon="lucide:search" class="mr-2"></iconify-icon>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12 mt-8">
        {results.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE).map((d, idx) => (
          <div key={d.name || idx} className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-md transition-shadow flex flex-col h-full relative group">
            <div className="flex justify-between items-start mb-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-blue-50 text-blue-600`}>
                <iconify-icon icon="lucide:activity" class="text-xl"></iconify-icon>
              </div>
              <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border bg-amber-100 text-amber-700 border-amber-200`}>{d.category || 'Condition'}</span>
            </div>
            <h3 className="text-xl font-heading font-semibold text-foreground group-hover:text-primary transition-colors mb-2">{d.name}</h3>
            <p className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">{d.description || 'No description available.'}</p>
            <div className="flex flex-wrap gap-1.5 mb-6">
               <span className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded-md">API Data</span>
            </div>
            <button
              onClick={() => navigate(localStorage.getItem('access_token') ? `/app/diseases/${encodeURIComponent(d.name)}` : `/diseases/${encodeURIComponent(d.name)}`)}
              className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-secondary hover:text-primary transition-colors mt-auto"
            >
              View Details
            </button>
          </div>
        ))}
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

export default DiseaseSearch;
