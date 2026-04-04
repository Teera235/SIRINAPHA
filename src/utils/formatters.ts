export const formatNumber = (value: number, decimals: number = 0): string => {
  return value.toLocaleString('th-TH', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatNDVI = (value: number): string => {
  return value.toFixed(4);
};

export const formatArea = (value: number): string => {
  return `${formatNumber(value, 2)} rai`;
};

export const formatCurrency = (value: number): string => {
  return `${formatNumber(value)} Baht`;
};

export const formatPercentage = (value: number): string => {
  return `${formatNumber(value, 1)}%`;
};

export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 30) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
};
