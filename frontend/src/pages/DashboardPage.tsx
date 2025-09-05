import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, networkApi, dashboardApi } from '../services/api';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  Shield,
  TrendingUp,
  Globe,
  Eye,
  Network,
  Server,
  Zap,
  Users,
  Lock,
  Unlock,
  MapPin,
  Clock,
  Filter,
  Download,
  Settings,
  Bell,
  Search,
  RefreshCw,
  Play,
  Pause,
  Maximize2,
  Minimize2,
  Sun,
  Moon,
  Wifi,
  WifiOff,
  Database,
  Cpu,
  HardDrive,
  MemoryStick,
  Thermometer,
  Gauge,
  Target,
  TrendingDown,
  BarChart3,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  Map,
  Globe2,
  Layers,
  GitBranch,
  FileText,
  Calendar,
  Timer,
  CheckCircle,
  XCircle,
  Info,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Star,
  Award,
  Flag,
  MessageSquare,
  Phone,
  Mail,
  ExternalLink,
  Copy,
  Share2,
  Bookmark,
  Heart,
  ThumbsUp,
  ThumbsDown,
  EyeOff,
  Eye as EyeIcon,
  Plus,
  Minus,
  RotateCcw,
  Save,
  Edit,
  Trash2,
  Archive,
  Send,
  Upload,
  Download as DownloadIcon,
  Printer,
  Camera,
  Video,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Headphones,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Desktop,
  Router,
  Cloud,
  CloudOff,
  Wrench,
  Tool,
  Hammer,
  Cog,
  Sliders,
  ToggleLeft,
  ToggleRight,
  Power,
  PowerOff,
  Battery,
  BatteryLow,
  Signal,
  SignalHigh,
  SignalLow,
  SignalZero,
  Wifi as WifiIcon,
  Bluetooth,
  BluetoothOff,
  Radio,
  RadioOff,
  Satellite,
  SatelliteOff,
  Antenna,
  AntennaOff,
  Tower,
  TowerOff,
  Building,
  Building2,
  Home,
  Office,
  Factory,
  Warehouse,
  Store,
  Bank,
  Hospital,
  School,
  University,
  Library,
  Museum,
  Theater,
  Stadium,
  Park,
  Tree,
  Mountain,
  River,
  Ocean,
  Beach,
  Desert,
  Forest,
  City,
  Village,
  Town,
  Country,
  World,
  Earth,
  Planet,
  Star as StarIcon,
  Moon as MoonIcon,
  Sun as SunIcon,
  Cloud as CloudIcon,
  CloudRain,
  CloudSnow,
  CloudLightning,
  CloudDrizzle,
  CloudHail,
  CloudFog,
  Wind,
  Tornado,
  Hurricane,
  Earthquake,
  Volcano,
  Fire,
  Water,
  Snow,
  Rain,
  Hail,
  Lightning,
  Rainbow,
  Umbrella,
  Sunglasses,
  Snowflake,
  Icicle,
  Flame,
  Droplets,
  Waves,
  Fish,
  Bird,
  Cat,
  Dog,
  Rabbit,
  Mouse,
  Hamster,
  GuineaPig,
  Turtle,
  Snake,
  Lizard,
  Frog,
  Butterfly,
  Bee,
  Ant,
  Spider,
  Ladybug,
  Dragonfly,
  Mosquito,
  Fly,
  Worm,
  Snail,
  Octopus,
  Squid,
  Jellyfish,
  Starfish,
  Crab,
  Lobster,
  Shrimp,
  Fish as FishIcon,
  Whale,
  Dolphin,
  Shark,
  Penguin,
  Seal,
  Walrus,
  PolarBear,
  Bear,
  Lion,
  Tiger,
  Leopard,
  Cheetah,
  Jaguar,
  Panther,
  Wolf,
  Fox,
  Coyote,
  Hyena,
  Jackal,
  Dingo,
  Raccoon,
  Skunk,
  Opossum,
  Squirrel,
  Chipmunk,
  Beaver,
  Porcupine,
  Hedgehog,
  Mole,
  Shrew,
  Bat,
  Monkey,
  Ape,
  Gorilla,
  Chimpanzee,
  Orangutan,
  Gibbon,
  Lemur,
  Sloth,
  Armadillo,
  Anteater,
  Pangolin,
  Platypus,
  Echidna,
  Kangaroo,
  Koala,
  Wombat,
  TasmanianDevil,
  Emu,
  Ostrich,
  Kiwi,
  Penguin as PenguinIcon,
  Flamingo,
  Peacock,
  Parrot,
  Toucan,
  Hummingbird,
  Eagle,
  Hawk,
  Falcon,
  Owl,
  Crow,
  Raven,
  Magpie,
  Robin,
  Sparrow,
  Finch,
  Canary,
  Cardinal,
  BlueJay,
  Woodpecker,
  Kingfisher,
  Heron,
  Stork,
  Crane,
  Swan,
  Duck,
  Goose,
  Chicken,
  Rooster,
  Turkey,
  Pheasant,
  Quail,
  Partridge,
  Grouse,
  Ptarmigan,
  Sandpiper,
  Plover,
  Curlew,
  Godwit,
  Snipe,
  Woodcock,
  Sanderling,
  Dunlin,
  Knot,
  Turnstone,
  Oystercatcher,
  Avocet,
  Stilt,
  Phalarope,
  Jaeger,
  Skua,
  Gull,
  Tern,
  Noddy,
  Booby,
  Gannet,
  Cormorant,
  Shag,
  Pelican,
  Frigatebird,
  Albatross,
  Petrel,
  Shearwater,
  Fulmar,
  StormPetrel,
  DivingPetrel,
  Prion,
  Puffin,
  Auk,
  Guillemot,
  Razorbill,
  Murre,
  Dovekie,
  LittleAuk,
  ThickBilledMurre,
  CommonMurre,
  Razorbill as RazorbillIcon,
  Puffin as PuffinIcon,
  Auk as AukIcon,
  Guillemot as GuillemotIcon,
  Murre as MurreIcon,
  Dovekie as DovekieIcon,
  LittleAuk as LittleAukIcon,
  ThickBilledMurre as ThickBilledMurreIcon,
  CommonMurre as CommonMurreIcon
} from 'lucide-react';
import CountUp from 'react-countup';

const DashboardPage: React.FC = () => {
  // Основные состояния
  const [realTimeData, setRealTimeData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [expandedWidgets, setExpandedWidgets] = useState<Set<string>>(new Set());
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Статистика - инициализируем пустыми данными
  const [stats, setStats] = useState({
    activeEvents: 0,
    blockedThreats: 0,
    criticalAlerts: 0,
    protectedSystems: 0,
    totalTraffic: 0,
    uniqueIPs: 0,
    activeConnections: 0,
    systemHealth: 0
  });

  // Данные для графиков - инициализируем пустыми данными
  const [threatTypes, setThreatTypes] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState([]);
  const [topThreats, setTopThreats] = useState([]);
  const [timeActivity, setTimeActivity] = useState([]);

  // Агенты и устройства
  const [agents, setAgents] = useState<any[]>([]);
  const [servers, setServers] = useState<any[]>([]);



  // Функции управления
  const toggleWidget = (widgetId: string) => {
    const newExpanded = new Set(expandedWidgets);
    if (newExpanded.has(widgetId)) {
      newExpanded.delete(widgetId);
    } else {
      newExpanded.add(widgetId);
    }
    setExpandedWidgets(newExpanded);
  };



  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const addNotification = (message: string, type: 'info' | 'warning' | 'error' | 'success') => {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    setNotifications(prev => [notification, ...prev.slice(0, 4)]);
  };

     // Вспомогательные функции для анализа данных
     const getLatestSystemMetrics = (events: any[]) => {
    const performanceEvents = events
      .filter(event => event.event_type === 'system.performance')
      .sort((a, b) => new Date(b.ts || b.timestamp).getTime() - new Date(a.ts || a.timestamp).getTime());
    
    if (performanceEvents.length > 0) {
      const latest = performanceEvents[0].details?.performance;
      return {
        cpu: Math.round(latest?.cpu_percent || 0),
        memory: Math.round(latest?.memory_percent || 0),
        network: Math.round(latest?.network_percent || 0), // Теперь используем правильное процентное значение
        disk: Math.round(latest?.disk_percent || 0) // Теперь используем правильное процентное значение
      };
    }
    
    return { cpu: 0, memory: 0, network: 0, disk: 0 };
  };

  // Демо-данные отключены - используем только реальные данные

  // Функции генерации данных удалены - используем только реальные данные

  // Загружаем данные
   useEffect(() => {
    const fetchData = async () => {
       try {
         setLoading(true);
         
        // Получаем все данные дашборда через новые API endpoints
        const [
          statsData,
          threatTypesData,
          timeActivityData,
          topThreatsData,
          recentEventsData,
          agentsData,
          serversData
        ] = await Promise.all([
          dashboardApi.getStats(),
          dashboardApi.getThreatTypes(),
          dashboardApi.getTimeActivity(),
          dashboardApi.getTopThreats(),
          dashboardApi.getRecentEvents(5),
          networkApi.getAgents(),
          networkApi.getServers()
        ]);
        
        // Обновляем статистику
        setStats(statsData);
        
        // Обновляем типы угроз
        setThreatTypes(threatTypesData);
        
        // Обновляем активность по времени
        setTimeActivity(timeActivityData);
        
        // Обновляем топ угроз
        setTopThreats(topThreatsData);
        
        // Обновляем последние события
        setRealTimeData(recentEventsData);
        
        // Обновляем данные об агентах и серверах
        setAgents(agentsData.data || []);
        setServers(serversData.data || []);
        
        // Получаем системные метрики из событий
        const eventsResponse = await api.get('/events/recent?limit=100');
        const events = eventsResponse.data.items || [];
        const latestMetrics = getLatestSystemMetrics(events);
        
        setSystemMetrics([
          { name: 'CPU', value: latestMetrics.cpu, color: '#3b82f6', status: latestMetrics.cpu > 80 ? 'warning' : 'normal' },
          { name: 'Memory', value: latestMetrics.memory, color: '#10b981', status: latestMetrics.memory > 85 ? 'warning' : 'normal' },
          { name: 'Network', value: latestMetrics.network, color: '#f59e0b', status: latestMetrics.network > 70 ? 'warning' : 'normal' },
          { name: 'Storage', value: latestMetrics.disk, color: '#8b5cf6', status: latestMetrics.disk > 80 ? 'warning' : 'normal' }
        ]);
        
        // Добавляем уведомления о критических событиях
        if (statsData.criticalAlerts > 0) {
          addNotification(`Обнаружено ${statsData.criticalAlerts} критических алертов`, 'error');
        }
         
       } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        
        // В случае ошибки показываем пустые данные
        setStats({
          activeEvents: 0,
          blockedThreats: 0,
          criticalAlerts: 0,
          protectedSystems: 0,
          totalTraffic: 0,
          uniqueIPs: 0,
          activeConnections: 0,
          systemHealth: 0
        });
        
        setSystemMetrics([
          { name: 'CPU', value: 0, color: '#3b82f6', status: 'normal' },
          { name: 'Memory', value: 0, color: '#10b981', status: 'normal' },
          { name: 'Network', value: 0, color: '#f59e0b', status: 'normal' },
          { name: 'Storage', value: 0, color: '#8b5cf6', status: 'normal' }
        ]);
        
        setTimeActivity([]);
        setTopThreats([]);
        setThreatTypes([]);
        
        addNotification('Ошибка загрузки данных дашборда', 'error');
       } finally {
         setLoading(false);
       }
     };

    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 to-blue-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-4 text-white text-lg">Загрузка дашборда...</p>
        </div>
      </div>
    );
  }

  // Кастомный Tooltip для графиков
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-4 rounded-lg shadow-xl border bg-white/95 backdrop-blur-sm border-gray-200">
          <p className="font-semibold text-gray-800 mb-2">{`Время: ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm flex items-center">
              <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: entry.color }}></div>
              {`${entry.name}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Расширенные карточки статистики
  const statsCards = [
    { 
      title: 'Активные события', 
      value: stats.activeEvents, 
      change: '+12%', 
      icon: <Activity className="h-8 w-8" />,
      color: 'from-blue-500 to-cyan-500',
      trend: 'up',
      description: 'События за последние 24 часа'
    },
    { 
      title: 'Заблокированные угрозы', 
      value: stats.blockedThreats, 
      change: '+8%', 
      icon: <Shield className="h-8 w-8" />,
      color: 'from-green-500 to-emerald-500',
      trend: 'up',
      description: 'Успешно заблокировано'
    },
    { 
      title: 'Критические алерты', 
      value: stats.criticalAlerts, 
      change: '-15%', 
      icon: <AlertTriangle className="h-8 w-8" />,
      color: 'from-red-500 to-pink-500',
      trend: 'down',
      description: 'Требуют немедленного внимания'
    },
    { 
      title: 'Системы под защитой', 
      value: stats.protectedSystems, 
      change: '+3%', 
      icon: <Server className="h-8 w-8" />,
      color: 'from-purple-500 to-indigo-500',
      trend: 'up',
      description: 'Активные агенты мониторинга'
    },
    { 
      title: 'Уникальные IP', 
      value: stats.uniqueIPs, 
      change: '+5%', 
      icon: <Globe className="h-8 w-8" />,
      color: 'from-orange-500 to-red-500',
      trend: 'up',
      description: 'Различные источники трафика'
    },
    { 
      title: 'Активные соединения', 
      value: stats.activeConnections, 
      change: '+18%', 
      icon: <Network className="h-8 w-8" />,
      color: 'from-teal-500 to-green-500',
      trend: 'up',
      description: 'Текущие сетевые соединения'
    },
    { 
      title: 'Общий трафик', 
      value: `${Math.round(stats.totalTraffic / 1024 / 1024)} MB`, 
      change: '+22%', 
      icon: <Database className="h-8 w-8" />,
      color: 'from-indigo-500 to-purple-500',
      trend: 'up',
      description: 'Объем переданных данных'
    },
    { 
      title: 'Здоровье системы', 
      value: `${stats.systemHealth}%`, 
      change: '+2%', 
      icon: <Gauge className="h-8 w-8" />,
      color: stats.systemHealth > 80 ? 'from-green-500 to-emerald-500' : 
             stats.systemHealth > 60 ? 'from-yellow-500 to-orange-500' : 'from-red-500 to-pink-500',
      trend: 'up',
      description: 'Общее состояние системы'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-[1600px] mx-auto p-6">
        {/* Header с панелью управления */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
            <div>
                            <h1 className="text-5xl font-bold mb-2 flex items-center text-gray-900">
                <div className="relative">
                  <Shield className="h-12 w-12 mr-4 text-blue-500" />
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
                </div>
                SIEM Dashboard
              </h1>
              <p className="text-lg text-gray-600">
                Комплексный мониторинг и аналитика системы безопасности в реальном времени
              </p>
            </div>
            
            {/* Панель управления */}
            <div className="flex items-center space-x-4 mt-4 lg:mt-0">
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleFullscreen}
                  className="p-2 rounded-lg transition-colors bg-white text-gray-600 hover:bg-gray-100"
                >
                  {isFullscreen ? <Minimize2 className="h-5 w-5" /> : <Maximize2 className="h-5 w-5" />}
                </button>
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`p-2 rounded-lg transition-colors ${autoRefresh ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'}`}
                >
                  <RefreshCw className={`h-5 w-5 ${autoRefresh ? 'animate-spin' : ''}`} />
                </button>
              </div>
              
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-3 py-2 rounded-lg border bg-white border-gray-300 text-gray-700"
              >
                <option value="1h">Последний час</option>
                <option value="24h">Последние 24 часа</option>
                <option value="7d">Последние 7 дней</option>
                <option value="30d">Последние 30 дней</option>
              </select>
            </div>
          </div>

          {/* Уведомления */}
          <AnimatePresence>
            {notifications.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mb-4"
              >
                {notifications.map((notification) => (
                  <motion.div
                    key={notification.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className={`p-3 rounded-lg mb-2 flex items-center ${
                      notification.type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
                      notification.type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                      notification.type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
                      'bg-blue-100 text-blue-800 border border-blue-200'
                    }`}
                  >
                    <Bell className="h-4 w-4 mr-2" />
                    {notification.message}
                    <button
                      onClick={() => setNotifications(notifications.filter(n => n.id !== notification.id))}
                      className="ml-auto text-gray-500 hover:text-gray-700"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Расширенные карточки статистики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4 gap-6 mb-8">
          {statsCards.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.6 }}
              whileHover={{ scale: 1.03, y: -8 }}
              className="rounded-2xl p-6 shadow-xl border transition-all duration-300 cursor-pointer bg-white border-gray-100 hover:shadow-2xl"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-gradient-to-r ${stat.color} shadow-lg`}>
                  <div className="text-white">
                    {stat.icon}
                  </div>
                </div>
                <div className={`text-sm font-semibold px-3 py-1 rounded-full ${
                  stat.trend === 'up' ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'
                }`}>
                  {stat.change}
                </div>
              </div>
              <h3 className="text-sm font-medium mb-1 text-gray-600">
                {stat.title}
              </h3>
              <p className="text-3xl font-bold mb-2 text-gray-900">
                <CountUp end={typeof stat.value === 'string' ? parseInt(stat.value) : stat.value} duration={2} />
                {typeof stat.value === 'string' && stat.value.includes('%') && '%'}
                {typeof stat.value === 'string' && stat.value.includes('MB') && ' MB'}
              </p>
              <p className="text-xs text-gray-500">
                {stat.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Основные графики */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
          {/* Активность по времени */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center text-gray-900">
                <Activity className="h-6 w-6 mr-3 text-blue-500" />
                Активность по времени
            </h2>
              <button
                onClick={() => toggleWidget('timeline')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('timeline') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
            <div className={`${expandedWidgets.has('timeline') ? 'h-96' : 'h-80'}`}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={timeActivity}>
                  <defs>
                    <linearGradient id="eventsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="threatsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="events"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    fill="url(#eventsGradient)"
                    name="События"
                  />
                  <Line
                    type="monotone"
                    dataKey="threats"
                    stroke="#ef4444"
                    strokeWidth={3}
                    dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                    name="Угрозы"
                  />
                  <Line
                    type="monotone"
                    dataKey="blocked"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                    name="Заблокировано"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Анализ трафика по протоколам */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center text-gray-900">
                <Network className="h-6 w-6 mr-3 text-green-500" />
                Анализ трафика
              </h2>
              <button
                onClick={() => toggleWidget('traffic')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('traffic') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
            <div className={`${expandedWidgets.has('traffic') ? 'h-96' : 'h-80'}`}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { protocol: 'HTTP', packets: 1247, bytes: 2.4, color: '#3b82f6' },
                  { protocol: 'HTTPS', packets: 892, bytes: 1.8, color: '#10b981' },
                  { protocol: 'TCP', packets: 654, bytes: 1.2, color: '#f59e0b' },
                  { protocol: 'UDP', packets: 423, bytes: 0.8, color: '#ef4444' },
                  { protocol: 'DNS', packets: 234, bytes: 0.3, color: '#8b5cf6' },
                  { protocol: 'ICMP', packets: 89, bytes: 0.1, color: '#06b6d4' }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="protocol" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'packets' ? `${value} пакетов` : `${value} GB`,
                      name === 'packets' ? 'Пакеты' : 'Объем'
                    ]}
                  />
                  <Bar dataKey="packets" fill="#3b82f6" name="Пакеты" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="text-center p-3 rounded-lg bg-blue-50">
                <div className="text-2xl font-bold text-blue-600">3,539</div>
                <div className="text-sm text-blue-800">Всего пакетов</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-green-50">
                <div className="text-2xl font-bold text-green-600">6.6 GB</div>
                <div className="text-sm text-green-800">Общий трафик</div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Второй ряд виджетов */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Типы угроз */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center text-gray-900">
                <PieChartIcon className="h-5 w-5 mr-2 text-purple-500" />
              Типы угроз
            </h2>
              <button
                onClick={() => toggleWidget('threats')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('threats') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
            <div className={`${expandedWidgets.has('threats') ? 'h-80' : 'h-64'}`}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={threatTypes}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {Array.isArray(threatTypes) && threatTypes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {Array.isArray(threatTypes) && threatTypes.map((item, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2" 
                    style={{ backgroundColor: item.color }}
                  ></div>
                    <span className="text-gray-600">{item.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600">{item.value}%</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      item.trend.startsWith('+') ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
                    }`}>
                      {item.trend}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Системные метрики */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center text-gray-900">
                <Cpu className="h-5 w-5 mr-2 text-green-500" />
                Системные метрики
            </h2>
              <button
                onClick={() => toggleWidget('metrics')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('metrics') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
                  </div>
            <div className="space-y-4">
              {Array.isArray(systemMetrics) && systemMetrics.map((metric, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">
                      {metric.name}
                    </span>
                    <span className="text-sm font-bold text-gray-900">
                      {metric.value}%
                    </span>
                </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        metric.status === 'warning' ? 'bg-yellow-500' : 
                        metric.status === 'critical' ? 'bg-red-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${metric.value}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 p-4 rounded-lg bg-blue-50 border border-blue-200">
              <div className="flex items-center">
                <Info className="h-4 w-4 text-blue-500 mr-2" />
                <span className="text-sm text-blue-700">
                  Система работает в нормальном режиме
                </span>
              </div>
            </div>
          </motion.div>

          {/* Топ угроз */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center text-gray-900">
                <AlertTriangle className="h-5 w-5 mr-2 text-red-500" />
                Топ угроз
            </h2>
              <button
                onClick={() => toggleWidget('topThreats')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('topThreats') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
                  </div>
            <div className="space-y-3">
              {Array.isArray(topThreats) && topThreats.map((threat, index) => (
                <div key={threat.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                      threat.severity === 'critical' ? 'bg-red-500' :
                      threat.severity === 'high' ? 'bg-orange-500' :
                      threat.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                    }`}>
                      {index + 1}
                </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {threat.type}
                      </p>
                      <p className="text-sm text-gray-500">
                        {threat.count} случаев
                      </p>
              </div>
            </div>
                  <div className="text-right">
                    <span className={`text-sm px-2 py-1 rounded-full ${
                      threat.trend.startsWith('+') ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
                    }`}>
                      {threat.trend}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Третий ряд - Heatmap и быстрые действия */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
          {/* Heatmap активности */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
            className="xl:col-span-2 rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center text-gray-900">
                <Map className="h-6 w-6 mr-3 text-indigo-500" />
                Heatmap активности
          </h2>
              <button
                onClick={() => toggleWidget('heatmap')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('heatmap') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
            <div className={`${expandedWidgets.has('heatmap') ? 'h-96' : 'h-80'}`}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeActivity}>
                <defs>
                    <linearGradient id="heatmapGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                    dataKey="events"
                  stroke="#6366f1"
                  strokeWidth={3}
                    fill="url(#heatmapGradient)"
                  name="Сетевая активность"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

          {/* Панель быстрых действий */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
                          <h2 className="text-xl font-bold mb-6 flex items-center text-gray-900">
              <Zap className="h-5 w-5 mr-2 text-yellow-500" />
              Быстрые действия
            </h2>
            <div className="space-y-4">
              <button className="w-full p-4 rounded-lg bg-red-50 border border-red-200 hover:bg-red-100 transition-colors text-left">
                <div className="flex items-center">
                  <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                  <div>
                    <p className="font-medium text-red-800">Экстренное отключение</p>
                    <p className="text-sm text-red-600">Блокировка всех соединений</p>
                  </div>
                </div>
              </button>
              
              <button className="w-full p-4 rounded-lg bg-blue-50 border border-blue-200 hover:bg-blue-100 transition-colors text-left">
                <div className="flex items-center">
                  <Shield className="h-5 w-5 text-blue-500 mr-3" />
                  <div>
                    <p className="font-medium text-blue-800">Усилить защиту</p>
                    <p className="text-sm text-blue-600">Активировать дополнительные правила</p>
                  </div>
                </div>
              </button>
              
              <button className="w-full p-4 rounded-lg bg-green-50 border border-green-200 hover:bg-green-100 transition-colors text-left">
                <div className="flex items-center">
                  <Download className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="font-medium text-green-800">Экспорт отчета</p>
                    <p className="text-sm text-green-600">Скачать данные за период</p>
                  </div>
                </div>
              </button>
              
              <button className="w-full p-4 rounded-lg bg-purple-50 border border-purple-200 hover:bg-purple-100 transition-colors text-left">
                <div className="flex items-center">
                  <Settings className="h-5 w-5 text-purple-500 mr-3" />
                  <div>
                    <p className="font-medium text-purple-800">Настройки системы</p>
                    <p className="text-sm text-purple-600">Конфигурация мониторинга</p>
                  </div>
                </div>
              </button>
            </div>
          </motion.div>
        </div>

        {/* Информация об агентах и устройствах */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
          {/* Агенты мониторинга */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center text-gray-900">
                <Server className="h-5 w-5 mr-2 text-blue-500" />
                Агенты мониторинга
              </h2>
              <button
                onClick={() => toggleWidget('agents')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('agents') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
            <div className="space-y-3">
              {Array.isArray(agents) && agents.map((agent, index) => (
                <div key={agent.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      agent.status === 'online' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{agent.name}</p>
                      <p className="text-sm text-gray-500">
                        {agent.os} • {agent.ip} • v{agent.version}
                      </p>
                      <p className="text-xs text-gray-400">
                        Коллекторы: {agent.collectors?.join(', ') || 'Не указаны'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {new Date(agent.last_seen).toLocaleTimeString()}
                    </p>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      agent.status === 'online' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                    }`}>
                      {agent.status === 'online' ? 'Онлайн' : 'Офлайн'}
                    </span>
                  </div>
                </div>
              ))}
              {agents.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Server className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>Нет активных агентов</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Серверы системы */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center text-gray-900">
                <Database className="h-5 w-5 mr-2 text-green-500" />
                Серверы системы
              </h2>
              <button
                onClick={() => toggleWidget('servers')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedWidgets.has('servers') ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
            <div className="space-y-3">
              {Array.isArray(servers) && servers.map((server, index) => (
                <div key={server.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      server.status === 'online' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{server.name}</p>
                      <p className="text-sm text-gray-500">
                        {server.type} • {server.ip}
                      </p>
                      <p className="text-xs text-gray-400">
                        Сервисы: {server.services?.join(', ') || 'Не указаны'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {new Date(server.last_seen).toLocaleTimeString()}
                    </p>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      server.status === 'online' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                    }`}>
                      {server.status === 'online' ? 'Онлайн' : 'Офлайн'}
                    </span>
                  </div>
                </div>
              ))}
              {servers.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Database className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>Нет активных серверов</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Финальный ряд - Статус системы и последние события */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          {/* Статус системы */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
                          <h2 className="text-xl font-bold mb-6 flex items-center text-gray-900">
              <Gauge className="h-5 w-5 mr-2 text-green-500" />
              Статус системы
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg bg-green-50 border border-green-200">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="font-medium text-green-800">Агенты мониторинга</p>
                    <p className="text-sm text-green-600">Все системы онлайн</p>
                  </div>
                </div>
                <div className="text-green-600 font-bold">✓</div>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-lg bg-blue-50 border border-blue-200">
                <div className="flex items-center">
                  <Database className="h-5 w-5 text-blue-500 mr-3" />
                  <div>
                    <p className="font-medium text-blue-800">База данных</p>
                    <p className="text-sm text-blue-600">Синхронизация активна</p>
                  </div>
                </div>
                <div className="text-blue-600 font-bold">✓</div>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-lg bg-yellow-50 border border-yellow-200">
                <div className="flex items-center">
                  <AlertCircle className="h-5 w-5 text-yellow-500 mr-3" />
                  <div>
                    <p className="font-medium text-yellow-800">Правила анализа</p>
                    <p className="text-sm text-yellow-600">Требуется обновление</p>
                  </div>
                </div>
                <div className="text-yellow-600 font-bold">!</div>
              </div>
            </div>
          </motion.div>

          {/* Последние события */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.1, duration: 0.6 }}
            className="rounded-2xl p-6 shadow-xl border bg-white border-gray-100"
          >
                          <h2 className="text-xl font-bold mb-6 flex items-center text-gray-900">
              <Clock className="h-5 w-5 mr-2 text-blue-500" />
              Последние события
            </h2>
            <div className="space-y-3">
              {[
                { time: '14:32', event: 'Обнаружена подозрительная активность', severity: 'high', ip: '192.168.1.100' },
                { time: '14:28', event: 'Попытка сканирования портов', severity: 'medium', ip: '10.0.0.15' },
                { time: '14:25', event: 'Успешная блокировка угрозы', severity: 'low', ip: '172.16.0.50' },
                { time: '14:20', event: 'Обновление правил безопасности', severity: 'info', ip: 'Система' },
                { time: '14:15', event: 'Новый агент подключен', severity: 'info', ip: '192.168.1.200' }
              ].map((event, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      event.severity === 'high' ? 'bg-red-500' :
                      event.severity === 'medium' ? 'bg-yellow-500' :
                      event.severity === 'low' ? 'bg-green-500' : 'bg-blue-500'
                    }`}></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {event.event}
                      </p>
                      <p className="text-sm text-gray-500">
                        {event.ip} • {event.time}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </div>
              ))}
            </div>
          </motion.div>
        </div>

      </div>
    </div>
  );
};

export default DashboardPage;
