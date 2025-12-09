import React from 'react';
import NodeGraph from './NodeGraph';
import { Explanation } from '../types';

interface ResultsSplitViewProps {
  explanation: Explanation | null;
}

const ResultsSplitView: React.FC<ResultsSplitViewProps> = ({ explanation }) => {
  if (!explanation) return null;

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left: Attention Flow Graph */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-white mb-3">Attention Flow</h3>
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 h-full min-h-[400px] overflow-hidden relative">
          {explanation.graphs?.attention_flow ? (
            <NodeGraph graphData={explanation.graphs.attention_flow} width={400} height={350} />
          ) : (
            <div className="flex items-center justify-center h-full text-white/60">
              <div className="text-center">
                <div className="mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <p>No attention flow data available</p>
                <p className="text-sm mt-2">This method doesn't generate graph visualizations</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right: AI Response */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-white mb-3">AI Response</h3>
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 h-full min-h-[400px] overflow-y-auto">
          <div className="space-y-4">
            {/* Model and Method Info */}
            <div className="flex items-center space-x-4 text-sm text-white/80">
              <div className="flex items-center space-x-2">
                <span className="font-medium">Model:</span>
                <span className="bg-cyan-500/20 text-cyan-300 px-2 py-1 rounded">
                  {explanation.model}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-medium">Method:</span>
                <span className="bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                  {explanation.method?.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Output Text */}
            <div className="space-y-2">
              <h4 className="text-lg font-semibold text-white">Generated Explanation</h4>
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <p className="text-white/90 leading-relaxed whitespace-pre-wrap">
                  {explanation.output_text || 'No response text available'}
                </p>
              </div>
            </div>

            {/* Narrative */}
            {explanation.narrative && (
              <div className="space-y-2">
                <h4 className="text-lg font-semibold text-white">Analysis Summary</h4>
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <p className="text-white/80 text-sm leading-relaxed">
                    {explanation.narrative}
                  </p>
                </div>
              </div>
            )}

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
              <div className="text-center">
                <div className="text-2xl font-bold text-cyan-400">
                  {explanation.tokens?.length || 0}
                </div>
                <div className="text-sm text-white/60">Tokens Analyzed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {explanation.scores?.length || 0}
                </div>
                <div className="text-sm text-white/60">Importance Scores</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsSplitView;
