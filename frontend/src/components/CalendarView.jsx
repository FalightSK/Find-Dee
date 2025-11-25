import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Edit, Plus, Trash2, X, CheckCircle, Circle } from 'lucide-react'

export default function CalendarView() {
    const [tasks, setTasks] = useState([])
    const [showAddTaskModal, setShowAddTaskModal] = useState(false)
    const [showManageModal, setShowManageModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)

    const [selectedTask, setSelectedTask] = useState(null)
    const [editingTask, setEditingTask] = useState(null)

    const [newTask, setNewTask] = useState({ title: '', tags: '', date: '', color: 'primary' })

    // Realtime Calendar State
    const [currentDate, setCurrentDate] = useState(new Date())
    const [calendarDays, setCalendarDays] = useState([])
    const [loading, setLoading] = useState(false)

    // Mock User ID (Replace with LIFF context in real app)
    const userId = "Ua8e2b0a894035997230eab28885ce36f"
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

    const daysOfWeek = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

    useEffect(() => {
        generateCalendarDays(currentDate)
    }, [currentDate])

    useEffect(() => {
        fetchTasks()
    }, [])

    const fetchTasks = async () => {
        setLoading(true)
        try {
            const response = await fetch(`${apiUrl}/api/dates/${userId}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            })
            if (response.ok) {
                const data = await response.json()
                setTasks(data.dates || [])
            }
        } catch (error) {
            console.error("Failed to fetch tasks:", error)
        } finally {
            setLoading(false)
        }
    }

    const generateCalendarDays = (date) => {
        const year = date.getFullYear()
        const month = date.getMonth()

        const firstDayOfMonth = new Date(year, month, 1).getDay()
        const daysInMonth = new Date(year, month + 1, 0).getDate()

        const days = []

        // Empty cells before first day
        for (let i = 0; i < firstDayOfMonth; i++) {
            days.push(null)
        }

        // Actual days
        for (let day = 1; day <= daysInMonth; day++) {
            days.push(day)
        }

        setCalendarDays(days)
    }

    const changeMonth = (offset) => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + offset, 1)
        setCurrentDate(newDate)
    }

    const handleAddTask = async () => {
        if (!newTask.title || !newTask.date) {
            alert("Please fill in at least title and date")
            return
        }

        const tagsList = newTask.tags.split(',').map(t => t.trim()).filter(t => t)

        try {
            const response = await fetch(`${apiUrl}/api/dates`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    ...newTask,
                    tags: tagsList,
                    owner_id: userId
                })
            })

            if (response.ok) {
                await fetchTasks()
                setNewTask({ title: '', tags: '', date: '', color: 'primary' })
                setShowAddTaskModal(false)
            } else {
                alert("Failed to add task")
            }
        } catch (error) {
            alert("Error adding task: " + error.message)
        }
    }

    const handleUpdateTask = async () => {
        if (!editingTask || !editingTask.title || !editingTask.date) return

        const tagsList = typeof editingTask.tags === 'string'
            ? editingTask.tags.split(',').map(t => t.trim()).filter(t => t)
            : editingTask.tags

        try {
            const response = await fetch(`${apiUrl}/api/dates/${editingTask.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    title: editingTask.title,
                    tags: tagsList,
                    date: editingTask.date,
                    color: editingTask.color
                })
            })

            if (response.ok) {
                await fetchTasks()
                setShowEditModal(false)
                setEditingTask(null)
            } else {
                alert("Failed to update task")
            }
        } catch (error) {
            alert("Error updating task: " + error.message)
        }
    }

    const handleDeleteTask = async (taskId) => {
        if (!confirm("Are you sure you want to delete this task?")) return

        try {
            const response = await fetch(`${apiUrl}/api/dates/${taskId}`, {
                method: 'DELETE',
                headers: { 'ngrok-skip-browser-warning': 'true' }
            })

            if (response.ok) {
                await fetchTasks()
                if (selectedTask?.id === taskId) setSelectedTask(null)
                if (showManageModal) setShowManageModal(true) // Refresh list
            } else {
                alert("Failed to delete task")
            }
        } catch (error) {
            alert("Error deleting task: " + error.message)
        }
    }

    const handleToggleComplete = async (task) => {
        try {
            const response = await fetch(`${apiUrl}/api/dates/${task.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    is_complete: !task.is_complete
                })
            })

            if (response.ok) {
                await fetchTasks()
                if (selectedTask?.id === task.id) {
                    setSelectedTask(prev => ({ ...prev, is_complete: !prev.is_complete }))
                }
            }
        } catch (error) {
            console.error("Error toggling complete:", error)
        }
    }

    const openEditModal = (task) => {
        // Convert tags array to string for editing
        const tagsStr = Array.isArray(task.tags) ? task.tags.join(', ') : (task.tags || '')
        setEditingTask({ ...task, tags: tagsStr })
        setShowEditModal(true)
        setShowManageModal(false)
        setSelectedTask(null)
    }

    const handleTaskClick = (task) => {
        setSelectedTask(task)
    }

    const formatMonthYear = (date) => {
        return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    }

    const isToday = (day) => {
        const today = new Date()
        return day === today.getDate() &&
            currentDate.getMonth() === today.getMonth() &&
            currentDate.getFullYear() === today.getFullYear()
    }

    const getTasksForDay = (day) => {
        if (!day) return []
        const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
        return tasks.filter(task => task.date === dateStr)
    }

    // Sort tasks: Incomplete first, then by date
    const sortedTasks = [...tasks].sort((a, b) => {
        if (a.is_complete === b.is_complete) {
            return new Date(a.date) - new Date(b.date)
        }
        return a.is_complete ? 1 : -1
    })

    return (
        <div className="mt-3 position-relative" style={{ minHeight: 'calc(100vh - 180px)' }}>
            {/* Header */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2 className="fw-bold mb-0">Planner</h2>
                <button className="btn btn-link text-dark p-2" onClick={() => setShowManageModal(true)}>
                    <Edit size={20} />
                </button>
            </div>

            {/* Calendar Widget */}
            <div className="card shadow-soft mb-4" style={{ borderRadius: '16px' }}>
                <div className="card-body p-2">
                    {/* Month Navigation */}
                    <div className="d-flex justify-content-between align-items-center mb-3">
                        <button className="btn btn-link text-dark p-1" onClick={() => changeMonth(-1)}>
                            <ChevronLeft size={20} />
                        </button>
                        <h5 className="mb-0 fw-semibold">{formatMonthYear(currentDate)}</h5>
                        <button className="btn btn-link text-dark p-1" onClick={() => changeMonth(1)}>
                            <ChevronRight size={20} />
                        </button>
                    </div>

                    {/* Days of Week */}
                    <div className="row g-0 mb-2">
                        {daysOfWeek.map((day, index) => (
                            <div key={index} className="col text-center">
                                <small className="text-muted fw-semibold">{day}</small>
                            </div>
                        ))}
                    </div>

                    {/* Calendar Grid */}
                    <div className="calendar-grid">
                        {calendarDays.map((day, index) => {
                            const dayTasks = getTasksForDay(day)
                            const hasIncompleteTasks = dayTasks.some(t => !t.is_complete)

                            return (
                                <div key={index} className="calendar-cell">
                                    {day && (
                                        <div className="position-relative w-100 h-100 d-flex align-items-center justify-content-center">
                                            <div
                                                className={`calendar-day ${isToday(day) ? 'active' : ''}`}
                                                onClick={() => {
                                                    const firstTask = dayTasks[0]
                                                    if (firstTask) handleTaskClick(firstTask)
                                                }}
                                            >
                                                {day}
                                            </div>
                                            <div className="d-flex gap-1 position-absolute" style={{ bottom: '4px' }}>
                                                {dayTasks.slice(0, 3).map(task => (
                                                    <div
                                                        key={task.id}
                                                        className={`rounded-circle bg-${task.is_complete ? 'secondary' : task.color || 'primary'}`}
                                                        style={{ width: '4px', height: '4px' }}
                                                    ></div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Upcoming Section */}
            <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                    <h5 className="fw-bold mb-0">Upcoming Tasks</h5>
                </div>
                <div className="d-grid gap-3">
                    {loading ? (
                        <div className="text-center py-4 text-muted">Loading tasks...</div>
                    ) : sortedTasks.length === 0 ? (
                        <div className="text-center py-4 text-muted">No upcoming tasks</div>
                    ) : (
                        sortedTasks.map((item) => {
                            const dateObj = new Date(item.date)
                            const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase()
                            const dayNum = dateObj.getDate()

                            return (
                                <div
                                    key={item.id}
                                    className={`card shadow-soft ${item.is_complete ? 'opacity-50' : ''}`}
                                    style={{ borderRadius: '12px', cursor: 'pointer' }}
                                    onClick={() => handleTaskClick(item)}
                                >
                                    <div className="card-body p-3">
                                        <div className="d-flex align-items-center">
                                            <div className="text-center me-3" style={{ width: '50px' }}>
                                                <div className={`text-${item.color || 'success'} fw-bold`} style={{ fontSize: '11px', letterSpacing: '0.5px' }}>
                                                    {dayName}
                                                </div>
                                                <div className="fw-bold" style={{ fontSize: '24px', lineHeight: '1' }}>
                                                    {dayNum}
                                                </div>
                                            </div>
                                            <div className="flex-grow-1">
                                                <h6 className={`mb-1 fw-semibold ${item.is_complete ? 'text-decoration-line-through' : ''}`} style={{ fontSize: '15px' }}>
                                                    {item.title}
                                                </h6>
                                                <div className="d-flex gap-1 flex-wrap">
                                                    {item.tags && item.tags.map((tag, idx) => (
                                                        <span key={idx} className={`badge bg-${item.color || 'primary'} bg-opacity-25 text-${item.color || 'primary'}`} style={{ fontSize: '11px' }}>
                                                            {tag}
                                                        </span>
                                                    ))}
                                                    {(!item.tags || item.tags.length === 0) && (
                                                        <span className="text-muted small">No tags</span>
                                                    )}
                                                </div>
                                            </div>
                                            {item.is_complete && <CheckCircle size={20} className="text-success" />}
                                        </div>
                                    </div>
                                </div>
                            )
                        })
                    )}
                </div>
            </div>

            {/* Floating Action Button */}
            <button className="fab" onClick={() => setShowAddTaskModal(true)}>
                <Plus size={24} />
            </button>

            {/* Add Task Modal */}
            {showAddTaskModal && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Add New Task</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowAddTaskModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Task Title</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            placeholder="e.g., Final Exam"
                                            value={newTask.title}
                                            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Tags</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            placeholder="e.g., Math, Homework (comma separated)"
                                            value={newTask.tags}
                                            onChange={(e) => setNewTask({ ...newTask, tags: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Due Date</label>
                                        <input
                                            type="date"
                                            className="form-control"
                                            value={newTask.date}
                                            onChange={(e) => setNewTask({ ...newTask, date: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Color Tag</label>
                                        <div className="d-flex gap-2">
                                            {['primary', 'success', 'warning', 'danger'].map(color => (
                                                <div
                                                    key={color}
                                                    className={`rounded-circle bg-${color} ${newTask.color === color ? 'border border-dark border-2' : ''}`}
                                                    style={{ width: '24px', height: '24px', cursor: 'pointer' }}
                                                    onClick={() => setNewTask({ ...newTask, color })}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </div>
                                <div className="modal-footer border-0">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowAddTaskModal(false)}>Cancel</button>
                                    <button type="button" className="btn bg-line-green text-white" onClick={handleAddTask}>Add Task</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}

            {/* Edit Task Modal */}
            {showEditModal && editingTask && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Edit Task</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowEditModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Task Title</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={editingTask.title}
                                            onChange={(e) => setEditingTask({ ...editingTask, title: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Tags</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            placeholder="e.g., Math, Homework"
                                            value={editingTask.tags}
                                            onChange={(e) => setEditingTask({ ...editingTask, tags: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Due Date</label>
                                        <input
                                            type="date"
                                            className="form-control"
                                            value={editingTask.date}
                                            onChange={(e) => setEditingTask({ ...editingTask, date: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label fw-semibold">Color Tag</label>
                                        <div className="d-flex gap-2">
                                            {['primary', 'success', 'warning', 'danger'].map(color => (
                                                <div
                                                    key={color}
                                                    className={`rounded-circle bg-${color} ${editingTask.color === color ? 'border border-dark border-2' : ''}`}
                                                    style={{ width: '24px', height: '24px', cursor: 'pointer' }}
                                                    onClick={() => setEditingTask({ ...editingTask, color })}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </div>
                                <div className="modal-footer border-0">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowEditModal(false)}>Cancel</button>
                                    <button type="button" className="btn bg-line-green text-white" onClick={handleUpdateTask}>Save Changes</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}

            {/* Manage Tasks Modal */}
            {showManageModal && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Manage Tasks</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowManageModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <p className="text-muted small mb-3">Edit details or remove tasks.</p>
                                    <div className="list-group list-group-flush">
                                        {sortedTasks.map(task => (
                                            <div key={task.id} className="list-group-item d-flex justify-content-between align-items-center px-0">
                                                <div>
                                                    <div className={`fw-semibold ${task.is_complete ? 'text-decoration-line-through text-muted' : ''}`}>
                                                        {task.title}
                                                    </div>
                                                    <small className="text-muted">
                                                        {task.tags && task.tags.length > 0 ? task.tags.join(', ') : 'No tags'} • {task.date}
                                                    </small>
                                                </div>
                                                <div className="d-flex gap-2">
                                                    <button className="btn btn-sm btn-outline-secondary" onClick={() => openEditModal(task)}>
                                                        <Edit size={16} />
                                                    </button>
                                                    <button className="btn btn-sm btn-outline-danger" onClick={() => handleDeleteTask(task.id)}>
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="modal-footer border-0">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowManageModal(false)}>Close</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}

            {/* Task Detail Modal */}
            {selectedTask && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Task Details</h5>
                                    <button type="button" className="btn-close" onClick={() => setSelectedTask(null)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="text-center mb-4">
                                        <div className="d-flex gap-1 justify-content-center mb-2 flex-wrap">
                                            {selectedTask.tags && selectedTask.tags.map((tag, idx) => (
                                                <div key={idx} className={`badge bg-${selectedTask.color || 'primary'} bg-opacity-25 text-${selectedTask.color || 'primary'}`} style={{ fontSize: '12px' }}>
                                                    {tag}
                                                </div>
                                            ))}
                                            {(!selectedTask.tags || selectedTask.tags.length === 0) && (
                                                <span className="text-muted small">No tags</span>
                                            )}
                                        </div>
                                        <h4 className={`fw-bold ${selectedTask.is_complete ? 'text-decoration-line-through' : ''}`}>{selectedTask.title}</h4>
                                        <p className="text-muted">Due: {selectedTask.date}</p>
                                    </div>
                                    {!selectedTask.is_complete && (
                                        <div className="alert alert-warning">
                                            <small>⏰ Don't forget to complete this task!</small>
                                        </div>
                                    )}
                                    {selectedTask.is_complete && (
                                        <div className="alert alert-success">
                                            <small>🎉 Great job! This task is complete.</small>
                                        </div>
                                    )}
                                </div>
                                <div className="modal-footer border-0">
                                    <button type="button" className="btn btn-outline-danger" onClick={() => handleDeleteTask(selectedTask.id)}>Delete</button>
                                    <button type="button" className="btn btn-outline-secondary" onClick={() => openEditModal(selectedTask)}>Edit</button>
                                    <button
                                        type="button"
                                        className={`btn ${selectedTask.is_complete ? 'btn-secondary' : 'bg-line-green text-white'}`}
                                        onClick={() => handleToggleComplete(selectedTask)}
                                    >
                                        {selectedTask.is_complete ? 'Mark Undone' : 'Mark as Done'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}
        </div>
    )
}
