import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TrendAnalytics = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('90');
  const [comparison, setComparison] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardTrends();
    fetchComparisons();
  }, [selectedPeriod]);

  const fetchDashboardTrends = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/trends/dashboard?days=${selectedPeriod}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch trends');
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchComparisons = async () => {
    const metrics = ['risk_score', 'compliance_score', 'control_effectiveness', 'open_issues'];
    const token = localStorage.getItem('token');
    const comparisons = {};
    
    for (const metric of metrics) {
      try {
        const response = await fetch(`${API_URL}/api/trends/comparison/${metric}?period_days=30`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          comparisons[metric] = await response.json();
        }
      } catch (err) {
        console.error(`Error fetching ${metric} comparison:`, err);
      }
    }
    setComparison(comparisons);
  };

  const generateSampleData = async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_URL}/api/trends/generate-sample-data?days=90`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchDashboardTrends();
      fetchComparisons();
    } catch (err) {
      setError(err.message);
    }
  };

  const MetricCard = ({ title, metric, color, inverted = false }) => {
    const comp = comparison[metric];
    const trend = dashboardData?.trends?.[metric];
    
    const getTrendIcon = () => {
      if (!comp) return null;
      const isImproving = inverted ? comp.change_percent < 0 : comp.change_percent > 0;
      if (isImproving) {
        return <span className="text-emerald-400">↑</span>;
      } else if (comp.change_percent === 0) {
        return <span className="text-gray-400">→</span>;
      } else {
        return <span className="text-red-400">↓</span>;
      }
    };

    const getTrendColor = () => {
      if (!comp) return 'text-gray-400';
      const isImproving = inverted ? comp.change_percent < 0 : comp.change_percent > 0;
      return isImproving ? 'text-emerald-400' : comp.change_percent === 0 ? 'text-gray-400' : 'text-red-400';
    };

    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${color}`}>
              {comp?.current_period?.average?.toFixed(1) || '—'}
              {metric.includes('score') || metric === 'control_effectiveness' ? '%' : ''}
            </span>
            {getTrendIcon()}
          </div>
          {comp && (
            <div className={`text-sm ${getTrendColor()} mt-1`}>
              {comp.change_percent > 0 ? '+' : ''}{comp.change_percent?.toFixed(1)}% vs last period
            </div>
          )}
          {trend && (
            <div className="mt-4 h-16">
              <MiniChart data={trend.values} color={color} />
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const MiniChart = ({ data, color }) => {
    if (!data || data.length === 0) return <div className="text-slate-500 text-sm">No data</div>;
    
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const height = 60;
    const width = 200;
    
    const points = data.map((value, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <polyline
          fill="none"
          stroke={color.includes('emerald') ? '#10b981' : color.includes('blue') ? '#3b82f6' : color.includes('amber') ? '#f59e0b' : '#8b5cf6'}
          strokeWidth="2"
          points={points}
        />
      </svg>
    );
  };

  const TrendChart = ({ title, metric, color }) => {
    const trend = dashboardData?.trends?.[metric];
    
    if (!trend || !trend.values.length) {
      return (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-lg text-white">{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center text-slate-500">
              No data available
            </div>
          </CardContent>
        </Card>
      );
    }

    const max = Math.max(...trend.values);
    const min = Math.min(...trend.values);
    const range = max - min || 1;
    const height = 180;
    const width = 500;
    const padding = 40;

    const points = trend.values.map((value, i) => {
      const x = padding + (i / (trend.values.length - 1)) * (width - 2 * padding);
      const y = padding + (height - 2 * padding) - ((value - min) / range) * (height - 2 * padding);
      return { x, y, value, label: trend.labels[i] };
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-lg text-white">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
            {/* Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => (
              <g key={i}>
                <line
                  x1={padding}
                  x2={width - padding}
                  y1={padding + (1 - pct) * (height - 2 * padding)}
                  y2={padding + (1 - pct) * (height - 2 * padding)}
                  stroke="#374151"
                  strokeDasharray="4"
                />
                <text
                  x={padding - 8}
                  y={padding + (1 - pct) * (height - 2 * padding) + 4}
                  fill="#6b7280"
                  fontSize="10"
                  textAnchor="end"
                >
                  {(min + pct * range).toFixed(0)}
                </text>
              </g>
            ))}
            
            {/* Area fill */}
            <path
              d={`${pathD} L ${points[points.length - 1].x} ${height - padding} L ${padding} ${height - padding} Z`}
              fill={color.includes('emerald') ? 'rgba(16, 185, 129, 0.1)' : color.includes('blue') ? 'rgba(59, 130, 246, 0.1)' : 'rgba(139, 92, 246, 0.1)'}
            />
            
            {/* Line */}
            <path
              d={pathD}
              fill="none"
              stroke={color.includes('emerald') ? '#10b981' : color.includes('blue') ? '#3b82f6' : '#8b5cf6'}
              strokeWidth="2"
            />
            
            {/* Data points */}
            {points.map((p, i) => (
              <circle
                key={i}
                cx={p.x}
                cy={p.y}
                r="4"
                fill={color.includes('emerald') ? '#10b981' : color.includes('blue') ? '#3b82f6' : '#8b5cf6'}
              />
            ))}
            
            {/* X-axis labels (show every few) */}
            {points.filter((_, i) => i % Math.ceil(points.length / 6) === 0).map((p, i) => (
              <text
                key={i}
                x={p.x}
                y={height - 10}
                fill="#6b7280"
                fontSize="9"
                textAnchor="middle"
              >
                {p.label?.slice(5) || ''}
              </text>
            ))}
          </svg>
        </CardContent>
      </Card>
    );
  };

  if (loading && !dashboardData) {
    return (
      <div className="p-6 bg-slate-900 min-h-screen text-white">
        <div className="animate-pulse">Loading trend analytics...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="trend-analytics-page">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Trend Analytics</h1>
            <p className="text-slate-400">Track risk, compliance, and control effectiveness over time</p>
          </div>
          <div className="flex items-center gap-4">
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-36 bg-slate-800 border-slate-700 text-white">
                <SelectValue placeholder="Select period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="60">Last 60 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
                <SelectItem value="180">Last 6 months</SelectItem>
                <SelectItem value="365">Last year</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              variant="outline" 
              onClick={generateSampleData}
              className="border-slate-600 text-slate-300 hover:bg-slate-800"
              data-testid="generate-sample-data-btn"
            >
              Generate Sample Data
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500 text-red-300 p-4 rounded-lg">
            {error}
          </div>
        )}

        {/* Key Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard 
            title="Risk Score" 
            metric="risk_score" 
            color="text-emerald-400"
          />
          <MetricCard 
            title="Compliance Score" 
            metric="compliance_score" 
            color="text-blue-400"
          />
          <MetricCard 
            title="Control Effectiveness" 
            metric="control_effectiveness" 
            color="text-violet-400"
          />
          <MetricCard 
            title="Open Issues" 
            metric="open_issues" 
            color="text-amber-400"
            inverted={true}
          />
        </div>

        {/* Detailed Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TrendChart 
            title="Risk Score Trend" 
            metric="risk_score" 
            color="text-emerald-400"
          />
          <TrendChart 
            title="Compliance Score Trend" 
            metric="compliance_score" 
            color="text-blue-400"
          />
          <TrendChart 
            title="Control Effectiveness Trend" 
            metric="control_effectiveness" 
            color="text-violet-400"
          />
          <TrendChart 
            title="Gap Count Trend" 
            metric="gap_count" 
            color="text-red-400"
          />
        </div>

        {/* Summary Stats */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-lg text-white">Period Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-slate-400">Period:</span>
                <span className="ml-2 text-white">{selectedPeriod} days</span>
              </div>
              <div>
                <span className="text-slate-400">Aggregation:</span>
                <span className="ml-2 text-white">{dashboardData?.aggregation || 'weekly'}</span>
              </div>
              <div>
                <span className="text-slate-400">Data Points:</span>
                <span className="ml-2 text-white">
                  {dashboardData?.trends?.risk_score?.values?.length || 0}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Last Updated:</span>
                <span className="ml-2 text-white">
                  {dashboardData?.generated_at 
                    ? new Date(dashboardData.generated_at).toLocaleString() 
                    : '—'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TrendAnalytics;
