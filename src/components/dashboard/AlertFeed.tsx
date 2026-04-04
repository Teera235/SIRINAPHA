import React from 'react';
import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import { DegradationAlert } from '@/types';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { formatRelativeTime } from '@/utils/formatters';
import { getSeverityColor } from '@/utils/colorScales';

interface AlertFeedProps {
  alerts: DegradationAlert[];
  onAcknowledge?: (alertId: string) => void;
}

export const AlertFeed: React.FC<AlertFeedProps> = ({ alerts, onAcknowledge }) => {
  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger';
      case 'high': return 'warning';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'encroachment': return 'Encroachment';
      case 'deforestation': return 'Deforestation';
      case 'die_off': return 'Die-off';
      case 'anomaly': return 'Anomaly';
      default: return type;
    }
  };

  return (
    <div className="bg-surface rounded-lg shadow-sm">
      <div className="p-4 border-b border-neutral-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-text-primary">Recent Alerts</h3>
          <Badge variant="danger" size="sm">{alerts.length}</Badge>
        </div>
        <Link to="/alerts" className="text-sm text-primary hover:underline">
          View All
        </Link>
      </div>

      <div className="max-h-[600px] overflow-y-auto">
        {alerts.map((alert) => (
          <div
            key={alert.alertId}
            className="p-4 border-b border-neutral-200 last:border-b-0 hover:bg-neutral-50 transition-colors"
          >
            <div className="flex gap-3">
              <div
                className="w-1 rounded-full flex-shrink-0"
                style={{ backgroundColor: getSeverityColor(alert.severity) }}
              />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="font-medium text-text-primary">{alert.zoneName}</div>
                  <div className="text-xs text-text-secondary whitespace-nowrap">
                    {formatRelativeTime(alert.detectedAt)}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-2">
                  <Badge variant={getSeverityVariant(alert.severity)} size="sm">
                    {alert.severity.toUpperCase()}
                  </Badge>
                  <Badge variant="default" size="sm">
                    {getAlertTypeLabel(alert.alertType)}
                  </Badge>
                </div>

                <div className="text-sm text-text-secondary mb-2">
                  <div>Delta NDVI: {alert.deltaNDVI.toFixed(2)}</div>
                  <div>Affected: {alert.affectedAreaRai.toFixed(2)} rai</div>
                </div>

                {alert.isAcknowledged ? (
                  <div className="flex items-center gap-1 text-xs text-success">
                    <Check size={14} />
                    <span>Acknowledged by {alert.acknowledgedBy}</span>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onAcknowledge?.(alert.alertId)}
                  >
                    Acknowledge
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
