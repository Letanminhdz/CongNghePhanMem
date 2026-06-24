import React, { useState, useEffect } from 'react';
import { AdminService } from '../client';

const AdminAILogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  
  // Model Config State
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash');
  const [apiKey, setApiKey] = useState('');
  const [quotaUsed, setQuotaUsed] = useState(0); 
  const [quotaPercent, setQuotaPercent] = useState(0);
  
  // New States for AI Config
  const [systemVersion, setSystemVersion] = useState('v4.2 Active');
  const [performanceStats, setPerformanceStats] = useState({ accuracy: 98.4, safety_overrides: 1.2, latency: 850 });
  const [featureModules, setFeatureModules] = useState({ symptom_checker: true, interaction_check: true, gemini_integration: true });
  const [disclaimers, setDisclaimers] = useState([]);
  
  const [configSaving, setConfigSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchLogs = async (pageNum = 1) => {
    try {
      setLoading(true);
      const data = await AdminService.getAiLogsApiV1AdminAiLogsGet({ limit: 10, page: pageNum });
      if (pageNum === 1) {
        setLogs(data.items || []);
      } else {
        setLogs(prev => [...prev, ...(data.items || [])]);
      }
      
      // Fetch available models
      try {
        const token = localStorage.getItem('access_token');
        const modelsRes = await fetch(`${API_URL}/api/v1/admin/ai-models`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (modelsRes.ok) {
          const modelsData = await modelsRes.json();
          if (modelsData.models && modelsData.models.length > 0) {
            setAvailableModels(modelsData.models);
          }
        }
      } catch (e) {
        console.error("Failed to fetch ai models", e);
      }

      // Fetch ai-config
      try {
        const token = localStorage.getItem('access_token');
        const configRes = await fetch(`${API_URL}/api/v1/admin/ai-config`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (configRes.ok) {
          const config = await configRes.json();
          if (config.model) setSelectedModel(config.model);
          if (config.api_key !== undefined) setApiKey(config.api_key);
          if (config.quota_used !== undefined) {
            setQuotaUsed(config.quota_used);
            setQuotaPercent(Math.min(100, Math.round((config.quota_used / 30000) * 100)));
          }
          if (config.system_version) setSystemVersion(config.system_version);
          if (config.performance_stats) setPerformanceStats(config.performance_stats);
          if (config.feature_modules) setFeatureModules(config.feature_modules);
          if (config.disclaimers) setDisclaimers(config.disclaimers);
        }
      } catch (e) {
        console.error("Failed to fetch ai config", e);
      }
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

  // Ensure selectedModel is valid once availableModels are loaded
  useEffect(() => {
    if (availableModels.length > 0 && !availableModels.includes(selectedModel)) {
      setSelectedModel(availableModels[0]);
    }
  }, [availableModels, selectedModel]);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchLogs(nextPage);
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const saveConfig = async () => {
    try {
      setConfigSaving(true);
      setTestResult(null);
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_URL}/api/v1/admin/ai-config`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          model: selectedModel, 
          api_key: apiKey,
          system_version: systemVersion,
          performance_stats: performanceStats,
          feature_modules: featureModules,
          disclaimers: disclaimers
        })
      });
      if (res.ok) {
        alert("Configuration saved successfully!");
      } else {
        alert("Failed to save configuration.");
      }
    } catch (e) {
      alert("Error saving configuration.");
    } finally {
      setConfigSaving(false);
    }
  };

  const testConnection = async () => {
    if (!apiKey) {
      alert("Please enter an API Key to test.");
      return;
    }
    try {
      setTestingConnection(true);
      setTestResult(null);
      const token = localStorage.getItem('access_token');
      
      // Update models list when testing connection too
      fetch(`${API_URL}/api/v1/admin/ai-models?api_key=${apiKey}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data.models && data.models.length > 0) setAvailableModels(data.models);
      }).catch(e => console.error(e));

      const res = await fetch(`${API_URL}/api/v1/admin/ai-config/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ api_key: apiKey })
      });
      const data = await res.json();
      setTestResult({ success: data.success, message: data.message });
    } catch (e) {
      setTestResult({ success: false, message: "Network error during test." });
    } finally {
      setTestingConnection(false);
    }
  };

  // Disclaimers Handlers
  const handleAddDisclaimer = () => {
    const title = window.prompt("Enter disclaimer title:");
    if (!title) return;
    const text = window.prompt("Enter disclaimer text:");
    if (!text) return;
    const newId = "desc_" + Date.now();
    setDisclaimers([...disclaimers, { id: newId, title, text }]);
  };

  const handleEditDisclaimer = (id) => {
    const item = disclaimers.find(d => d.id === id);
    if (!item) return;
    const title = window.prompt("Edit title:", item.title);
    if (title === null) return;
    const text = window.prompt("Edit text:", item.text);
    if (text === null) return;
    setDisclaimers(disclaimers.map(d => d.id === id ? { ...d, title, text } : d));
  };

  const handleDeleteDisclaimer = (id) => {
    if (window.confirm("Are you sure you want to delete this disclaimer?")) {
      setDisclaimers(disclaimers.filter(d => d.id !== id));
    }
  };

  // Format model name for UI
  const formatModelName = (name) => {
    return name.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

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
            <span className="px-2.5 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full border border-primary/20">
              {systemVersion || 'v4.2 Active'}
            </span>
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
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-background border border-input rounded-lg pl-10 py-2 text-sm text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all appearance-none"
                  >
                    {availableModels.length > 0 ? (
                      availableModels.map(model => (
                        <option key={model} value={model}>{formatModelName(model)}</option>
                      ))
                    ) : (
                      <>
                        <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                        <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
                      </>
                    )}
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
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full bg-background border border-input rounded-lg pl-10 pr-3 py-2 text-sm text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
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
                  { id: 'symptom_checker', label: 'Symptom Checker', desc: 'Analyze user symptoms' },
                  { id: 'interaction_check', label: 'Medication Interaction Check', desc: 'Check Neo4j for drug interactions' },
                  { id: 'gemini_integration', label: 'Gemini API Integration', desc: 'Use AI models for natural responses' },
                ].map((item) => (
                  <label key={item.id} className="flex items-start justify-between cursor-pointer group">
                    <div>
                      <span className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{item.label}</span>
                      <p className="text-xs text-muted-foreground mt-0.5">{item.desc}</p>
                    </div>
                    <div className="relative inline-flex items-center cursor-pointer mt-1">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={featureModules[item.id] || false} 
                        onChange={(e) => setFeatureModules({...featureModules, [item.id]: e.target.checked})}
                      />
                      <div className="w-9 h-5 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            
            {testResult && (
              <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${testResult.success ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                <iconify-icon icon={testResult.success ? "lucide:check-circle" : "lucide:alert-circle"}></iconify-icon>
                <span>{testResult.message}</span>
              </div>
            )}
          </div>
          <div className="mt-6 pt-5 border-t border-border flex justify-end gap-3">
            <button 
              onClick={testConnection}
              disabled={testingConnection}
              className="px-5 py-2 rounded-lg text-sm font-medium border border-border text-foreground hover:bg-muted transition-colors disabled:opacity-50"
            >
              {testingConnection ? 'Testing...' : 'Test Connection'}
            </button>
            <button 
              onClick={saveConfig}
              disabled={configSaving}
              className="bg-primary hover:bg-primary/90 text-primary-foreground px-5 py-2 rounded-lg text-sm font-medium shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <iconify-icon icon="lucide:save"></iconify-icon> {configSaving ? 'Saving...' : 'Save Configuration'}
            </button>
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
                { label: 'Response Accuracy', value: `${performanceStats.accuracy || 0}%`, width: `${performanceStats.accuracy || 0}%`, color: 'bg-blue-400' },
                { label: 'Safety Overrides', value: `${performanceStats.safety_overrides || 0}%`, width: `${performanceStats.safety_overrides || 0}%`, color: 'bg-destructive' },
                { label: 'Avg Latency', value: `${performanceStats.latency || 0}ms`, width: '40%', color: 'bg-primary' },
              ].map((m) => (
                <div key={m.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">{m.label}</span>
                    <span className="font-medium text-foreground">{m.value}</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className={`${m.color} h-2 rounded-full`} style={{ width: m.width }}></div>
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
              <button 
                onClick={handleAddDisclaimer}
                className="text-sm text-primary font-medium hover:underline flex items-center gap-1"
              >
                <iconify-icon icon="lucide:plus"></iconify-icon> Add New
              </button>
            </div>
            <div className="p-6 space-y-4">
              {disclaimers.length > 0 ? disclaimers.map((d) => (
                <div key={d.id} className="flex items-start justify-between gap-4 p-4 border border-border rounded-lg bg-background">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-1">{d.title}</h4>
                    <p className="text-xs text-muted-foreground">{d.text}</p>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <button onClick={() => handleEditDisclaimer(d.id)} className="p-1.5 text-muted-foreground hover:text-primary transition-colors">
                      <iconify-icon icon="lucide:pencil"></iconify-icon>
                    </button>
                    <button onClick={() => handleDeleteDisclaimer(d.id)} className="p-1.5 text-muted-foreground hover:text-destructive transition-colors">
                      <iconify-icon icon="lucide:trash-2"></iconify-icon>
                    </button>
                  </div>
                </div>
              )) : (
                <p className="text-sm text-muted-foreground text-center py-4">No disclaimers configured.</p>
              )}
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
