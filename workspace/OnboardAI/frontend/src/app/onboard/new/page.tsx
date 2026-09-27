'use client';
import { useState } from 'react';
import Navbar from '@/components/Navbar';

const roles = ['Software Engineer', 'Product Manager', 'Designer', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations'];
const departments = ['Engineering', 'Product', 'Design', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations'];

export default function NewOnboard() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ name: '', email: '', role: '', department: '', startDate: '' });
  const [plan, setPlan] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 2000));
    setPlan([
      '✅ Send welcome email with company handbook',
      '✅ Setup laptop and required software tools',
      '✅ Schedule intro meeting with team lead',
      '✅ Complete HR compliance documents',
      '✅ Assign onboarding buddy / mentor',
      '✅ Complete role-specific training modules',
      '✅ 30-day performance check-in scheduled',
      '✅ Access provisioning for all required systems',
    ]);
    setLoading(false);
    setStep(3);
  };

  const handleSubmit = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 1500));
    setLoading(false);
    setDone(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            {[1,2,3].map(s => (
              <div key={s} className={`flex items-center gap-2`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  step >= s ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-500'
                }`}>{s}</div>
                {s < 3 && <div className={`h-1 w-16 ${step > s ? 'bg-indigo-600' : 'bg-gray-200'}`} />}
              </div>
            ))}
          </div>
          <p className="text-gray-500 text-sm">
            {step === 1 && 'Employee Information'}
            {step === 2 && 'Role & Department'}
            {step === 3 && 'AI-Generated Plan'}
          </p>
        </div>

        {!done ? (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            {step === 1 && (
              <div className="space-y-4">
                <h2 className="text-xl font-bold text-gray-800 mb-6">Employee Details</h2>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="John Smith" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                  <input className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="john@company.com" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                  <input type="date" className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none" value={form.startDate} onChange={e => setForm({...form, startDate: e.target.value})} />
                </div>
                <button onClick={() => setStep(2)} className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 mt-4">Continue →</button>
              </div>
            )}
            {step === 2 && (
              <div className="space-y-4">
                <h2 className="text-xl font-bold text-gray-800 mb-6">Role & Department</h2>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Job Role</label>
                  <select className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none" value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
                    <option value="">Select role...</option>
                    {roles.map(r => <option key={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                  <select className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none" value={form.department} onChange={e => setForm({...form, department: e.target.value})}>
                    <option value="">Select department...</option>
                    {departments.map(d => <option key={d}>{d}</option>)}
                  </select>
                </div>
                <div className="flex gap-3 mt-4">
                  <button onClick={() => setStep(1)} className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold">← Back</button>
                  <button onClick={handleGenerate} disabled={loading} className="flex-1 bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50">
                    {loading ? '🤖 Generating AI Plan...' : '✨ Generate AI Plan'}
                  </button>
                </div>
              </div>
            )}
            {step === 3 && (
              <div className="space-y-4">
                <h2 className="text-xl font-bold text-gray-800 mb-2">🤖 AI-Generated Onboarding Plan</h2>
                <p className="text-gray-500 text-sm mb-6">Customized for <strong>{form.role}</strong> in <strong>{form.department}</strong></p>
                <div className="space-y-3">
                  {plan.map((item, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-indigo-50 rounded-lg">
                      <span className="text-indigo-600 font-bold text-sm w-6">{i+1}.</span>
                      <span className="text-gray-700 text-sm">{item}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-3 mt-6">
                  <button onClick={() => setStep(2)} className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold">← Edit</button>
                  <button onClick={handleSubmit} disabled={loading} className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50">
                    {loading ? 'Launching...' : '🚀 Launch Onboarding'}
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Onboarding Launched!</h2>
            <p className="text-gray-500 mb-6">{form.name} has been sent their onboarding plan. They will receive an email at {form.email} with next steps.</p>
            <div className="flex gap-3">
              <button onClick={() => { setDone(false); setStep(1); setForm({ name: '', email: '', role: '', department: '', startDate: '' }); }} className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold">Create Another</button>
              <a href="/dashboard" className="flex-1 bg-indigo-600 text-white py-3 rounded-lg font-semibold text-center hover:bg-indigo-700">Go to Dashboard →</a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
