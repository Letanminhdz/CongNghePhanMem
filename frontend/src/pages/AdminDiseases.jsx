import React, { useState, useEffect } from 'react';
import { AdminService, DiseasesService } from '../client';

const categories = ['Endocrine', 'Respiratory', 'Cardiovascular', 'Neurological', 'Digestive', 'Musculoskeletal', 'Infectious', 'General'];
const severities = [
  { label: 'Low', color: 'bg-blue-50 text-blue-700' },
  { label: 'Moderate', color: 'bg-amber-50 text-amber-700' },
  { label: 'High', color: 'bg-red-50 text-red-700' },
  { label: 'Critical', color: 'bg-red-100 text-red-800' },
];

const emptyForm = { name: '', sub: '', icd: '', category: 'General', severity: 'Low', severityColor: 'bg-blue-50 text-blue-700', icon: 'lucide:activity', iconBg: 'bg-blue-50 text-blue-600', description: '', symptoms: '', treatments: '', relatedMedicines: '' };

const Modal = ({ title, onClose, children }) => (
  <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
    <div className="bg-card rounded-2xl shadow-xl border border-border w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
      <div className="flex items-center justify-between p-6 border-b border-border">
        <h2 className="text-lg font-heading font-semibold text-foreground">{title}</h2>
        <button onClick={onClose} className="p-1.5 rounded-full hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
          <iconify-icon icon="lucide:x" class="text-xl"></iconify-icon>
        </button>
      </div>
      <div className="p-6">{children}</div>
    </div>
  </div>
);

const Field = ({ label, value }) => (
  <div className="py-3 border-b border-border last:border-0">
    <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">{label}</p>
    <p className="text-sm text-foreground">{value || '—'}</p>
  </div>
);

const FormField = ({ label, name, value, onChange, as }) => (
  <div className="mb-4">
    <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">{label}</label>
    {as === 'textarea' ? (
      <textarea name={name} value={value} onChange={onChange} rows={3} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none" />
    ) : (
      <input name={name} value={value} onChange={onChange} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
    )}
  </div>
);

const AdminDiseases = () => {
  const [diseases, setDiseases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const fetchDiseases = async () => {
    try {
      setLoading(true);
      const data = await DiseasesService.searchDiseasesApiV1DiseasesSearchGet({ q: '', limit: 100, skip: 0 });
      setDiseases(data.items || []);
    } catch (err) {
      console.error('Failed to fetch diseases', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiseases();
  }, []);

  const openView = (item) => { 
    setSelected(item); 
    setModal('view'); 
  };
  const openEdit = (item) => { 
    const s = severities.find(sev => sev.label === item.severity) || severities[0];
    setForm({
      name: item.name || '',
      sub: '',
      icd: '',
      category: item.category || 'General',
      severity: item.severity || 'Low',
      severityColor: s.color,
      icon: 'lucide:activity',
      iconBg: 'bg-blue-50 text-blue-600',
      description: item.description || '',
      symptoms: '',
      treatments: '',
      relatedMedicines: ''
    }); 
    setModal('edit'); 
  };
  const openAdd = () => { setForm({ ...emptyForm }); setModal('add'); };
  const closeModal = () => setModal(null);

  const handleDelete = async (name) => {
    if (window.confirm(`Are you sure you want to delete disease ${name}?`)) {
      try {
        await AdminService.deleteDiseaseApiV1AdminDiseasesIdDelete({ id: name });
        setDiseases(prev => prev.filter(d => d.name !== name));
      } catch (err) {
        console.error('Failed to delete disease', err);
        alert('Failed to delete disease');
      }
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'severity') {
      const s = severities.find(s => s.label === value);
      setForm(prev => ({ ...prev, severity: value, severityColor: s?.color || prev.severityColor }));
    } else {
      setForm(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSaveEdit = async () => {
    try {
      const payload = {
        category: form.category || '',
        severity: form.severity || '',
        description: form.description || ''
      };
      await AdminService.updateDiseaseApiV1AdminDiseasesIdPut({
        id: form.name,
        requestBody: payload
      });
      fetchDiseases();
      closeModal();
    } catch (err) {
      console.error('Failed to update disease', err);
      alert('Failed to update disease');
    }
  };

  const handleSaveAdd = async () => {
    if (!form.name.trim()) return;
    try {
      const payload = {
        name: form.name,
        category: form.category || '',
        severity: form.severity || '',
        description: form.description || ''
      };
      await AdminService.createDiseaseApiV1AdminDiseasesPost({
        requestBody: payload
      });
      fetchDiseases();
      closeModal();
    } catch (err) {
      console.error('Failed to add disease', err);
      alert('Failed to add disease');
    }
  };



  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-heading font-semibold">Disease Database</h1>
          <span className="px-2 py-0.5 rounded-md bg-accent text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            {loading ? '...' : diseases.length} Records
          </span>
        </div>
        <button onClick={openAdd} className="px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
          <iconify-icon icon="lucide:plus"></iconify-icon>
          <span>Add New Disease</span>
        </button>
      </div>

      <div className="space-y-6">
        {/* Table */}
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-accent/50 border-b border-border">
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Disease Name</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Category</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Severity</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr><td colSpan={4} className="px-6 py-12 text-center text-muted-foreground text-sm">Loading diseases...</td></tr>
                ) : diseases.length === 0 ? (
                  <tr><td colSpan={4} className="px-6 py-12 text-center text-muted-foreground text-sm">No diseases found.</td></tr>
                ) : (
                  diseases.map((d) => {
                    const s = severities.find(sev => sev.label === d.severity) || severities[0];
                    return (
                      <tr key={d.name} className="hover:bg-accent/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 bg-blue-50 text-blue-600`}>
                              <iconify-icon icon="lucide:activity" class="text-xl"></iconify-icon>
                            </div>
                            <div className="flex flex-col">
                              <span className="font-medium text-sm">{d.name}</span>
                              <span className="text-xs text-muted-foreground">{d.category}</span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-accent text-foreground">{d.category || 'General'}</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${s.color}`}>{d.severity || 'Low'}</span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button onClick={() => openView(d)} className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-primary transition-colors" title="View details">
                              <iconify-icon icon="lucide:eye"></iconify-icon>
                            </button>
                            <button onClick={() => openEdit(d)} className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-primary transition-colors" title="Edit">
                              <iconify-icon icon="lucide:pencil"></iconify-icon>
                            </button>
                            <button onClick={() => handleDelete(d.name)} className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-destructive transition-colors" title="Delete">
                              <iconify-icon icon="lucide:trash-2"></iconify-icon>
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* View Modal */}
      {modal === 'view' && selected && (
        <Modal title="Disease Details" onClose={closeModal}>
          <div className={`flex items-center gap-4 mb-6 p-4 rounded-xl bg-blue-50`}>
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-blue-600`}>
              <iconify-icon icon="lucide:activity" class="text-2xl"></iconify-icon>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{selected.name}</h3>
              <p className="text-xs text-muted-foreground">{selected.category}</p>
            </div>
            <span className={`ml-auto px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${(severities.find(sev => sev.label === selected.severity) || severities[0]).color}`}>{selected.severity || 'Low'}</span>
          </div>
          <Field label="Category" value={selected.category} />
          <Field label="Description" value={selected.description} />
          <div className="mt-6 flex justify-end gap-3">
            <button onClick={() => { closeModal(); openEdit(selected); }} className="px-4 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
              <iconify-icon icon="lucide:pencil"></iconify-icon> Edit
            </button>
            <button onClick={closeModal} className="px-4 py-2 border border-border rounded-full text-sm font-medium hover:bg-muted transition-colors">Close</button>
          </div>
        </Modal>
      )}

      {/* Edit Modal */}
      {modal === 'edit' && (
        <Modal title="Edit Disease" onClose={closeModal}>
          <FormField label="Disease Name (ID - Cannot Edit)" name="name" value={form.name} onChange={() => {}} />
          <div className="mb-4">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Category</label>
            <select name="category" value={form.category} onChange={handleChange} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20">
              {categories.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Severity</label>
            <select name="severity" value={form.severity} onChange={handleChange} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20">
              {severities.map(s => <option key={s.label}>{s.label}</option>)}
            </select>
          </div>
          <FormField label="Description" name="description" value={form.description} onChange={handleChange} as="textarea" />
          <div className="mt-2 flex justify-end gap-3">
            <button onClick={handleSaveEdit} className="px-5 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors">Save Changes</button>
            <button onClick={closeModal} className="px-5 py-2 border border-border rounded-full text-sm font-medium hover:bg-muted transition-colors">Cancel</button>
          </div>
        </Modal>
      )}

      {/* Add Modal */}
      {modal === 'add' && (
        <Modal title="Add New Disease" onClose={closeModal}>
          <FormField label="Disease Name *" name="name" value={form.name} onChange={handleChange} />
          <div className="mb-4">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Category</label>
            <select name="category" value={form.category} onChange={handleChange} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20">
              {categories.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Severity</label>
            <select name="severity" value={form.severity} onChange={handleChange} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20">
              {severities.map(s => <option key={s.label}>{s.label}</option>)}
            </select>
          </div>
          <FormField label="Description" name="description" value={form.description} onChange={handleChange} as="textarea" />
          <div className="mt-2 flex justify-end gap-3">
            <button onClick={handleSaveAdd} className="px-5 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors">Add Disease</button>
            <button onClick={closeModal} className="px-5 py-2 border border-border rounded-full text-sm font-medium hover:bg-muted transition-colors">Cancel</button>
          </div>
        </Modal>
      )}
    </>
  );
};

export default AdminDiseases;
