import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const AnalysisDashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const res = await axios.get('/api/dashboard/analysis');
                setData(res.data);
            } catch (err) {
                console.error(err);
                setError('Failed to load analysis data');
            } finally {
                setLoading(false);
            }
        };
        fetchAnalysis();
    }, []);

    if (loading) return <div>Loading ML Analysis...</div>;
    if (error) return <div className="error-text">{error}</div>;
    if (!data) return <div>No data available</div>;

    // Chart Data
    const riskCounts = data.risk_counts || {};
    const riskDoughnutData = {
        labels: ['Low Risk', 'Medium Risk', 'High Risk'],
        datasets: [{
            data: [
                riskCounts.Low || 0,
                riskCounts.Medium || 0,
                riskCounts.High || 0
            ],
            backgroundColor: [
                '#10b981', // green
                '#f59e0b', // yellow
                '#ef4444'  // red
            ],
            borderWidth: 0,
        }]
    };

    const classesData = data.classes_data || [];
    const classBarData = {
        labels: classesData.map(c => c.name || 'Unknown Class'),
        datasets: [{
            label: 'Average Attendance %',
            data: classesData.map(c => c.attendance || 0),
            backgroundColor: 'rgba(56, 189, 248, 0.8)',
            borderRadius: 4
        }]
    };

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header">
                <h1>Overall ML Analysis</h1>
                <p>Aggregated metrics and predictive insights across all your classes.</p>
            </div>

            {/* Top Stats */}
            <div className="stats-grid" style={{ marginTop: '2rem' }}>
                <div className="stat-card">
                    <div className="stat-value">{data.total_students}</div>
                    <div className="stat-label">Total Students</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{data.avg_attendance}%</div>
                    <div className="stat-label">Global Attendance</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: 'var(--error-color)' }}>
                        {data.low_attendance_count}
                    </div>
                    <div className="stat-label">Critical Attendance (&lt;75%)</div>
                </div>
            </div>

            {/* Charts Area */}
            <div style={{ display: 'flex', gap: '2rem', marginTop: '2rem', flexWrap: 'wrap' }}>
                <div className="glass-card" style={{ flex: '1 1 300px' }}>
                    <h3 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>ML Risk Distribution</h3>
                    <div style={{ maxWidth: '250px', margin: '0 auto' }}>
                        <Doughnut data={riskDoughnutData} options={{ maintainAspectRatio: true }} />
                    </div>
                </div>

                <div className="glass-card" style={{ flex: '2 1 400px' }}>
                    <h3 style={{ marginBottom: '1.5rem' }}>Class Performance</h3>
                    <Bar 
                        data={classBarData} 
                        options={{ 
                            scales: { y: { min: 0, max: 100 } },
                            plugins: { legend: { display: false } }
                        }} 
                    />
                </div>
            </div>

            {/* Critical Alerts Table */}
            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <h3 style={{ marginBottom: '1rem', color: 'var(--error-color)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    ⚠️ Critical Alerts Portfolio
                </h3>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
                        Students requiring immediate attention based on ML risk scoring or low attendance trajectory.
                    </p>
                    <input 
                        type="text" 
                        placeholder="Search by student or class name..." 
                        className="form-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{ width: '300px' }}
                    />
                </div>

                <table className="data-table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Student Name</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Class</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Attendance</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>ML Risk Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(() => {
                            const list = data.at_risk_students || [];
                            if (list.length === 0) {
                                return (
                                    <tr>
                                        <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                            No students currently at risk. Great job!
                                        </td>
                                    </tr>
                                );
                            }

                            const filtered = list.filter(s => 
                                (s.name || '').toLowerCase().includes(searchQuery.toLowerCase()) || 
                                (s.class_name || '').toLowerCase().includes(searchQuery.toLowerCase())
                            );
                            
                            if (filtered.length === 0) {
                                return <tr><td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No matches found for your search.</td></tr>;
                            }
                            
                            return filtered.map((student, idx) => (
                                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '1rem', fontWeight: 500 }}>{student.name || 'Unnamed Student'}</td>
                                    <td style={{ padding: '1rem' }}>{student.class_name || 'N/A'}</td>
                                    <td style={{ padding: '1rem', color: (student.attendance_pct || 0) < 75 ? 'var(--error-color)' : 'inherit' }}>
                                        {student.attendance_pct || 0}%
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <span className={`badge badge-${student.risk_level?.toLowerCase() || 'high'}`}>
                                            {student.risk_level || 'High'} Priority
                                        </span>
                                    </td>
                                </tr>
                            ));
                        })()}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AnalysisDashboard;
