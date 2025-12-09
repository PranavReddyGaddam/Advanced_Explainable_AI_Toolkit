import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { HeatmapProps } from '../types';

const Heatmap: React.FC<HeatmapProps> = ({ 
  tokens, 
  scores 
}) => {
  // Prepare data for Recharts BarChart
  const data = tokens.map((token, index) => ({
    token: token,
    score: scores[index] || 0,
    index: index
  }));

  // Enhanced color scale with gradients
  const getColor = (score: number) => {
    if (score > 0.8) return '#dc2626'; // red-600 (more vibrant)
    if (score > 0.6) return '#ea580c'; // orange-600
    if (score > 0.4) return '#ca8a04'; // yellow-600
    if (score > 0.2) return '#65a30d'; // lime-600
    return '#16a34a'; // green-600
  };

  // Enhanced tooltip with more info
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const score = payload[0].value;
      const percentile = ((score * 100).toFixed(1));
      return (
        <div className="bg-gray-900/95 backdrop-blur-md border border-white/30 rounded-xl p-4 text-white shadow-2xl">
          <p className="font-bold text-lg mb-2">Token Analysis</p>
          <p className="text-sm mb-1"><span className="text-gray-400">Token:</span> {payload[0].payload.token}</p>
          <p className="text-sm mb-1"><span className="text-gray-400">Score:</span> {score.toFixed(4)}</p>
          <p className="text-sm"><span className="text-gray-400">Percentile:</span> {percentile}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <div className="mb-4">
        <h4 className="text-lg font-bold text-white mb-2">Token Importance Distribution</h4>
        <p className="text-sm text-white/70">Showing {data.length} tokens with importance scores</p>
      </div>
      
      <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart 
            data={data} 
            layout="horizontal"
            margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
            barCategoryGap="8%"
          >
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#16a34a" stopOpacity={0.8}/>
                <stop offset="25%" stopColor="#65a30d" stopOpacity={0.8}/>
                <stop offset="50%" stopColor="#ca8a04" stopOpacity={0.8}/>
                <stop offset="75%" stopColor="#ea580c" stopOpacity={0.8}/>
                <stop offset="100%" stopColor="#dc2626" stopOpacity={0.8}/>
              </linearGradient>
            </defs>
            
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="rgba(255,255,255,0.08)" 
              vertical={false}
            />
            
            <XAxis 
              dataKey="token" 
              angle={-45} 
              textAnchor="end" 
              height={100}
              tick={{ fill: 'white', fontSize: 11, fontWeight: 500 }}
              stroke="rgba(255,255,255,0.2)"
              interval={0}
            />
            
            <YAxis 
              tick={{ fill: 'white', fontSize: 11 }}
              stroke="rgba(255,255,255,0.2)"
              domain={[0, 1]}
              label={{ value: 'Importance Score', angle: -90, position: 'insideLeft', fill: 'white', style: { fontSize: 12 } }}
            />
            
            <ReferenceLine y={0.5} stroke="rgba(255,255,255,0.3)" strokeDasharray="5 5" />
            <ReferenceLine y={0.8} stroke="rgba(239,68,68,0.5)" strokeDasharray="3 3" />
            
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.1)' }} />
            
            <Bar 
              dataKey="score" 
              radius={[6, 6, 0, 0]}
              animationDuration={1000}
              animationBegin={0}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={getColor(entry.score)}
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth={1}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Enhanced Legend */}
      <div className="mt-6 bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10">
        <h5 className="text-sm font-semibold text-white mb-3">Importance Scale</h5>
        <div className="grid grid-cols-5 gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-600 rounded shadow-lg"></div>
            <span className="text-white/80">Low (0-0.2)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-lime-600 rounded shadow-lg"></div>
            <span className="text-white/80">Med-Low (0.2-0.4)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-600 rounded shadow-lg"></div>
            <span className="text-white/80">Medium (0.4-0.6)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-600 rounded shadow-lg"></div>
            <span className="text-white/80">Med-High (0.6-0.8)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-600 rounded shadow-lg"></div>
            <span className="text-white/80">High (0.8-1.0)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Heatmap;
