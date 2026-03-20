import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const DailyAttendance = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    
    // YYYY-MM-DD
    const getTodayStr = () => {
        const d = new Date();
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    };

    const [date, setDate] = useState(getTodayStr());
    const [classroom, setClassroom] = useState(null);
    const [attendanceData, setAttendanceData] = useState({}); // { studentId: { sessionName: boolean } }
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    const fetchData = async (selectedDate) => {
        setLoading(true);
        try {
            // First we need class details for roster and sessions
            const classRes = await axios.get(`/api/classes/${id}`);
            setClassroom(classRes.data);
            
            // Note: Our current API doesn't fetch sessions inside /api/classes/:id
            // so we fetch sessions separately
            const sessionsRes = await axios.get(`/api/classes/${id}/sessions`);
            // Attach sessions to classroom obj
            const classObj = { ...classRes.data, sessions: sessionsRes.data };
            
            // If no sessions exist, simulate standard morning/afternoon for a smooth UI experience
            if (!classObj.sessions || classObj.sessions.length === 0) {
                 classObj.sessions = [{id: 1, name: 'Morning'}, {id: 2, name: 'Afternoon'}];
            }
            setClassroom(classObj);
            
            // Now fetch attendance for this date
            const attRes = await axios.get(`/api/classes/${id}/attendance`, { params: { date: selectedDate } });
            
            const attMap = attRes.data?.attendance || {};
            const initialMap = {};
            (classObj.students || []).forEach(student => {
                initialMap[student.id] = {};
                (classObj.sessions || []).forEach(session => {
                     initialMap[student.id][session.name] = attMap[student.id]?.[session.name] || false;
                });
            });
            setAttendanceData(initialMap);

        } catch (err) {
            console.error(err);
            alert('Failed to load attendance data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData(date);
    }, [id, date]);

    const handleToggle = (studentId, sessionName) => {
        setAttendanceData(prev => ({
            ...prev,
            [studentId]: {
                ...prev[studentId],
                [sessionName]: !prev[studentId][sessionName]
            }
        }));
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await axios.post(`/api/classes/${id}/attendance/daily`, {
                date: date,
                attendance: attendanceData
            });
            alert('Attendance saved successfully!');
            navigate(`/class/${id}`);
        } catch (err) {
            alert('Failed to save attendance');
        } finally {
            setIsSaving(false);
        }
    };

    if (loading && !classroom) return <div>Loading roster...</div>;
    if (!classroom) return <div>Class not found</div>;

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <button onClick={() => navigate(`/class/${id}`)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.5rem', color: 'var(--text-secondary)' }}>←</button>
                        Mark Attendance
                    </h1>
                    <p>{classroom.name}</p>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'var(--surface-color)', padding: '0.5rem', borderRadius: '12px', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '1.25rem' }}>📅</span>
                        <input 
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            style={{
                                background: 'transparent',
                                border: 'none',
                                color: 'var(--text-primary)',
                                fontWeight: 600,
                                fontSize: '1rem',
                                colorScheme: 'dark', // Native dark mode calendar fix
                                outline: 'none'
                            }}
                        />
                    </div>
                    <button 
                        onClick={handleSave} 
                        className="btn btn-primary" 
                        disabled={isSaving}
                        style={{ padding: '0.75rem 2rem' }}
                    >
                        {isSaving ? 'Saving...' : 'Save Attendance'}
                    </button>
                </div>
            </div>

            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <table className="data-table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, width: '120px' }}>Roll No.</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Name</th>
                            {classroom.sessions.map((sess, idx) => (
                                <th key={idx} style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textAlign: 'center' }}>
                                    {sess.name}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {(!classroom.students || classroom.students.length === 0) ? (
                            <tr>
                                <td colSpan={2 + (classroom.sessions || []).length} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                    No students enrolled in this class.
                                </td>
                            </tr>
                        ) : (
                            classroom.students
                                .sort((a, b) => (a.roll_number || '').localeCompare(b.roll_number || ''))
                                .map(student => (
                                <tr key={student.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '1rem', fontFamily: 'monospace' }}>{student.roll_number || 'N/A'}</td>
                                    <td style={{ padding: '1rem', fontWeight: 500 }}>{student.name || 'Unnamed'}</td>
                                    {(classroom.sessions || []).map((sess, idx) => (
                                        <td key={idx} style={{ padding: '1rem', textAlign: 'center' }}>
                                            <input 
                                                type="checkbox"
                                                checked={attendanceData[student.id]?.[sess.name] || false}
                                                onChange={() => handleToggle(student.id, sess.name)}
                                                style={{
                                                    width: '20px',
                                                    height: '20px',
                                                    cursor: 'pointer',
                                                    accentColor: 'var(--accent-primary)'
                                                }}
                                            />
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DailyAttendance;
