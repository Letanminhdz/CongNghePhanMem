import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MedicinesService, DiseasesService } from '../client';
import { useUser } from '../context/UserContext';

const colorMap = {
  blue: 'bg-blue-50 text-blue-600',
  emerald: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  purple: 'bg-purple-50 text-purple-600',
  red: 'bg-red-50 text-red-600',
};

const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchTimeoutRef = useRef(null);

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
        const [medRes, disRes] = await Promise.all([
          MedicinesService.searchMedicinesApiV1MedicinesSearchGet({ q: query.trim(), limit: 3, skip: 0 }).catch(() => ({items: []})),
          DiseasesService.searchDiseasesApiV1DiseasesSearchGet({ q: query.trim(), limit: 3, skip: 0 }).catch(() => ({items: []}))
        ]);
        const meds = (medRes.items || []).map(m => ({ ...m, type: 'medicine' }));
        const diseases = (disRes.items || []).map(d => ({ ...d, type: 'disease' }));
        setSuggestions([...meds, ...diseases]);
        setShowSuggestions(true);
      } catch (err) {
        console.error('Failed to fetch suggestions', err);
      }
    }, 300);
  }, [query]);

  const handleSearch = async (searchQuery = query) => {
    setQuery(searchQuery);
    setShowSuggestions(false);
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const [medRes, disRes] = await Promise.all([
        MedicinesService.searchMedicinesApiV1MedicinesSearchGet({ q: searchQuery.trim(), limit: 6, skip: 0 }).catch(() => ({items: []})),
        DiseasesService.searchDiseasesApiV1DiseasesSearchGet({ q: searchQuery.trim(), limit: 6, skip: 0 }).catch(() => ({items: []}))
      ]);
      const meds = (medRes.items || []).map(m => ({ ...m, type: 'medicine' }));
      const diseases = (disRes.items || []).map(d => ({ ...d, type: 'disease' }));
      setSearchResults([...meds, ...diseases]);
      // Scroll to search results
      setTimeout(() => {
        document.getElementById('search-results')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error(err);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const openDetails = (name, type = 'medicine') => {
    const prefix = user ? '/app' : '';
    if (type === 'disease') {
      navigate(`${prefix}/diseases/${encodeURIComponent(name)}`);
    } else {
      navigate(`${prefix}/medicines/${encodeURIComponent(name)}`);
    }
  };

  return (
    <>
      <main className="flex-1 flex flex-col">
        <section className="relative w-full py-20 lg:py-32 overflow-hidden">
          <div className="absolute inset-0 z-0">
            <img src="https://uxmagic.blob.core.windows.net/public/agent-images/hero-med-1779611524787-d5of8fj4cs6.png"
              alt="Medical AI Background" className="w-full h-full object-cover opacity-20 object-center" />
            <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background/80 to-background"></div>
          </div>

          <div className="relative z-10 max-w-7xl mx-auto px-6 flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8">
              <iconify-icon icon="lucide:sparkles" class="text-base"></iconify-icon>
              <span>Powered by Advanced Medical AI</span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-heading font-bold text-foreground max-w-4xl leading-tight tracking-tight mb-6">
              Your Intelligent Companion for <span class="text-primary">Medical Insights</span>
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 leading-relaxed">
              Instantly check drug interactions, explore comprehensive medicine details, and consult our AI assistant for
              safe, reliable healthcare information.
            </p>

            {/* Medicine Search Box directly on Landing Page */}
            <div className="w-full max-w-xl mx-auto mb-8 relative">
              <div className="relative shadow-md rounded-2xl z-20">
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
                  placeholder="Search medicine name or generic name..."
                  className="w-full pl-12 pr-28 py-4 bg-card border border-border rounded-2xl text-base focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-foreground text-left"
                />
                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute z-30 w-full mt-2 bg-card border border-border rounded-xl shadow-lg max-h-60 overflow-auto text-left">
                    {suggestions.map((item) => (
                      <button
                        key={item.name + item.type}
                        className="w-full text-left px-5 py-3 text-sm hover:bg-secondary transition-colors border-b border-border last:border-0 flex items-center justify-between"
                        onMouseDown={() => handleSearch(item.name)}
                      >
                        <div className="flex flex-col">
                          <span className="font-semibold text-foreground">{item.name}</span>
                          {item.generic_name && <span className="text-xs text-muted-foreground mt-0.5">{item.generic_name}</span>}
                        </div>
                        <span className="text-xs font-medium px-2 py-1 bg-secondary rounded-md text-muted-foreground capitalize">{item.type}</span>
                      </button>
                    ))}
                  </div>
                )}
                <button 
                  onClick={() => handleSearch()} 
                  disabled={loading} 
                  className="absolute right-3 top-1/2 -translate-y-1/2 bg-primary text-primary-foreground px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors z-10"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-4 w-full max-w-md mx-auto justify-center">
              <button
                className="w-full sm:w-auto flex-1 bg-primary text-primary-foreground px-8 py-3.5 rounded-full font-medium text-base hover:bg-primary/90 transition-all shadow-md flex items-center justify-center gap-2"
                onClick={() => navigate('/chat')}
              >
                <iconify-icon icon="lucide:message-circle"></iconify-icon>
                Chat with AI
              </button>
            </div>
          </div>
        </section>

        {/* Search Results Section */}
        {searchResults.length > 0 && (
          <section id="search-results" className="py-16 bg-background relative z-10 border-t border-border">
            <div className="max-w-7xl mx-auto px-6">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-heading font-semibold text-foreground">Search Results ({searchResults.length})</h2>
                <button 
                  onClick={() => {
                    setSearchResults([]);
                    setQuery('');
                  }} 
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  Clear Results
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {searchResults.map((item, idx) => {
                  const colorKey = Object.keys(colorMap)[idx % Object.keys(colorMap).length];
                  return (
                    <div key={item.name + item.type} className="bg-card rounded-2xl border border-border p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col relative group">
                      <div className="flex items-center gap-3 mb-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorMap[colorKey]}`}>
                          <iconify-icon icon={item.type === 'disease' ? "lucide:activity" : "lucide:pill"} class="text-2xl"></iconify-icon>
                        </div>
                        <div className="text-left">
                          <h3 className="font-heading font-semibold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-1">{item.name}</h3>
                          <p className="text-xs text-muted-foreground line-clamp-1 capitalize">{item.type}</p>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-4 flex-1 text-left">{item.description || item.dosage || 'No description available.'}</p>
                      <button
                        onClick={() => openDetails(item.name, item.type)}
                        className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-secondary hover:text-primary transition-colors mt-auto"
                      >
                        View Details
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        <section className="py-16 bg-background relative z-10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-heading font-semibold text-foreground mb-4">Comprehensive Healthcare Tools</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">Everything you need to make informed decisions about your
                medications and health conditions.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-card rounded-2xl p-8 shadow-sm border border-border/50 hover:shadow-md transition-all flex flex-col items-start group">
                <div className="w-14 h-14 rounded-full bg-blue-50 text-primary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <iconify-icon icon="lucide:bot" class="text-3xl"></iconify-icon>
                </div>
                <h3 className="text-xl font-semibold mb-3">AI Consultation</h3>
                <p className="text-muted-foreground text-sm leading-relaxed mb-6 flex-1">
                  Have a natural conversation about symptoms, treatments, and general medical inquiries with our trained
                  AI model.
                </p>
                <button onClick={() => navigate('/chat')} className="text-primary font-medium text-sm flex items-center gap-1 hover:gap-2 transition-all">
                  Try AI Chat <iconify-icon icon="lucide:arrow-right"></iconify-icon>
                </button>
              </div>

              <div className="bg-card rounded-2xl p-8 shadow-sm border border-border/50 hover:shadow-md transition-all flex flex-col items-start group">
                <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <iconify-icon icon="lucide:pill" class="text-3xl"></iconify-icon>
                </div>
                <h3 className="text-xl font-semibold mb-3">Medicine Lookup</h3>
                <p className="text-muted-foreground text-sm leading-relaxed mb-6 flex-1">
                  Search a vast database of medications to find dosages, side effects, and detailed descriptions
                  instantly.
                </p>
                <button 
                  onClick={() => {
                    document.querySelector('input[placeholder*="Search medicine"]')?.focus();
                  }} 
                  className="text-emerald-600 font-medium text-sm flex items-center gap-1 hover:gap-2 transition-all"
                >
                  Search Database <iconify-icon icon="lucide:arrow-right"></iconify-icon>
                </button>
              </div>

              <div className="bg-card rounded-2xl p-8 shadow-sm border border-border/50 hover:shadow-md transition-all flex flex-col items-start group">
                <div className="w-14 h-14 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <iconify-icon icon="lucide:activity" class="text-3xl"></iconify-icon>
                </div>
                <h3 className="text-xl font-semibold mb-3">Disease Lookup</h3>
                <p className="text-muted-foreground text-sm leading-relaxed mb-6 flex-1">
                  Search for medical conditions, symptoms, and treatment guidelines to stay informed about your health.
                </p>
                <button onClick={() => navigate('/diseases')} className="text-amber-600 font-medium text-sm flex items-center gap-1 hover:gap-2 transition-all">
                  Browse Diseases <iconify-icon icon="lucide:arrow-right"></iconify-icon>
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 bg-card border-y border-border">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest mb-8">Trusted by Healthcare
              Professionals</p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-60 grayscale">
              <div className="flex items-center gap-2 font-heading font-bold text-xl"><iconify-icon
                  icon="lucide:cross"></iconify-icon> MedTech</div>
              <div className="flex items-center gap-2 font-heading font-bold text-xl"><iconify-icon
                  icon="lucide:heart-pulse"></iconify-icon> HealthCare+</div>
              <div className="flex items-center gap-2 font-heading font-bold text-xl"><iconify-icon
                  icon="lucide:microscope"></iconify-icon> BioPharma</div>
              <div className="flex items-center gap-2 font-heading font-bold text-xl"><iconify-icon
                  icon="lucide:stethoscope"></iconify-icon> ClinicOS</div>
            </div>
          </div>
        </section>
      </main>
    </>
  );
};

export default LandingPage;
