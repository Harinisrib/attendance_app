import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
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
  ArcElement
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const ClassAnalysis = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const res = await axios.get(`/api/classes/${id}/analysis`);
                setData(res.data);
            } catch (err) {
                setError('Failed to load class analysis');
            } finally {
                setLoading(false);
            }
        };
        fetchAnalysis();
    }, [id]);

    if (loading) return <div style={{padding: '2rem'}}>Loading Analysis...</div>;
    if (error) return <div className="error-text" style={{padding: '2rem'}}>{error}</div>;
    if (!data) return <div style={{padding: '2rem'}}>No data found</div>;

    const trend = data.trend || [];
    const lineData = {
        labels: trend.map(t => `${t.date || ''} (${t.session || ''})`),
        datasets: [{
            label: 'Attendance Rate %',
            data: trend.map(t => t.rate || 0),
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            fill: true,
            tension: 0.4
        }]
    };

    const riskCounts = data.risk_counts || {};
    const doughnutData = {
        labels: ['Low Risk', 'Medium Risk', 'High Risk'],
        datasets: [{
            data: [
                riskCounts.Low || 0,
                riskCounts.Medium || 0,
                riskCounts.High || 0
            ],
            backgroundColor: ['#10b981', '#f59e0b', '#f43f5e'],
            borderWidth: 0
        }]
    };

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header">
                <h1>
                    <button onClick={() => navigate(`/class/${id}`)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.5rem', color: 'var(--text-secondary)', marginRight: '1rem' }}>←</button>
                    {data.name} Insights
                </h1>
                <p>Detailed performance analytics and ML risk projections.</p>
            </div>

            <div className="stats-grid" style={{ marginTop: '2rem' }}>
                <div className="stat-card">
                    <div className="stat-value">{data.avg_attendance}%</div>
                    <div className="stat-label">Avg Attendance</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">
                         <span className={`badge badge-${(data.risk_level || 'Low').toLowerCase()}`}>
                            {data.risk_level || 'Low'}
                        </span>
                    </div>
                    <div className="stat-label">ML Risk Assessment</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: 'var(--error-color)' }}>{(data.risk_counts || {}).High || 0}</div>
                    <div className="stat-label">Critical Risks</div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem', marginTop: '2rem' }}>
                <div className="glass-card">
                    <h3 style={{ marginBottom: '1.5rem' }}>Attendance Trend (Last 10 Sessions)</h3>
                    <div style={{ height: '300px' }}>
                        <Line data={lineData} options={{ maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } } }} />
                    </div>
                </div>
                <div className="glass-card">
                    <h3 style={{ marginBottom: '1.5rem' }}>Risk Profile</h3>
                    <div style={{ height: '300px' }}>
                        <Doughnut data={doughnutData} options={{ maintainAspectRatio: false }} />
                    </div>
                </div>
            </div>
            
            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Recent Attendance Logs</h3>
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Session</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(data.history || []).length === 0 ? (
                                <tr><td colSpan="3" style={{textAlign: 'center', padding: '2rem'}}>No logs available</td></tr>
                            ) : (
                                (data.history || []).map((log, idx) => (
                                    <tr key={idx}>
                                        <td>{log.date || 'N/A'}</td>
                                        <td>{log.session || 'N/A'}</td>
                                        <td>
                                            <span style={{ color: log.is_present ? 'var(--success-color)' : 'var(--error-color)', fontWeight: 700 }}>
                                                {log.is_present ? 'PRESENT' : 'ABSENT'}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                 <button onClick={() => window.print()} className="btn btn-secondary">
                    🖨️ Print Analysis Report
                </button>
            </div>
        </div>
    );
};

export default ClassAnalysis;
