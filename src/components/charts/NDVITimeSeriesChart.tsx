import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { NDVIObservation } from '@/types';

interface NDVITimeSeriesChartProps {
  data: NDVIObservation[];
  title?: string;
}

export const NDVITimeSeriesChart: React.FC<NDVITimeSeriesChartProps> = ({ data, title }) => {
  return (
    <div className="bg-surface rounded-lg p-6 shadow-sm">
      {title && <h3 className="text-lg font-semibold text-text-primary mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="ndviGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2D7A4F" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#2D7A4F" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            stroke="#6B7280"
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 12 }}
            stroke="#6B7280"
            label={{ value: 'NDVI', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
            }}
            formatter={(value: number) => value.toFixed(4)}
          />
          <ReferenceLine y={0.5} stroke="#2D7A4F" strokeDasharray="3 3" label="Healthy" />
          <ReferenceLine y={0.3} stroke="#C53030" strokeDasharray="3 3" label="Degraded" />
          <Area
            type="monotone"
            dataKey="meanNDVI"
            stroke="#2D7A4F"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#ndviGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
