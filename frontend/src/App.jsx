
import { useState, useEffect, createContext } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate, Link } from 'react-router-dom'
import liff from '@line/liff'
import FileListView from './components/FileListView'
import ShareView from './components/ShareView'
import SettingsView from './components/SettingsView'
import { Search, FileText, Share2, Settings } from 'lucide-react'

export const UserContext = createContext(null);

function NavItem({ to, icon: Icon, label }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link to={to} className={`nav-item ${isActive ? 'active' : ''}`}>
      <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
      <span style={{ fontSize: '10px', fontWeight: 500 }}>{label}</span>
    </Link>
  )
}

function AppContent() {
  const [liffError, setLiffError] = useState(null)
  const [isMockMode, setIsMockMode] = useState(false)
  const [userId, setUserId] = useState(null)

  useEffect(() => {
    const liffId = import.meta.env.VITE_LIFF_ID

    if (!liffId || liffId === 'mock-liff-id') {
      console.log('LIFF ID not found, running in Mock Mode')
      setIsMockMode(true)
      setUserId("Ua8e2b0a894035997230eab28885ce36f") // Set mock ID
      return
    }

    liff.init({ liffId })
      .then(() => {
        console.log('LIFF initialized')
        if (liff.isLoggedIn()) {
          liff.getProfile().then(profile => setUserId(profile.userId))
        } else {
          if (import.meta.env.DEV) {
            setUserId("Ua8e2b0a894035997230eab28885ce36f")
          } else {
            liff.login()
          }
        }
      })
      .catch((error) => {
        console.error('LIFF init failed', error)
        setLiffError(error.toString())
        if (import.meta.env.DEV) {
          setUserId("Ua8e2b0a894035997230eab28885ce36f")
        }
      })
  }, [])

  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/share': return 'Share';
      case '/settings': return 'Settings';
      default: return 'Files';
    }
  };

  return (
    <UserContext.Provider value={userId}>
      <div style={{ minHeight: '100vh', paddingBottom: '120px' }}>
        {/* Header */}
        <header className="px-4 pt-4 pb-3 sticky-top shadow-sm" style={{ backgroundColor: '#06c755', color: 'white', borderBottomLeftRadius: '24px', borderBottomRightRadius: '24px' }}>
          <div className="d-flex justify-content-between align-items-center">
            <h1 className="fw-bold mb-0" style={{ fontSize: '28px' }}>{getPageTitle()}</h1>
          </div>
        </header>

        <main className="px-4 pb-4">
          {liffError && (
            <div className="alert alert-danger mb-3">
              <p className="mb-1">LIFF Error: {liffError}</p>
              <small>Check your VITE_LIFF_ID in .env</small>
            </div>
          )}

          <Routes>
            <Route path="/" element={<FileListView />} />
            <Route path="/share" element={<ShareView />} />
            <Route path="/settings" element={<SettingsView />} />
          </Routes>
        </main>

        {/* Bottom Navigation */}
        <nav className="bottom-nav">
          <NavItem to="/" icon={FileText} label="Files" />
          <NavItem to="/share" icon={Share2} label="Share" />
          <NavItem to="/settings" icon={Settings} label="Settings" />
        </nav>
      </div>
    </UserContext.Provider>
  )
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
