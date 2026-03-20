import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import useStore from '../store/useStore';

const ClassList = () => {
    const { classes, loading, error, fetchClasses, addClass, deleteClass } = useStore();
    const [newClassName, setNewClassName] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchClasses();
    }, [fetchClasses]);

    const handleAddClass = async (e) => {
        e.preventDefault();
        if (!newClassName.trim()) return;
        setIsSubmitting(true);
        await addClass(newClassName);
        setNewClassName('');
        setIsSubmitting(false);
    };

    const filteredClasses = (classes || []).filter(cls => 
        (cls.name || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    const totalStudents = (classes || []).reduce((acc, curr) => acc + (curr.student_count || 0), 0);

    if (loading && (!classes || classes.length === 0)) return <div style={{padding: '2rem'}}>Loading classes...</div>;
    if (error) return <div className="error-text" style={{padding: '2rem'}}>{error}</div>;

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1>Classes Workspace</h1>
                    <p>Managing {(classes || []).length} active classrooms with {totalStudents} students.</p>
                </div>
                
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <div style={{ position: 'relative' }}>
                        <input 
                            type="text" 
                            placeholder="Search classes..." 
                            className="form-input"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{ width: '250px' }}
                        />
                        {searchQuery && (
                            <button 
                                onClick={() => setSearchQuery('')}
                                style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                            >
                                ×
                            </button>
                        )}
                    </div>
                    <form onSubmit={handleAddClass} style={{ display: 'flex', gap: '0.5rem' }}>
                        <input 
                            type="text" 
                            value={newClassName}
                            onChange={(e) => setNewClassName(e.target.value)}
                            placeholder="New Class Name" 
                            className="form-input"
                            disabled={isSubmitting}
                            required
                        />
                        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                            {isSubmitting ? '...' : '+'}
                        </button>
                    </form>
                </div>
            </div>

            <div className="stats-grid" style={{ marginTop: '2rem' }}>
                <div className="stat-card" style={{ padding: '1.5rem', textAlign: 'left', borderLeft: '4px solid var(--accent-primary)' }}>
                    <div className="stat-value" style={{ fontSize: '1.5rem' }}>{(classes || []).length}</div>
                    <div className="stat-label">Total Classes</div>
                </div>
                <div className="stat-card" style={{ padding: '1.5rem', textAlign: 'left', borderLeft: '4px solid var(--accent-secondary)' }}>
                    <div className="stat-value" style={{ fontSize: '1.5rem' }}>{totalStudents}</div>
                    <div className="stat-label">Total Students</div>
                </div>
            </div>

            <div className="stats-grid" style={{ marginTop: '1rem' }}>
                {filteredClasses.length === 0 ? (
                    <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }}>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            {searchQuery ? `No classes found matching "${searchQuery}"` : "No classes created yet. Add one above!"}
                        </p>
                    </div>
                ) : (
                    filteredClasses.map((cls) => (
                        <div key={cls.id} className="stat-card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                                        {cls.name}
                                    </h3>
                                    <div className="stat-label">
                                        {cls.student_count || 0} Students Enrolled
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {
                                        if(window.confirm(`Are you sure you want to delete ${cls.name}?`)) {
                                            deleteClass(cls.id);
                                        }
                                    }}
                                    style={{ 
                                        background: 'none', border: 'none', color: 'var(--error-color)', 
                                        cursor: 'pointer', opacity: 0.6 
                                    }}
                                    title="Delete Class"
                                >
                                    🗑️
                                </button>
                            </div>
                            
                            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem' }}>
                                <Link to={`/class/${cls.id}`} className="btn btn-secondary" style={{ flex: 1, textAlign: 'center', justifyContent: 'center' }}>
                                    Manage
                                </Link>
                                <Link to={`/class/${cls.id}/attendance`} className="btn btn-primary" style={{ flex: 1, textAlign: 'center', justifyContent: 'center' }}>
                                    Attendance
                                </Link>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ClassList;
