import { useState, useEffect, useContext } from 'react';
import { Search, MoreVertical, FileText, Image as ImageIcon, Plus, X, Upload, ArrowUpRight, Trash2, Edit2, ExternalLink } from 'lucide-react';
import { UserContext } from '../App';

const FileListView = () => {
    const userId = useContext(UserContext);
    const [groupedFiles, setGroupedFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [uploading, setUploading] = useState(false);

    // Edit State
    const [editingFile, setEditingFile] = useState(null);
    const [editForm, setEditForm] = useState({ filename: '', tags: '' });

    // Detail Modal State
    const [selectedFile, setSelectedFile] = useState(null);

    // Expanded Groups State
    const [expandedGroups, setExpandedGroups] = useState({});

    const toggleGroup = (index) => {
        setExpandedGroups(prev => ({
            ...prev,
            [index]: !prev[index]
        }));
    };

    // Dropdown State
    const [activeDropdown, setActiveDropdown] = useState(null);

    useEffect(() => {
        if (userId) {
            fetchFiles();
        }
    }, [userId]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = () => setActiveDropdown(null);
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    const fetchFiles = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            // Check for URL params for filtering
            const params = new URLSearchParams(window.location.search);
            const tagFilter = params.get('tag');
            const groupFilter = params.get('group_id');

            const response = await fetch(`${apiUrl}/api/files/${userId}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            let groups = data.groups || [];

            // Apply filters if present
            if (tagFilter || groupFilter || searchQuery) {
                groups = groups.map(group => ({
                    ...group,
                    files: group.files.filter(file => {
                        const matchesTag = tagFilter ? (file.tags && file.tags.includes(tagFilter)) : true;
                        const matchesGroup = groupFilter ? file.group_id === groupFilter : true;
                        const matchesSearch = searchQuery ? (
                            file.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            (file.tags && file.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())))
                        ) : true;
                        return matchesTag && matchesGroup && matchesSearch;
                    })
                })).filter(group => group.files.length > 0);
            }

            setGroupedFiles(groups);
        } catch (error) {
            console.error("Failed to fetch files:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (file) => {
        if (!file) return;
        setUploading(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', userId);
            // formData.append('group_id', '...'); // Optional: Add group selection logic later
            // formData.append('tags', '...'); // Optional: Add tag input in upload modal

            const response = await fetch(`${apiUrl}/api/upload`, {
                method: 'POST',
                body: formData,
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });

            if (!response.ok) throw new Error('Upload failed');

            await fetchFiles(); // Refresh list
            setShowUploadModal(false);
        } catch (error) {
            alert('Upload failed: ' + error.message);
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (fileId) => {
        if (!confirm('Are you sure you want to delete this file?')) return;
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/files/${fileId}`, {
                method: 'DELETE',
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });

            if (!response.ok) throw new Error('Delete failed');
            await fetchFiles();
        } catch (error) {
            alert('Delete failed: ' + error.message);
        }
    };

    const openEditModal = (file) => {
        setEditingFile(file);
        setEditForm({
            filename: file.filename,
            tags: file.tags ? file.tags.join(', ') : ''
        });
        setShowEditModal(true);
        setActiveDropdown(null);
    };

    const handleUpdate = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/files/${editingFile.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    filename: editForm.filename,
                    tags: editForm.tags.split(',').map(t => t.trim()).filter(t => t)
                })
            });

            if (!response.ok) throw new Error('Update failed');
            await fetchFiles();
            setShowEditModal(false);
        } catch (error) {
            alert('Update failed: ' + error.message);
        }
    };

    const getFileIcon = (type) => {
        if (type === 'pdf') return <FileText size={24} className="text-danger" />;
        if (type === 'image' || type === 'png' || type === 'jpg') return <ImageIcon size={24} className="text-success" />;
        return <FileText size={24} className="text-secondary" />;
    };

    const getIconBgColor = (type) => {
        if (type === 'pdf') return 'bg-danger bg-opacity-10';
        if (type === 'image' || type === 'png' || type === 'jpg') return 'bg-success bg-opacity-10';
        return 'bg-secondary bg-opacity-10';
    }

    return (
        <div className="mt-3">
            {/* Search Bar */}
            <div className="mb-4">
                <div className="position-relative">
                    <input
                        type="text"
                        className="form-control bg-clean-gray border-0 ps-5"
                        placeholder="Search files..."
                        style={{ borderRadius: '12px', height: '48px' }}
                        value={searchQuery}
                        onChange={(e) => {
                            setSearchQuery(e.target.value);
                            fetchFiles(); // Trigger re-filter
                        }}
                    />
                    <Search className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" size={18} />
                </div>
            </div>

            {/* File Sections */}
            {loading ? (
                <div className="text-center py-5 text-muted">Loading files...</div>
            ) : groupedFiles.length === 0 ? (
                <div className="text-center py-5 text-muted">No files found.</div>
            ) : (
                groupedFiles.map((group, index) => {
                    const isExpanded = expandedGroups[index];
                    const displayedFiles = isExpanded ? group.files : group.files.slice(0, 3);
                    const hasMore = group.files.length > 3;

                    return (
                        <div key={index} className="mb-4">
                            <div className="d-flex justify-content-between align-items-center mb-3 px-1">
                                <h5 className="fw-bold mb-0">{group.group_name}</h5>
                                {hasMore && (
                                    <button
                                        className="btn btn-link text-decoration-none text-success p-0 fw-medium"
                                        style={{ fontSize: '14px' }}
                                        onClick={() => toggleGroup(index)}
                                    >
                                        {isExpanded ? 'Show Less' : `View all (${group.files.length})`}
                                    </button>
                                )}
                            </div>
                            <div className="d-flex flex-column gap-3">
                                {displayedFiles.map((file) => (
                                    <div
                                        key={file.id}
                                        className="card border-0 shadow-sm"
                                        style={{ borderRadius: '16px', cursor: 'pointer' }}
                                        onClick={() => setSelectedFile(file)}
                                    >
                                        <div className="card-body p-3">
                                            <div className="d-flex align-items-start">
                                                {/* File Icon */}
                                                <div className={`file-icon ${getIconBgColor(file.file_type)} me-3 flex-shrink-0`} style={{ width: '48px', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '12px' }}>
                                                    {getFileIcon(file.file_type)}
                                                </div>

                                                {/* File Info */}
                                                <div className="flex-grow-1" style={{ minWidth: 0 }}>
                                                    <div className="d-flex justify-content-between align-items-start">
                                                        <h6 className="card-title mb-1 fw-bold text-truncate pe-2" style={{ fontSize: '15px' }}>{file.filename}</h6>

                                                        {/* Actions Dropdown */}
                                                        <div className="position-relative ms-2">
                                                            <button
                                                                className="btn btn-link text-muted p-0"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setActiveDropdown(activeDropdown === file.id ? null : file.id);
                                                                }}
                                                            >
                                                                <MoreVertical size={20} />
                                                            </button>

                                                            {activeDropdown === file.id && (
                                                                <div className="position-absolute end-0 mt-2 bg-white shadow-sm rounded-3 py-2" style={{ zIndex: 100, minWidth: '150px', border: '1px solid #eee' }}>
                                                                    <button className="dropdown-item px-3 py-2 d-flex align-items-center gap-2" onClick={(e) => { e.stopPropagation(); openEditModal(file); }}>
                                                                        <Edit2 size={16} /> Edit
                                                                    </button>
                                                                    <a href={file.url} target="_blank" rel="noopener noreferrer" className="dropdown-item px-3 py-2 d-flex align-items-center gap-2 text-decoration-none text-dark" onClick={(e) => e.stopPropagation()}>
                                                                        <ExternalLink size={16} /> Preview
                                                                    </a>
                                                                    <div className="dropdown-divider my-1 border-top"></div>
                                                                    <button className="dropdown-item px-3 py-2 d-flex align-items-center gap-2 text-danger" onClick={(e) => { e.stopPropagation(); handleDelete(file.id); }}>
                                                                        <Trash2 size={16} /> Delete
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Tags & Date */}
                                                    <div className="d-flex align-items-center flex-wrap gap-1 mt-1">
                                                        {file.tags && file.tags.slice(0, 3).map((tag, i) => (
                                                            <span key={i} className="badge bg-secondary bg-opacity-10 text-secondary fw-normal" style={{ fontSize: '10px', maxWidth: '80px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                {tag}
                                                            </span>
                                                        ))}
                                                        {file.tags && file.tags.length > 3 && (
                                                            <span className="badge bg-secondary bg-opacity-10 text-secondary fw-normal" style={{ fontSize: '10px' }}>
                                                                +{file.tags.length - 3}
                                                            </span>
                                                        )}
                                                        <small className="text-muted ms-auto" style={{ fontSize: '10px' }}>{new Date(file.upload_date).toLocaleDateString()}</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })
            )}

            {/* Floating Action Button */}
            <button
                onClick={() => setShowUploadModal(true)}
                className="fab border-0"
            >
                <Plus size={24} />
            </button>

            {/* Upload Modal */}
            {showUploadModal && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Upload File</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowUploadModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <input
                                        type="file"
                                        id="fileInput"
                                        className="d-none"
                                        onChange={(e) => handleUpload(e.target.files[0])}
                                        accept=".pdf,.jpg,.jpeg,.png"
                                    />
                                    <label htmlFor="fileInput" className="d-block cursor-pointer">
                                        <div className="border border-2 border-dashed rounded-3 p-5 text-center mb-3 bg-light">
                                            <div className="bg-success bg-opacity-10 rounded-circle d-inline-flex p-3 mb-3">
                                                {uploading ? <div className="spinner-border text-success" role="status"></div> : <Upload className="text-success" size={32} />}
                                            </div>
                                            <p className="mb-1 fw-medium">{uploading ? "Uploading..." : "Tap to browse files"}</p>
                                            <small className="text-muted">PDF, JPG, PNG (Max 10MB)</small>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}

            {/* Edit Modal */}
            {showEditModal && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Edit File</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowEditModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label className="form-label">Filename</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={editForm.filename}
                                            onChange={(e) => setEditForm({ ...editForm, filename: e.target.value })}
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Tags (comma separated)</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={editForm.tags}
                                            onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                                        />
                                    </div>
                                    <button className="btn bg-line-green text-white w-100 py-2 rounded-3 fw-bold" onClick={handleUpdate}>
                                        Save Changes
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}

            {/* File Detail Modal */}
            {selectedFile && (
                <>
                    <div className="modal show d-block" tabIndex="-1" onClick={() => setSelectedFile(null)}>
                        <div className="modal-dialog modal-dialog-centered modal-dialog-scrollable">
                            <div className="modal-content" style={{ borderRadius: '16px' }} onClick={e => e.stopPropagation()}>
                                <div className="modal-header border-0 pb-0">
                                    <h5 className="modal-title fw-bold text-truncate pe-2">{selectedFile.filename}</h5>
                                    <button type="button" className="btn-close" onClick={() => setSelectedFile(null)}></button>
                                </div>
                                <div className="modal-body">
                                    {/* Tags */}
                                    <div className="mb-3">
                                        <div className="d-flex flex-wrap gap-2">
                                            {selectedFile.tags && selectedFile.tags.map((tag, i) => (
                                                <span key={i} className="badge bg-secondary bg-opacity-10 text-secondary fw-normal">
                                                    {tag}
                                                </span>
                                            ))}
                                            {(!selectedFile.tags || selectedFile.tags.length === 0) && (
                                                <span className="text-muted small">No tags</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Summary */}
                                    <div className="mb-4">
                                        <h6 className="fw-bold mb-2">Summary</h6>
                                        <div className="bg-light p-3 rounded-3 text-muted small" style={{ lineHeight: '1.6' }}>
                                            {selectedFile.detail_summary || "No summary available for this file."}
                                        </div>
                                    </div>

                                    {/* Meta Info */}
                                    <div className="d-flex justify-content-between text-muted small mb-3">
                                        <span>Type: {selectedFile.file_type.toUpperCase()}</span>
                                        <span>Uploaded: {new Date(selectedFile.upload_date).toLocaleDateString()}</span>
                                    </div>
                                </div>
                                <div className="modal-footer border-0 pt-0 flex-column gap-2">
                                    <a href={selectedFile.url} target="_blank" rel="noopener noreferrer" className="btn bg-line-green text-white w-100 fw-bold py-2 rounded-3">
                                        Download / View File
                                    </a>
                                    <div className="d-flex gap-2 w-100">
                                        <button className="btn btn-outline-secondary flex-grow-1 rounded-3" onClick={() => { setSelectedFile(null); openEditModal(selectedFile); }}>
                                            Edit
                                        </button>
                                        <button className="btn btn-outline-danger flex-grow-1 rounded-3" onClick={() => { setSelectedFile(null); handleDelete(selectedFile.id); }}>
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}
        </div>
    );
};

export default FileListView;
