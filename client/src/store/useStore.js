import { create } from 'zustand';
import axios from 'axios';

const useStore = create((set) => ({
    classes: [],
    loading: false,
    error: null,

    // Fetch all classes for the faculty
    fetchClasses: async () => {
        set({ loading: true });
        try {
            const res = await axios.get('/api/classes');
            set({ classes: res.data, loading: false });
        } catch (err) {
            set({ error: 'Failed to fetch classes', loading: false });
        }
    },

    // Add a new class
    addClass: async (className) => {
        try {
            const res = await axios.post('/api/classes', { name: className });
            set((state) => ({ classes: [...state.classes, res.data] }));
        } catch (err) {
            set({ error: 'Failed to add class' });
        }
    },

    // Delete a class
    deleteClass: async (classId) => {
        try {
            await axios.delete(`/api/classes/${classId}`);
            set((state) => ({
                classes: state.classes.filter((c) => c.id !== classId)
            }));
        } catch (err) {
            set({ error: 'Failed to delete class' });
        }
    }
}));

export default useStore;
