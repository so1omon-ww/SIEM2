import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Shield, Activity, AlertTriangle, Users, Globe, Zap, TrendingUp, Eye, Lock, Network } from 'lucide-react';
import CountUp from 'react-countup';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [stats, setStats] = useState({
    eventsProcessed: 0,
    threatsBlocked: 0,
    systemsProtected: 0,
    uptime: 0
  });

  useEffect(() => {
    // Симуляция загрузки статистики
    setTimeout(() => {
      setStats({
        eventsProcessed: 1247589,
        threatsBlocked: 3247,
        systemsProtected: 156,
        uptime: 99.9
      });
    }, 1000);
  }, []);

  const handleNavigateToMonitoring = () => {
    if (isAuthenticated) {
      navigate('/events');
    } else {
      navigate('/register');
    }
  };

  const handleNavigateToAnalytics = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/register');
    }
  };

  const handleStartMonitoring = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/register');
    }
  };

  const features = [
    {
      icon: <Activity className="h-8 w-8" />,
      title: "Мониторинг в реальном времени",
      description: "Непрерывный анализ сетевого трафика и событий безопасности 24/7",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: <AlertTriangle className="h-8 w-8" />,
      title: "Интеллектуальные алерты",
      description: "Система правил с корреляцией событий для точного обнаружения угроз",
      color: "from-orange-500 to-red-500"
    },
    {
      icon: <TrendingUp className="h-8 w-8" />,
      title: "Аналитика и отчеты",
      description: "Детальная аналитика с визуализацией трендов и паттернов безопасности",
      color: "from-green-500 to-emerald-500"
    },
    {
      icon: <Lock className="h-8 w-8" />,
      title: "Защита периметра",
      description: "Комплексная защита сетевой инфраструктуры от внешних и внутренних угроз",
      color: "from-purple-500 to-indigo-500"
    }
  ];

  const networkFacts = [
    { label: "Кибератак в день по всему миру", value: "4000+", icon: <Globe className="h-6 w-6" /> },
    { label: "Стоимость одной утечки данных", value: "$4.45M", icon: <TrendingUp className="h-6 w-6" /> },
    { label: "Время обнаружения атаки", value: "287 дней", icon: <Eye className="h-6 w-6" /> },
    { label: "Рост числа угроз в год", value: "+67%", icon: <AlertTriangle className="h-6 w-6" /> }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Animation */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
          <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl animate-pulse animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl animate-pulse animation-delay-4000"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <div className="flex justify-center mb-8">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="relative"
              >
                <Shield className="h-24 w-24 text-blue-400" />
                <div className="absolute inset-0 bg-blue-400 opacity-20 rounded-full animate-ping"></div>
              </motion.div>
            </div>

            <h1 className="text-6xl md:text-7xl font-bold text-white mb-6">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                SIEM System
              </span>
            </h1>

            <p className="text-2xl md:text-3xl text-blue-200 mb-4 font-light">
              Система управления информационной безопасностью
            </p>

            <p className="text-lg text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              Современное решение для мониторинга, анализа и защиты от киберугроз в режиме реального времени.
              Защитите свою инфраструктуру с помощью интеллектуальной системы обнаружения вторжений.
            </p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
              className="flex flex-col sm:flex-row gap-6 justify-center"
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleNavigateToMonitoring}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <span className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  Перейти к мониторингу
                </span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleNavigateToAnalytics}
                className="px-8 py-4 bg-white/10 text-white font-semibold rounded-xl backdrop-blur-sm border border-white/20 hover:bg-white/20 transition-all duration-300"
              >
                <span className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Посмотреть аналитику
                </span>
              </motion.button>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-20 bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { label: "События обработано", value: stats.eventsProcessed, suffix: "", icon: <Activity className="h-8 w-8" /> },
              { label: "Угроз заблокировано", value: stats.threatsBlocked, suffix: "", icon: <Shield className="h-8 w-8" /> },
              { label: "Систем под защитой", value: stats.systemsProtected, suffix: "", icon: <Network className="h-8 w-8" /> },
              { label: "Время работы", value: stats.uptime, suffix: "%", icon: <Zap className="h-8 w-8" /> }
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                className="text-center p-6 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20"
              >
                <div className="flex justify-center mb-4 text-blue-400">
                  {stat.icon}
                </div>
                <div className="text-3xl font-bold text-white mb-2">
                  <CountUp end={stat.value} duration={2.5} separator="," />
                  {stat.suffix}
                </div>
                <div className="text-slate-300 text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ключевые возможности
            </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Комплексное решение для защиты вашей IT-инфраструктуры от современных киберугроз
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.2, duration: 0.6 }}
                whileHover={{ scale: 1.02, y: -5 }}
                className="group p-8 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/20 transition-all duration-300"
              >
                <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${feature.color} mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <div className="text-white">
                    {feature.icon}
                  </div>
                </div>
                <h3 className="text-2xl font-semibold text-white mb-4">{feature.title}</h3>
                <p className="text-slate-300 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Network Security Facts */}
      <div className="py-20 bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Факты о кибербезопасности
            </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Актуальная статистика угроз информационной безопасности в мире
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {networkFacts.map((fact, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                whileHover={{ scale: 1.05 }}
                className="p-6 rounded-xl bg-gradient-to-br from-red-500/20 to-orange-500/20 backdrop-blur-sm border border-red-500/30 hover:border-red-400/50 transition-all duration-300"
              >
                <div className="flex items-center justify-center mb-4 text-red-400">
                  {fact.icon}
                </div>
                <div className="text-2xl font-bold text-white mb-2 text-center">
                  {fact.value}
                </div>
                <div className="text-slate-300 text-sm text-center leading-tight">
                  {fact.label}
                </div>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="mt-12 text-center"
          >
            <div className="p-8 rounded-2xl bg-gradient-to-r from-red-500/20 to-orange-500/20 backdrop-blur-sm border border-red-500/30">
              <h3 className="text-2xl font-bold text-white mb-4">
                Why is SIEM system critically important?
              </h3>
              <p className="text-slate-300 text-lg leading-relaxed max-w-4xl mx-auto">
                В условиях постоянно растущих киберугроз, каждая организация нуждается в надежной защите. 
                Наша SIEM система обеспечивает раннее обнаружение атак, автоматизированный анализ инцидентов 
                и быстрое реагирование на угрозы, сокращая время от обнаружения до устранения с 287 дней до нескольких минут.
              </p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="p-12 rounded-3xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-sm border border-blue-500/30"
          >
            <h2 className="text-4xl font-bold text-white mb-6">
              Начните защищать свою инфраструктуру уже сегодня
            </h2>
            <p className="text-xl text-slate-300 mb-8">
              Попробуйте нашу SIEM систему и убедитесь в её эффективности
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStartMonitoring}
              className="px-12 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 text-lg"
            >
              <span className="flex items-center">
                <Shield className="h-6 w-6 mr-3" />
                Запустить мониторинг
              </span>
            </motion.button>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;