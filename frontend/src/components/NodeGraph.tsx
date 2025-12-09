import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { NodeGraphProps, SimulationNode, SimulationLink } from '../types';

const NodeGraph: React.FC<NodeGraphProps> = ({ 
  graphData, 
  width = 800, 
  height = 600 
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<SimulationNode | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    if (!svgRef.current || !graphData || graphData.nodes.length === 0) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();
    
    // Remove any existing tooltips
    d3.selectAll('.node-tooltip').remove();

    // Set up dimensions
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create SVG with zoom capability
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoomLevel(event.transform.k);
      });

    svg.call(zoom);

    // Prepare data for simulation
    const nodes: SimulationNode[] = graphData.nodes.map(node => ({ ...node }));
    const links: SimulationLink[] = graphData.edges.map(edge => ({ ...edge }));

    // Create force simulation
    const simulation = d3.forceSimulation<SimulationNode>(nodes)
      .force('link', d3.forceLink<SimulationNode, SimulationLink>(links)
        .id(d => d.id)
        .distance(100)
        .strength(d => (d.weight || 0.5) * 2))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(innerWidth / 2, innerHeight / 2))
      .force('collision', d3.forceCollide().radius(20)); // Reduced from 30 for smaller nodes

    // Create scales for visual properties
    const nodeSizeScale = d3.scaleLinear()
      .domain([0, 1])
      .range([6, 15]); // Reduced from [10, 30] for smaller nodes

    const edgeWidthScale = d3.scaleLinear()
      .domain([0, 1])
      .range([1, 4]); // Reduced from [1, 8] for thinner edges

    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

    // Create tooltip within the container
    const tooltip = d3.select('body').append('div')
      .attr('class', 'node-tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '11px')
      .style('max-width', '180px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');

    // Create arrow markers for directed edges
    svg.append('defs').selectAll('marker')
      .data(['end'])
      .enter().append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // Draw edges
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => edgeWidthScale(d.weight || 0.5))
      .attr('marker-end', 'url(#arrow)');

    // Draw nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter().append('g')
      .style('cursor', 'pointer')
      .call(d3.drag<SVGGElement, SimulationNode>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded) as any);

    // Add circles for nodes
    node.append('circle')
      .attr('r', d => nodeSizeScale(d.importance || 0.5))
      .attr('fill', d => colorScale(d.node_type || 'default'))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('mouseover', function(this: any, event: any, d: any) {
        d3.select(this)
          .attr('stroke-width', 4)
          .attr('stroke', '#ff6b6b');
        
        // Highlight connected edges
        link.style('stroke', l => 
          (l.source as SimulationNode).id === d.id || (l.target as SimulationNode).id === d.id 
            ? '#ff6b6b' : '#999'
        ).style('stroke-width', l => 
          (l.source as SimulationNode).id === d.id || (l.target as SimulationNode).id === d.id 
            ? edgeWidthScale((l.weight || 0.5) * 1.5) : edgeWidthScale(l.weight || 0.5)
        );
        
        tooltip.transition()
          .duration(200)
          .style('opacity', 0.95);
        
        const tooltipContent = `
          <strong>${d.label || d.id}</strong><br/>
          Type: ${d.node_type || 'unknown'}<br/>
          Importance: ${(d.importance || 0).toFixed(3)}<br/>
          Layer: ${d.layer || 'N/A'}<br/>
          Position: ${d.position || 'N/A'}
        `;
        
        tooltip.html(tooltipContent)
          .style('left', (event.pageX + 15) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function(this: any) {
        d3.select(this)
          .attr('stroke-width', 2)
          .attr('stroke', '#fff');
        
        link.style('stroke', '#999')
          .style('stroke-width', d => edgeWidthScale(d.weight || 0.5));
        
        tooltip.transition()
          .duration(500)
          .style('opacity', 0);
      })
      .on('click', function(this: any, d: any) {
        setSelectedNode(d);
      });

    // Add labels for nodes
    node.append('text')
      .text(d => {
        const label = d.label || d.id;
        return label.length > 15 ? label.substring(0, 12) + '...' : label;
      })
      .attr('x', 0)
      .attr('y', d => nodeSizeScale(d.importance || 0.5) + 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333');

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as SimulationNode).x || 0)
        .attr('y1', d => (d.source as SimulationNode).y || 0)
        .attr('x2', d => (d.target as SimulationNode).x || 0)
        .attr('y2', d => (d.target as SimulationNode).y || 0);

      node.attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
    });

    // Drag functions
    function dragStarted(this: any, event: any, d: SimulationNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(this: any, event: any, d: SimulationNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(this: any, event: any, d: SimulationNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = undefined;
      d.fy = undefined;
    }

    // Add controls
    const controls = svg.append('g')
      .attr('class', 'controls')
      .attr('transform', `translate(${width - 150}, 20)`);

    // Reset zoom button
    controls.append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', 60)
      .attr('height', 25)
      .attr('fill', '#f0f0f0')
      .attr('stroke', '#ccc')
      .attr('rx', 3)
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().duration(750).call(
          zoom.transform as any,
          d3.zoomIdentity
        );
      });

    controls.append('text')
      .attr('x', 30)
      .attr('y', 17)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .style('pointer-events', 'none')
      .text('Reset');

    // Cleanup on unmount
    return () => {
      simulation.stop();
      d3.selectAll('.node-tooltip').remove();
    };

  }, [graphData, width, height]);

  return (
    <div className="node-graph-container relative">
      <svg ref={svgRef}></svg>
      {selectedNode && (
        <div className="absolute top-2.5 left-2.5 bg-white bg-opacity-95 border border-gray-300 p-2.5 rounded text-xs max-w-48">
          <h4 className="m-0 mb-2">Selected Node</h4>
          <p><strong>ID:</strong> {selectedNode.id}</p>
          <p><strong>Label:</strong> {selectedNode.label || 'N/A'}</p>
          <p><strong>Type:</strong> {selectedNode.node_type || 'N/A'}</p>
          <p><strong>Importance:</strong> {(selectedNode.importance || 0).toFixed(3)}</p>
          <button 
            onClick={() => setSelectedNode(null)}
            className="mt-2 p-1 text-xs cursor-pointer"
          >
            Close
          </button>
        </div>
      )}
      <div className="absolute bottom-2.5 right-2.5 bg-gray-900 bg-opacity-70 text-white p-1.25 px-2.5 rounded text-xs">
        Zoom: {(zoomLevel * 100).toFixed(0)}%
      </div>
    </div>
  );
};

export default NodeGraph;
