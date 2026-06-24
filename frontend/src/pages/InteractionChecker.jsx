import React, { useState, useEffect, useRef } from 'react';
import { InteractionsService, MedicinesService } from '../client';

const InteractionChecker = () => {
  const [drugs, setDrugs] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [checked, setChecked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const searchTimeoutRef = useRef(null);

  useEffect(() => {
    if (inputValue.trim() === '') {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await MedicinesService.searchMedicinesApiV1MedicinesSearchGet({ q: inputValue.trim(), limit: 5, skip: 0 });
        setSuggestions(res.items || []);
        setShowSuggestions(true);
      } catch (err) {
        console.error('Failed to fetch medicine suggestions', err);
      }
    }, 300);
  }, [inputValue]);

  const addDrug = (drugName) => {
    const name = typeof drugName === 'string' ? drugName : inputValue.trim();
    if (name && !drugs.includes(name)) {
      setDrugs([...drugs, name]);
      setInputValue('');
      setSuggestions([]);
      setShowSuggestions(false);
      setChecked(false);
    }
  };

  const removeDrug = (drug) => {
    setDrugs(drugs.filter((d) => d !== drug));
    setChecked(false);
  };

  const handleCheck = async () => {
    if (drugs.length >= 2) {
      setLoading(true);
      try {
        const response = await InteractionsService.analyzeDrugCombinationApiV1InteractionsAnalyzeCombinationPost({
          requestBody: {
            drug_names: drugs
          }
        });
        setResultData(response);
        setChecked(true);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-foreground mb-2">Check Drug Interactions</h1>
        <p className="text-muted-foreground text-sm">Add two or more drugs to your list to check for potential interactions, side effects, and safety recommendations.</p>
      </div>

      <div className="bg-card rounded-2xl border border-border p-6 shadow-sm mb-8">
        <label className="block text-sm font-medium text-foreground mb-3">Add Medications</label>

        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1">
            <iconify-icon icon="lucide:search" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"></iconify-icon>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addDrug()}
              onFocus={() => {
                if (suggestions.length > 0) setShowSuggestions(true);
              }}
              onBlur={() => {
                // Delay hiding so clicks on suggestions register
                setTimeout(() => setShowSuggestions(false), 200);
              }}
              placeholder="Search a medicine name (e.g. Aspirin)"
              className="w-full pl-10 pr-4 py-3 bg-secondary border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            />
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-card border border-border rounded-xl shadow-lg max-h-60 overflow-auto">
                {suggestions.map((med) => (
                  <button
                    key={med.name}
                    className="w-full text-left px-4 py-3 text-sm hover:bg-secondary transition-colors border-b border-border last:border-0 flex flex-col"
                    onMouseDown={() => addDrug(med.name)}
                  >
                    <span className="font-semibold text-foreground">{med.name}</span>
                    {med.generic_name && <span className="text-xs text-muted-foreground">{med.generic_name}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={() => addDrug()}
            disabled={!inputValue.trim()}
            className="bg-card text-foreground border border-border px-6 py-3 rounded-xl text-sm font-medium hover:bg-secondary transition-colors whitespace-nowrap shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add Drug
          </button>
        </div>

        <div className="flex flex-wrap gap-2 mb-6 min-h-[40px]">
          {drugs.map((drug) => (
            <div key={drug} className="flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-full text-sm font-medium border border-primary/20">
              <iconify-icon icon="lucide:pill" class="text-xs"></iconify-icon>
              {drug}
              <button onClick={() => removeDrug(drug)} className="hover:text-primary/70 ml-1">
                <iconify-icon icon="lucide:x"></iconify-icon>
              </button>
            </div>
          ))}
        </div>

        <button
          onClick={handleCheck}
          disabled={drugs.length < 2 || loading}
          className="w-full bg-primary text-primary-foreground py-3 rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <iconify-icon icon="lucide:shield-alert"></iconify-icon>
          {loading ? 'Checking...' : `Check Interactions ${drugs.length < 2 ? '(add at least 2 drugs)' : ''}`}
        </button>
      </div>

      {checked && resultData && drugs.length >= 2 && (
        <div className="space-y-6">
          <h3 className="font-heading font-semibold text-lg border-b border-border pb-2">Interaction Results</h3>

          <div className={`${resultData.is_safe ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} border rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4`}>
            <div className={`w-12 h-12 rounded-full ${resultData.is_safe ? 'bg-green-100 text-green-700' : 'bg-red-100 text-destructive'} flex items-center justify-center flex-shrink-0`}>
              <iconify-icon icon={resultData.is_safe ? "lucide:check-circle" : "lucide:alert-triangle"} class="text-2xl"></iconify-icon>
            </div>
            <div className="flex-1">
              <h4 className={`${resultData.is_safe ? 'text-green-700' : 'text-destructive'} font-bold text-lg`}>{resultData.is_safe ? 'No High Risk Identified' : 'High Risk Identified'}</h4>
              <p className={`text-sm ${resultData.is_safe ? 'text-green-900' : 'text-red-900'} mt-1`}>{resultData.summary}</p>
            </div>
            <button className={`px-4 py-2 bg-card border ${resultData.is_safe ? 'border-green-200 text-green-700 hover:bg-green-50' : 'border-red-200 text-red-700 hover:bg-red-50'} rounded-full text-sm font-medium transition-colors shadow-sm`}>
              Export Report
            </button>
          </div>

          {(resultData.interactions || []).map((result, i) => {
            const isMajor = result.severity === 'Major';
            const severityColor = isMajor ? 'bg-destructive text-primary-foreground' : 'bg-amber-500 text-white';
            const borderColor = isMajor ? 'border-red-200' : 'border-amber-200';
            const bgColor = isMajor ? 'bg-red-50/50 border-b-red-100' : 'bg-amber-50/50 border-b-amber-100';

            return (
              <div key={i} className={`bg-card rounded-2xl border shadow-sm overflow-hidden ${borderColor}`}>
                <div className={`px-6 py-4 border-b flex items-center justify-between ${bgColor}`}>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide ${severityColor}`}>{result.severity || 'Moderate'}</span>
                    <span className="font-semibold text-foreground">{result.drug_1} + {result.drug_2}</span>
                  </div>
                </div>
                <div className="p-6 space-y-4">
                  <div>
                    <h5 className="text-sm font-semibold text-foreground mb-1">What happens:</h5>
                    <p className="text-sm text-muted-foreground leading-relaxed">{result.description || 'Interaction detected.'}</p>
                  </div>
                </div>
              </div>
            );
          })}

          <div className="mt-8 text-center">
            <p className="text-xs text-muted-foreground max-w-2xl mx-auto">
              Disclaimer: This information is generalized and not intended as specific medical advice. Always consult your healthcare provider or pharmacist before changing your medication regimen.
            </p>
          </div>
        </div>
      )}
    </>
  );
};

export default InteractionChecker;
