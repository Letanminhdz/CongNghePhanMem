import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { SearchHistoryService, ChatService, InteractionsService } from '../client';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [searchHistory, setSearchHistory] = useState([]);
  const [totalSearches, setTotalSearches] = useState(0);
  const [totalChats, setTotalChats] = useState(0);
  const [totalInteractions, setTotalInteractions] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const searchData = await SearchHistoryService.getSearchHistoryApiV1SearchHistoryGet({ limit: 10, skip: 0 });
        setSearchHistory(searchData?.items || searchData || []);
        setTotalSearches(searchData?.total || 0);

        const chatData = await ChatService.getChatHistoryApiV1ChatHistoryGet({ limit: 1, skip: 0 });
        setTotalChats(chatData?.total || 0);

        const interactionData = await InteractionsService.getInteractionHistoryCountApiV1InteractionsHistoryCountGet();
        setTotalInteractions(interactionData?.total || 0);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      }
    };
    fetchData();
  }, []);

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'there';

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-heading font-bold text-foreground">Welcome back, {firstName}</h1>
          <p className="text-muted-foreground mt-1 text-sm">Here is your health and search overview for today.</p>
        </div>
        <button
          className="bg-primary text-primary-foreground px-4 py-2 rounded-full text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2 shadow-sm"
          onClick={() => navigate('/app/chat')}
        >
          <iconify-icon icon="lucide:message-circle"></iconify-icon>
          New Consultation
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-card p-5 rounded-2xl border border-border shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-primary flex items-center justify-center">
            <iconify-icon icon="lucide:search" class="text-xl"></iconify-icon>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{totalSearches}</p>
            <p className="text-xs text-muted-foreground font-medium">Recent Searches</p>
          </div>
        </div>
        <div className="bg-card p-5 rounded-2xl border border-border shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <iconify-icon icon="lucide:message-square" class="text-xl"></iconify-icon>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{totalChats}</p>
            <p className="text-xs text-muted-foreground font-medium">AI Consultations</p>
          </div>
        </div>
        <div className="bg-card p-5 rounded-2xl border border-border shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
            <iconify-icon icon="lucide:shield-alert" class="text-xl"></iconify-icon>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{totalInteractions}</p>
            <p className="text-xs text-muted-foreground font-medium">Interaction Checks</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Activity */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h2 className="font-heading font-semibold text-lg">Recent Searches</h2>
              <button onClick={() => navigate('/app/medicines')} className="text-sm text-primary hover:underline">View All</button>
            </div>
            <div className="divide-y divide-border">
              {searchHistory.length > 0 ? searchHistory.map((item, i) => (
                <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-secondary/50 transition-colors cursor-pointer" onClick={() => navigate(`/app/${item.item_type === 'disease' ? 'diseases' : 'medicines'}/${encodeURIComponent(item.query_text)}`)}>
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
                      <iconify-icon icon={item.item_type === 'disease' ? 'lucide:activity' : 'lucide:pill'}></iconify-icon>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.query_text}</p>
                      <p className="text-xs text-muted-foreground capitalize">{item.item_type || 'Search'} • {new Date(item.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <button className="text-muted-foreground hover:text-primary"><iconify-icon icon="lucide:chevron-right"></iconify-icon></button>
                </div>
              )) : (
                <div className="px-6 py-8 text-center text-muted-foreground text-sm">
                  <iconify-icon icon="lucide:search" class="text-3xl mb-2 block"></iconify-icon>
                  No recent searches yet. Start by searching for a medicine or disease!
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          <div className="bg-card rounded-2xl border border-border shadow-sm p-6">
            <h2 className="font-heading font-semibold text-lg mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button onClick={() => navigate('/app/medicines')} className="w-full p-3 rounded-xl border border-border bg-background hover:border-primary/30 hover:bg-primary/5 transition-colors flex items-center gap-3 text-left group">
                <div className="w-9 h-9 rounded-lg bg-blue-50 text-primary flex items-center justify-center">
                  <iconify-icon icon="lucide:pill"></iconify-icon>
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">Search Medicines</p>
                  <p className="text-xs text-muted-foreground">Find drug information</p>
                </div>
              </button>
              <button onClick={() => navigate('/app/diseases')} className="w-full p-3 rounded-xl border border-border bg-background hover:border-primary/30 hover:bg-primary/5 transition-colors flex items-center gap-3 text-left group">
                <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <iconify-icon icon="lucide:microscope"></iconify-icon>
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">Disease Lookup</p>
                  <p className="text-xs text-muted-foreground">Search conditions</p>
                </div>
              </button>
              <button onClick={() => navigate('/app/interactions')} className="w-full p-3 rounded-xl border border-border bg-background hover:border-primary/30 hover:bg-primary/5 transition-colors flex items-center gap-3 text-left group">
                <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                  <iconify-icon icon="lucide:shield-alert"></iconify-icon>
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">Check Interactions</p>
                  <p className="text-xs text-muted-foreground">Drug safety checker</p>
                </div>
              </button>
              <button onClick={() => navigate('/app/chat')} className="w-full p-3 rounded-xl border border-border bg-background hover:border-primary/30 hover:bg-primary/5 transition-colors flex items-center gap-3 text-left group">
                <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
                  <iconify-icon icon="lucide:bot"></iconify-icon>
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">AI Consultation</p>
                  <p className="text-xs text-muted-foreground">Ask AI about health</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
