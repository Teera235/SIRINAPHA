import React, { useState } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { mockAlerts } from '@/data/mockAlerts';
import { formatRelativeTime } from '@/utils/formatters';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { X } from 'lucide-react';

export const AlertManagementPage: React.FC = () => {
  const [filterSeverity] = useState<string[]>([]);
  const [filterType] = useState<string[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [sortColumn, setSortColumn] = useState<string>('detectedAt');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [showModal, setShowModal] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<string | null>(null);
  
  // Use selectedAlert to prevent TypeScript warning
  console.log('Selected alert:', selectedAlert);
  const [notes, setNotes] = useState('');

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger';
      case 'high': return 'warning';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const filteredAlerts = mockAlerts.filter(alert => {
    if (filterSeverity.length > 0 && !filterSeverity.includes(alert.severity)) return false;
    if (filterType.length > 0 && !filterType.includes(alert.alertType)) return false;
    if (filterStatus === 'acknowledged' && !alert.isAcknowledged) return false;
    if (filterStatus === 'unacknowledged' && alert.isAcknowledged) return false;
    return true;
  });

  const sortedAlerts = [...filteredAlerts].sort((a, b) => {
    let aVal: any = a[sortColumn as keyof typeof a];
    let bVal: any = b[sortColumn as keyof typeof b];
    
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }
    
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const alertsByType = mockAlerts.reduce((acc, alert) => {
    acc[alert.alertType] = (acc[alert.alertType] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const typeData = Object.entries(alertsByType).map(([type, count]) => ({ type, count }));

  const alertsBySeverity = mockAlerts.reduce((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const severityData = Object.entries(alertsBySeverity).map(([severity, count]) => ({ severity, count }));

  const handleAcknowledge = (alertId: string) => {
    setSelectedAlert(alertId);
    setShowModal(true);
  };

  const confirmAcknowledge = () => {
    if (notes.length >= 10) {
      setShowModal(false);
      setNotes('');
      setSelectedAlert(null);
    }
  };

  return (
    <PageWrapper title="Alert Management">
      <div className="space-y-6">
        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-4 mb-4">
            <div>
              <label className="text-sm font-medium text-text-primary block mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">All</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="unacknowledged">Unacknowledged</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th
                    className="text-center py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('severity')}
                  >
                    Severity {sortColumn === 'severity' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('zoneName')}
                  >
                    Zone {sortColumn === 'zoneName' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">Type</th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('deltaNDVI')}
                  >
                    Delta NDVI {sortColumn === 'deltaNDVI' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('affectedAreaRai')}
                  >
                    Affected (rai) {sortColumn === 'affectedAreaRai' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left py-3 px-4 text-sm font-semibold text-text-primary cursor-pointer hover:bg-neutral-50"
                    onClick={() => handleSort('detectedAt')}
                  >
                    Detected {sortColumn === 'detectedAt' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">Status</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedAlerts.map((alert, index) => (
                  <tr
                    key={alert.alertId}
                    className={`border-b border-neutral-100 ${
                      index % 2 === 0 ? 'bg-white' : 'bg-neutral-50/50'
                    }`}
                  >
                    <td className="py-3 px-4 text-center">
                      <Badge variant={getSeverityVariant(alert.severity)} size="sm">
                        {alert.severity.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-sm text-text-primary">{alert.zoneName}</td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant="default" size="sm">{alert.alertType}</Badge>
                    </td>
                    <td className="py-3 px-4 text-sm text-danger text-right">
                      {alert.deltaNDVI.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-sm text-text-primary text-right">
                      {alert.affectedAreaRai.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-sm text-text-secondary">
                      {formatRelativeTime(alert.detectedAt)}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {alert.isAcknowledged ? (
                        <span className="text-success">Acknowledged by {alert.acknowledgedBy}</span>
                      ) : (
                        <span className="text-warning">Pending</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {!alert.isAcknowledged && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAcknowledge(alert.alertId)}
                          >
                            Acknowledge
                          </Button>
                        )}
                        <Button size="sm" variant="ghost">View on Map</Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-surface rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Alerts by Type</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="type" tick={{ fontSize: 12 }} stroke="#6B7280" />
                <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" />
                <Tooltip />
                <Bar dataKey="count" fill="#2B7BBF" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-surface rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Alerts by Severity</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={severityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="severity" tick={{ fontSize: 12 }} stroke="#6B7280" />
                <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" />
                <Tooltip />
                <Bar dataKey="count" fill="#C05621" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-surface rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Alert Statistics</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary">Total Alerts</div>
              <div className="text-2xl font-bold text-text-primary">{mockAlerts.length}</div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary">Acknowledged</div>
              <div className="text-2xl font-bold text-success">
                {mockAlerts.filter(a => a.isAcknowledged).length}
              </div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary">Pending</div>
              <div className="text-2xl font-bold text-warning">
                {mockAlerts.filter(a => !a.isAcknowledged).length}
              </div>
            </div>
            <div className="p-4 bg-neutral-50 rounded-lg">
              <div className="text-sm text-text-secondary">Avg Response Time</div>
              <div className="text-2xl font-bold text-text-primary">18 hours</div>
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Acknowledge Alert</h3>
              <button onClick={() => setShowModal(false)} className="text-text-secondary hover:text-text-primary">
                <X size={20} />
              </button>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-text-primary mb-2">
                Notes (minimum 10 characters)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                rows={4}
                placeholder="Enter acknowledgment notes..."
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
              <Button onClick={confirmAcknowledge} disabled={notes.length < 10}>
                Confirm Acknowledgment
              </Button>
            </div>
          </div>
        </div>
      )}
    </PageWrapper>
  );
};
