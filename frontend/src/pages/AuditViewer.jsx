import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuditLogs, getBlockchainTransactions, exportAuditLogs } from '../services/api';
import './AuditViewer.css';

const AuditViewer = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('auth');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Auth logs state
  const [authLogs, setAuthLogs] = useState([]);
  const [authFilters, setAuthFilters] = useState({
    startDate: '',
    endDate: '',
    voterId: '',
    outcome: '',
    page: 1,
    limit: 10,
  });
  const [authPagination, setAuthPagination] = useState({
    total: 0,
    pages: 0,
    currentPage: 1,
  });

  // Blockchain transactions state
  const [transactions, setTransactions] = useState([]);
  const [txFilters, setTxFilters] = useState({
    voterId: '',
    txHash: '',
    page: 1,
    limit: 10,
  });
  const [txPagination, setTxPagination] = useState({
    total: 0,
    pages: 0,
    currentPage: 1,
  });

  useEffect(() => {
    if (activeTab === 'auth') {
      fetchAuthLogs();
    } else {
      fetchTransactions();
    }
  }, [activeTab, authFilters.page, txFilters.page]);

  const fetchAuthLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAuditLogs(authFilters);

      // Handle response structure
      if (response.logs) {
        setAuthLogs(response.logs);
        setAuthPagination({
          total: response.total || response.logs.length,
          pages: response.pages || Math.ceil((response.total || response.logs.length) / authFilters.limit),
          currentPage: response.page || authFilters.page,
        });
      } else {
        // If response is just an array
        setAuthLogs(response);
        setAuthPagination({
          total: response.length,
          pages: 1,
          currentPage: 1,
        });
      }
    } catch (err) {
      console.error('Failed to fetch auth logs:', err);
      setError('Failed to load authentication logs');
      setAuthLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getBlockchainTransactions(txFilters);

      // Handle response structure
      if (response.transactions) {
        setTransactions(response.transactions);
        setTxPagination({
          total: response.total || response.transactions.length,
          pages: response.pages || Math.ceil((response.total || response.transactions.length) / txFilters.limit),
          currentPage: response.page || txFilters.page,
        });
      } else {
        // If response is just an array
        setTransactions(response);
        setTxPagination({
          total: response.length,
          pages: 1,
          currentPage: 1,
        });
      }
    } catch (err) {
      console.error('Failed to fetch blockchain transactions:', err);
      setError('Failed to load blockchain transactions');
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthFilterChange = (key, value) => {
    setAuthFilters({
      ...authFilters,
      [key]: value,
      page: 1, // Reset to first page when filters change
    });
  };

  const handleTxFilterChange = (key, value) => {
    setTxFilters({
      ...txFilters,
      [key]: value,
      page: 1, // Reset to first page when filters change
    });
  };

  const handleApplyAuthFilters = () => {
    setAuthFilters({ ...authFilters, page: 1 });
    fetchAuthLogs();
  };

  const handleApplyTxFilters = () => {
    setTxFilters({ ...txFilters, page: 1 });
    fetchTransactions();
  };

  const handleExportCSV = async () => {
    try {
      setLoading(true);
      const blob = await exportAuditLogs(authFilters);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert('Audit logs exported successfully!');
    } catch (err) {
      console.error('Failed to export logs:', err);
      alert('Failed to export audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleAuthPageChange = (newPage) => {
    setAuthFilters({ ...authFilters, page: newPage });
  };

  const handleTxPageChange = (newPage) => {
    setTxFilters({ ...txFilters, page: newPage });
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getOutcomeBadge = (outcome) => {
    return outcome === 'success' ? 'badge-success' : 'badge-failure';
  };

  return (
    <div className="audit-viewer">
      <header className="audit-header">
        <button className="btn-back" onClick={() => navigate('/admin/dashboard')}>
          ← Back to Dashboard
        </button>
        <h1>Audit Viewer</h1>
        {activeTab === 'auth' && (
          <button className="btn-export" onClick={handleExportCSV} disabled={loading}>
            Export to CSV
          </button>
        )}
      </header>

      <div className="audit-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'auth' ? 'active' : ''}`}
            onClick={() => setActiveTab('auth')}
          >
            Authentication Logs
          </button>
          <button
            className={`tab ${activeTab === 'blockchain' ? 'active' : ''}`}
            onClick={() => setActiveTab('blockchain')}
          >
            Blockchain Transactions
          </button>
        </div>

        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)} className="btn-close-error">×</button>
          </div>
        )}

        {/* Authentication Logs Tab */}
        {activeTab === 'auth' && (
          <div className="tab-content">
            <div className="filters-section">
              <h3>Filters</h3>
              <div className="filters-grid">
                <div className="filter-group">
                  <label>Start Date</label>
                  <input
                    type="datetime-local"
                    value={authFilters.startDate}
                    onChange={(e) => handleAuthFilterChange('startDate', e.target.value)}
                  />
                </div>

                <div className="filter-group">
                  <label>End Date</label>
                  <input
                    type="datetime-local"
                    value={authFilters.endDate}
                    onChange={(e) => handleAuthFilterChange('endDate', e.target.value)}
                  />
                </div>

                <div className="filter-group">
                  <label>Voter ID</label>
                  <input
                    type="text"
                    value={authFilters.voterId}
                    onChange={(e) => handleAuthFilterChange('voterId', e.target.value)}
                    placeholder="Enter voter ID"
                  />
                </div>

                <div className="filter-group">
                  <label>Outcome</label>
                  <select
                    value={authFilters.outcome}
                    onChange={(e) => handleAuthFilterChange('outcome', e.target.value)}
                  >
                    <option value="">All</option>
                    <option value="success">Success</option>
                    <option value="failure">Failure</option>
                  </select>
                </div>
              </div>

              <button className="btn-apply-filters" onClick={handleApplyAuthFilters}>
                Apply Filters
              </button>
            </div>

            {loading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading authentication logs...</p>
              </div>
            ) : (
              <>
                <div className="table-container">
                  <table className="audit-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Voter ID</th>
                        <th>Method</th>
                        <th>Outcome</th>
                        <th>IP Address</th>
                      </tr>
                    </thead>
                    <tbody>
                      {authLogs.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="empty-row">
                            No authentication logs found
                          </td>
                        </tr>
                      ) : (
                        authLogs.map((log, index) => (
                          <tr key={log.id || index}>
                            <td>{formatTimestamp(log.timestamp)}</td>
                            <td>{log.voter_id || log.voterId}</td>
                            <td>
                              <span className="method-badge">{log.method}</span>
                            </td>
                            <td>
                              <span className={`outcome-badge ${getOutcomeBadge(log.outcome)}`}>
                                {log.outcome}
                              </span>
                            </td>
                            <td>{log.ip_address || log.ipAddress || 'N/A'}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {authPagination.pages > 1 && (
                  <div className="pagination">
                    <button
                      onClick={() => handleAuthPageChange(authPagination.currentPage - 1)}
                      disabled={authPagination.currentPage === 1}
                      className="btn-page"
                    >
                      Previous
                    </button>
                    <span className="page-info">
                      Page {authPagination.currentPage} of {authPagination.pages}
                    </span>
                    <button
                      onClick={() => handleAuthPageChange(authPagination.currentPage + 1)}
                      disabled={authPagination.currentPage === authPagination.pages}
                      className="btn-page"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Blockchain Transactions Tab */}
        {activeTab === 'blockchain' && (
          <div className="tab-content">
            <div className="filters-section">
              <h3>Search</h3>
              <div className="filters-grid">
                <div className="filter-group">
                  <label>Voter ID</label>
                  <input
                    type="text"
                    value={txFilters.voterId}
                    onChange={(e) => handleTxFilterChange('voterId', e.target.value)}
                    placeholder="Enter voter ID"
                  />
                </div>

                <div className="filter-group">
                  <label>Transaction Hash</label>
                  <input
                    type="text"
                    value={txFilters.txHash}
                    onChange={(e) => handleTxFilterChange('txHash', e.target.value)}
                    placeholder="Enter transaction hash"
                  />
                </div>
              </div>

              <button className="btn-apply-filters" onClick={handleApplyTxFilters}>
                Search
              </button>
            </div>

            {loading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading blockchain transactions...</p>
              </div>
            ) : (
              <>
                <div className="table-container">
                  <table className="audit-table">
                    <thead>
                      <tr>
                        <th>Transaction Hash</th>
                        <th>Voter ID</th>
                        <th>Timestamp</th>
                        <th>Block Number</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.length === 0 ? (
                        <tr>
                          <td colSpan="4" className="empty-row">
                            No blockchain transactions found
                          </td>
                        </tr>
                      ) : (
                        transactions.map((tx, index) => (
                          <tr key={tx.id || index}>
                            <td className="tx-hash">{tx.tx_hash || tx.txHash}</td>
                            <td>{tx.voter_id || tx.voterId}</td>
                            <td>{formatTimestamp(tx.timestamp)}</td>
                            <td>{tx.block_number || tx.blockNumber || 'Pending'}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {txPagination.pages > 1 && (
                  <div className="pagination">
                    <button
                      onClick={() => handleTxPageChange(txPagination.currentPage - 1)}
                      disabled={txPagination.currentPage === 1}
                      className="btn-page"
                    >
                      Previous
                    </button>
                    <span className="page-info">
                      Page {txPagination.currentPage} of {txPagination.pages}
                    </span>
                    <button
                      onClick={() => handleTxPageChange(txPagination.currentPage + 1)}
                      disabled={txPagination.currentPage === txPagination.pages}
                      className="btn-page"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditViewer;
