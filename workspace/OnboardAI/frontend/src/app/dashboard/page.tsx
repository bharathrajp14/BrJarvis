'use client';
import { useState } from 'react';

const employees = [
  { id: 1, name: 'Sarah Johnson', role: 'Frontend Developer', progress: 75, status: 'In Progress', startDate: '2026-08-25' },
  { id: 2, name: 'Mike Chen', role: 'Product Manager', progress: 100, status: 'Completed', startDate: '2026-08-20' },
  { id: 3, name: 'Emily Davis', role: 'UX Designer', progress: 30, status: 'In Progress', startDate: '2026-08-27' },
  { id: 4, name: 'James Wilson', role: 'Backend Engineer', progress: 0, status: 'Pending', startDate: '2026-08-29' },
];

export default function Dashboard() {
  const [search, setSearch] = useState('');

  const filtered = employees.filter(e =>
    e.name.toLowerCase().includes(search.toLowerCase()) ||
    e.role.toLowerCase().includes(search.toLowerCase())
  );

  const stats = [
    { label: 'Total Employees', value: employees.length, color: 'bg-blue-500' },
    { label: 'In Progress', value: employees.filter(e => e.status === 'In Progress').length, color: 'bg-yellow-500' },
    { label: 'Completed', value: employees.filter(e => e.status === 'Completed').length, color: 'bg-green-500' },
    { label: 'Pending', value: employees.filter(e => e.status === 'Pending').length, color: 'bg-red-500' },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-sm font-bold">OA</div>
          <span className="text-xl font-bold">OnboardAI</span>
        </div>
        <nav className="flex gap-6 text-sm text-gray-400">
          <a href="/dashboard" className="text-white font-medium">Dashboard</a>
          <a href="/onboard/new" className="hover:text-white">New Onboard</a>
          <a href="/analytics" className="hover:text-white">Analytics</a>
        </nav>
        <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition">
          + Add Employee
        </button>
      </header>

      <main className="p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-1">Dashboard</h1>
          <p className="text-gray-400">Manage and track all employee onboarding</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {stats.map((stat, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className={`w-3 h-3 rounded-full ${stat.color} mb-3`}></div>
              <div className="text-3xl font-bold mb-1">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search employees..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-sm w-72 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-800 text-gray-400">
              <tr>
                <th className="text-left px-6 py-4">Employee</th>
                <th className="text-left px-6 py-4">Role</th>
                <th className="text-left px-6 py-4">Start Date</th>
                <th className="text-left px-6 py-4">Progress</th>
                <th className="text-left px-6 py-4">Status</th>
                <th className="text-left px-6 py-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered.map(emp => (
                <tr key={emp.id} className="hover:bg-gray-800/50 transition">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-xs font-bold">
                        {emp.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <span className="font-medium">{emp.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-400">{emp.role}</td>
                  <td className="px-6 py-4 text-gray-400">{emp.startDate}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-700 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-blue-500"
                          style={{ width: `${emp.progress}%` }}
                        ></div>
                      </div>
                      <span className="text-gray-400 text-xs">{emp.progress}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      emp.status === 'Completed' ? 'bg-green-500/20 text-green-400' :
                      emp.status === 'In Progress' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {emp.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button className="text-blue-400 hover:text-blue-300 text-xs">View →</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}