// src/components/ChatWidget.tsx
import React from 'react';

interface ChatWidgetProps {
  className?: string;
  style?: React.CSSProperties;
  adoptionRequestId?: number;
  petName?: string;
  petId?: string | number;
  status?: "pending" | "approved" | "rejected";
  onClose?: () => void;
  embedded?: boolean;
}

export function ChatWidget({ className, style, adoptionRequestId, petName, petId, status, onClose, embedded }: ChatWidgetProps) {
  return (
    <div className={className} style={style}>
      {/* Chat widget placeholder */}
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Chat widget not available
      </div>
    </div>
  );
}

export default ChatWidget;
