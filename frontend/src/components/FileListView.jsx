import { useState, useEffect, useContext, useRef } from 'react';
import { Search, MoreVertical, FileText, Image as ImageIcon, Plus, X, Upload, ArrowUpRight, Trash2, Edit2, ExternalLink, Folder, ArrowLeft, Filter, CheckCircle, Circle, Layers } from 'lucide-react';
import { UserContext } from '../App';

const FileListView = () => {
    const userId = useContext(UserContext);
    const [groupedFiles, setGroupedFiles] = useState([]);
    const [knownUsers, setKnownUsers] = useState({});
    const [loading, setLoading] = useState(true);
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [uploading, setUploading] = useState(false);

    // Navigation & Filter State
    const [currentFolder, setCurrentFolder] = useState(null); // null = Home, object = Folder
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [uploaderFilter, setUploaderFilter] = useState('');

    // Edit State
    const [editingFile, setEditingFile] = useState(null);
    const [editForm, setEditForm] = useState({ filename: '', tags: '' });

    // Detail Modal State
    const [selectedFile, setSelectedFile] = useState(null);

    // Dropdown State
    const [activeDropdown, setActiveDropdown] = useState(null);

    // Selection Mode State
    const [selectionMode, setSelectionMode] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState(new Set());
    const longPressTimer = useRef(null);

    // Collection Modal State
    const [showCollectionModal, setShowCollectionModal] = useState(false);
    const [userCollections, setUserCollections] = useState([]);

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

    useEffect(() => {
        if (searchQuery.trim()) {
            performSearch();
        }
    }, [uploaderFilter]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            if (searchQuery.trim()) {
                performSearch();
            } else {
                setSearchResults([]);
                setIsSearching(false);
            }
        }
    };

    const performSearch = async () => {
        setIsSearching(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const groupId = currentFolder ? currentFolder.group_id : null;

            const response = await fetch(`${apiUrl}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    query: searchQuery,
                    user_id: userId,
                    group_id: groupId,
                    owner_id: uploaderFilter || null
                })
            });

            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            setSearchResults(data.results || []);
        } catch (error) {
            console.error("Search error:", error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    };

    const fetchFiles = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/files/${userId}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            setGroupedFiles(data.groups || []);
            setKnownUsers(data.known_users || {});
        } catch (error) {
            console.error("Failed to fetch files:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchCollections = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/collections/${userId}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            const data = await response.json();
            setUserCollections(data.collections || []);
        } catch (error) {
            console.error("Failed to fetch collections:", error);
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

            // If inside a folder (and it's not "My Uploads"), pre-fill group_id
            if (currentFolder && currentFolder.group_name !== "My Uploads" && currentFolder.files.length > 0) {
                const groupId = currentFolder.files[0].group_id;
                if (groupId) {
                    formData.append('group_id', groupId);
                }
            }

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

            const updatedGroups = await (await fetch(`${apiUrl}/api/files/${userId}`)).json();
            setGroupedFiles(updatedGroups.groups || []);
            if (currentFolder) {
                const updatedFolder = updatedGroups.groups.find(g => g.group_name === currentFolder.group_name);
                setCurrentFolder(updatedFolder || null);
            }
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

            // Update current folder view if active
            if (currentFolder) {
                // Re-fetch to get updated data
                const updatedGroups = await (await fetch(`${apiUrl}/api/files/${userId}`)).json();
                setGroupedFiles(updatedGroups.groups || []);
                const updatedFolder = updatedGroups.groups.find(g => g.group_name === currentFolder.group_name);
                setCurrentFolder(updatedFolder || null);
            }

            setShowEditModal(false);
        } catch (error) {
            alert('Update failed: ' + error.message);
        }
    };

    // --- Selection Mode Logic ---

    const handleTouchStart = (file) => {
        if (selectionMode) return;
        longPressTimer.current = setTimeout(() => {
            setSelectionMode(true);
            toggleSelection(file.id);
            // Vibrate if supported
            if (navigator.vibrate) navigator.vibrate(50);
        }, 500); // 500ms long press
    };

    const handleTouchEnd = () => {
        if (longPressTimer.current) {
            clearTimeout(longPressTimer.current);
            longPressTimer.current = null;
        }
    };

    const toggleSelection = (fileId) => {
        const newSelected = new Set(selectedFiles);
        if (newSelected.has(fileId)) {
            newSelected.delete(fileId);
        } else {
            newSelected.add(fileId);
        }
        setSelectedFiles(newSelected);

        if (newSelected.size === 0 && selectionMode) {
            setSelectionMode(false);
        }
    };

    const handleCardClick = (file) => {
        if (selectionMode) {
            toggleSelection(file.id);
        } else {
            setSelectedFile(file);
        }
    };

    const openCollectionModal = () => {
        fetchCollections();
        setShowCollectionModal(true);
    };

    const addSelectedToCollection = async (collection) => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            // 1. Get current collection details to get existing file IDs
            const detailResponse = await fetch(`${apiUrl}/api/collections/detail/${collection.id}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            const detailData = await detailResponse.json();
            const existingIds = detailData.files.map(f => f.id);

            // 2. Merge with selected files
            const newIds = Array.from(selectedFiles);
            const mergedIds = Array.from(new Set([...existingIds, ...newIds]));

            // 3. Update collection
            await fetch(`${apiUrl}/api/collections/${collection.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    file_ids: mergedIds
                })
            });

            alert(`Added ${newIds.length} files to ${collection.name}`);
            setSelectionMode(false);
            setSelectedFiles(new Set());
            setShowCollectionModal(false);
        } catch (error) {
            alert('Failed to add to collection: ' + error.message);
        }
    };

    // --- Render Helpers ---

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

    const getUploaderName = (ownerId) => {
        if (ownerId === userId) return "You";
        return knownUsers[ownerId] || `User ${ownerId.substring(0, 4)}...`;
    };

    // Filter files based on search and uploader
    const getFilteredFiles = (files) => {
        return files.filter(file => {
            const matchesSearch = searchQuery ? (
                file.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                (file.tags && file.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())))
            ) : true;

            const matchesUploader = uploaderFilter ? file.owner_id === uploaderFilter : true;

            return matchesSearch && matchesUploader;
        });
    };

    // Get unique uploaders for filter dropdown
    const getUploadersInFolder = (files) => {
        const uploaders = new Set(files.map(f => f.owner_id));
        return Array.from(uploaders).map(id => ({
            id,
            name: getUploaderName(id)
        }));
    };

    // --- Views ---

    const renderHomeView = () => {
        return (
            <>
                {/* Global Search Bar */}
                <div className="d-flex gap-2 mb-4">
                    <div className="position-relative flex-grow-1">
                        <input
                            type="text"
                            className="form-control bg-clean-gray border-0 ps-5"
                            placeholder="Search all files..."
                            style={{ borderRadius: '12px', height: '48px' }}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <Search className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" size={18} />
                    </div>

                    {/* Global Uploader Filter Dropdown */}
                    <div className="dropdown">
                        <button
                            className={`btn h-100 px-3 d-flex align-items-center justify-content-center ${uploaderFilter ? 'btn-success text-white' : 'btn-light text-secondary'}`}
                            style={{ borderRadius: '12px', minWidth: '48px' }}
                            type="button"
                            data-bs-toggle="dropdown"
                            aria-expanded="false"
                            onClick={() => setActiveDropdown(activeDropdown === 'global-filter' ? null : 'global-filter')}
                        >
                            <Filter size={20} />
                        </button>
                        {activeDropdown === 'global-filter' && (
                            <ul className="dropdown-menu show end-0 mt-2 shadow-sm border-0 rounded-3 p-2" style={{ minWidth: '200px', display: 'block', position: 'absolute', right: 0, zIndex: 1000 }}>
                                <li><h6 className="dropdown-header">Filter by Uploader</h6></li>
                                <li>
                                    <button
                                        className={`dropdown-item rounded-2 ${uploaderFilter === '' ? 'active bg-success' : ''}`}
                                        onClick={() => { setUploaderFilter(''); setActiveDropdown(null); }}
                                    >
                                        All Uploaders
                                    </button>
                                </li>
                                {Object.entries(knownUsers).map(([id, name]) => (
                                    <li key={id}>
                                        <button
                                            className={`dropdown-item rounded-2 ${uploaderFilter === id ? 'active bg-success' : ''}`}
                                            onClick={() => { setUploaderFilter(id); setActiveDropdown(null); }}
                                        >
                                            {name}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>

                {/* Folder Grid (Hide when searching) */}
                {!searchQuery && (
                    <>
                        <h6 className="fw-bold mb-3 text-secondary">Folders</h6>
                        <div className="row g-3">
                            {groupedFiles.map((group, index) => (
                                <div key={index} className="col-6">
                                    <div
                                        className="card border-0 shadow-sm h-100"
                                        style={{ borderRadius: '16px', cursor: 'pointer', transition: 'transform 0.2s' }}
                                        onClick={() => {
                                            setCurrentFolder(group);
                                            setSearchQuery(''); // Clear global search when entering folder
                                            setSearchResults([]);
                                            setUploaderFilter('');
                                        }}
                                    >
                                        <div className="card-body p-3 d-flex flex-column align-items-center text-center">
                                            <div className={`rounded-circle p-3 mb-3 ${group.group_name === 'My Uploads' ? 'bg-primary bg-opacity-10 text-primary' : 'bg-warning bg-opacity-10 text-warning'}`}>
                                                <Folder size={32} fill={group.group_name === 'My Uploads' ? "currentColor" : "currentColor"} />
                                            </div>
                                            <h6 className="fw-bold mb-1 text-truncate w-100">{group.group_name}</h6>
                                            <small className="text-muted">{group.files.length} files</small>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}

                {/* Global Search Results (if searching) */}
                {searchQuery && (
                    <div className="mt-4">
                        <h6 className="fw-bold mb-3 text-secondary">Search Results</h6>
                        {isSearching ? (
                            <div className="text-center py-5">
                                <div className="spinner-border text-success" role="status">
                                    <span className="visually-hidden">Loading...</span>
                                </div>
                                <p className="text-muted mt-2">Searching...</p>
                            </div>
                        ) : (
                            <div className="d-flex flex-column gap-3">
                                {searchResults.map(file => renderFileCard(file))}
                                {searchResults.length === 0 && <div className="text-center text-muted">No files match your search.</div>}
                            </div>
                        )}
                    </div>
                )}
            </>
        );
    };

    const renderFolderView = () => {
        if (!currentFolder) return null;

        let displayFiles = [];
        if (searchQuery) {
            displayFiles = searchResults;
        } else {
            displayFiles = currentFolder.files.filter(file =>
                uploaderFilter ? file.owner_id === uploaderFilter : true
            );
        }

        const uploaders = getUploadersInFolder(currentFolder.files);

        return (
            <>
                {/* Header */}
                <div className="d-flex align-items-center mb-4">
                    <button
                        className="btn btn-light rounded-circle p-2 me-3 shadow-sm"
                        onClick={() => {
                            setCurrentFolder(null);
                            setSearchQuery('');
                            setSearchResults([]);
                            setUploaderFilter('');
                        }}
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <h5 className="fw-bold mb-0">{currentFolder.group_name}</h5>
                </div>

                {/* Scoped Search & Filter */}
                <div className="d-flex gap-2 mb-4">
                    <div className="position-relative flex-grow-1">
                        <input
                            type="text"
                            className="form-control bg-clean-gray border-0 ps-5"
                            placeholder="Search in folder..."
                            style={{ borderRadius: '12px', height: '48px' }}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <Search className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" size={18} />
                    </div>

                    {/* Uploader Filter Dropdown */}
                    <div className="dropdown">
                        <button
                            className={`btn h-100 px-3 d-flex align-items-center justify-content-center ${uploaderFilter ? 'btn-success text-white' : 'btn-light text-secondary'}`}
                            style={{ borderRadius: '12px', minWidth: '48px' }}
                            type="button"
                            data-bs-toggle="dropdown"
                            aria-expanded="false"
                            onClick={() => setActiveDropdown(activeDropdown === 'filter' ? null : 'filter')}
                        >
                            <Filter size={20} />
                        </button>
                        {activeDropdown === 'filter' && (
                            <ul className="dropdown-menu show end-0 mt-2 shadow-sm border-0 rounded-3 p-2" style={{ minWidth: '200px', display: 'block', position: 'absolute', right: 0, zIndex: 1000 }}>
                                <li><h6 className="dropdown-header">Filter by Uploader</h6></li>
                                <li>
                                    <button
                                        className={`dropdown-item rounded-2 ${uploaderFilter === '' ? 'active bg-success' : ''}`}
                                        onClick={() => { setUploaderFilter(''); setActiveDropdown(null); }}
                                    >
                                        All Uploaders
                                    </button>
                                </li>
                                {uploaders.map(u => (
                                    <li key={u.id}>
                                        <button
                                            className={`dropdown-item rounded-2 ${uploaderFilter === u.id ? 'active bg-success' : ''}`}
                                            onClick={() => { setUploaderFilter(u.id); setActiveDropdown(null); }}
                                        >
                                            {u.name}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>

                {/* File List */}
                <div className="d-flex flex-column gap-3">
                    {isSearching ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-success" role="status">
                                <span className="visually-hidden">Loading...</span>
                            </div>
                            <p className="text-muted mt-2">Searching...</p>
                        </div>
                    ) : (
                        displayFiles.length > 0 ? (
                            displayFiles.map(file => renderFileCard(file))
                        ) : (
                            <div className="text-center py-5 text-muted">
                                {searchQuery ? "No files match your search." : "No files found in this folder."}
                            </div>
                        )
                    )}
                </div>
            </>
        );
    };

    const renderFileCard = (file) => {
        const isSelected = selectedFiles.has(file.id);

        return (
            <div
                key={file.id}
                className={`card border-0 shadow-sm ${isSelected ? 'bg-success bg-opacity-10' : ''}`}
                style={{ borderRadius: '16px', cursor: 'pointer', transition: 'background-color 0.2s' }}
                onClick={() => handleCardClick(file)}
                onTouchStart={() => handleTouchStart(file)}
                onTouchEnd={handleTouchEnd}
                onMouseDown={() => handleTouchStart(file)} // For desktop testing
                onMouseUp={handleTouchEnd}
                onMouseLeave={handleTouchEnd}
            >
                <div className="card-body p-3">
                    <div className="d-flex align-items-start">
                        {/* Selection Indicator */}
                        {selectionMode && (
                            <div className="me-3 d-flex align-items-center" style={{ height: '48px' }}>
                                {isSelected ? (
                                    <CheckCircle className="text-success" size={24} fill="currentColor" color="white" />
                                ) : (
                                    <Circle className="text-muted" size={24} />
                                )}
                            </div>
                        )}

                        {/* File Icon */}
                        <div className={`file-icon ${getIconBgColor(file.file_type)} me-3 flex-shrink-0`} style={{ width: '48px', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '12px' }}>
                            {getFileIcon(file.file_type)}
                        </div>

                        {/* File Info */}
                        <div className="flex-grow-1" style={{ minWidth: 0 }}>
                            <div className="d-flex justify-content-between align-items-start">
                                <h6 className="card-title mb-1 fw-bold text-truncate pe-2" style={{ fontSize: '15px' }}>{file.filename}</h6>

                                {/* Actions Dropdown (Hide in selection mode) */}
                                {!selectionMode && (
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
                                )}
                            </div>

                            {/* Uploader Name */}
                            <div className="text-muted small mb-1" style={{ fontSize: '11px' }}>
                                Uploaded by: <span className="fw-medium text-dark">{getUploaderName(file.owner_id)}</span>
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
        );
    };

    return (
        <div className="mt-3 pb-5">
            {loading ? (
                <div className="text-center py-5 text-muted">Loading files...</div>
            ) : (
                currentFolder ? renderFolderView() : renderHomeView()
            )}

            {/* Floating Action Button (Hide in selection mode) */}
            {!selectionMode && (
                <button
                    onClick={() => setShowUploadModal(true)}
                    className="fab border-0"
                >
                    <Plus size={24} />
                </button>
            )}

            {/* Selection Mode Bottom Bar */}
            {selectionMode && (
                <div className="fixed-bottom bg-white shadow-lg p-3 d-flex align-items-center justify-content-between" style={{ zIndex: 1030, borderTopLeftRadius: '16px', borderTopRightRadius: '16px', bottom: '80px' }}>
                    <div className="d-flex align-items-center gap-2">
                        <button className="btn btn-light rounded-circle p-2" onClick={() => { setSelectionMode(false); setSelectedFiles(new Set()); }}>
                            <X size={20} />
                        </button>
                        <span className="fw-bold">{selectedFiles.size} selected</span>
                    </div>
                    <button
                        className="btn btn-primary rounded-pill px-4 fw-bold d-flex align-items-center gap-2"
                        disabled={selectedFiles.size === 0}
                        onClick={openCollectionModal}
                    >
                        <Layers size={18} />
                        Add to Collection
                    </button>
                </div>
            )}

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

            {/* Select Collection Modal */}
            {showCollectionModal && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered modal-dialog-scrollable">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">Add to Collection</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowCollectionModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <p className="text-muted small mb-3">Select a collection to add {selectedFiles.size} files to:</p>
                                    <div className="d-flex flex-column gap-2">
                                        {userCollections.length === 0 ? (
                                            <div className="text-center py-4 text-muted">
                                                No collections found. <br />
                                                Create one in the Share tab first!
                                            </div>
                                        ) : (
                                            userCollections.map(col => (
                                                <button
                                                    key={col.id}
                                                    className="btn btn-light text-start p-3 rounded-3 d-flex align-items-center"
                                                    onClick={() => addSelectedToCollection(col)}
                                                >
                                                    <Folder size={20} className="me-3 text-primary" />
                                                    <div className="flex-grow-1">
                                                        <div className="fw-bold">{col.name}</div>
                                                        <small className="text-muted">{col.file_ids ? col.file_ids.length : 0} files</small>
                                                    </div>
                                                    <Plus size={20} className="text-muted" />
                                                </button>
                                            ))
                                        )}
                                    </div>
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
                                    <div className="text-muted small mb-3">
                                        Uploaded by: {getUploaderName(selectedFile.owner_id)}
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
