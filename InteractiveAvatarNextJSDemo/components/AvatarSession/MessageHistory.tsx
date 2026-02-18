import React, { useEffect, useRef } from "react";

import { useMessageHistory, MessageSender } from "../logic";

export const MessageHistory: React.FC = () => {
  const { messages } = useMessageHistory();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;

    if (!container || messages.length === 0) return;

    container.scrollTop = container.scrollHeight;
  }, [messages]);

  return (
    <div
      ref={containerRef}
      className="w-[600px] overflow-y-auto flex flex-col gap-2 px-4 py-4 text-white self-center max-h-[200px] bg-black rounded-lg border border-gray-600"
    >
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex flex-col gap-1 max-w-[350px] ${
            message.sender === MessageSender.CLIENT
              ? "self-end items-end"
              : "self-start items-start"
          }`}
        >
          <p className="text-xs text-gray-400">
            {message.sender === MessageSender.AVATAR ? "🤖 Avatar" : "👤 You"}
          </p>
          <div className={`px-3 py-2 rounded-lg ${
            message.sender === MessageSender.CLIENT
              ? "bg-blue-600 text-white"
              : "bg-gray-700 text-white"
          }`}>
            <p className="text-sm">{message.content}</p>
          </div>
        </div>
      ))}
    </div>
  );
};
