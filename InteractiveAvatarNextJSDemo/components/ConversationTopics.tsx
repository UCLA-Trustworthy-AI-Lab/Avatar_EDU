"use client";

import { useState } from 'react';
import { Button } from './Button';

interface ConversationTopicsProps {
  onTopicSelect: (topic: string) => void;
  selectedTopic: string;
  disabled?: boolean;
}

export const CONVERSATION_TOPICS = [
  {
    id: 'general',
    name: 'General Conversation',
    description: 'Open-ended conversation about anything',
    icon: '💬'
  },
  {
    id: 'daily_life',
    name: 'Daily Life & Experiences',
    description: 'Talk about your daily activities and experiences',
    icon: '🌅'
  },
  {
    id: 'academic',
    name: 'Academic & Studies',
    description: 'Discuss academic topics and learning',
    icon: '📚'
  },
  {
    id: 'business',
    name: 'Business & Professional',
    description: 'Practice professional communication',
    icon: '💼'
  },
  {
    id: 'travel',
    name: 'Travel & Culture',
    description: 'Explore different cultures and travel experiences',
    icon: '✈️'
  }
];

export function ConversationTopics({ onTopicSelect, selectedTopic, disabled = false }: ConversationTopicsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800">Choose Conversation Topic</h3>
        <Button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm"
          disabled={disabled}
        >
          {isExpanded ? 'Hide Topics' : 'Show All Topics'}
        </Button>
      </div>

      {isExpanded ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {CONVERSATION_TOPICS.map((topic) => (
            <button
              key={topic.id}
              onClick={() => {
                onTopicSelect(topic.id);
                setIsExpanded(false);
              }}
              disabled={disabled}
              className={`p-4 rounded-lg border-2 text-left transition-all duration-200 ${
                selectedTopic === topic.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="flex items-start space-x-3">
                <span className="text-2xl">{topic.icon}</span>
                <div>
                  <h4 className="font-medium text-gray-900">{topic.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{topic.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {CONVERSATION_TOPICS.map((topic) => (
            <button
              key={topic.id}
              onClick={() => onTopicSelect(topic.id)}
              disabled={disabled}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                selectedTopic === topic.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {topic.icon} {topic.name}
            </button>
          ))}
        </div>
      )}

      {selectedTopic && (
        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Selected:</strong>{' '}
            {CONVERSATION_TOPICS.find(t => t.id === selectedTopic)?.description}
          </p>
        </div>
      )}
    </div>
  );
}