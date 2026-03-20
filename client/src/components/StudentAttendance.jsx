import React, { useState, useEffect } from 'react';
import axios from 'axios';

const StudentAttendance = () => {
    const [attendance, setAttendance] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAttendance = async () => {
            try {
                const res = await axios.get('/api/student/attendance');
                setAttendance(res.data);
            } catch (err) {
                console.error(err);
                setError('Failed to load attendance records');
            } finally {
                setLoading(false);
            }
        };
        fetchAttendance();
    }, []);

    if (loading) return <div className="dashboard-content">Loading records...</div>;
    if (error) return <div className="dashboard-content error-text">{error}</div>;

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header">
                <h1>My Attendance Log</h1>
                <p>Full history of your presence in all sessions.</p>
            </div>

            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <table className="data-table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Date</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Session</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {attendance.length === 0 ? (
                            <tr>
                                <td colSpan="3" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                    No attendance records found.
                                </td>
                            </tr>
                        ) : (
                            attendance.map((record, idx) => (
                                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '1rem' }}>{record.date || 'N/A'}</td>
                                    <td style={{ padding: '1rem', fontWeight: 500 }}>{record.session || 'N/A'}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <span className={`badge badge-${record.status === 'Present' ? 'low' : 'high'}`}>
                                            {record.status || 'Status Unknown'}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default StudentAttendance;
