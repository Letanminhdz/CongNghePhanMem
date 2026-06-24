import React, { useState, useEffect } from 'react';
import { AdminService, MedicinesService } from '../client';

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

const FormField = ({ label, name, value, onChange, type = 'text', as }) => (
  <div className="mb-4">
    <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">{label}</label>
    {as === 'textarea' ? (
      <textarea name={name} value={value} onChange={onChange} rows={3} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none" />
    ) : (
      <input type={type} name={name} value={value} onChange={onChange} className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
    )}
  </div>
);

const AdminMedicines = () => {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // 'view' | 'edit' | 'add'
  const [selected, setSelected] = useState(null);
  
  const emptyForm = { name: '', sub: '', category: 'Anti-Infective', manufacturer: '', status: 'Prescription', statusColor: 'bg-blue-50 text-blue-700', description: '', dosage: '', sideEffects: '', contraindications: '' };
  const [form, setForm] = useState(emptyForm);

  const fetchMedicines = async () => {
    try {
      setLoading(true);
      const data = await MedicinesService.searchMedicinesApiV1MedicinesSearchGet({ q: '', limit: 100, skip: 0 });
      setMedicines(data.items || []);
    } catch (err) {
      console.error('Failed to fetch medicines', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMedicines();
  }, []);

  const openView = (item) => { setSelected(item); setModal('view'); };
  const openEdit = (item) => { 
    setForm({
      name: item.name || '',
      sub: item.generic_name ? `${item.generic_name}` : '',
      category: 'General',
      manufacturer: item.manufacturer || '',
      status: 'Prescription',
      description: item.purpose || item.indications || '',
      dosage: item.dosage || '',
      sideEffects: '',
      contraindications: ''
    }); 
    setModal('edit'); 
  };
  const openAdd = () => { setForm({ ...emptyForm }); setModal('add'); };
  const closeModal = () => setModal(null);

  const handleDelete = async (name) => {
    if (window.confirm(`Are you sure you want to delete medicine ${name}?`)) {
      try {
        await AdminService.deleteMedicineApiV1AdminMedicinesIdDelete({ id: name });
        setMedicines(prev => prev.filter(m => m.name !== name));
      } catch (err) {
        console.error('Failed to delete medicine', err);
        alert('Failed to delete medicine');
      }
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveEdit = async () => {
    try {
      const payload = {
        brand_name: form.sub || '',
        generic_name: form.sub || '',
        purpose: form.description || '',
        dosage: form.dosage || '',
        manufacturer: form.manufacturer || ''
      };
      await AdminService.updateMedicineApiV1AdminMedicinesIdPut({
        id: form.name,
        requestBody: payload
      });
      fetchMedicines();
      closeModal();
    } catch (err) {
      console.error('Failed to update medicine', err);
      alert('Failed to update medicine');
    }
  };

  const handleSaveAdd = async () => {
    if (!form.name.trim()) return;
    try {
      const payload = {
        name: form.name,
        brand_name: form.sub || '',
        generic_name: form.sub || '',
        purpose: form.description || '',
        dosage: form.dosage || '',
        manufacturer: form.manufacturer || ''
      };
      await AdminService.createMedicineApiV1AdminMedicinesPost({
        requestBody: payload
      });
      fetchMedicines();
      closeModal();
    } catch (err) {
      console.error('Failed to create medicine', err);
      alert('Failed to add medicine');
    }
  };



  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-heading font-semibold">Medicine Database</h1>
          <span className="px-2 py-0.5 rounded-md bg-accent text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            {loading ? '...' : medicines.length.toLocaleString()} Drugs
          </span>
        </div>
        <button onClick={openAdd} className="px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
          <iconify-icon icon="lucide:plus"></iconify-icon>
          <span>Add New Medicine</span>
        </button>
      </div>

      <div className="space-y-6">
        {/* Table */}
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-accent/50 border-b border-border">
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Medicine Name</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Generic Name</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Manufacturer</th>
                  <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr><td colSpan={4} className="px-6 py-12 text-center text-muted-foreground text-sm">Loading medicines...</td></tr>
                ) : medicines.length === 0 ? (
                  <tr><td colSpan={4} className="px-6 py-12 text-center text-muted-foreground text-sm">No medicines found.</td></tr>
                ) : (
                  medicines.map((m) => (
                    <tr key={m.name} className="hover:bg-accent/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-primary flex-shrink-0">
                            <iconify-icon icon="lucide:pill" class="text-xl"></iconify-icon>
                          </div>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{m.name}</span>
                            <span className="text-xs text-muted-foreground">{m.brand_name || m.generic_name}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-accent text-foreground">{m.generic_name || '—'}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">{m.manufacturer || '—'}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                        <button onClick={() => openView(m)} className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-primary transition-colors" title="View details">
                          <iconify-icon icon="lucide:eye"></iconify-icon>
                        </button>
                        <button onClick={() => openEdit(m)} className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-primary transition-colors" title="Edit">
                          <iconify-icon icon="lucide:pencil"></iconify-icon>
                        </button>
                        <button onClick={() => handleDelete(m.name)} className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-destructive transition-colors" title="Delete">
                            <iconify-icon icon="lucide:trash-2"></iconify-icon>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* View Modal */}
      {modal === 'view' && selected && (
        <Modal title="Medicine Details" onClose={closeModal}>
          <div className="flex items-center gap-4 mb-6 p-4 bg-blue-50 rounded-xl">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <iconify-icon icon="lucide:pill" class="text-2xl"></iconify-icon>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{selected.name}</h3>
              <p className="text-xs text-muted-foreground">{selected.brand_name || selected.generic_name}</p>
            </div>
          </div>
          <Field label="Generic Name" value={selected.generic_name} />
          <Field label="Manufacturer" value={selected.manufacturer} />
          <Field label="Description / Purpose" value={selected.purpose || selected.indications} />
          <Field label="Dosage" value={selected.dosage} />
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
        <Modal title="Edit Medicine" onClose={closeModal}>
          <FormField label="Medicine Name (ID - Cannot edit)" name="name" value={form.name} onChange={() => {}} />
          <FormField label="Generic Name" name="sub" value={form.sub} onChange={handleChange} />
          <FormField label="Manufacturer" name="manufacturer" value={form.manufacturer} onChange={handleChange} />
          <FormField label="Description / Purpose" name="description" value={form.description} onChange={handleChange} as="textarea" />
          <FormField label="Dosage" name="dosage" value={form.dosage} onChange={handleChange} />
          <div className="mt-4 flex justify-end gap-3">
            <button onClick={handleSaveEdit} className="px-5 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors">Save Changes</button>
            <button onClick={closeModal} className="px-5 py-2 border border-border rounded-full text-sm font-medium hover:bg-muted transition-colors">Cancel</button>
          </div>
        </Modal>
      )}

      {/* Add Modal */}
      {modal === 'add' && (
        <Modal title="Add New Medicine" onClose={closeModal}>
          <FormField label="Medicine Name *" name="name" value={form.name} onChange={handleChange} />
          <FormField label="Generic Name" name="sub" value={form.sub} onChange={handleChange} />
          <FormField label="Manufacturer" name="manufacturer" value={form.manufacturer} onChange={handleChange} />
          <FormField label="Description / Purpose" name="description" value={form.description} onChange={handleChange} as="textarea" />
          <FormField label="Dosage" name="dosage" value={form.dosage} onChange={handleChange} />
          <div className="mt-4 flex justify-end gap-3">
            <button onClick={handleSaveAdd} className="px-5 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 transition-colors">Add Medicine</button>
            <button onClick={closeModal} className="px-5 py-2 border border-border rounded-full text-sm font-medium hover:bg-muted transition-colors">Cancel</button>
          </div>
        </Modal>
      )}
    </>
  );
};

export default AdminMedicines;
