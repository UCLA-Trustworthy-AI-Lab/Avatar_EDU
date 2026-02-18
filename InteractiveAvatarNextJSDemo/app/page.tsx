"use client";

import { useAuth, AuthProvider } from "@/components/auth/AuthContext";
import { LoginForm } from "@/components/auth/LoginForm";
import InteractiveAvatar from "@/components/InteractiveAvatar";

function AppContent() {
  const { isAuthenticated, loading, user, logout } = useAuth();

  if (loading) {
    return (
      <div className="w-screen h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <div className="w-screen h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                English Learning Avatar
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, <strong>{user?.username}</strong>
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded-md border border-gray-300 hover:bg-gray-50"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="w-[900px] flex flex-col items-start justify-start gap-5 mx-auto pt-6 pb-20">
          <div className="w-full">
            <InteractiveAvatar />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}