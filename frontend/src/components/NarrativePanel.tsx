import React, { useState, useEffect } from 'react';
import { NarrativePanelProps } from '../types';

const NarrativePanel: React.FC<NarrativePanelProps> = ({ 
  narrative, 
  metadata 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [highlightedTokens, setHighlightedTokens] = useState<string[]>([]);

  useEffect(() => {
    // Extract tokens mentioned in narrative for highlighting
    if (narrative) {
      const tokenRegex = /'([^']+)'/g;
      const matches = narrative.match(tokenRegex) || [];
      const tokens = matches.map(match => match.replace(/'/g, ''));
      setHighlightedTokens(tokens);
    }
  }, [narrative]);

  const formatNarrative = (text: string): JSX.Element[] => {
    // Split narrative by sentences and format
    const sentences = text.split('. ').filter(s => s.trim());
    
    return sentences.map((sentence, index) => {
      // Highlight tokens in quotes
      const tokenRegex = /'([^']+)'/g;
      const parts: JSX.Element[] = [];
      let lastIndex = 0;
      let match;

      while ((match = tokenRegex.exec(sentence)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
          parts.push(
            <span key={`text-${index}-${lastIndex}`}>
              {sentence.substring(lastIndex, match.index)}
            </span>
          );
        }

        // Add highlighted token
        const token = match[1];
        parts.push(
          <span 
            key={`token-${index}-${match.index}`}
            style={{
              backgroundColor: '#ffeb3b',
              padding: '2px 4px',
              borderRadius: '3px',
              fontWeight: 'bold',
              color: '#000'
            }}
          >
            {token}
          </span>
        );

        lastIndex = tokenRegex.lastIndex;
      }

      // Add remaining text
      if (lastIndex < sentence.length) {
        parts.push(
          <span key={`text-${index}-${lastIndex}`}>
            {sentence.substring(lastIndex)}
          </span>
        );
      }

      return (
        <p key={index} style={{ 
          marginBottom: '12px', 
          lineHeight: '1.6',
          textAlign: 'justify'
        }}>
          {parts.length > 0 ? parts : sentence}.
        </p>
      );
    });
  };

  const formatExecutionTime = (seconds?: number): string => {
    if (!seconds) return 'N/A';
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    if (seconds < 60) return `${seconds.toFixed(2)}s`;
    return `${(seconds / 60).toFixed(2)}min`;
  };

  const getMethodIcon = (method: string): string => {
    const icons: Record<string, string> = {
      'lime': 'LIME',
      'shap': 'SHAP',
      'inseq': 'InSeq',
      'gaf': 'GAF',
      'contrast_cat': 'ContrastCAT',
      'attribution_patching': 'Attr Patching',
      'slalom': 'SLALOM'
    };
    return icons[method] || 'Method';
  };

  const getCapabilityBadge = (available: boolean): JSX.Element => {
    return (
      <span
        style={{
          padding: '2px 6px',
          borderRadius: '12px',
          fontSize: '10px',
          fontWeight: 'bold',
          backgroundColor: available ? '#4caf50' : '#f44336',
          color: 'white'
        }}
      >
        {available ? '✓' : '✗'}
      </span>
    );
  };

  return (
    <div className="bg-white border border-gray-300 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div 
        className="p-4 lg:p-5 bg-gray-50 border-b border-gray-300 cursor-pointer flex justify-between items-center"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <h3 className="m-0 text-base font-bold">
            Explanation Summary
          </h3>
          {metadata && (
            <span className="text-sm">
              {getMethodIcon(metadata.method_params?.method || 'unknown')}
            </span>
          )}
        </div>
        <span className="text-sm text-gray-600 transition-transform duration-200"
          aria-hidden="true"
          style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
        >
          ▾
        </span>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-5">
          {/* Narrative Content */}
          <div className="mb-6">
            <h4 className="m-0 mb-3 text-sm text-gray-700 font-semibold">
              Natural Language Explanation
            </h4>
            <div className="text-sm text-gray-900 leading-relaxed">
              {narrative ? formatNarrative(narrative) : (
                <p className="italic text-gray-600">
                  No narrative explanation available.
                </p>
              )}
            </div>
          </div>

          {/* Metadata Section */}
          {metadata && (
            <div className="mb-5">
              <h4 className="m-0 mb-3 text-sm text-gray-700 font-semibold">
                Execution Details
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                <div className="p-2 lg:p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <strong>Execution Time:</strong> {formatExecutionTime(metadata.execution_time)}
                </div>
                
                <div className="p-2 lg:p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <strong>Samples Used:</strong> {metadata.num_samples || 'N/A'}
                </div>
                
                <div className="p-2 lg:p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <strong>Method:</strong> {metadata.method_params?.method || 'unknown'}
                </div>
              </div>
            </div>
          )}

          {/* Model Capabilities */}
          {metadata?.model_capabilities && (
            <div className="mb-5">
              <h4 className="m-0 mb-3 text-sm text-gray-700 font-semibold">
                Model Capabilities
              </h4>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                <div className="flex justify-between items-center p-1.5 lg:p-2.5 bg-gray-50 rounded-lg border border-gray-200">
                  <span>Logprobs</span>
                  {getCapabilityBadge(metadata.model_capabilities.logprobs)}
                </div>
                
                <div className="flex justify-between items-center p-1.5 lg:p-2.5 bg-gray-50 rounded-lg border border-gray-200">
                  <span>Attention Weights</span>
                  {getCapabilityBadge(metadata.model_capabilities.attention_weights)}
                </div>
                
                <div className="flex justify-between items-center p-1.5 lg:p-2.5 bg-gray-50 rounded-lg border border-gray-200">
                  <span>Hidden States</span>
                  {getCapabilityBadge(metadata.model_capabilities.hidden_states)}
                </div>
                
                <div className="flex justify-between items-center p-1.5 lg:p-2.5 bg-gray-50 rounded-lg border border-gray-200">
                  <span>Gradients</span>
                  {getCapabilityBadge(metadata.model_capabilities.gradients)}
                </div>
              </div>
            </div>
          )}

          {/* Highlighted Tokens */}
          {highlightedTokens.length > 0 && (
            <div>
              <h4 className="m-0 mb-2 text-sm text-gray-700 font-semibold">
                Key Tokens Mentioned
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {highlightedTokens.map((token, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-yellow-200 border border-yellow-400 rounded-full text-xs font-bold text-black"
                  >
                    {token}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NarrativePanel;
