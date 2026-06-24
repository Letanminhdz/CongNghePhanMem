import React, { useEffect, useRef, useState } from 'react';
import { AdminService } from '../client';

const AdminReports = () => {
  const activityChartRef = useRef(null);
  const medicineChartRef = useRef(null);
  const chartsRef = useRef([]);

  const [realStats, setRealStats] = useState({
    totalUsers: 0,
    aiQueries: 0,
    medicineDb: 0,
    topMedicines: [],
    chatTopics: null
  });
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsResponse, logsResponse] = await Promise.all([
          AdminService.getStatsApiV1AdminStatsGet(),
          AdminService.getAiLogsApiV1AdminAiLogsGet({ limit: 5, page: 1 })
        ]);
        
        const usersCount = statsResponse.users?.total_users || 0;
        const medsCount = statsResponse.graph?.label_counts?.Drug || 0;
        const diseaseCount = statsResponse.graph?.label_counts?.Disease || 0;
        const queriesCount = logsResponse.total || 0;
        
        setRealStats({
          totalUsers: usersCount,
          aiQueries: queriesCount,
          medicineDb: medsCount + diseaseCount,
          topMedicines: statsResponse.top_medicines || [],
          chatTopics: statsResponse.chat_topics || { counts: {}, total: 0 }
        });

        setLogs(logsResponse.items || []);
      } catch (err) {
        console.error("Failed to load admin reports data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  useEffect(() => {
    const loadCharts = () => {
      if (!window.Chart || loading) return;

      chartsRef.current.forEach(c => c && c.destroy());
      chartsRef.current = [];

      // Activity Chart
      if (activityChartRef.current) {
        const total = realStats.aiQueries;
        const mockData = [
          Math.max(0, Math.floor(total * 0.05)),
          Math.max(0, Math.floor(total * 0.1)),
          Math.max(0, Math.floor(total * 0.15)),
          Math.max(0, Math.floor(total * 0.2)),
          Math.max(0, Math.floor(total * 0.18)),
          Math.max(0, Math.floor(total * 0.12)),
          total
        ];

        chartsRef.current.push(new window.Chart(activityChartRef.current, {
          type: 'line',
          data: {
            labels: ['Day 1', 'Day 5', 'Day 10', 'Day 15', 'Day 20', 'Day 25', 'Today'],
            datasets: [{ label: 'Consultations', data: mockData, borderColor: '#2563eb', backgroundColor: '#2563eb20', borderWidth: 2, tension: 0.4, fill: true, pointBackgroundColor: '#fff', pointBorderColor: '#2563eb', pointRadius: 4 }]
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#e2e8f0' }, ticks: { color: '#64748b' } }, x: { grid: { display: false }, ticks: { color: '#64748b' } } } }
        }));
      }

      // Medicines Chart
      if (medicineChartRef.current) {
        const topMeds = realStats.topMedicines || [];
        const labels = topMeds.length > 0 ? topMeds.map(m => m.name) : ['Tylenol', 'Amoxicillin', 'Aspirin', 'Ibuprofen', 'Nexium'];
        const data = topMeds.length > 0 ? topMeds.map(m => m.count) : [0, 0, 0, 0, 0];
        
        chartsRef.current.push(new window.Chart(medicineChartRef.current, {
          type: 'bar',
          data: { labels: labels, datasets: [{ label: 'Searches', data: data, backgroundColor: '#38bdf8', borderRadius: 4 }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#e2e8f0' }, ticks: { color: '#64748b', stepSize: 1 } }, x: { grid: { display: false }, ticks: { color: '#64748b' } } } }
        }));
      }
    };

    if (!window.Chart) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
      script.onload = loadCharts;
      document.head.appendChild(script);
    } else {
      loadCharts();
    }

    return () => { chartsRef.current.forEach(c => c && c.destroy()); };
  }, [loading, realStats.aiQueries]);

  const stats = [
    { label: 'Total Consultations', value: loading ? '...' : realStats.aiQueries.toLocaleString(), icon: 'lucide:message-square', iconBg: 'bg-primary/10 text-primary', trend: '+12.5%' },
    { label: 'Avg Response Time', value: '1.2s', icon: 'lucide:clock', iconBg: 'bg-accent text-primary', trend: '-0.3s' },
    { label: 'AI Accuracy Rate', value: '98.4%', icon: 'lucide:check-circle', iconBg: 'bg-primary/10 text-primary', trend: '+1.1%' },
  ];

  const [showExportMenu, setShowExportMenu] = useState(false);

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const handleExportPDF = () => {
    // Basic print trick for PDF
    window.print();
  };

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <h1 className="text-xl font-heading font-semibold text-foreground">Reports & Statistics</h1>
        <div className="flex items-center gap-4">
          <button onClick={handleExportPDF} className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-full text-sm font-medium shadow-sm transition-colors flex items-center gap-2">
            <iconify-icon icon="lucide:download"></iconify-icon> Export Report
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Analytics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {stats.map((s) => (
            <div key={s.label} className="bg-card p-5 rounded-xl border border-border shadow-sm flex flex-col justify-between">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{s.label}</p>
                  <h3 className="text-2xl font-bold text-foreground mt-1">{s.value}</h3>
                </div>
                <div className={`p-2 rounded-lg ${s.iconBg}`}>
                  <iconify-icon icon={s.icon} class="text-xl"></iconify-icon>
                </div>
              </div>
              <div className="flex items-center text-sm">
                <span className="text-blue-400 font-medium flex items-center">
                  <iconify-icon icon="lucide:trending-up" class="mr-1"></iconify-icon>{s.trend}
                </span>
                <span className="text-muted-foreground ml-2">vs last month</span>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 gap-6">
          <div className="bg-card border border-border rounded-xl shadow-sm p-5 w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-foreground">User Activity (30 Days)</h3>
              <select className="bg-muted border-none text-xs rounded-md px-2 py-1 focus:ring-0 text-foreground cursor-pointer outline-none">
                <option>Last 30 Days</option>
                <option>Last 7 Days</option>
                <option>This Year</option>
              </select>
            </div>
            <div className="h-64 w-full"><canvas ref={activityChartRef}></canvas></div>
            <div className="mt-4 flex items-center justify-center gap-6 border-t border-border pt-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-primary inline-block"></span>
                <span>Total Consultations (Lượt tư vấn)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row: Medicine Chart & Activity Log */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-card border border-border rounded-xl shadow-sm p-5">
            <h3 className="text-base font-semibold text-foreground mb-4">Top Searched Medicines</h3>
            <div className="h-64 w-full"><canvas ref={medicineChartRef}></canvas></div>
          </div>

          <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden flex flex-col">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <h3 className="text-base font-semibold text-foreground">Recent AI Activity Logs</h3>
              <button className="text-sm text-primary hover:underline font-medium">View All</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3 font-medium">Topic</th>
                    <th className="px-5 py-3 font-medium">Time</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-foreground">
                  {loading ? (
                    <tr><td colSpan={3} className="px-5 py-6 text-center text-muted-foreground">Loading...</td></tr>
                  ) : logs.length === 0 ? (
                    <tr><td colSpan={3} className="px-5 py-6 text-center text-muted-foreground">No logs found.</td></tr>
                  ) : (
                    logs.map((log) => (
                      <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <iconify-icon icon="lucide:message-square" class="text-muted-foreground"></iconify-icon>
                            {log.intent || 'Unknown Topic'}
                          </div>
                        </td>
                        <td className="px-5 py-3 text-muted-foreground">{formatTime(log.created_at)}</td>
                        <td className="px-5 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-600`}>Success</span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AdminReports;
