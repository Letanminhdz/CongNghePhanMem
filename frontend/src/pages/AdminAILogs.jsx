import React, { useState, useEffect } from 'react';
import { AdminService } from '../client';

const AdminAILogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  // Model Config State (Read Only — SDK chưa hỗ trợ)
  const [selectedModel] = useState('gemini-1.5-flash');
  const [apiKey] = useState('••••••••••••');
  const [quotaUsed] = useState(0);
  const [quotaPercent] = useState(0);


  const fetchLogs = async (pageNum = 1) => {
    try {
      setLoading(true);
      const data = await AdminService.getAiLogsApiV1AdminAiLogsGet({ limit: 10, page: pageNum });
      if (pageNum === 1) {
        setLogs(data.items || []);
      } else {
        setLogs(prev => [...prev, ...(data.items || [])]);
      }
      // ai-config: SDK chưa hỗ trợ, bỏ qua fetch
      setHasMore(data.items?.length === 10);
    } catch (err) {
      console.error('Failed to fetch AI logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(1);
  }, []);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchLogs(nextPage);
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // saveConfig & testConnection: bỏ — SDK chưa hỗ trợ, chế độ Read Only

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <h1 className="text-xl font-heading font-semibold text-foreground">AI Management</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-500 rounded-full text-xs font-medium border border-blue-200">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            System Operational
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Model Configuration - full width */}
        <div className="bg-card border border-border rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-heading font-semibold text-foreground flex items-center gap-2">
              <iconify-icon icon="lucide:cpu" class="text-primary"></iconify-icon> Model Configuration
            </h2>
            <span className="px-2.5 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full border border-primary/20">v4.2 Active</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-4">
              {/* Active model */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">Active AI Model</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted-foreground">
                    <iconify-icon icon="lucide:bot"></iconify-icon>
                  </div>
                  <select 
                    value={selectedModel}
                    disabled
                    className="w-full bg-muted/50 border border-input rounded-lg pl-10 py-2 text-sm text-muted-foreground outline-none transition-all appearance-none cursor-not-allowed"
                  >
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Google)</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Google)</option>
                    <option value="gemini-2.0-flash">Gemini 2.0 Flash (Stable)</option>
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash (Preview - High Load)</option>
                  </select>
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-muted-foreground">
                    <iconify-icon icon="lucide:chevron-down"></iconify-icon>
                  </div>
                </div>
              </div>

              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">Provider API Key</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted-foreground">
                    <iconify-icon icon="lucide:key"></iconify-icon>
                  </div>
                  <input 
                    type="password"
                    value={apiKey}
                    disabled
                    className="w-full bg-muted/50 border border-input rounded-lg pl-10 pr-3 py-2 text-sm text-muted-foreground outline-none transition-all cursor-not-allowed"
                    placeholder="Enter API Key"
                  />
                </div>
              </div>

              {/* Quota Usage */}
              <div className="p-4 border border-border rounded-lg bg-muted/20">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-foreground flex items-center gap-2">
                    <iconify-icon icon="lucide:activity" class="text-primary"></iconify-icon> API Quota Usage (This Month)
                  </span>
                  <span className="text-sm font-semibold text-foreground">{quotaPercent}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2.5">
                  <div className="bg-primary h-2.5 rounded-full" style={{ width: `${quotaPercent}%` }}></div>
                </div>
                <p className="text-xs text-muted-foreground mt-2">{quotaUsed.toLocaleString()} / 30,000 requests used</p>
              </div>
            </div>

            {/* Active Modules */}
            <div className="space-y-4 bg-background p-5 border border-border rounded-xl shadow-sm">
              <label className="block text-sm font-bold text-foreground border-b border-border pb-3 flex items-center gap-2">
                <iconify-icon icon="lucide:blocks" class="text-primary"></iconify-icon> Feature Modules
              </label>
              <div className="space-y-4 pt-2">
                {[
                  { label: 'Symptom Checker', checked: true, desc: 'Analyze user symptoms' },
                  { label: 'Medication Interaction Check', checked: true, desc: 'Check Neo4j for drug interactions' },
                  { label: 'Web Search Fallback', checked: false, desc: 'Search web if DB fails' },
                ].map((item) => (
                  <label key={item.label} className="flex items-start justify-between group">
                    <div>
                      <span className="text-sm font-semibold text-foreground">{item.label}</span>
                      <p className="text-xs text-muted-foreground mt-0.5">{item.desc}</p>
                    </div>
                    <div className="relative inline-flex items-center mt-1 opacity-60 cursor-not-allowed">
                      <input type="checkbox" className="sr-only peer" defaultChecked={item.checked} disabled />
                      <div className="w-9 h-5 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            
          </div>
          <div className="mt-6 pt-5 border-t border-border flex items-center justify-between">
            <span className="text-xs text-muted-foreground flex items-center gap-1.5">
              <iconify-icon icon="lucide:lock" class="text-sm"></iconify-icon>
              Read Only — SDK chưa hỗ trợ chỉnh sửa
            </span>
            <div className="flex gap-3">
              <button 
                disabled
                className="px-5 py-2 rounded-lg text-sm font-medium border border-border text-muted-foreground opacity-50 cursor-not-allowed"
              >
                Test Connection
              </button>
              <button 
                disabled
                className="bg-primary/50 text-primary-foreground px-5 py-2 rounded-lg text-sm font-medium shadow-sm flex items-center gap-2 opacity-50 cursor-not-allowed"
              >
                <iconify-icon icon="lucide:save"></iconify-icon> Save Configuration
              </button>
            </div>
          </div>
        </div>

        {/* Middle Row: Analytics & Disclaimers */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* AI Performance */}
          <div className="bg-card border border-border rounded-xl shadow-sm p-6 flex flex-col justify-between">
            <h2 className="text-lg font-heading font-semibold text-foreground mb-4 flex items-center gap-2">
              <iconify-icon icon="lucide:bar-chart" class="text-primary"></iconify-icon> AI Performance
            </h2>
            <div className="space-y-4">
              {[
                { label: 'Response Accuracy', value: '98.4%', width: 'w-[98%]', color: 'bg-blue-400' },
                { label: 'Safety Overrides', value: '1.2%', width: 'w-[1.2%]', color: 'bg-destructive' },
                { label: 'Avg Latency', value: '850ms', width: 'w-[40%]', color: 'bg-primary' },
              ].map((m) => (
                <div key={m.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">{m.label}</span>
                    <span className="font-medium text-foreground">{m.value}</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className={`${m.color} h-2 rounded-full ${m.width}`}></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 p-4 bg-primary/5 rounded-lg border border-primary/10">
              <div className="flex items-center gap-3">
                <iconify-icon icon="lucide:check-circle" class="text-primary text-2xl"></iconify-icon>
                <div>
                  <p className="text-sm font-medium text-foreground">System Healthy</p>
                  <p className="text-xs text-muted-foreground">No critical errors in 24h</p>
                </div>
              </div>
            </div>
          </div>

          {/* Standard Disclaimers */}
          <div className="bg-card border border-border rounded-xl shadow-sm lg:col-span-2 flex flex-col">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg font-heading font-semibold text-foreground flex items-center gap-2">
                <iconify-icon icon="lucide:message-square-plus" class="text-primary"></iconify-icon> Standard Disclaimers
              </h2>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <iconify-icon icon="lucide:lock" class="text-sm"></iconify-icon> Read Only
              </span>
            </div>
            <div className="p-6 space-y-4">
              {[
                { title: 'Emergency Prefix', text: '"If you are experiencing a medical emergency, please call 911 or visit the nearest emergency room immediately."' },
                { title: 'Standard Medical Disclaimer', text: '"I am an AI assistant, not a doctor. The information provided is for educational purposes and should not replace professional medical advice."' },
              ].map((d) => (
                <div key={d.title} className="flex items-start justify-between gap-4 p-4 border border-border rounded-lg bg-background">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-1">{d.title}</h4>
                    <p className="text-xs text-muted-foreground">{d.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Conversation Logs */}
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="text-lg font-heading font-semibold text-foreground flex items-center gap-2">
              <iconify-icon icon="lucide:list" class="text-primary"></iconify-icon> Conversation Logs
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-muted/50 text-muted-foreground">
                <tr>
                  <th className="px-6 py-4 font-medium">Timestamp</th>
                  <th className="px-6 py-4 font-medium">User Query Snippet</th>
                  <th className="px-6 py-4 font-medium">AI Response Snippet</th>
                  <th className="px-6 py-4 font-medium">Topic Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-foreground">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 text-muted-foreground">{formatTime(log.created_at)}</td>
                    <td className="px-6 py-4 font-medium truncate max-w-[200px]" title={log.message}>{log.message}</td>
                    <td className="px-6 py-4 text-muted-foreground truncate max-w-[300px]" title={log.response}>{log.response}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground`}>
                        {log.intent || 'Unknown'}
                      </span>
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && !loading && (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-muted-foreground">No AI logs found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {hasMore && (
            <div className="p-4 border-t border-border flex justify-center bg-muted/20">
              <button 
                onClick={loadMore} 
                disabled={loading}
                className="text-sm text-primary font-medium hover:underline disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Load More Logs'}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default AdminAILogs;
