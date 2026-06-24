import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DiseasesService } from '../client';

const DiseaseDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [disease, setDisease] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDisease = async () => {
      try {
        const data = await DiseasesService.getDiseaseDetailApiV1DiseasesDiseaseNameDetailGet({ diseaseName: id });
        setDisease(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDisease();
  }, [id]);

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading...</div>;
  }

  if (!disease) {
    return <div className="p-8 text-center text-muted-foreground">Disease not found.</div>;
  }

  return (
    <div className="flex flex-col lg:flex-row gap-8 max-w-5xl mx-auto w-full">
      {/* Left Column */}
      <div className="flex-1 flex flex-col gap-8">
        {/* Overview */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <span className="bg-secondary text-secondary-foreground px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase">{disease.category || 'Condition'}</span>
            <span className="bg-muted text-muted-foreground px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase flex items-center gap-1">
              <iconify-icon icon="lucide:circle-alert" class="text-base"></iconify-icon> API Data
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-heading font-bold text-foreground leading-tight">{disease.name}</h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            {disease.description || 'No detailed description available.'}
          </p>
        </section>

        {/* Warning Signs */}
        <section className="bg-destructive/10 border border-destructive/20 rounded-xl p-6 flex gap-4 items-start">
          <div className="bg-destructive text-white p-3 rounded-full flex-shrink-0">
            <iconify-icon icon="lucide:flame" class="text-xl"></iconify-icon>
          </div>
          <div>
            <h3 className="text-lg font-heading font-semibold text-destructive mb-2">Immediate Warning Signs</h3>
            <p className="text-sm text-foreground/80 mb-3">Seek emergency medical care if you experience any of the following:</p>
            <ul className="grid sm:grid-cols-2 gap-2 text-sm text-foreground/90">
              {['Fruity-scented breath', 'Confusion or delirium', 'Nausea and vomiting', 'Shortness of breath'].map(s => (
                <li key={s} className="flex items-center gap-2">
                  <iconify-icon icon="lucide:circle-alert" class="text-destructive flex-shrink-0"></iconify-icon> {s}
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Symptoms */}
        <section className="bg-card rounded-xl p-6 md:p-8 shadow-sm border border-border">
          <h2 className="text-2xl font-heading font-semibold text-foreground mb-6 flex items-center gap-2">
            <iconify-icon icon="lucide:activity" class="text-primary"></iconify-icon> Common Symptoms
          </h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {(disease.symptoms || []).length > 0 ? disease.symptoms.map(({ name, description }) => (
              <div key={name} className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border border-border/50">
                <iconify-icon icon={'lucide:activity'} class="text-primary text-xl mt-0.5 flex-shrink-0"></iconify-icon>
                <div>
                  <h4 className="font-medium text-foreground">{name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">{description}</p>
                </div>
              </div>
            )) : <p className="text-muted-foreground text-sm col-span-2">No symptoms listed.</p>}
          </div>
        </section>


        <div className="grid md:grid-cols-2 gap-8">
          <section className="bg-card rounded-xl p-6 shadow-sm border border-border">
            <h2 className="text-xl font-heading font-semibold text-foreground mb-4 flex items-center gap-2">
              <iconify-icon icon="lucide:microscope" class="text-primary"></iconify-icon> Causes
            </h2>
            <ul className="space-y-3 text-muted-foreground text-sm">
              {[
                { label: 'Insulin Resistance', desc: "Muscle, liver and fat cells don't use insulin properly." },
                { label: 'Genetics', desc: 'Family history increases risk significantly.' },
                { label: 'Weight', desc: 'Being overweight is a primary risk factor.' },
                { label: 'Inactivity', desc: 'Less physical activity means higher risk.' },
              ].map(({ label, desc }) => (
                <li key={label} className="flex gap-2">
                  <iconify-icon icon="lucide:check" class="text-primary flex-shrink-0 mt-0.5"></iconify-icon>
                  <span><strong>{label}:</strong> {desc}</span>
                </li>
              ))}
            </ul>
          </section>
          <section className="bg-card rounded-xl p-6 shadow-sm border border-border">
            <h2 className="text-xl font-heading font-semibold text-foreground mb-4 flex items-center gap-2">
              <iconify-icon icon="lucide:shield-check" class="text-primary"></iconify-icon> Prevention
            </h2>
            <ul className="space-y-3 text-muted-foreground text-sm">
              {[
                { label: 'Healthy Diet', desc: 'Focus on lower fat, calories and higher fiber.' },
                { label: 'Active Lifestyle', desc: 'Aim for 150 minutes of moderate aerobic activity weekly.' },
                { label: 'Weight Loss', desc: 'Losing 7-10% of body weight can reduce risk.' },
                { label: 'Avoid Inactivity', desc: 'Try not to sit still for long periods.' },
              ].map(({ label, desc }) => (
                <li key={label} className="flex gap-2">
                  <iconify-icon icon="lucide:check" class="text-primary flex-shrink-0 mt-0.5"></iconify-icon>
                  <span><strong>{label}:</strong> {desc}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      {/* Right Sidebar */}
      <aside className="w-full lg:w-80 flex flex-col gap-6">
        <div className="bg-card rounded-xl p-6 shadow-sm border border-border">
          <h3 className="text-lg font-heading font-semibold text-foreground mb-4">Recommended Medicines</h3>
          <p className="text-xs text-muted-foreground mb-4 pb-4 border-b border-border">Always consult your healthcare provider before starting any medication.</p>
          <div className="space-y-4">
            {(disease.treatments || []).length > 0 ? disease.treatments.map((name) => (
              <div key={name} className="flex gap-3 items-center cursor-pointer hover:bg-secondary/50 p-2 rounded-lg transition-colors" onClick={() => navigate(`/app/medicines/${encodeURIComponent(name)}`)}>
                <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center text-primary flex-shrink-0">
                  <iconify-icon icon={'lucide:pill'} class="text-xl"></iconify-icon>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-foreground">{name}</h4>
                  <p className="text-xs text-muted-foreground">Medicine</p>
                </div>
              </div>
            )) : <p className="text-muted-foreground text-sm">No treatments listed.</p>}
          </div>
          <button onClick={() => navigate('/app/medicines')} className="w-full mt-6 text-sm text-primary font-medium hover:underline">
            View full medication list
          </button>
        </div>

        <div className="bg-card rounded-xl p-6 shadow-sm border border-border">
          <h3 className="text-lg font-heading font-semibold text-foreground mb-4">Related Conditions</h3>
          <div className="flex flex-wrap gap-2">
            {['Type 1 Diabetes', 'Prediabetes', 'Hypertension', 'Obesity', 'Neuropathy'].map(c => (
              <button key={c} onClick={() => navigate('/app/diseases')} className="px-3 py-1.5 bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground text-xs font-medium rounded-full transition-colors">
                {c}
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Ask AI FAB */}
      <div className="fixed bottom-6 right-6 z-50">
        <button onClick={() => navigate(localStorage.getItem('access_token') ? '/app/chat' : '/chat', { state: { q: `Tell me about the condition: ${disease.name}. What are the symptoms and treatments?` } })} className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/30 rounded-full py-3 px-6 flex items-center gap-3 transition-transform hover:scale-105">
          <iconify-icon icon="lucide:bot" class="text-2xl"></iconify-icon>
          <div className="text-left">
            <div className="text-sm font-bold">Ask AI Assistant</div>
            <div className="text-xs text-primary-foreground/80 font-medium">Get instant medical answers</div>
          </div>
        </button>
      </div>
    </div>
  );
};

export default DiseaseDetail;
