import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, logout, getElections, getStats } from '../services/api';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({
    totalElections: 0,
    activeVoters: 0,
    totalVotes: 0,
    activeElections: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch current user
      const userData = await getCurrentUser();
      setUser(userData);

      // Check if user has admin role (any valid admin role)
      const validRoles = ['super_admin', 'election_administrator', 'polling_officer', 'auditor'];
      if (!validRoles.includes(userData.role)) {
        navigate('/login');
        return;
      }

      // Fetch dashboard stats from backend
      const statsData = await getStats();

      // Update stats with real data from backend
      setStats({
        totalElections: statsData.total_elections || 0,
        activeElections: statsData.active_elections || 0,
        activeVoters: statsData.registered_voters || 0,
        totalVotes: statsData.total_votes || 0,
      });
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setError('Failed to load dashboard data');

      // If authentication fails, redirect to login
      if (err.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
      // Force navigation even if logout fails
      navigate('/login');
    }
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-dashboard">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={fetchDashboardData} className="btn-retry">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* Mobile Menu Toggle */}
      <button
        className="mobile-menu-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle menu"
      >
        <span className={`hamburger ${sidebarOpen ? 'open' : ''}`}>
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Admin Panel</h2>
          <p className="admin-username">{user?.username || 'Admin'}</p>
        </div>

        <nav className="sidebar-nav">
          <button
            className="nav-item active"
            onClick={() => {
              navigate('/admin/dashboard');
              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">📊</span>
            Dashboard
          </button>
          <button
            className="nav-item"
            onClick={() => {
              navigate('/admin/elections');
              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">🗳️</span>
            Election Manager
          </button>
          <button
            className="nav-item"
            onClick={() => {
              navigate('/admin/voters');
              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">👤</span>
            Voter Registration
          </button>
          <button
            className="nav-item"
            onClick={() => {
              navigate('/admin/audit');
              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">📋</span>
            Audit Viewer
          </button>
        </nav>

        <div className="sidebar-footer">
          <button className="btn-logout" onClick={handleLogout}>
            <span className="nav-icon">🚪</span>
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="content-header">
          <h1>Welcome, {user?.username || 'Admin'}!</h1>
          <p className="subtitle">Manage your voting system from this dashboard</p>
        </header>

        <div className="stats-grid">
          <button
            className="stat-card card-blue clickable"
            onClick={() => navigate('/admin/elections')}
            title="Click to view all elections"
          >
            <div className="stat-icon">🗳️</div>
            <div className="stat-content">
              <h3>{stats.totalElections}</h3>
              <p>Total Elections</p>
            </div>
          </button>

          <button
            className="stat-card card-green clickable"
            onClick={() => navigate('/admin/elections')}
            title="Click to view active elections"
          >
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h3>{stats.activeElections}</h3>
              <p>Active Elections</p>
            </div>
          </button>

          <button
            className="stat-card card-purple clickable"
            onClick={() => navigate('/admin/voters')}
            title="Click to view registered voters"
          >
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>{stats.activeVoters}</h3>
              <p>Registered Voters</p>
            </div>
          </button>

          <button
            className="stat-card card-orange clickable"
            onClick={() => navigate('/admin/audit')}
            title="Click to view voting details"
          >
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <h3>{stats.totalVotes}</h3>
              <p>Total Votes Cast</p>
            </div>
          </button>
        </div>

        <div className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <button
              className="action-card"
              onClick={() => navigate('/admin/elections')}
            >
              <span className="action-icon">➕</span>
              <h3>Create Election</h3>
              <p>Set up a new election</p>
            </button>

            <button
              className="action-card"
              onClick={() => navigate('/admin/voters')}
            >
              <span className="action-icon">👤</span>
              <h3>Register Voter</h3>
              <p>Add a new voter to the system</p>
            </button>

            <button
              className="action-card"
              onClick={() => navigate('/admin/audit')}
            >
              <span className="action-icon">🔍</span>
              <h3>View Audit Logs</h3>
              <p>Monitor system activity</p>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
