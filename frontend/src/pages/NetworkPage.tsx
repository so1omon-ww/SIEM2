import React, { useState, useEffect, useRef } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { Network, Server, Monitor, Router, Wifi, RefreshCw, Settings, Eye, EyeOff, Search } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { api } from '../services/api';
import NetworkDiscovery from '../components/NetworkDiscovery';

interface NetworkNode {
  id: string;
  type: 'server' | 'agent' | 'router' | 'switch';
  label: string;
  ip: string;
  status: 'online' | 'offline' | 'unknown';
  position?: { x: number; y: number };
  metadata?: any;
}

interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  type: 'connection' | 'data_flow';
  bandwidth?: string;
  latency?: number;
}

const NetworkPage: React.FC = () => {
  const { darkMode } = useTheme();
  const [nodes, setNodes] = useState<NetworkNode[]>([]);
  const [edges, setEdges] = useState<NetworkEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showDetails, setShowDetails] = useState(true);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [showDiscovery, setShowDiscovery] = useState(false);
  const [networkStats, setNetworkStats] = useState({
    totalNodes: 0,
    onlineNodes: 0,
    totalConnections: 0,
    activeAgents: 0
  });
  const [topologyWidth, setTopologyWidth] = useState(75); // Процент от общей ширины
  const [isResizing, setIsResizing] = useState(false);

  const cyRef = useRef<any>(null);
  const resizeRef = useRef<HTMLDivElement>(null);

  // Обработчики для изменения размера панели топологии
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return;
    
    const container = document.querySelector('.network-container') as HTMLElement;
    if (!container) return;
    
    const containerRect = container.getBoundingClientRect();
    const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
    
    // Ограничиваем размер от 30% до 90%
    const clampedWidth = Math.min(Math.max(newWidth, 30), 90);
    setTopologyWidth(clampedWidth);
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  // Добавляем обработчики событий мыши
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // Загрузка данных о сети
  const loadNetworkData = async () => {
    try {
      setLoading(true);
      
      // Загружаем данные о серверах и агентах
      const [serversResponse, agentsResponse] = await Promise.all([
        api.get('/network/servers'),
        api.get('/network/agents')
      ]);

      const servers = Array.isArray(serversResponse.data) ? serversResponse.data : [];
      const agents = Array.isArray(agentsResponse.data) ? agentsResponse.data : [];

      // Создаем узлы сети
      const networkNodes: NetworkNode[] = [];
      
      // Добавляем сервер
      networkNodes.push({
        id: 'server-1',
        type: 'server',
        label: 'SIEM Server',
        ip: '192.168.1.100',
        status: 'online',
        position: { x: 400, y: 200 }
      });

      // Добавляем агенты
      agents.forEach((agent: any, index: number) => {
        networkNodes.push({
          id: `agent-${agent.id}`,
          type: 'agent',
          label: `Agent ${agent.id}`,
          ip: agent.ip || `192.168.1.${100 + index}`,
          status: agent.status || 'online',
          position: {
            x: 200 + (index % 3) * 200,
            y: 400 + Math.floor(index / 3) * 150
          }
        });
      });

      // В реальной реализации здесь будет получение сетевого оборудования
      // из API или базы данных

      // Создаем связи на основе реальных данных
      const networkEdges: NetworkEdge[] = [];
      
      // В реальной реализации здесь будет получение связей из API
      // или анализ сетевого трафика для определения топологии

      setNodes(networkNodes);
      setEdges(networkEdges);

      // Обновляем статистику
      setNetworkStats({
        totalNodes: networkNodes.length,
        onlineNodes: networkNodes.filter(n => n.status === 'online').length,
        totalConnections: networkEdges.length,
        activeAgents: agents.length
      });

    } catch (error) {
      console.error('Ошибка загрузки данных сети:', error);
      // Используем тестовые данные в случае ошибки
      setNodes([
        {
          id: 'server-1',
          type: 'server',
          label: 'SIEM Server',
          ip: '192.168.1.100',
          status: 'online',
          position: { x: 400, y: 200 }
        },
        {
          id: 'agent-1',
          type: 'agent',
          label: 'Agent 1',
          ip: '192.168.1.101',
          status: 'online',
          position: { x: 200, y: 400 }
        },
        {
          id: 'agent-2',
          type: 'agent',
          label: 'Agent 2',
          ip: '192.168.1.102',
          status: 'online',
          position: { x: 600, y: 400 }
        },
        {
          id: 'router-1',
          type: 'router',
          label: 'Router',
          ip: '192.168.1.1',
          status: 'online',
          position: { x: 400, y: 100 }
        },
        {
          id: 'switch-1',
          type: 'switch',
          label: 'Switch',
          ip: '192.168.1.10',
          status: 'online',
          position: { x: 300, y: 300 }
        }
      ]);

      setEdges([
        {
          id: 'server-router-1',
          source: 'server-1',
          target: 'router-1',
          type: 'connection',
          bandwidth: '1 Gbps'
        },
        {
          id: 'router-1-switch-1',
          source: 'router-1',
          target: 'switch-1',
          type: 'connection',
          bandwidth: '100 Mbps'
        },
        {
          id: 'switch-1-agent-1',
          source: 'switch-1',
          target: 'agent-1',
          type: 'data_flow',
          bandwidth: '10 Mbps'
        },
        {
          id: 'switch-1-agent-2',
          source: 'switch-1',
          target: 'agent-2',
          type: 'data_flow',
          bandwidth: '10 Mbps'
        }
      ]);

      setNetworkStats({
        totalNodes: 5,
        onlineNodes: 5,
        totalConnections: 4,
        activeAgents: 2
      });
    } finally {
      setLoading(false);
    }
  };

  // Автообновление данных
  useEffect(() => {
    loadNetworkData();
    
    if (autoRefresh) {
      const interval = setInterval(loadNetworkData, 30000); // Обновление каждые 30 секунд
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Конфигурация Cytoscape
  const cyStylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'color': '#fff',
        'font-size': '12px',
        'font-weight': 'bold',
        'width': '60px',
        'height': '60px',
        'border-width': '2px',
        'border-color': '#333'
      }
    },
    {
      selector: 'node[type="server"]',
      style: {
        'background-color': '#3B82F6',
        'shape': 'rectangle',
        'width': '80px',
        'height': '60px'
      }
    },
    {
      selector: 'node[type="agent"]',
      style: {
        'background-color': '#10B981',
        'shape': 'ellipse'
      }
    },
    {
      selector: 'node[type="router"]',
      style: {
        'background-color': '#F59E0B',
        'shape': 'diamond',
        'width': '70px',
        'height': '70px'
      }
    },
    {
      selector: 'node[type="switch"]',
      style: {
        'background-color': '#8B5CF6',
        'shape': 'rectangle',
        'width': '70px',
        'height': '50px'
      }
    },
    {
      selector: 'node[status="offline"]',
      style: {
        'background-color': '#EF4444',
        'opacity': '0.5'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': '2px',
        'line-color': '#666',
        'target-arrow-color': '#666',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(bandwidth)',
        'font-size': '10px',
        'text-rotation': 'autorotate',
        'text-margin-y': '-10px'
      }
    },
    {
      selector: 'edge[type="data_flow"]',
      style: {
        'line-color': '#10B981',
        'target-arrow-color': '#10B981',
        'line-style': 'dashed'
      }
    }
  ];

  const cyLayout = {
    name: 'preset',
    positions: (node: any) => {
      const nodeData = nodes.find(n => n.id === node.id());
      return nodeData?.position || { x: 0, y: 0 };
    },
    fit: true,
    padding: 50
  };

  const handleNodeClick = (event: any) => {
    const nodeId = event.target.id();
    const node = nodes.find(n => n.id === nodeId);
    setSelectedNode(node || null);
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'server': return <Server className="h-5 w-5" />;
      case 'agent': return <Monitor className="h-5 w-5" />;
      case 'router': return <Router className="h-5 w-5" />;
      case 'switch': return <Wifi className="h-5 w-5" />;
      default: return <Network className="h-5 w-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-500';
      case 'offline': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const handleDevicesDiscovered = (devices: any[]) => {
    // Обновляем узлы сети с новыми обнаруженными устройствами
    const newNodes = devices.map((device, index) => ({
      id: `discovered-${index}`,
      type: device.type as 'server' | 'agent' | 'router' | 'switch',
      label: device.hostname || device.type,
      ip: device.ip,
      status: device.status as 'online' | 'offline' | 'unknown',
      position: {
        x: 100 + (index % 4) * 150,
        y: 500 + Math.floor(index / 4) * 100
      }
    }));

    setNodes(prevNodes => [...prevNodes, ...newNodes]);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="p-6">
        {/* Заголовок */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Network className={`h-8 w-8 mr-3 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Визуализация сети
              </h1>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowDiscovery(!showDiscovery)}
                className={`p-2 rounded-lg transition-colors ${
                  showDiscovery 
                    ? (darkMode ? 'bg-green-600 hover:bg-green-700' : 'bg-green-500 hover:bg-green-600')
                    : (darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100')
                }`}
              >
                <Search className={`h-5 w-5 ${showDiscovery ? 'text-white' : ''}`} />
              </button>
              <button
                onClick={() => setShowDetails(!showDetails)}
                className={`p-2 rounded-lg transition-colors ${
                  darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                }`}
              >
                {showDetails ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-2 rounded-lg transition-colors ${
                  autoRefresh 
                    ? (darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600')
                    : (darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100')
                }`}
              >
                <RefreshCw className={`h-5 w-5 ${autoRefresh ? 'text-white' : ''}`} />
              </button>
              <button
                onClick={loadNetworkData}
                disabled={loading}
                className={`p-2 rounded-lg transition-colors ${
                  darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center">
              <Network className={`h-8 w-8 mr-3 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              <div>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Всего узлов</p>
                <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {networkStats.totalNodes}
                </p>
              </div>
            </div>
          </div>
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center">
              <Monitor className={`h-8 w-8 mr-3 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />
              <div>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Онлайн</p>
                <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {networkStats.onlineNodes}
                </p>
              </div>
            </div>
          </div>
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center">
              <Wifi className={`h-8 w-8 mr-3 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
              <div>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Соединения</p>
                <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {networkStats.totalConnections}
                </p>
              </div>
            </div>
          </div>
          <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center">
              <Server className={`h-8 w-8 mr-3 ${darkMode ? 'text-orange-400' : 'text-orange-600'}`} />
              <div>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Агенты</p>
                <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {networkStats.activeAgents}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Основной контент */}
        <div className="network-container flex gap-6">
          {/* Граф сети */}
          <div 
            className="relative"
            style={{ width: `${topologyWidth}%` }}
          >
            <div className={`rounded-lg border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} p-4 h-full`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  Топология сети
                </h2>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {Math.round(topologyWidth)}%
                  </span>
                  <button
                    onClick={() => setTopologyWidth(75)}
                    className={`px-2 py-1 text-xs rounded ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-600'}`}
                    title="Сбросить размер"
                  >
                    Сброс
                  </button>
                </div>
              </div>
              {loading ? (
                <div className="flex items-center justify-center h-96">
                  <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
                  <span className={`ml-2 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Загрузка данных...
                  </span>
                </div>
              ) : (
                <div className="h-96 border rounded-lg">
                  <CytoscapeComponent
                    elements={[
                      ...nodes.map(node => ({
                        data: {
                          id: node.id,
                          label: showDetails ? `${node.label}\n${node.ip}` : node.label,
                          type: node.type,
                          status: node.status,
                          ip: node.ip
                        },
                        position: node.position
                      })),
                      ...edges.map(edge => ({
                        data: {
                          id: edge.id,
                          source: edge.source,
                          target: edge.target,
                          type: edge.type,
                          bandwidth: showDetails ? edge.bandwidth : undefined
                        }
                      }))
                    ]}
                    style={{ width: '100%', height: '100%' }}
                    stylesheet={cyStylesheet}
                    layout={cyLayout}
                    cy={(cy) => {
                      cyRef.current = cy;
                      cy.on('tap', 'node', handleNodeClick);
                    }}
                  />
                </div>
              )}
            </div>
            
            {/* Элемент для изменения размера */}
            <div
              ref={resizeRef}
              className={`absolute top-0 right-0 w-2 h-full cursor-col-resize hover:bg-blue-500 transition-all duration-200 group ${
                isResizing ? 'bg-blue-500' : 'bg-gray-300 hover:bg-gray-400'
              }`}
              onMouseDown={handleMouseDown}
              title="Перетащите для изменения размера панели"
            >
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="flex flex-col space-y-1">
                  <div className="w-1 h-1 bg-white rounded-full"></div>
                  <div className="w-1 h-1 bg-white rounded-full"></div>
                  <div className="w-1 h-1 bg-white rounded-full"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Панель обнаружения устройств */}
          {showDiscovery && (
            <div className="flex-1 min-w-0">
              <NetworkDiscovery onDevicesDiscovered={handleDevicesDiscovered} />
            </div>
          )}

          {/* Панель деталей */}
          <div className="flex-1 min-w-0">
            <div className={`rounded-lg border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} p-4`}>
              <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Детали узла
              </h2>
              {selectedNode ? (
                <div className="space-y-4">
                  <div className="flex items-center">
                    {getNodeIcon(selectedNode.type)}
                    <span className={`ml-2 font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {selectedNode.label}
                    </span>
                  </div>
                  <div>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>IP адрес</p>
                    <p className={`font-mono ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {selectedNode.ip}
                    </p>
                  </div>
                  <div>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Тип</p>
                    <p className={`capitalize ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {selectedNode.type}
                    </p>
                  </div>
                  <div>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Статус</p>
                    <p className={`flex items-center ${getStatusColor(selectedNode.status)}`}>
                      <div className={`w-2 h-2 rounded-full mr-2 ${
                        selectedNode.status === 'online' ? 'bg-green-500' : 
                        selectedNode.status === 'offline' ? 'bg-red-500' : 'bg-gray-500'
                      }`} />
                      {selectedNode.status}
                    </p>
                  </div>
                </div>
              ) : (
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Выберите узел на графике для просмотра деталей
                </p>
              )}
            </div>

            {/* Легенда */}
            <div className={`mt-6 rounded-lg border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} p-4`}>
              <h3 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Легенда
              </h3>
              <div className="space-y-3">
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-blue-500 rounded mr-3"></div>
                  <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Сервер</span>
                </div>
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-green-500 rounded-full mr-3"></div>
                  <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Агент</span>
                </div>
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-yellow-500 transform rotate-45 mr-3"></div>
                  <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Роутер</span>
                </div>
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-purple-500 rounded mr-3"></div>
                  <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Коммутатор</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkPage;
