import React, { useState, useEffect } from 'react';
import { TopBar } from './TopBar';
import { Skeleton } from '@/components/common/Skeleton';

interface PageWrapperProps {
  title: string;
  children: React.ReactNode;
}

export const PageWrapper: React.FC<PageWrapperProps> = ({ title, children }) => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title={title} />
      <div className="flex-1 overflow-auto bg-background">
        <div className="max-w-[1920px] mx-auto p-6">
          {loading ? (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(i => (
                  <Skeleton key={i} className="h-32" />
                ))}
              </div>
              <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2">
                  <Skeleton className="h-96" />
                </div>
                <Skeleton className="h-96" />
              </div>
            </div>
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
};
