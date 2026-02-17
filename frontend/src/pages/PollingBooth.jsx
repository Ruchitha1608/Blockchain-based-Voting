import React, { useState, useEffect, useCallback } from 'react';
import WebcamCapture from '../components/WebcamCapture';
import SessionTimeout from '../components/SessionTimeout';
import CandidateCard from '../components/CandidateCard';
import {
  authenticateFace,
  authenticateFingerprint,
  getCandidates,
  castVote
} from '../services/api';

// Helper function to extract error message from different error formats
const getErrorMessage = (err, fallback = 'An error occurred') => {
  // If err is a string, return it directly
  if (typeof err === 'string') return err;

  // If detail is a string, return it
  if (typeof err.detail === 'string') return err.detail;

  // If detail is an array (validation errors), extract first message
  if (Array.isArray(err.detail) && err.detail.length > 0) {
    return err.detail[0].msg || fallback;
  }

  // Try message property
  if (err.message) return err.message;

  // Fallback
  return fallback;
};

const STATES = {
  IDLE: 'idle',
  VOTER_ID_INPUT: 'voter_id_input',
  FACE_CAPTURE: 'face_capture',
  AUTHENTICATING: 'authenticating',
  FINGERPRINT_FALLBACK: 'fingerprint_fallback',
  CONFIRMED: 'confirmed',
  VOTING: 'voting',
  SUBMITTED: 'submitted'
};

const PollingBooth = () => {
  const [state, setState] = useState(STATES.IDLE);
  const [error, setError] = useState(null);
  const [authAttempts, setAuthAttempts] = useState(3);
  const [voterData, setVoterData] = useState(null);
  const [voterId, setVoterId] = useState('');
  const [electionId, setElectionId] = useState('ELECT-2026-001'); // Default election ID
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [txHash, setTxHash] = useState(null);
  const [fingerprintData, setFingerprintData] = useState('');
  const [sessionActive, setSessionActive] = useState(false);

  // Auto-reset to idle after success
  useEffect(() => {
    if (state === STATES.SUBMITTED) {
      const timer = setTimeout(() => {
        resetSession();
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [state]);

  const resetSession = useCallback(() => {
    setState(STATES.IDLE);
    setError(null);
    setAuthAttempts(3);
    setVoterData(null);
    setVoterId('');
    setCandidates([]);
    setSelectedCandidate(null);
    setTxHash(null);
    setFingerprintData('');
    setSessionActive(false);
  }, []);

  const handleSessionTimeout = useCallback(() => {
    setError('Session timed out. Please start again.');
    setTimeout(resetSession, 3000);
  }, [resetSession]);

  const handleStartVoting = () => {
    setState(STATES.VOTER_ID_INPUT);
    setSessionActive(true);
    setError(null);
  };

  const handleVoterIdSubmit = (e) => {
    e.preventDefault();
    if (!voterId.trim()) {
      setError('Please enter your Voter ID.');
      return;
    }
    setState(STATES.FACE_CAPTURE);
    setError(null);
  };

  const handleFaceCapture = async (faceImage) => {
    setState(STATES.AUTHENTICATING);
    setError(null);

    console.log('=== FACE AUTH DEBUG ===');
    console.log('voterId:', voterId);
    console.log('voterId type:', typeof voterId);
    console.log('voterId length:', voterId?.length);
    console.log('electionId:', electionId);
    console.log('faceImage length:', faceImage?.length);
    console.log('=======================');

    try {
      const response = await authenticateFace(voterId, faceImage, electionId);

      if (response.success || response.auth_token) {
        setVoterData({
          ...response,
          voterId: voterId,
          authToken: response.auth_token
        });
        setState(STATES.CONFIRMED);

        // Auto-transition to voting after confirmation
        setTimeout(async () => {
          const constituencyId = response.constituency_id || 'CONST-001';
          await loadCandidates(constituencyId);
        }, 2000);
      } else {
        setAuthAttempts(prev => prev - 1);

        if (authAttempts - 1 <= 0) {
          setError('Maximum authentication attempts exceeded. Please contact election officials.');
          setTimeout(resetSession, 5000);
        } else {
          setError(response.message || 'Face authentication failed. Please try again or use fingerprint.');
          setState(STATES.FINGERPRINT_FALLBACK);
        }
      }
    } catch (err) {
      console.error('Face authentication error:', err);
      const errorMsg = getErrorMessage(err, 'Authentication service error');
      setError(`${errorMsg}. Switching to fingerprint authentication.`);
      setState(STATES.FINGERPRINT_FALLBACK);
    }
  };

  const handleFingerprintAuth = async (e) => {
    e.preventDefault();

    if (!fingerprintData.trim()) {
      setError('Please enter fingerprint data.');
      return;
    }

    setState(STATES.AUTHENTICATING);
    setError(null);

    try {
      const response = await authenticateFingerprint(voterId, fingerprintData, electionId);

      if (response.success || response.auth_token) {
        setVoterData({
          ...response,
          voterId: voterId,
          authToken: response.auth_token
        });
        setState(STATES.CONFIRMED);

        // Auto-transition to voting after confirmation
        setTimeout(async () => {
          const constituencyId = response.constituency_id || 'CONST-001';
          await loadCandidates(constituencyId);
        }, 2000);
      } else {
        setAuthAttempts(prev => prev - 1);

        if (authAttempts - 1 <= 0) {
          setError('Maximum authentication attempts exceeded. Please contact election officials.');
          setTimeout(resetSession, 5000);
        } else {
          setError(response.message || 'Fingerprint authentication failed.');
          setState(STATES.FINGERPRINT_FALLBACK);
        }
      }
    } catch (err) {
      console.error('Fingerprint authentication error:', err);
      const errorMsg = getErrorMessage(err, 'Authentication service error');
      setError(`${errorMsg}. Please try again.`);
      setState(STATES.FINGERPRINT_FALLBACK);
    }
  };

  const loadCandidates = async (constituencyId) => {
    try {
      const response = await getCandidates(constituencyId);
      const candidateList = response.candidates || response || [];
      setCandidates(candidateList);
      setState(STATES.VOTING);
    } catch (err) {
      console.error('Error loading candidates:', err);
      const errorMsg = getErrorMessage(err, 'Failed to load candidates');
      setError(`${errorMsg}. Please contact election officials.`);
      setTimeout(resetSession, 5000);
    }
  };

  const handleCandidateSelect = (candidate) => {
    setSelectedCandidate(candidate);
  };

  const handleCastVote = async () => {
    if (!selectedCandidate) {
      setError('Please select a candidate.');
      return;
    }

    if (!voterData || !voterData.authToken) {
      setError('Authentication token missing. Please restart voting.');
      setTimeout(resetSession, 3000);
      return;
    }

    setError(null);

    try {
      const response = await castVote(
        selectedCandidate.candidate_id || selectedCandidate.id,
        voterData.authToken
      );

      if (response.success || response.tx_hash) {
        setTxHash(response.tx_hash || response.txHash);
        setState(STATES.SUBMITTED);
      } else {
        setError(response.message || 'Failed to cast vote. Please try again.');
      }
    } catch (err) {
      console.error('Vote casting error:', err);
      const errorMsg = getErrorMessage(err, 'Failed to submit vote');
      setError(`${errorMsg}. Please contact election officials.`);
    }
  };

  const handleRetryFaceAuth = () => {
    setState(STATES.FACE_CAPTURE);
    setError(null);
  };

  return (
    <div className="polling-booth">
      {sessionActive && state !== STATES.SUBMITTED && (
        <SessionTimeout timeout={120} onTimeout={handleSessionTimeout} />
      )}

      <div className="polling-booth-container">
        {/* IDLE STATE */}
        {state === STATES.IDLE && (
          <div className="state-content idle-state">
            <div className="icon-container">
              <svg className="vote-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h1>Voter Polling Booth</h1>
            <p>Secure blockchain-based voting system</p>
            <button className="btn-primary btn-large" onClick={handleStartVoting}>
              Start Voting
            </button>
          </div>
        )}

        {/* VOTER ID INPUT STATE */}
        {state === STATES.VOTER_ID_INPUT && (
          <div className="state-content voter-id-state">
            <h2>Enter Voter ID</h2>
            <p>Please enter your registered Voter ID to continue</p>

            <form onSubmit={handleVoterIdSubmit} style={{ width: '100%', maxWidth: '400px', margin: '20px auto' }}>
              <input
                type="text"
                value={voterId}
                onChange={(e) => setVoterId(e.target.value.trim())}
                placeholder="Enter Voter ID (e.g., TEST001)"
                style={{
                  width: '100%',
                  padding: '16px',
                  fontSize: '18px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  marginBottom: '20px',
                  textAlign: 'center',
                  textTransform: 'uppercase'
                }}
                autoFocus
              />

              {error && (
                <div className="error-message" style={{ marginBottom: '20px' }}>
                  <span className="error-icon">⚠️</span>
                  {error}
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                  Continue to Face Auth
                </button>
                <button type="button" className="btn-secondary" onClick={resetSession} style={{ flex: 1 }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* FACE CAPTURE STATE */}
        {state === STATES.FACE_CAPTURE && (
          <div className="state-content face-capture-state">
            <h2>Face Authentication</h2>
            <p>Position your face in the frame and capture when ready</p>
            <WebcamCapture onCapture={handleFaceCapture} />
            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
            <button className="btn-secondary" onClick={resetSession}>
              Cancel
            </button>
          </div>
        )}

        {/* AUTHENTICATING STATE */}
        {state === STATES.AUTHENTICATING && (
          <div className="state-content authenticating-state">
            <div className="spinner-container">
              <div className="spinner"></div>
            </div>
            <h2>Authenticating...</h2>
            <p>Please wait while we verify your identity</p>
          </div>
        )}

        {/* FINGERPRINT FALLBACK STATE */}
        {state === STATES.FINGERPRINT_FALLBACK && (
          <div className="state-content fingerprint-state">
            <h2>Fingerprint Authentication</h2>
            <p>Face authentication failed. Please use fingerprint authentication.</p>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="attempts-remaining">
              Attempts remaining: <span className="attempts-count">{authAttempts}</span>
            </div>

            <form onSubmit={handleFingerprintAuth} className="fingerprint-form">
              <div className="form-group">
                <label htmlFor="fingerprint">Fingerprint Data</label>
                <input
                  type="text"
                  id="fingerprint"
                  value={fingerprintData}
                  onChange={(e) => setFingerprintData(e.target.value)}
                  placeholder="Enter fingerprint hash"
                  className="form-input"
                />
              </div>

              <div className="button-group">
                <button type="submit" className="btn-primary">
                  Authenticate
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleRetryFaceAuth}
                >
                  Try Face Auth Again
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={resetSession}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* CONFIRMED STATE */}
        {state === STATES.CONFIRMED && (
          <div className="state-content confirmed-state">
            <div className="success-icon-container">
              <svg className="success-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2>Authentication Successful!</h2>
            {voterData && (
              <div className="voter-info">
                <p><strong>Name:</strong> {voterData.name}</p>
                <p><strong>Voter ID:</strong> {voterData.id}</p>
                <p><strong>Constituency:</strong> {voterData.constituency}</p>
              </div>
            )}
            <p className="loading-text">Loading candidates...</p>
          </div>
        )}

        {/* VOTING STATE */}
        {state === STATES.VOTING && (
          <div className="state-content voting-state">
            <h2>Cast Your Vote</h2>
            {voterData && (
              <p className="constituency-info">Constituency: {voterData.constituency}</p>
            )}

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="candidates-grid">
              {candidates.map((candidate) => (
                <CandidateCard
                  key={candidate.id}
                  candidate={candidate}
                  selected={selectedCandidate?.id === candidate.id}
                  onSelect={() => handleCandidateSelect(candidate)}
                />
              ))}
            </div>

            {candidates.length === 0 && (
              <p className="no-candidates">No candidates available for your constituency.</p>
            )}

            <div className="voting-actions">
              <button
                className="btn-primary btn-large"
                onClick={handleCastVote}
                disabled={!selectedCandidate}
              >
                Submit Vote
              </button>
              <button className="btn-secondary" onClick={resetSession}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* SUBMITTED STATE */}
        {state === STATES.SUBMITTED && (
          <div className="state-content submitted-state">
            <div className="success-icon-container">
              <svg className="success-icon animate-check" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2>Vote Submitted Successfully!</h2>
            <p>Your vote has been securely recorded on the blockchain.</p>

            {txHash && (
              <div className="tx-info">
                <p className="tx-label">Transaction Hash:</p>
                <code className="tx-hash">{txHash}</code>
              </div>
            )}

            <p className="reset-info">This booth will reset in 10 seconds...</p>

            <button className="btn-secondary" onClick={resetSession}>
              Reset Now
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        .polling-booth {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }

        .polling-booth-container {
          width: 100%;
          max-width: 1200px;
          background: white;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
          padding: 40px;
          min-height: 600px;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: slideUp 0.5s ease-out;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .state-content {
          text-align: center;
          width: 100%;
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        /* IDLE STATE */
        .idle-state {
          padding: 40px;
        }

        .icon-container {
          margin-bottom: 30px;
        }

        .vote-icon {
          width: 120px;
          height: 120px;
          color: #667eea;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.05);
            opacity: 0.8;
          }
        }

        .idle-state h1 {
          font-size: 2.5rem;
          color: #2d3748;
          margin-bottom: 10px;
        }

        .idle-state p {
          font-size: 1.2rem;
          color: #718096;
          margin-bottom: 40px;
        }

        /* BUTTONS */
        .btn-primary,
        .btn-secondary {
          padding: 15px 40px;
          border: none;
          border-radius: 10px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          margin: 10px;
        }

        .btn-primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #e2e8f0;
          color: #4a5568;
        }

        .btn-secondary:hover {
          background: #cbd5e0;
        }

        .btn-large {
          padding: 20px 60px;
          font-size: 1.3rem;
        }

        /* AUTHENTICATING STATE */
        .authenticating-state {
          padding: 60px 40px;
        }

        .spinner-container {
          margin-bottom: 30px;
        }

        .spinner {
          width: 80px;
          height: 80px;
          border: 6px solid #e2e8f0;
          border-top-color: #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .authenticating-state h2 {
          font-size: 2rem;
          color: #2d3748;
          margin-bottom: 10px;
        }

        .authenticating-state p {
          font-size: 1.1rem;
          color: #718096;
        }

        /* CONFIRMED STATE */
        .confirmed-state {
          padding: 40px;
        }

        .success-icon-container {
          margin-bottom: 30px;
        }

        .success-icon {
          width: 100px;
          height: 100px;
          color: #48bb78;
          animation: scaleIn 0.5s ease-out;
        }

        @keyframes scaleIn {
          from {
            transform: scale(0);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        .animate-check {
          animation: scaleIn 0.5s ease-out, pulse 2s infinite 0.5s;
        }

        .confirmed-state h2 {
          font-size: 2rem;
          color: #2d3748;
          margin-bottom: 20px;
        }

        .voter-info {
          background: #f7fafc;
          border-radius: 10px;
          padding: 20px;
          margin: 20px auto;
          max-width: 500px;
          text-align: left;
        }

        .voter-info p {
          margin: 10px 0;
          color: #4a5568;
          font-size: 1rem;
        }

        .loading-text {
          color: #718096;
          font-style: italic;
          margin-top: 20px;
        }

        /* FINGERPRINT STATE */
        .fingerprint-state {
          padding: 40px;
          max-width: 600px;
          margin: 0 auto;
        }

        .fingerprint-state h2 {
          font-size: 2rem;
          color: #2d3748;
          margin-bottom: 10px;
        }

        .fingerprint-state > p {
          color: #718096;
          margin-bottom: 20px;
        }

        .attempts-remaining {
          background: #fff5f5;
          border: 2px solid #fc8181;
          border-radius: 10px;
          padding: 15px;
          margin: 20px 0;
          color: #c53030;
          font-weight: 600;
        }

        .attempts-count {
          font-size: 1.5rem;
          color: #e53e3e;
        }

        .fingerprint-form {
          margin-top: 30px;
        }

        .form-group {
          margin-bottom: 25px;
          text-align: left;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          color: #4a5568;
          font-weight: 600;
        }

        .form-input {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          font-size: 1rem;
          transition: border-color 0.3s ease;
        }

        .form-input:focus {
          outline: none;
          border-color: #667eea;
        }

        .button-group {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 10px;
          margin-top: 30px;
        }

        /* VOTING STATE */
        .voting-state {
          padding: 40px 20px;
        }

        .voting-state h2 {
          font-size: 2rem;
          color: #2d3748;
          margin-bottom: 10px;
        }

        .constituency-info {
          color: #718096;
          font-size: 1.1rem;
          margin-bottom: 30px;
        }

        .candidates-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 20px;
          margin: 30px 0;
          max-height: 500px;
          overflow-y: auto;
          padding: 10px;
        }

        .no-candidates {
          color: #718096;
          font-style: italic;
          padding: 40px;
        }

        .voting-actions {
          margin-top: 30px;
          display: flex;
          justify-content: center;
          gap: 15px;
          flex-wrap: wrap;
        }

        /* SUBMITTED STATE */
        .submitted-state {
          padding: 40px;
        }

        .submitted-state h2 {
          font-size: 2rem;
          color: #2d3748;
          margin-bottom: 15px;
        }

        .submitted-state > p {
          color: #718096;
          font-size: 1.1rem;
          margin-bottom: 25px;
        }

        .tx-info {
          background: #f7fafc;
          border-radius: 10px;
          padding: 20px;
          margin: 25px auto;
          max-width: 700px;
        }

        .tx-label {
          font-weight: 600;
          color: #4a5568;
          margin-bottom: 10px;
        }

        .tx-hash {
          display: block;
          background: #2d3748;
          color: #48bb78;
          padding: 15px;
          border-radius: 8px;
          font-family: 'Courier New', monospace;
          font-size: 0.9rem;
          word-break: break-all;
          margin-top: 10px;
        }

        .reset-info {
          color: #a0aec0;
          font-style: italic;
          margin: 25px 0;
        }

        /* ERROR MESSAGE */
        .error-message {
          background: #fff5f5;
          border: 2px solid #fc8181;
          border-radius: 10px;
          padding: 15px 20px;
          margin: 20px auto;
          max-width: 600px;
          color: #c53030;
          display: flex;
          align-items: center;
          gap: 10px;
          animation: shake 0.5s ease-out;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }

        .error-icon {
          font-size: 1.5rem;
        }

        /* RESPONSIVE */
        @media (max-width: 768px) {
          .polling-booth-container {
            padding: 20px;
          }

          .idle-state h1 {
            font-size: 2rem;
          }

          .vote-icon {
            width: 80px;
            height: 80px;
          }

          .candidates-grid {
            grid-template-columns: 1fr;
          }

          .button-group {
            flex-direction: column;
          }

          .btn-primary,
          .btn-secondary {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default PollingBooth;
