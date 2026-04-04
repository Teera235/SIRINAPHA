export const getHealthColor = (status: 'healthy' | 'stressed' | 'degraded'): string => {
  switch (status) {
    case 'healthy':
      return '#2D7A4F';
    case 'stressed':
      return '#D69E2E';
    case 'degraded':
      return '#C53030';
  }
};

export const getHealthFillColor = (status: 'healthy' | 'stressed' | 'degraded'): string => {
  switch (status) {
    case 'healthy':
      return 'rgba(45, 122, 79, 0.4)';
    case 'stressed':
      return 'rgba(214, 158, 46, 0.4)';
    case 'degraded':
      return 'rgba(197, 48, 48, 0.4)';
  }
};

export const getSeverityColor = (severity: 'low' | 'medium' | 'high' | 'critical'): string => {
  switch (severity) {
    case 'low':
      return '#2B7BBF';
    case 'medium':
      return '#D69E2E';
    case 'high':
      return '#C05621';
    case 'critical':
      return '#C53030';
  }
};

export const getFSIColor = (score: number): string => {
  if (score > 0.7) return '#2D7A4F';
  if (score > 0.4) return '#D69E2E';
  return '#C53030';
};

export const getVerificationColor = (status: string): string => {
  switch (status) {
    case 'measured':
      return '#4A5568';
    case 'reported':
      return '#2B7BBF';
    case 'verified':
      return '#D69E2E';
    case 'issued':
      return '#2D7A4F';
    default:
      return '#4A5568';
  }
};
