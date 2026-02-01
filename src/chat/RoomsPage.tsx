// src/chat/RoomsPage.tsx
import React from 'react';

interface RoomsPageProps {
  className?: string;
}

export function RoomsPage({ className }: RoomsPageProps) {
  return (
    <div className={className}>
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Chat Rooms</h2>
        <p>Chat functionality is not available in this deployment.</p>
      </div>
    </div>
  );
}

export default RoomsPage;
