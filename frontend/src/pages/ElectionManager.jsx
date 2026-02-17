import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getElections,
  createElection,
  updateElection,
  startElection,
  closeElection,
  finalizeElection,
  getResults,
  addConstituency,
  addCandidate,
} from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './ElectionManager.css';

const ElectionManager = () => {
  const navigate = useNavigate();
  const [elections, setElections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingElection, setEditingElection] = useState(null);
  const [selectedElection, setSelectedElection] = useState(null);
  const [resultsData, setResultsData] = useState(null);

  // Form states
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    startDate: '',
    endDate: '',
  });

  // Constituency form
  const [constituencyForm, setConstituencyForm] = useState({
    electionId: null,
    name: '',
    code: '',
  });

  // Candidate form
  const [candidateForm, setCandidateForm] = useState({
    electionId: null,
    constituencyId: '',
    name: '',
    party: '',
    symbol: '',
  });

  useEffect(() => {
    fetchElections();
  }, []);

  const fetchElections = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getElections();
      setElections(data);
    } catch (err) {
      console.error('Failed to fetch elections:', err);
      setError('Failed to load elections');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateElection = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);

      // Transform field names to match backend schema
      const electionData = {
        name: formData.name,
        description: formData.description,
        voting_start_at: formData.startDate || null,
        voting_end_at: formData.endDate || null,
      };

      await createElection(electionData);
      setFormData({ name: '', description: '', startDate: '', endDate: '' });
      setShowCreateForm(false);
      await fetchElections();
      alert('Election created successfully!');
    } catch (err) {
      console.error('Failed to create election:', err);
      alert('Failed to create election: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleEditElection = (election) => {
    // Populate form with election data
    setFormData({
      name: election.name,
      description: election.description || '',
      startDate: election.voting_start_at ? election.voting_start_at.slice(0, 16) : '',
      endDate: election.voting_end_at ? election.voting_end_at.slice(0, 16) : '',
    });
    setEditingElection(election);
    setShowCreateForm(true);
  };

  const handleUpdateElection = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);

      // Transform field names to match backend schema
      const electionData = {
        name: formData.name,
        description: formData.description,
        voting_start_at: formData.startDate || null,
        voting_end_at: formData.endDate || null,
      };

      await updateElection(editingElection.id, electionData);
      setFormData({ name: '', description: '', startDate: '', endDate: '' });
      setEditingElection(null);
      setShowCreateForm(false);
      await fetchElections();
      alert('Election updated successfully!');
    } catch (err) {
      console.error('Failed to update election:', err);
      alert('Failed to update election: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setFormData({ name: '', description: '', startDate: '', endDate: '' });
    setEditingElection(null);
    setShowCreateForm(false);
  };

  const handleStartElection = async (id) => {
    if (!window.confirm('Are you sure you want to start this election?')) return;
    try {
      setLoading(true);
      await startElection(id);
      await fetchElections();
      alert('Election started successfully!');
    } catch (err) {
      alert('Failed to start election: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCloseElection = async (id) => {
    if (!window.confirm('Are you sure you want to close this election?')) return;
    try {
      setLoading(true);
      await closeElection(id);
      await fetchElections();
      alert('Election closed successfully!');
    } catch (err) {
      alert('Failed to close election: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleFinalizeElection = async (id) => {
    if (!window.confirm('Are you sure you want to finalize this election? This cannot be undone.')) return;
    try {
      setLoading(true);
      await finalizeElection(id);
      await fetchElections();
      alert('Election finalized successfully!');
    } catch (err) {
      alert('Failed to finalize election: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleViewResults = async (id) => {
    try {
      setLoading(true);
      const results = await getResults(id);
      setResultsData(results);
      setSelectedElection(id);
    } catch (err) {
      alert('Failed to load results: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddConstituency = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await addConstituency(constituencyForm.electionId, {
        name: constituencyForm.name,
        code: constituencyForm.code,
      });
      setConstituencyForm({ electionId: null, name: '', code: '' });
      alert('Constituency added successfully!');
    } catch (err) {
      alert('Failed to add constituency: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddCandidate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await addCandidate(candidateForm.electionId, {
        constituency_id: candidateForm.constituencyId,
        name: candidateForm.name,
        party: candidateForm.party,
        bio: candidateForm.symbol, // Map symbol to bio field
      });
      setCandidateForm({
        electionId: null,
        constituencyId: '',
        name: '',
        party: '',
        symbol: '',
      });
      alert('Candidate added successfully!');
    } catch (err) {
      alert('Failed to add candidate: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'badge-draft',
      configured: 'badge-draft',
      active: 'badge-active',
      ended: 'badge-closed',
      finalized: 'badge-finalized',
    };
    return badges[status] || 'badge-draft';
  };

  const formatChartData = (results) => {
    if (!results || !results.constituencies) return [];

    // Flatten all candidates from all constituencies
    const allCandidates = [];
    results.constituencies.forEach(constituency => {
      if (constituency.candidates) {
        constituency.candidates.forEach(candidate => {
          allCandidates.push({
            name: `${candidate.candidate_name} (${constituency.constituency_name})`,
            votes: candidate.vote_count || 0,
            party: candidate.party,
            constituency: constituency.constituency_name
          });
        });
      }
    });

    return allCandidates;
  };

  return (
    <div className="election-manager">
      <header className="manager-header">
        <button className="btn-back" onClick={() => navigate('/admin/dashboard')}>
          ← Back to Dashboard
        </button>
        <h1>Election Manager</h1>
        <button className="btn-create" onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? 'Cancel' : '+ Create Election'}
        </button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {showCreateForm && (
        <div className="create-form-container">
          <h2>{editingElection ? 'Edit Election' : 'Create New Election'}</h2>
          <form onSubmit={editingElection ? handleUpdateElection : handleCreateElection} className="election-form">
            <div className="form-group">
              <label>Election Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., General Election 2026"
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Enter election description"
                rows="3"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="datetime-local"
                  value={formData.startDate}
                  onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>End Date</label>
                <input
                  type="datetime-local"
                  value={formData.endDate}
                  onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? (editingElection ? 'Updating...' : 'Creating...') : (editingElection ? 'Update Election' : 'Create Election')}
              </button>
              {editingElection && (
                <button type="button" className="btn-cancel" onClick={handleCancelEdit}>
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {/* Constituency Form */}
      {constituencyForm.electionId && (
        <div className="modal-overlay" onClick={() => setConstituencyForm({ electionId: null, name: '', code: '' })}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Constituency</h2>
            <form onSubmit={handleAddConstituency}>
              <div className="form-group">
                <label>Constituency Name</label>
                <input
                  type="text"
                  value={constituencyForm.name}
                  onChange={(e) => setConstituencyForm({ ...constituencyForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Constituency Code</label>
                <input
                  type="text"
                  value={constituencyForm.code}
                  onChange={(e) => setConstituencyForm({ ...constituencyForm, code: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="btn-submit">Add Constituency</button>
            </form>
          </div>
        </div>
      )}

      {/* Candidate Form */}
      {candidateForm.electionId && (
        <div className="modal-overlay" onClick={() => setCandidateForm({ electionId: null, constituencyId: '', name: '', party: '', symbol: '' })}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Candidate</h2>
            <form onSubmit={handleAddCandidate}>
              <div className="form-group">
                <label>Constituency</label>
                <select
                  value={candidateForm.constituencyId}
                  onChange={(e) => setCandidateForm({ ...candidateForm, constituencyId: e.target.value })}
                  required
                >
                  <option value="">Select Constituency</option>
                  {elections
                    .find(e => e.id === candidateForm.electionId)
                    ?.constituencies?.map(constituency => (
                      <option key={constituency.id} value={constituency.id}>
                        {constituency.name} ({constituency.code})
                      </option>
                    ))}
                </select>
              </div>
              <div className="form-group">
                <label>Candidate Name</label>
                <input
                  type="text"
                  value={candidateForm.name}
                  onChange={(e) => setCandidateForm({ ...candidateForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Party</label>
                <input
                  type="text"
                  value={candidateForm.party}
                  onChange={(e) => setCandidateForm({ ...candidateForm, party: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Symbol</label>
                <input
                  type="text"
                  value={candidateForm.symbol}
                  onChange={(e) => setCandidateForm({ ...candidateForm, symbol: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="btn-submit">Add Candidate</button>
            </form>
          </div>
        </div>
      )}

      <div className="elections-list">
        <h2>Elections</h2>
        {loading && <div className="loading-spinner">Loading...</div>}

        {!loading && elections.length === 0 && (
          <div className="empty-state">
            <p>No elections found. Create your first election!</p>
          </div>
        )}

        {!loading && elections.map((election) => (
          <div key={election.id} className="election-card">
            <div className="election-header">
              <div>
                <h3>{election.name}</h3>
                <p className="election-description">{election.description}</p>
              </div>
              <span className={`status-badge ${getStatusBadge(election.status)}`}>
                {election.status}
              </span>
            </div>

            <div className="election-dates">
              <span>Start: {election.voting_start_at ? new Date(election.voting_start_at).toLocaleString() : 'Not set'}</span>
              <span>End: {election.voting_end_at ? new Date(election.voting_end_at).toLocaleString() : 'Not set'}</span>
            </div>

            {election.stats && (
              <div className="election-stats">
                <div className="stat">
                  <span className="stat-label">Turnout:</span>
                  <span className="stat-value">{election.stats.turnout || 0}%</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Votes Cast:</span>
                  <span className="stat-value">{election.stats.votesCast || 0}</span>
                </div>
              </div>
            )}

            <div className="election-actions">
              <button
                className="btn-action btn-constituency"
                onClick={() => setConstituencyForm({ electionId: election.id, name: '', code: '' })}
              >
                Add Constituency
              </button>
              <button
                className="btn-action btn-candidate"
                onClick={() => setCandidateForm({ electionId: election.id, constituencyId: '', name: '', party: '', symbol: '' })}
              >
                Add Candidate
              </button>
              {election.status === 'draft' && (
                <>
                  <button
                    className="btn-action btn-edit"
                    onClick={() => handleEditElection(election)}
                  >
                    Edit Election
                  </button>
                  <button
                    className="btn-action btn-start"
                    onClick={() => handleStartElection(election.id)}
                  >
                    Start Election
                  </button>
                </>
              )}
              {election.status === 'active' && (
                <button
                  className="btn-action btn-close"
                  onClick={() => handleCloseElection(election.id)}
                >
                  Close Election
                </button>
              )}
              {election.status === 'ended' && (
                <button
                  className="btn-action btn-finalize"
                  onClick={() => handleFinalizeElection(election.id)}
                >
                  Finalize Election
                </button>
              )}
              <button
                className="btn-action btn-results"
                onClick={() => handleViewResults(election.id)}
              >
                View Results
              </button>
            </div>

            {selectedElection === election.id && resultsData && (
              <div className="results-section">
                <h4>Election Results</h4>

                {/* Overall Statistics */}
                <div className="results-stats">
                  <p><strong>Total Votes Cast:</strong> {resultsData.total_votes_cast || 0}</p>
                  <p><strong>Total Constituencies:</strong> {resultsData.total_constituencies || 0}</p>
                  {resultsData.turnout_percentage !== undefined && (
                    <p><strong>Turnout:</strong> {resultsData.turnout_percentage.toFixed(2)}%</p>
                  )}
                </div>

                {/* Constituency Results */}
                {resultsData.constituencies && resultsData.constituencies.map((constituency, idx) => (
                  <div key={idx} className="constituency-results">
                    <h5>{constituency.constituency_name} ({constituency.constituency_code})</h5>

                    {constituency.is_tied && (
                      <div className="tie-warning">⚠️ This constituency has a tie!</div>
                    )}

                    {constituency.winner && !constituency.is_tied && (
                      <div className="winner-announcement">
                        🏆 Winner: <strong>{constituency.winner.candidate_name}</strong> ({constituency.winner.party})
                        - {constituency.winner.vote_count} votes
                      </div>
                    )}

                    <p><strong>Total Votes:</strong> {constituency.total_votes}</p>

                    {/* Candidates table */}
                    {constituency.candidates && constituency.candidates.length > 0 && (
                      <table className="results-table">
                        <thead>
                          <tr>
                            <th>Candidate</th>
                            <th>Party</th>
                            <th>Votes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {constituency.candidates.map((candidate, cidx) => (
                            <tr key={cidx}>
                              <td>{candidate.candidate_name}</td>
                              <td>{candidate.party}</td>
                              <td><strong>{candidate.vote_count}</strong></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                ))}

                {/* Overall Chart */}
                <h5>Overall Vote Distribution</h5>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={formatChartData(resultsData)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="votes" fill="#667eea" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ElectionManager;
