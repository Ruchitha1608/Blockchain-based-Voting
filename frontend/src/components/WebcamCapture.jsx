import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';

const WebcamCapture = ({ onCapture, width = 640, height = 480 }) => {
  const webcamRef = useRef(null);
  const [countdown, setCountdown] = useState(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);

  const handleUserMedia = useCallback(() => {
    setPermissionDenied(false);
  }, []);

  const handleUserMediaError = useCallback(() => {
    setPermissionDenied(true);
  }, []);

  const startCountdown = useCallback(() => {
    if (isCapturing) return;

    setIsCapturing(true);
    let count = 3;
    setCountdown(count);

    const timer = setInterval(() => {
      count -= 1;
      if (count > 0) {
        setCountdown(count);
      } else {
        clearInterval(timer);
        setCountdown(null);

        // Capture the image
        if (webcamRef.current) {
          const imageSrc = webcamRef.current.getScreenshot();
          if (imageSrc && onCapture) {
            onCapture(imageSrc);
          }
        }

        setIsCapturing(false);
      }
    }, 1000);
  }, [onCapture, isCapturing]);

  return (
    <div style={styles.container}>
      <div style={styles.webcamWrapper}>
        {permissionDenied ? (
          <div style={styles.errorContainer}>
            <div style={styles.errorIcon}>⚠️</div>
            <h3 style={styles.errorTitle}>Camera Access Denied</h3>
            <p style={styles.errorText}>
              Please grant camera permissions to capture your photo.
            </p>
          </div>
        ) : (
          <>
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              width={width}
              height={height}
              videoConstraints={{
                width,
                height,
                facingMode: 'user',
              }}
              onUserMedia={handleUserMedia}
              onUserMediaError={handleUserMediaError}
              style={styles.webcam}
            />
            {countdown !== null && (
              <div style={styles.countdownOverlay}>
                <div style={styles.countdownNumber}>{countdown}</div>
              </div>
            )}
          </>
        )}
      </div>

      <button
        onClick={startCountdown}
        disabled={permissionDenied || isCapturing}
        style={{
          ...styles.captureButton,
          ...(permissionDenied || isCapturing ? styles.captureButtonDisabled : {}),
        }}
      >
        {isCapturing ? 'Capturing...' : 'Capture Photo'}
      </button>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px',
    padding: '20px',
  },
  webcamWrapper: {
    position: 'relative',
    borderRadius: '12px',
    overflow: 'hidden',
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
    backgroundColor: '#1a1a1a',
  },
  webcam: {
    display: 'block',
    borderRadius: '12px',
  },
  countdownOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    animation: 'pulse 1s ease-in-out',
  },
  countdownNumber: {
    fontSize: '120px',
    fontWeight: 'bold',
    color: '#ffffff',
    textShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
    animation: 'scaleIn 1s ease-in-out',
  },
  captureButton: {
    padding: '14px 32px',
    fontSize: '16px',
    fontWeight: '600',
    color: '#ffffff',
    backgroundColor: '#4CAF50',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
    transition: 'all 0.3s ease',
    minWidth: '160px',
  },
  captureButtonDisabled: {
    backgroundColor: '#cccccc',
    cursor: 'not-allowed',
    boxShadow: 'none',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 40px',
    backgroundColor: '#2a2a2a',
    color: '#ffffff',
    minWidth: '640px',
    minHeight: '480px',
  },
  errorIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  errorTitle: {
    margin: '0 0 12px 0',
    fontSize: '24px',
    fontWeight: '600',
  },
  errorText: {
    margin: 0,
    fontSize: '16px',
    color: '#cccccc',
    textAlign: 'center',
    maxWidth: '400px',
  },
};

export default WebcamCapture;
