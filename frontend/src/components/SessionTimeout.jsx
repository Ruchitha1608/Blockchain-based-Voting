import React, { useState, useEffect, useCallback, useRef } from 'react';

const SessionTimeout = ({ timeoutSeconds = 120, onTimeout }) => {
  const [remainingTime, setRemainingTime] = useState(timeoutSeconds);
  const [showWarning, setShowWarning] = useState(false);
  const timerRef = useRef(null);
  const lastActivityRef = useRef(Date.now());

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();
    setRemainingTime(timeoutSeconds);
    setShowWarning(false);
  }, [timeoutSeconds]);

  const handleActivity = useCallback(() => {
    resetTimer();
  }, [resetTimer]);

  useEffect(() => {
    // Add event listeners for user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    events.forEach(event => {
      document.addEventListener(event, handleActivity);
    });

    // Start the countdown timer
    timerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - lastActivityRef.current) / 1000);
      const remaining = timeoutSeconds - elapsed;

      if (remaining <= 0) {
        clearInterval(timerRef.current);
        if (onTimeout) {
          onTimeout();
        }
      } else {
        setRemainingTime(remaining);
        setShowWarning(remaining <= 30);
      }
    }, 1000);

    // Cleanup
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [timeoutSeconds, onTimeout, handleActivity]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!showWarning) {
    return null;
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.iconContainer}>
          <span style={styles.icon}>⏰</span>
        </div>
        <h2 style={styles.title}>Session Timeout Warning</h2>
        <p style={styles.message}>
          Your session will expire due to inactivity in:
        </p>
        <div style={styles.timeDisplay}>
          {formatTime(remainingTime)}
        </div>
        <p style={styles.subMessage}>
          Move your mouse or press any key to continue your session.
        </p>
        <button onClick={resetTimer} style={styles.button}>
          Continue Session
        </button>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10000,
    backdropFilter: 'blur(4px)',
  },
  modal: {
    backgroundColor: '#ffffff',
    borderRadius: '16px',
    padding: '40px',
    maxWidth: '480px',
    width: '90%',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
    textAlign: 'center',
    animation: 'slideIn 0.3s ease-out',
  },
  iconContainer: {
    marginBottom: '20px',
  },
  icon: {
    fontSize: '64px',
    display: 'inline-block',
    animation: 'pulse 2s infinite',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a1a1a',
  },
  message: {
    margin: '0 0 24px 0',
    fontSize: '16px',
    color: '#666666',
    lineHeight: '1.5',
  },
  timeDisplay: {
    fontSize: '56px',
    fontWeight: 'bold',
    color: '#FF5722',
    fontFamily: 'monospace',
    marginBottom: '24px',
    textShadow: '0 2px 8px rgba(255, 87, 34, 0.2)',
    letterSpacing: '4px',
  },
  subMessage: {
    margin: '0 0 32px 0',
    fontSize: '14px',
    color: '#999999',
    lineHeight: '1.5',
  },
  button: {
    padding: '14px 32px',
    fontSize: '16px',
    fontWeight: '600',
    color: '#ffffff',
    backgroundColor: '#2196F3',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(33, 150, 243, 0.3)',
    transition: 'all 0.3s ease',
    minWidth: '180px',
  },
};

// Add CSS animations
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.1);
      }
    }
  `;
  document.head.appendChild(style);
}

export default SessionTimeout;
