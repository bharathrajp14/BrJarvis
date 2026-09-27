'use client';
import Link from 'next/link';
import { useState } from 'react';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🚀</span>
            <span className="text-xl font-bold text-indigo-600">OnboardAI</span>
          </Link>
          <div className="hidden md:flex items-center gap-6">
            <Link href="/dashboard" className="text-gray-600 hover:text-indigo-600 font-medium">Dashboard</Link>
            <Link href="/onboard/new" className="text-gray-600 hover:text-indigo-600 font-medium">New Onboarding</Link>
            <Link href="/analytics" className="text-gray-600 hover:text-indigo-600 font-medium">Analytics</Link>
            <Link href="/dashboard" className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium">Get Started</Link>
          </div>
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100">
            <span className="text-xl">{menuOpen ? '✕' : '☰'}</span>
          </button>
        </div>
        {menuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200 flex flex-col gap-4">
            <Link href="/dashboard" className="text-gray-600 font-medium">Dashboard</Link>
            <Link href="/onboard/new" className="text-gray-600 font-medium">New Onboarding</Link>
            <Link href="/analytics" className="text-gray-600 font-medium">Analytics</Link>
          </div>
        )}
      </div>
    </nav>
  );
}
