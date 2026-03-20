import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const StudentDashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const res = await axios.get('/api/student/dashboard');
                setData(res.data);
            } catch (err) {
                console.error(err);
                setError('Failed to load student dashboard');
            } finally {
                setLoading(false);
            }
        };
        fetchDashboard();
    }, []);

    if (loading) return <div className="dashboard-content">Loading your stats...</div>;
    if (error) return <div className="dashboard-content error-text">{error}</div>;
    if (!data) return <div className="dashboard-content">No data available</div>;

    const metrics = data.metrics || {};
    const heatmap = metrics.heatmap || {};
    const heatmapDates = Object.keys(heatmap).sort();
    const chartData = {
        labels: heatmapDates,
        datasets: [{
            label: 'Attendance Status',
            data: heatmapDates.map(date => heatmap[date] === 'Present' ? 1 : (heatmap[date] === 'Absent' ? 0 : 0.5)),
            borderColor: 'var(--accent-primary)',
            backgroundColor: 'rgba(56, 189, 248, 0.2)',
            stepped: true,
            pointRadius: 5,
            pointHoverRadius: 8,
        }]
    };

    const chartOptions = {
        scales: {
            y: {
                min: -0.1,
                max: 1.1,
                ticks: {
                    callback: (value) => value === 1 ? 'Present' : (value === 0 ? 'Absent' : (value === 0.5 ? 'Mixed' : '')),
                    color: 'var(--text-secondary)'
                },
                grid: { color: 'rgba(255,255,255,0.05)' }
            },
            x: {
                grid: { display: false },
                ticks: { color: 'var(--text-secondary)' }
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (context) => {
                        const val = context.raw;
                        return val === 1 ? 'Present' : (val === 0 ? 'Absent' : 'Mixed');
                    }
                }
            }
        }
    };

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header">
                <h1>Welcome Back, {data.name}</h1>
                <p>Roll Number: {data.roll_number}</p>
            </div>

            <div className="stats-grid" style={{ marginTop: '2rem' }}>
                <div className="stat-card">
                    <div className="stat-value">{(data.metrics || {}).attendance_pct || 0}%</div>
                    <div className="stat-label">Total Attendance</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{(data.metrics || {}).streak || 0}</div>
                    <div className="stat-label">Current Streak 🔥</div>
                </div>
                <div className="stat-card">
                    <div className={`stat-value badge-${(data.risk_level || 'Low').toLowerCase()}`}>
                        {data.risk_level || 'Low'}
                    </div>
                    <div className="stat-label">Attendance Risk Level</div>
                </div>
            </div>

            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Personal Attendance History</h3>
                <div style={{ height: '300px' }}>
                    <Line data={chartData} options={chartOptions} />
                </div>
                <p style={{ marginTop: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    *1.0 = Present, 0.5 = Mixed (Partially Present), 0.0 = Absent
                </p>
            </div>
            
            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <h3 style={{ marginBottom: '1rem' }}>Performance Insights</h3>
                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                    <p>Your Consistency Score: <strong>{(data.metrics || {}).consistency || 0}/100</strong></p>
                    <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', marginTop: '0.5rem', overflow: 'hidden' }}>
                        <div style={{ width: `${(data.metrics || {}).consistency || 0}%`, height: '100%', background: 'var(--accent-primary)', transition: 'width 1s ease' }}></div>
                    </div>
                </div>
                {(data.risk_level || 'Low') === 'High' && (
                    <div style={{ marginTop: '1.5rem', padding: '1rem', borderLeft: '4px solid var(--error-color)', background: 'rgba(239, 68, 68, 0.1)' }}>
                        <p style={{ color: 'var(--error-color)', fontWeight: 600 }}>Action Required:</p>
                        <p style={{ fontSize: '0.9rem' }}>Your attendance is below 60%. Please meet with your faculty advisor to discuss your standing.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StudentDashboard;
