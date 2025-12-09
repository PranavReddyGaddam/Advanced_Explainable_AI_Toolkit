import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface FlowNode {
  id: string;
  type: 'input' | 'connector' | 'card';
  x?: number;
  y?: number;
  label?: string;
  subtitle?: string;
  stats?: {
    positive?: number;
    negative?: number;
  };
  color?: string;
}

interface FlowLink {
  source: string | FlowNode;
  target: string | FlowNode;
  color: string;
}

interface LandingFlowGraphProps {
  width?: number;
  height?: number;
  nodes?: FlowNode[];
  links?: FlowLink[];
}

const LandingFlowGraph: React.FC<LandingFlowGraphProps> = ({ 
  width = 800, 
  height = 400,
  nodes: propNodes,
  links: propLinks
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  // Default data structure (can be overridden by props)
  const defaultNodes: FlowNode[] = [
    // Input box (left side)
    {
      id: 'input',
      type: 'input',
      x: width * 0.125, // Responsive positioning
      y: height / 2,
      label: 'Input Text',
      color: '#6B47FF'
    },
    // Connector nodes (small circles)
    {
      id: 'connector1',
      type: 'connector',
      x: width * 0.375,
      y: height / 2 - height * 0.15,
      color: '#6B47FF'
    },
    {
      id: 'connector2',
      type: 'connector',
      x: width * 0.375,
      y: height / 2,
      color: '#CFCFCF'
    },
    {
      id: 'connector3',
      type: 'connector',
      x: width * 0.375,
      y: height / 2 + height * 0.15,
      color: '#CFCFCF'
    },
    // Cards (right side)
    {
      id: 'card1',
      type: 'card',
      x: width * 0.625,
      y: height / 2 - height * 0.2,
      label: 'Token Analysis',
      subtitle: 'Feature importance scoring',
      stats: { positive: 85, negative: 15 },
      color: '#6B47FF'
    },
    {
      id: 'card2',
      type: 'card',
      x: width * 0.625,
      y: height / 2,
      label: 'Attention Flow',
      subtitle: 'Neural pathway visualization',
      stats: { positive: 72, negative: 28 },
      color: '#CFCFCF'
    },
    {
      id: 'card3',
      type: 'card',
      x: width * 0.625,
      y: height / 2 + height * 0.2,
      label: 'Causal Analysis',
      subtitle: 'Cause-effect relationships',
      stats: { positive: 91, negative: 9 },
      color: '#CFCFCF'
    }
  ];

  const defaultLinks: FlowLink[] = [
    { source: 'input', target: 'connector1', color: '#6B47FF' },
    { source: 'input', target: 'connector2', color: '#CFCFCF' },
    { source: 'input', target: 'connector3', color: '#CFCFCF' },
    { source: 'connector1', target: 'card1', color: '#6B47FF' },
    { source: 'connector2', target: 'card2', color: '#CFCFCF' },
    { source: 'connector3', target: 'card3', color: '#CFCFCF' }
  ];

  const nodes = propNodes || defaultNodes;
  const links = propLinks || defaultLinks;

  useEffect(() => {
    if (!svgRef.current) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Create curved path generator
    const curvedPath = d3.linkHorizontal()
      .x((d: any) => d.x)
      .y((d: any) => d.y)
      .source((d: any) => {
        const sourceNode = nodes.find(n => n.id === d.source);
        return [sourceNode?.x ?? 0, sourceNode?.y ?? 0] as [number, number];
      })
      .target((d: any) => {
        const targetNode = nodes.find(n => n.id === d.target);
        return [targetNode?.x ?? 0, targetNode?.y ?? 0] as [number, number];
      });

    // Draw connections
    svg.selectAll('.connection')
      .data(links)
      .enter()
      .append('path')
      .attr('class', 'connection')
      .attr('d', curvedPath as any)
      .attr('fill', 'none')
      .attr('stroke', (d: FlowLink) => d.color)
      .attr('stroke-width', 2)
      .attr('opacity', 0.8);

    // Draw nodes
    const nodeGroups = svg.selectAll('.node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d: FlowNode) => `translate(${d.x}, ${d.y})`);

    // Draw input box
    nodeGroups.filter((d: FlowNode) => d.type === 'input')
      .append('rect')
      .attr('x', -60)
      .attr('y', -20)
      .attr('width', 120)
      .attr('height', 40)
      .attr('rx', 8)
      .attr('fill', '#6B47FF')
      .attr('stroke', 'none');

    nodeGroups.filter((d: FlowNode) => d.type === 'input')
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '14px')
      .attr('font-weight', '500')
      .attr('font-family', 'Aeonik, sans-serif')
      .text((d: FlowNode) => d.label ?? '');

    // Draw connector circles
    nodeGroups.filter((d: FlowNode) => d.type === 'connector')
      .append('circle')
      .attr('r', 8)
      .attr('fill', (d: FlowNode) => d.color ?? '#6B47FF')
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    // Draw cards
    const cardGroups = nodeGroups.filter((d: FlowNode) => d.type === 'card');
    
    cardGroups.append('rect')
      .attr('x', -80)
      .attr('y', -25)
      .attr('width', 160)
      .attr('height', 50)
      .attr('rx', 12)
      .attr('fill', 'white')
      .attr('stroke', '#E5E7EB')
      .attr('stroke-width', 1)
      .attr('filter', 'url(#cardShadow)')
      .style('cursor', 'pointer')
      .on('mouseenter', function() {
        d3.select(this)
          .attr('filter', 'url(#cardShadowHover)');
      })
      .on('mouseleave', function() {
        d3.select(this)
          .attr('filter', 'url(#cardShadow)');
      });

    // Card titles
    cardGroups.append('text')
      .attr('x', -70)
      .attr('y', -8)
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', 'black')
      .attr('font-family', 'Aeonik, sans-serif')
      .text((d: FlowNode) => d.label ?? '');

    // Card subtitles
    cardGroups.append('text')
      .attr('x', -70)
      .attr('y', 6)
      .attr('font-size', '10px')
      .attr('fill', '#6B7280')
      .attr('font-family', 'Aeonik, sans-serif')
      .text((d: FlowNode) => d.subtitle ?? '');

    // Card stats
    cardGroups.append('text')
      .attr('x', -70)
      .attr('y', 18)
      .attr('font-size', '10px')
      .attr('font-weight', '500')
      .attr('fill', '#32B768')
      .attr('font-family', 'Aeonik, sans-serif')
      .text((d: FlowNode) => `+${d.stats?.positive ?? 0}%`);

    cardGroups.append('text')
      .attr('x', -40)
      .attr('y', 18)
      .attr('font-size', '10px')
      .attr('font-weight', '500')
      .attr('fill', '#E14242')
      .attr('font-family', 'Aeonik, sans-serif')
      .text((d: FlowNode) => `-${d.stats?.negative ?? 0}%`);

    // Add shadows
    const defs = svg.append('defs');
    
    defs.append('filter')
      .attr('id', 'cardShadow')
      .html(`
        <feDropShadow dx="0" dy="2" stdDeviation="4" flood-opacity="0.1"/>
      `);

    defs.append('filter')
      .attr('id', 'cardShadowHover')
      .html(`
        <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.15"/>
      `);

  }, [width, height, nodes, links]);

  return (
    <div className="flex justify-center items-center bg-white rounded-xl">
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default LandingFlowGraph;
