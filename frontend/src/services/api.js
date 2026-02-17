import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    // Only add admin token if Authorization header is not already set
    if (!config.headers.Authorization) {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors and auto-refresh tokens
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refresh_token = localStorage.getItem('refresh_token');
        if (refresh_token) {
          const response = await axios.post(
            `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/auth/refresh`,
            { refresh_token }
          );

          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh token failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Authentication APIs
export const login = async (username, password) => {
  try {
    // Backend expects form data (OAuth2PasswordRequestForm)
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    const { access_token, refresh_token } = response.data;

    // Store tokens in localStorage
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const refreshToken = async () => {
  try {
    const refresh_token = localStorage.getItem('refresh_token');
    const response = await api.post('/api/auth/refresh', { refresh_token });
    const { access_token } = response.data;

    localStorage.setItem('access_token', access_token);

    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const logout = async () => {
  try {
    await api.post('/api/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    // Clear tokens regardless of API response
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

export const getCurrentUser = async () => {
  try {
    const response = await api.get('/api/auth/me');
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Voter Registration APIs
export const registerVoter = async (data) => {
  try {
    const response = await api.post('/api/voters/register', data);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getVoters = async (skip = 0, limit = 100) => {
  try {
    const response = await api.get(`/api/voters?skip=${skip}&limit=${limit}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Biometric Authentication APIs
export const authenticateFace = async (voterId, faceImage, electionId) => {
  try {
    const response = await api.post('/api/voting/authenticate/face', {
      voter_id: voterId,
      face_image: faceImage,
      election_id: electionId,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const authenticateFingerprint = async (voterId, fingerprintTemplate, electionId) => {
  try {
    const response = await api.post('/api/voting/authenticate/fingerprint', {
      voter_id: voterId,
      fingerprint_template: fingerprintTemplate,
      election_id: electionId,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Voting APIs
export const castVote = async (candidateId, authToken) => {
  try {
    const response = await api.post('/api/voting/cast', {
      candidate_id: candidateId,
    }, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getCandidates = async (constituencyId) => {
  try {
    const response = await api.get(`/api/voting/candidates/${constituencyId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const verifyVote = async (txHash) => {
  try {
    const response = await api.get(`/api/voting/verify/${txHash}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Election Management APIs
export const getElections = async () => {
  try {
    const response = await api.get('/api/elections');
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getStats = async () => {
  try {
    const response = await api.get('/api/elections/stats');
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getElection = async (id) => {
  try {
    const response = await api.get(`/api/elections/${id}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const createElection = async (data) => {
  try {
    const response = await api.post('/api/elections', data);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const updateElection = async (id, data) => {
  try {
    const response = await api.patch(`/api/elections/${id}`, data);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const startElection = async (id) => {
  try {
    const response = await api.post(`/api/elections/${id}/start`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const closeElection = async (id) => {
  try {
    const response = await api.post(`/api/elections/${id}/close`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const finalizeElection = async (id) => {
  try {
    const response = await api.post(`/api/elections/${id}/finalize`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getResults = async (electionId) => {
  try {
    const response = await api.get(`/api/elections/${electionId}/results`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Constituency APIs
export const addConstituency = async (electionId, data) => {
  try {
    const response = await api.post(`/api/elections/${electionId}/constituencies`, data);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Candidate APIs
export const addCandidate = async (electionId, data) => {
  try {
    const response = await api.post(`/api/elections/${electionId}/candidates`, data);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Audit APIs
export const getAuditLogs = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (filters.startDate) queryParams.append('startDate', filters.startDate);
    if (filters.endDate) queryParams.append('endDate', filters.endDate);
    if (filters.voterId) queryParams.append('voterId', filters.voterId);
    if (filters.outcome) queryParams.append('outcome', filters.outcome);
    if (filters.page) queryParams.append('page', filters.page);
    if (filters.limit) queryParams.append('limit', filters.limit);

    const response = await api.get(`/api/audit/logs?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getBlockchainTransactions = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (filters.voterId) queryParams.append('voterId', filters.voterId);
    if (filters.txHash) queryParams.append('txHash', filters.txHash);
    if (filters.page) queryParams.append('page', filters.page);
    if (filters.limit) queryParams.append('limit', filters.limit);

    const response = await api.get(`/api/audit/blockchain?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const exportAuditLogs = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (filters.startDate) queryParams.append('startDate', filters.startDate);
    if (filters.endDate) queryParams.append('endDate', filters.endDate);
    if (filters.voterId) queryParams.append('voterId', filters.voterId);
    if (filters.outcome) queryParams.append('outcome', filters.outcome);

    const response = await api.get(`/api/audit/export?${queryParams.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export default api;
