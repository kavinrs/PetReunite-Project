// src/chat/types.ts
export interface ChatMessage {
  id: string;
  content: string;
  timestamp: Date;
  userId: string;
  userName: string;
}

export interface ChatRoom {
  id: string;
  name: string;
  participants: string[];
  messages: ChatMessage[];
}

export interface WebSocketMessage {
  type: 'message' | 'join' | 'leave' | 'error';
  data: any;
}