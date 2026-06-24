import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { MedicinesService, BookmarksService } from '../client';
import { useUser } from '../context/UserContext';

const MedicineDetail = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const { id } = useParams();
  const [medicine, setMedicine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isSaved, setIsSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const checkBookmark = async () => {
      if (!user) return;
      try {
        const bookmarks = await BookmarksService.getBookmarksApiV1BookmarksGet({ limit: 100, skip: 0 });
        if (bookmarks.items.some(b => b.item_type === 'medicine' && b.item_neo4j_id === id)) {
          setIsSaved(true);
        }
      } catch (err) {
        console.error('Failed to check bookmarks', err);
      }
    };
    
    const fetchMedicine = async () => {
      try {
        const data = await MedicinesService.getMedicineDetailApiV1MedicinesNameDetailGet({ name: id });
        setMedicine(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMedicine();
    checkBookmark();
  }, [id]);

  const handleToggleSave = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    setIsSaving(true);
    try {
      if (isSaved) {
        const bookmarks = await BookmarksService.getBookmarksApiV1BookmarksGet({ limit: 100, skip: 0 });
        const target = bookmarks.items.find(b => b.item_type === 'medicine' && b.item_neo4j_id === id);
        if (target) {
          await BookmarksService.deleteBookmarkApiV1BookmarksIdDelete({ id: target.id });
          setIsSaved(false);
        }
      } else {
        await BookmarksService.createBookmarkApiV1BookmarksPost({
          requestBody: { item_type: 'medicine', item_neo4j_id: id }
        });
        setIsSaved(true);
      }
    } catch (err) {
      console.error('Failed to toggle bookmark', err);
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading...</div>;
  }

  if (!medicine) {
    return <div className="p-8 text-center text-muted-foreground">Medicine not found.</div>;
  }

  return (
    <>
      {/* Breadcrumbs & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
        <nav className="flex text-sm text-muted-foreground font-medium items-center gap-1">
          <button onClick={() => navigate(user ? '/app/medicines' : '/medicines')} className="hover:text-foreground transition-colors">Medicines</button>
          <span className="mx-1">/</span>
          <span className="text-foreground">{medicine.name}</span>
        </nav>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleToggleSave}
            disabled={isSaving}
            className={`px-4 py-2 border rounded-full text-sm font-medium transition-colors flex items-center ${isSaved ? 'bg-primary/10 border-primary/20 text-primary' : 'bg-card border-border hover:bg-secondary text-foreground'}`}
          >
            <iconify-icon icon={isSaved ? "lucide:bookmark-check" : "lucide:bookmark"} class="mr-2"></iconify-icon>
            {isSaved ? 'Saved' : 'Save'}
          </button>
          <button onClick={() => navigate(user ? '/app/chat' : '/chat', { state: { q: `Tell me detailed information about the medicine ${medicine.name}` } })} className="px-5 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full text-sm font-medium transition-colors flex items-center shadow-sm">
            <iconify-icon icon="lucide:sparkles" class="mr-2"></iconify-icon>
            Ask AI about this
          </button>
        </div>
      </div>

      {/* Header Profile */}
      <div className="bg-card rounded-2xl p-6 lg:p-8 border border-border shadow-sm mb-6 flex flex-col md:flex-row gap-8 items-start">
        <div className="w-full md:w-48 h-48 rounded-xl bg-secondary overflow-hidden flex-shrink-0 border border-border">
          <img src="https://uxmagic.blob.core.windows.net/public/agent-images/med-image-1-1779613274512-hgdx7kpm0oo.png" alt="Medicine Box" className="w-full h-full object-cover" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-heading font-bold text-foreground">{medicine.name}</h1>
            <span className="px-2.5 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full border border-green-200">API Data</span>
          </div>
          <p className="text-lg text-muted-foreground mb-4 font-medium">{medicine.brand_name || medicine.generic_name}</p>
          <p className="text-foreground leading-relaxed mb-6">
            {medicine.purpose || medicine.indications || 'No detailed description available.'}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: 'Generic', value: medicine.generic_name || 'N/A' },
              { label: 'Manufacturer', value: medicine.manufacturer || 'N/A' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-secondary/50 rounded-xl p-3">
                <p className="text-xs text-muted-foreground font-medium mb-1 uppercase tracking-wider">{label}</p>
                <p className="font-medium text-sm text-foreground">{value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Ingredients & Dosage */}
          <div className="bg-card rounded-2xl p-6 border border-border shadow-sm">
            <h2 className="text-lg font-heading font-semibold text-foreground mb-4 flex items-center">
              <iconify-icon icon="lucide:flask-conical" class="mr-2 text-primary"></iconify-icon>
              Active Ingredients & Dosage
            </h2>
            <div className="mb-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Active Ingredient</h3>
              <p className="text-foreground">{medicine.generic_name || 'Unknown'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Standard Dosage</h3>
              <div className="bg-secondary/30 rounded-xl p-4 border border-border">
                <p className="text-sm text-foreground leading-relaxed">{medicine.dosage || 'Please consult a doctor for dosage information.'}</p>
                <p className="mt-3 text-xs text-amber-600 bg-amber-50 p-2 rounded-lg border border-amber-100 flex items-start gap-1">
                  <iconify-icon icon="lucide:info" class="mt-0.5 flex-shrink-0"></iconify-icon>
                  Always complete the full course as prescribed, even if symptoms improve.
                </p>
              </div>
            </div>
          </div>

          {/* Side Effects */}
          <div className="bg-card rounded-2xl p-6 border border-border shadow-sm">
            <h2 className="text-lg font-heading font-semibold text-foreground mb-4 flex items-center">
              <iconify-icon icon="lucide:activity" class="mr-2 text-primary"></iconify-icon>
              Side Effects & Adverse Reactions
            </h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Side Effects</h3>
                <p className="text-sm text-foreground leading-relaxed">{medicine.side_effects || 'None listed.'}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-red-600 mb-3">Adverse Reactions</h3>
                <p className="text-sm text-foreground leading-relaxed">{medicine.adverse_reactions || 'None listed.'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Interactions Warning */}
          <div className="bg-amber-50 rounded-2xl p-6 border border-amber-200 shadow-sm">
            <h2 className="text-lg font-heading font-semibold text-amber-900 mb-3 flex items-center">
              <iconify-icon icon="lucide:triangle-alert" class="mr-2 text-amber-600"></iconify-icon>
              Drug Interactions
            </h2>
            <p className="text-sm text-amber-800 mb-4 leading-relaxed">
              This medicine has known interactions with <strong>{(medicine.interactions || []).filter(i => i && i.name).length}</strong> other drugs.
            </p>
            <div className="space-y-3 mb-4">
              {(medicine.interactions || []).filter(i => i && i.name).slice(0, 3).map((interaction, i) => (
                <div key={i} className="bg-white/60 p-3 rounded-xl border border-amber-100">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-foreground">{interaction.name || 'Unknown Drug'}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${interaction.severity === 'Major' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{interaction.severity || 'Moderate'}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{interaction.description}</p>
                </div>
              ))}
            </div>
            <button onClick={() => navigate(user ? '/app/interactions' : '/login')} className="w-full py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-full text-sm font-medium transition-colors">
              Check all interactions
            </button>
          </div>

          {/* Contraindications */}
          <div className="bg-card rounded-2xl p-6 border border-border shadow-sm">
            <h2 className="text-lg font-heading font-semibold text-foreground mb-4">Contraindications</h2>
            <p className="text-sm text-foreground mb-3 leading-relaxed">Do not use this medicine if you have:</p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {medicine.contraindications || 'None listed.'}
            </p>
          </div>
          <div className="bg-card rounded-2xl p-6 border border-border shadow-sm mt-6">
            <h2 className="text-lg font-heading font-semibold text-foreground mb-4">Warnings</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {medicine.warnings || 'None listed.'}
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default MedicineDetail;
