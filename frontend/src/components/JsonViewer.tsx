import React, { useState, useCallback } from 'react';
import { JsonViewerProps } from '../types';

const JsonViewer: React.FC<JsonViewerProps> = ({ data, expanded = false }) => {
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
    expanded ? new Set(['root']) : new Set()
  );

  const togglePath = useCallback((path: string) => {
    setExpandedPaths(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  }, []);

  const renderValue = (value: any, path: string, key: string): JSX.Element => {
    const isExpanded = expandedPaths.has(path);
    const isObject = value !== null && typeof value === 'object';
    const isArray = Array.isArray(value);
    const hasChildren = isObject && Object.keys(value).length > 0;

    const getTypeColor = (type: string): string => {
      const colors: Record<string, string> = {
        string: '#0451a5',
        number: '#098658',
        boolean: '#0000ff',
        null: '#808080',
        undefined: '#808080',
        object: '#000000',
        array: '#000000'
      };
      return colors[type] || '#000000';
    };

    const getDisplayValue = (): string => {
      if (value === null) return 'null';
      if (value === undefined) return 'undefined';
      if (typeof value === 'string') return `"${value}"`;
      if (typeof value === 'number' || typeof value === 'boolean') return String(value);
      return '';
    };

    if (!isObject) {
      return (
        <span style={{ color: getTypeColor(typeof value) }}>
          {getDisplayValue()}
        </span>
      );
    }

    const childCount = isArray ? value.length : Object.keys(value).length;
    const summary = isArray 
      ? `Array[${childCount}]` 
      : `Object{${childCount}}`;

    return (
      <div>
        <span
          style={{ 
            cursor: hasChildren ? 'pointer' : 'default',
            color: getTypeColor(isArray ? 'array' : 'object'),
            fontWeight: hasChildren ? 'bold' : 'normal'
          }}
          onClick={() => hasChildren && togglePath(path)}
        >
          {hasChildren && (
            <span style={{ marginRight: '4px' }}>
              {isExpanded ? 'v' : '>'}
            </span>
          )}
          {!isArray && <span style={{ marginRight: '4px' }}>"{key}":</span>}
          {summary}
        </span>
        
        {isExpanded && hasChildren && (
          <div style={{ marginLeft: '20px', marginTop: '4px' }}>
            {isArray ? (
              value.map((item: any, index: number) => (
                <div key={index} style={{ marginBottom: '2px' }}>
                  <span style={{ color: '#666' }}>{index}:</span>
                  {renderValue(item, `${path}[${index}]`, String(index))}
                  {index < value.length - 1 && ','}
                </div>
              ))
            ) : (
              Object.entries(value).map(([k, v]) => (
                <div key={k} style={{ marginBottom: '2px' }}>
                  {renderValue(v, `${path}.${k}`, k)}
                  {Object.keys(value).indexOf(k) < Object.keys(value).length - 1 && ','}
                </div>
              ))
            )}
          </div>
        )}
        {!isArray && ','}
      </div>
    );
  };

  const copyToClipboard = () => {
    const jsonString = JSON.stringify(data, null, 2);
    navigator.clipboard.writeText(jsonString).then(() => {
      // Could add a toast notification here
      console.log('JSON copied to clipboard');
    });
  };

  const downloadJson = () => {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'explanation.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const expandAll = () => {
    const paths = new Set<string>();
    const collectPaths = (obj: any, currentPath: string = 'root') => {
      if (obj !== null && typeof obj === 'object') {
        paths.add(currentPath);
        if (Array.isArray(obj)) {
          obj.forEach((item, index) => {
            collectPaths(item, `${currentPath}[${index}]`);
          });
        } else {
          Object.entries(obj).forEach(([key, value]) => {
            collectPaths(value, `${currentPath}.${key}`);
          });
        }
      }
    };
    collectPaths(data);
    setExpandedPaths(paths);
  };

  const collapseAll = () => {
    setExpandedPaths(new Set());
  };

  return (
    <div className="json-viewer font-mono text-xs leading-relaxed bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-auto max-h-96">
      <div className="flex justify-between items-center mb-3 pb-2 border-b border-gray-200">
        <h3 className="m-0 text-sm font-bold">
          JSON Data
        </h3>
        <div className="flex gap-2">
          <button
            onClick={expandAll}
            className="p-1 text-xs border border-gray-300 rounded cursor-pointer bg-gray-50"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="p-1 text-xs border border-gray-300 rounded cursor-pointer bg-gray-50"
          >
            Collapse All
          </button>
          <button
            onClick={copyToClipboard}
            className="p-1 text-xs border border-gray-300 rounded cursor-pointer bg-blue-50"
          >
            Copy
          </button>
          <button
            onClick={downloadJson}
            className="p-1 text-xs border border-gray-300 rounded cursor-pointer bg-green-50"
          >
            Download
          </button>
        </div>
      </div>
      
      <div className="json-content">
        {renderValue(data, 'root', 'root')}
      </div>
      
      <div className="mt-3 pt-2 border-t border-gray-200 text-xs text-gray-600">
        Size: {JSON.stringify(data).length} characters | 
        Keys: {Object.keys(data).length} top-level
      </div>
    </div>
  );
};

export default JsonViewer;
