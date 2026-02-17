import React from 'react';

const CandidateCard = ({ candidate, selected = false, onSelect }) => {
  const { id, name, party, age, image_url } = candidate;

  const handleClick = () => {
    if (onSelect) {
      onSelect(candidate);
    }
  };

  return (
    <div
      onClick={handleClick}
      style={{
        ...styles.card,
        ...(selected ? styles.cardSelected : {}),
      }}
    >
      {selected && (
        <div style={styles.selectedBadge}>
          <span style={styles.checkmark}>✓</span>
        </div>
      )}

      <div style={styles.imageContainer}>
        {image_url ? (
          <img
            src={image_url}
            alt={name}
            style={styles.image}
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" font-size="64" font-family="Arial" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3E%3F%3C/text%3E%3C/svg%3E';
            }}
          />
        ) : (
          <div style={styles.imagePlaceholder}>
            <span style={styles.placeholderIcon}>👤</span>
          </div>
        )}
      </div>

      <div style={styles.content}>
        <h3 style={styles.name}>{name}</h3>

        <div style={styles.details}>
          <div style={styles.detailItem}>
            <span style={styles.detailLabel}>Party:</span>
            <span style={styles.detailValue}>{party}</span>
          </div>

          <div style={styles.detailItem}>
            <span style={styles.detailLabel}>Age:</span>
            <span style={styles.detailValue}>{age}</span>
          </div>
        </div>

        <div style={styles.partyBadge}>
          {party}
        </div>
      </div>

      {selected && <div style={styles.selectedOverlay} />}
    </div>
  );
};

const styles = {
  card: {
    position: 'relative',
    backgroundColor: '#ffffff',
    borderRadius: '16px',
    overflow: 'hidden',
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    border: '3px solid transparent',
    width: '100%',
    maxWidth: '320px',
    '@media (hover: hover)': {
      ':hover': {
        transform: 'translateY(-4px)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
      },
    },
  },
  cardSelected: {
    borderColor: '#4CAF50',
    boxShadow: '0 8px 24px rgba(76, 175, 80, 0.3)',
    transform: 'translateY(-4px)',
  },
  selectedBadge: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    backgroundColor: '#4CAF50',
    borderRadius: '50%',
    width: '40px',
    height: '40px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 2px 8px rgba(76, 175, 80, 0.4)',
    zIndex: 10,
  },
  checkmark: {
    color: '#ffffff',
    fontSize: '24px',
    fontWeight: 'bold',
  },
  imageContainer: {
    width: '100%',
    height: '280px',
    overflow: 'hidden',
    backgroundColor: '#f5f5f5',
  },
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e0e0e0',
  },
  placeholderIcon: {
    fontSize: '96px',
    color: '#999999',
  },
  content: {
    padding: '24px',
  },
  name: {
    margin: '0 0 16px 0',
    fontSize: '24px',
    fontWeight: '700',
    color: '#1a1a1a',
    lineHeight: '1.3',
  },
  details: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginBottom: '16px',
  },
  detailItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  detailLabel: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#666666',
  },
  detailValue: {
    fontSize: '14px',
    color: '#1a1a1a',
    fontWeight: '500',
  },
  partyBadge: {
    display: 'inline-block',
    padding: '6px 16px',
    backgroundColor: '#2196F3',
    color: '#ffffff',
    fontSize: '13px',
    fontWeight: '600',
    borderRadius: '20px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  selectedOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
    pointerEvents: 'none',
  },
};

export default CandidateCard;
