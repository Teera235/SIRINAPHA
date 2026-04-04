import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color: string;
  progressBar?: {
    value: number;
    color: string;
  };
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color,
  progressBar,
}) => {
  return (
    <div className={`bg-surface rounded-lg p-6 border-l-4 shadow-sm`} style={{ borderLeftColor: color }}>
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-full`} style={{ backgroundColor: `${color}20` }}>
          <Icon size={24} style={{ color }} />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm ${trend.isPositive ? 'text-success' : 'text-danger'}`}>
            {trend.isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      
      <div className="text-3xl font-bold text-text-primary mb-1">{value}</div>
      <div className="text-sm text-text-secondary">{title}</div>
      
      {subtitle && (
        <div className="text-xs text-text-secondary mt-2">{subtitle}</div>
      )}
      
      {progressBar && (
        <div className="mt-4">
          <div className="w-full bg-neutral-200 rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all"
              style={{ width: `${progressBar.value}%`, backgroundColor: progressBar.color }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
