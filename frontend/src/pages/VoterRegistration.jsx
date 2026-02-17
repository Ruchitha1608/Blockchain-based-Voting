import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerVoter, getElections, getVoters } from '../services/api';
import WebcamCapture from '../components/WebcamCapture';
import './VoterRegistration.css';

const VoterRegistration = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [constituencies, setConstituencies] = useState([]);
  const [voters, setVoters] = useState([]);
  const [activeTab, setActiveTab] = useState('list'); // 'list' or 'register'

  const [formData, setFormData] = useState({
    voter_id: '',
    full_name: '',
    date_of_birth: '',
    constituency_id: '',
  });

  const [faceImage, setFaceImage] = useState(null);
  const [fingerprintTemplate, setFingerprintTemplate] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  // Fetch constituencies and voters on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch constituencies
        const elections = await getElections();
        const allConstituencies = elections.flatMap(e => e.constituencies || []);
        setConstituencies(allConstituencies);

        // Fetch voters
        const votersData = await getVoters();
        setVoters(votersData);
      } catch (err) {
        console.error('Failed to fetch data:', err);
      }
    };
    fetchData();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleFaceCapture = (imageSrc) => {
    setFaceImage(imageSrc);
    setShowPreview(true);
  };

  const handleRetakePhoto = () => {
    setFaceImage(null);
    setShowPreview(false);
  };

  const dataURLtoFile = (dataurl, filename) => {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!faceImage) {
      setError('Please capture a face image');
      return;
    }

    // Fingerprint is now optional
    // if (!fingerprintTemplate.trim()) {
    //   setError('Please provide a fingerprint template');
    //   return;
    // }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      // Calculate age from date of birth
      const birthDate = new Date(formData.date_of_birth);
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }

      // Validate age
      if (age < 0) {
        setError('Invalid date of birth. Please enter a date in the past, not the future.');
        setLoading(false);
        return;
      }

      if (age < 18) {
        setError(`Voter must be at least 18 years old. Current age: ${age}`);
        setLoading(false);
        return;
      }

      // Send JSON data with base64 images
      const data = {
        voter_id: formData.voter_id,
        full_name: formData.full_name,
        age: age,
        constituency_id: formData.constituency_id,
        face_image: faceImage,  // Already base64
      };

      // Only include fingerprint if provided
      if (fingerprintTemplate && fingerprintTemplate.trim()) {
        data.fingerprint_image = fingerprintTemplate;
      }

      const response = await registerVoter(data);

      setSuccess({
        message: 'Voter registered successfully!',
        blockchain_voter_id: response.blockchain_voter_id || response.voterId,
      });

      // Clear form
      setFormData({
        voter_id: '',
        full_name: '',
        date_of_birth: '',
        constituency_id: '',
      });
      setFaceImage(null);
      setFingerprintTemplate('');
      setShowPreview(false);

      // Refresh voter list
      const votersData = await getVoters();
      setVoters(votersData);

      // Switch to list tab to show the newly registered voter
      setTimeout(() => {
        setActiveTab('list');
        setSuccess(null);
      }, 2000);
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.message || 'Failed to register voter');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="voter-registration">
      <header className="registration-header">
        <button className="btn-back" onClick={() => navigate('/admin/dashboard')}>
          ← Back to Dashboard
        </button>
        <h1>Voter Management</h1>
      </header>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          📋 Registered Voters ({voters.length})
        </button>
        <button
          className={`tab ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => setActiveTab('register')}
        >
          ➕ Register New Voter
        </button>
      </div>

      {/* Voter List Tab */}
      {activeTab === 'list' && (
        <div className="voter-list-container">
          <div className="voter-list-header">
            <h2>Registered Voters</h2>
            <button
              className="btn-register-new"
              onClick={() => setActiveTab('register')}
            >
              ➕ Register New Voter
            </button>
          </div>

          <div className="table-container">
            <table className="voters-table">
              <thead>
                <tr>
                  <th>Voter ID</th>
                  <th>Full Name</th>
                  <th>Age</th>
                  <th>Constituency</th>
                  <th>Has Voted</th>
                  <th>Registered At</th>
                </tr>
              </thead>
              <tbody>
                {voters.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-row">
                      No voters registered yet
                    </td>
                  </tr>
                ) : (
                  voters.map((voter) => (
                    <tr key={voter.id}>
                      <td className="voter-id">{voter.voter_id}</td>
                      <td>{voter.full_name}</td>
                      <td>{voter.age}</td>
                      <td>{voter.constituency?.name || 'N/A'}</td>
                      <td>
                        <span className={`status-badge ${voter.has_voted ? 'voted' : 'not-voted'}`}>
                          {voter.has_voted ? '✓ Voted' : '✗ Not Voted'}
                        </span>
                      </td>
                      <td>{new Date(voter.registered_at).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Registration Form Tab */}
      {activeTab === 'register' && (
        <div className="registration-container">
          {success && (
          <div className="success-banner">
            <h3>{success.message}</h3>
            <p>Blockchain Voter ID: <strong>{success.blockchain_voter_id}</strong></p>
            <button onClick={() => setSuccess(null)} className="btn-dismiss">
              Dismiss
            </button>
          </div>
        )}

        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)} className="btn-close-error">×</button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="registration-form">
          <div className="form-section">
            <h2>Personal Information</h2>

            <div className="form-group">
              <label htmlFor="voter_id">Voter ID <span className="required">*</span></label>
              <input
                type="text"
                id="voter_id"
                name="voter_id"
                value={formData.voter_id}
                onChange={handleInputChange}
                placeholder="Enter unique voter ID"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="full_name">Full Name <span className="required">*</span></label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                placeholder="Enter full name"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="date_of_birth">Date of Birth <span className="required">*</span></label>
                <input
                  type="date"
                  id="date_of_birth"
                  name="date_of_birth"
                  value={formData.date_of_birth}
                  onChange={handleInputChange}
                  max={new Date().toISOString().split('T')[0]}
                  required
                />
                <p className="field-hint">Voter must be at least 18 years old</p>
              </div>

              <div className="form-group">
                <label htmlFor="constituency_id">Constituency <span className="required">*</span></label>
                <select
                  id="constituency_id"
                  name="constituency_id"
                  value={formData.constituency_id}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select Constituency</option>
                  {constituencies.map(constituency => (
                    <option key={constituency.id} value={constituency.id}>
                      {constituency.name} ({constituency.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Biometric Data</h2>

            <div className="biometric-section">
              <h3>Face Image <span className="required">*</span></h3>
              {!showPreview ? (
                <WebcamCapture onCapture={handleFaceCapture} width={400} height={300} />
              ) : (
                <div className="image-preview">
                  <img src={faceImage} alt="Captured face" />
                  <button
                    type="button"
                    className="btn-retake"
                    onClick={handleRetakePhoto}
                  >
                    Retake Photo
                  </button>
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="fingerprintTemplate">
                Fingerprint Template <span className="optional">(Optional - for testing without scanner)</span>
              </label>
              <textarea
                id="fingerprintTemplate"
                value={fingerprintTemplate}
                onChange={(e) => setFingerprintTemplate(e.target.value)}
                placeholder="Optional: Paste fingerprint template data here or leave blank"
                rows="6"
              />
              <p className="field-hint">
                Enter the fingerprint template data obtained from the fingerprint scanner
              </p>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn-cancel"
              onClick={() => navigate('/admin/dashboard')}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-submit"
              disabled={loading}
            >
              {loading ? 'Registering...' : 'Register Voter'}
            </button>
          </div>
        </form>
        </div>
      )}
    </div>
  );
};

export default VoterRegistration;
