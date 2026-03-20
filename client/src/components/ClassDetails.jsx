import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const ClassDetails = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [classroom, setClassroom] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    
    // Add Student Form State
    const [showAddForm, setShowAddForm] = useState(false);
    const [newStudent, setNewStudent] = useState({ name: '', roll_number: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    // Import CSV State
    const [showImportForm, setShowImportForm] = useState(false);
    const [importFile, setImportFile] = useState(null);
    const [isImporting, setIsImporting] = useState(false);

    const fetchClassDetails = async () => {
        try {
            const res = await axios.get(`/api/classes/${id}`);
            setClassroom(res.data);
            setError('');
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to fetch class details');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchClassDetails();
    }, [id]);

    const handleAddStudent = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await axios.post(`/api/classes/${id}/students`, newStudent);
            setNewStudent({ name: '', roll_number: '' });
            setShowAddForm(false);
            fetchClassDetails(); // Refresh list
        } catch (err) {
            alert(err.response?.data?.error || 'Failed to add student');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleImportCSV = async (e) => {
        e.preventDefault();
        if (!importFile) return;
        setIsImporting(true);
        
        const formData = new FormData();
        formData.append('file', importFile);
        
        try {
            const res = await axios.post(`/api/classes/${id}/students/import`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert(res.data.message);
            setImportFile(null);
            setShowImportForm(false);
            fetchClassDetails();
        } catch (err) {
            alert(err.response?.data?.error || 'Failed to import CSV');
        } finally {
            setIsImporting(false);
        }
    };

    const handleDeleteStudent = async (studentId) => {
        if (!window.confirm('Are you sure you want to remove this student?')) return;
        try {
            await axios.delete(`/api/classes/${id}/students/${studentId}`);
            setClassroom(prev => ({
                ...prev,
                students: prev.students.filter(s => s.id !== studentId)
            }));
        } catch (err) {
            alert('Failed to delete student');
        }
    };

    const handleExport = async () => {
        try {
            const res = await axios.get(`/api/classes/${id}/export`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${classroom.name.replace(/ /g, '_')}_Attendance.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert('Failed to export CSV');
        }
    };

    if (loading) return <div>Loading details...</div>;
    if (error) return <div className="error-text" style={{ padding: '2rem' }}>{error} <br/><button onClick={() => navigate('/')} className="btn btn-secondary" style={{marginTop:'1rem'}}>Back</button></div>;
    if (!classroom) return <div>Class not found</div>;

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.5rem', color: 'var(--text-secondary)' }}>←</button>
                        {classroom.name}
                    </h1>
                    <p>{classroom.students.length} Enrolled Students</p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button onClick={handleExport} className="btn btn-secondary" style={{ background: 'var(--surface-color)' }}>
                        ⬇️ Export CSV
                    </button>
                    <button onClick={() => { setShowImportForm(!showImportForm); setShowAddForm(false); }} className="btn btn-secondary" style={{ background: 'var(--surface-color)' }}>
                        ⬆️ Import CSV
                    </button>
                    <Link to={`/class/${id}/attendance`} className="btn btn-primary">
                        Mark Attendance
                    </Link>
                    <Link to={`/class/${id}/analysis`} className="btn btn-secondary">
                        📈 Insights
                    </Link>
                    <button onClick={() => { setShowAddForm(!showAddForm); setShowImportForm(false); }} className="btn btn-secondary">
                        {showAddForm ? 'Cancel' : '+ Student'}
                    </button>
                </div>
            </div>

            {showImportForm && (
                <div className="glass-card" style={{ marginTop: '2rem', padding: '1.5rem', border: '1px solid var(--accent-primary)' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Bulk Import Students (CSV)</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                        Upload a CSV file with at least two columns: <strong>Name, RollNumber</strong>.
                    </p>
                    <form onSubmit={handleImportCSV} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <input 
                            type="file" 
                            accept=".csv"
                            onChange={(e) => setImportFile(e.target.files[0])}
                            className="form-input"
                            style={{ flex: 1, padding: '0.5rem' }}
                            required
                        />
                        <button type="submit" className="btn btn-primary" disabled={isImporting || !importFile}>
                            {isImporting ? 'Importing...' : 'Upload CSV'}
                        </button>
                    </form>
                </div>
            )}

            {showAddForm && (
                <div className="glass-card" style={{ marginTop: '2rem', padding: '1.5rem' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Add New Student</h3>
                    <form onSubmit={handleAddStudent} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Full Name</label>
                            <input 
                                type="text" 
                                className="form-input" 
                                value={newStudent.name}
                                onChange={(e) => setNewStudent({...newStudent, name: e.target.value})}
                                style={{ width: '100%' }}
                                required
                            />
                        </div>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Roll Number</label>
                            <input 
                                type="text" 
                                className="form-input" 
                                value={newStudent.roll_number}
                                onChange={(e) => setNewStudent({...newStudent, roll_number: e.target.value})}
                                style={{ width: '100%' }}
                                required
                            />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                            {isSubmitting ? 'Saving...' : 'Save Student'}
                        </button>
                    </form>
                </div>
            )}
            
            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                <input 
                    type="text" 
                    placeholder="Search by name or roll number..." 
                    className="form-input"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ width: '300px' }}
                />
            </div>

            <div className="glass-card" style={{ marginTop: '1rem' }}>
                <table className="data-table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Roll No.</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Name</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Risk Status</th>
                            <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {classroom.students.length === 0 ? (
                            <tr>
                                <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                    No students enrolled yet.
                                </td>
                            </tr>
                        ) : (() => {
                            const filtered = (classroom.students || []).filter(s => 
                                (s.name || '').toLowerCase().includes(searchQuery.toLowerCase()) || 
                                (s.roll_number || '').toLowerCase().includes(searchQuery.toLowerCase())
                            );
                            
                            if (filtered.length === 0) {
                                return <tr><td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No matches found.</td></tr>;
                            }
                            
                            return filtered.map(student => (
                                <tr key={student.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '1rem', fontFamily: 'monospace' }}>{student.roll_number || 'N/A'}</td>
                                    <td style={{ padding: '1rem', fontWeight: 500 }}>{student.name || 'Unnamed'}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <span className={`badge badge-${student.risk_level?.toLowerCase() || 'low'}`}>
                                            {student.risk_level || 'Low'} Risk
                                        </span>
                                    </td>
                                    <td style={{ padding: '1rem', textAlign: 'right', display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                                        <button 
                                            onClick={() => navigate(`/student/${student.id}/analysis`)}
                                            style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: 600 }}
                                        >
                                            Stats
                                        </button>
                                        <button 
                                            onClick={() => handleDeleteStudent(student.id)}
                                            style={{ background: 'none', border: 'none', color: 'var(--error-color)', cursor: 'pointer', opacity: 0.8 }}
                                        >
                                            Remove
                                        </button>
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

export default ClassDetails;
