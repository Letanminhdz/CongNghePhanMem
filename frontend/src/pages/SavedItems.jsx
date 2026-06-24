import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookmarksService, MedicinesService, DiseasesService } from '../client';

const colorMap = {
  blue: 'bg-blue-50 text-blue-600',
  emerald: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  purple: 'bg-purple-50 text-purple-600',
  red: 'bg-red-50 text-red-600',
};

// Helper to assign randomish colors based on id/name
const getColorForId = (id) => {
  const colors = ['blue', 'emerald', 'amber', 'purple', 'red'];
  const num = typeof id === 'number' ? id : String(id).length;
  return colors[num % colors.length];
};

const SavedItems = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('medicines');
  const [savedMedicines, setSavedMedicines] = useState([]);
  const [savedDiseases, setSavedDiseases] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchBookmarks = async () => {
    try {
      setLoading(true);
      const data = await BookmarksService.getBookmarksApiV1BookmarksGet({ limit: 100 });
      const items = data.items || [];
      
      const medBookmarks = items.filter(i => i.item_type.toLowerCase() === 'medicine');
      const disBookmarks = items.filter(i => i.item_type.toLowerCase() === 'disease');

      // Fetch details for medicines
      const medDetails = await Promise.all(
        medBookmarks.map(async (bm) => {
          try {
            const detail = await MedicinesService.getMedicineDetailApiV1MedicinesNameDetailGet({ name: bm.item_neo4j_id });
            return {
              id: bm.item_neo4j_id,
              bookmarkId: bm.id,
              name: detail.name,
              type: detail.generic_name || 'Medicine',
              desc: detail.purpose || detail.indications || 'No description available',
              tags: detail.brand_name ? [detail.brand_name] : [],
              color: getColorForId(bm.item_neo4j_id)
            };
          } catch (e) {
            return {
              id: bm.item_neo4j_id,
              bookmarkId: bm.id,
              name: bm.item_neo4j_id,
              type: 'Medicine',
              desc: 'Could not load details',
              tags: [],
              color: 'blue'
            };
          }
        })
      );

      // Fetch details for diseases
      const disDetails = await Promise.all(
        disBookmarks.map(async (bm) => {
          try {
            const detail = await DiseasesService.getDiseaseDetailApiV1DiseasesDiseaseNameDetailGet({ diseaseName: bm.item_neo4j_id });
            return {
              id: bm.item_neo4j_id,
              bookmarkId: bm.id,
              name: detail.name,
              icon: 'lucide:activity',
              color: colorMap[getColorForId(bm.item_neo4j_id)],
              risk: 'Monitored',
              riskColor: 'bg-secondary text-secondary-foreground border-border',
              desc: detail.description || 'No description available',
              symptoms: detail.symptoms ? detail.symptoms.slice(0, 3) : [],
              category: 'Disease'
            };
          } catch (e) {
            return {
              id: bm.item_neo4j_id,
              bookmarkId: bm.id,
              name: bm.item_neo4j_id,
              icon: 'lucide:activity',
              color: 'bg-blue-50 text-blue-600',
              risk: 'Unknown',
              riskColor: 'bg-secondary text-secondary-foreground',
              desc: 'Could not load details',
              symptoms: [],
            };
          }
        })
      );

      setSavedMedicines(medDetails);
      setSavedDiseases(disDetails);
    } catch (err) {
      console.error('Failed to fetch bookmarks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookmarks();
  }, []);

  const handleRemoveBookmark = async (bookmarkId, e) => {
    e.stopPropagation();
    try {
      await BookmarksService.deleteBookmarkApiV1BookmarksIdDelete({ id: bookmarkId });
      // Refresh list
      fetchBookmarks();
    } catch (err) {
      console.error('Failed to remove bookmark', err);
    }
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground mb-2">Saved Items</h1>
        <p className="text-muted-foreground mb-8">Access your bookmarked medicines, diseases, and interactions quickly.</p>

        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('medicines')}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${activeTab === 'medicines' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'}`}
          >
            Medicines ({savedMedicines.length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-muted-foreground">Loading your bookmarks...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12">
          {activeTab === 'medicines' && savedMedicines.length === 0 && (
            <div className="col-span-full py-12 text-center">
              <p className="text-muted-foreground">No saved medicines yet.</p>
            </div>
          )}
          
          {activeTab === 'medicines' && savedMedicines.map((med) => (
            <div key={med.id} className="bg-card rounded-2xl border border-border p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col relative group">
              <button 
                onClick={(e) => handleRemoveBookmark(med.bookmarkId, e)}
                className="absolute top-4 right-4 transition-colors text-primary hover:text-muted-foreground"
                title="Remove Bookmark"
              >
                <iconify-icon icon="lucide:bookmark-minus" class="text-xl"></iconify-icon>
              </button>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorMap[med.color] || colorMap.blue}`}>
                  <iconify-icon icon="lucide:pill" class="text-2xl"></iconify-icon>
                </div>
                <div>
                  <h3 className="font-heading font-semibold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-1" title={med.name}>{med.name}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-1">{med.type}</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-4 flex-1">{med.desc}</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {med.tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 rounded bg-secondary text-[10px] font-medium text-foreground">{tag}</span>
                ))}
              </div>
              <button
                onClick={() => navigate(`/app/medicines/${encodeURIComponent(med.id)}`)}
                className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-secondary hover:text-primary transition-colors"
              >
                View Details
              </button>
            </div>
          ))}

          {activeTab === 'diseases' && savedDiseases.length === 0 && (
            <div className="col-span-full py-12 text-center">
              <p className="text-muted-foreground">No saved diseases yet.</p>
            </div>
          )}

          {activeTab === 'diseases' && savedDiseases.map((d) => (
            <div key={d.id} className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-md transition-shadow flex flex-col h-full relative group">
              <button 
                onClick={(e) => handleRemoveBookmark(d.bookmarkId, e)}
                className="absolute top-4 right-4 transition-colors text-primary hover:text-muted-foreground"
                title="Remove Bookmark"
              >
                <iconify-icon icon="lucide:bookmark-minus" class="text-xl"></iconify-icon>
              </button>
              <div className="flex justify-between items-start mb-4 pr-6">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${d.color}`}>
                  <iconify-icon icon={d.icon} class="text-xl"></iconify-icon>
                </div>
                <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${d.riskColor}`}>{d.risk}</span>
              </div>
              <h3 className="text-xl font-heading font-semibold text-foreground group-hover:text-primary transition-colors mb-2 line-clamp-1" title={d.name}>{d.name}</h3>
              <p className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">{d.desc}</p>
              <div className="flex flex-wrap gap-1.5 mb-6">
                {d.symptoms.map((s) => (
                  <span key={s} className="px-2 py-1 bg-secondary text-secondary-foreground text-[10px] font-medium rounded-md">{s}</span>
                ))}
              </div>
              <button
                onClick={() => navigate(`/app/diseases/${encodeURIComponent(d.id)}`)}
                className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-secondary hover:text-primary transition-colors mt-auto"
              >
                View Details
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default SavedItems;
