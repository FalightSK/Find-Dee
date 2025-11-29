import { useState, useEffect, useContext } from 'react';
import { Search, Plus, FileText, Image as ImageIcon, Share2, Folder, MoreVertical, Trash2, Edit2, ArrowRight, X, ArrowLeft, ExternalLink } from 'lucide-react';
import { UserContext } from '../App';
import liff from '@line/liff';
import { useLocation } from 'react-router-dom';

const ShareView = () => {
    const userId = useContext(UserContext);
    const location = useLocation();
    const [collections, setCollections] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newCollectionName, setNewCollectionName] = useState('');
    const [activeCollection, setActiveCollection] = useState(null); // For detail view
    const [collectionDetails, setCollectionDetails] = useState(null); // Detailed data with files

    // File Detail Modal State
    const [selectedFile, setSelectedFile] = useState(null);
    const [knownUsers, setKnownUsers] = useState({}); // To resolve uploader names if needed

    useEffect(() => {
        if (userId) {
            fetchCollections();
        }
    }, [userId]);

    // Deep Linking Handling
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const collectionId = params.get('collectionId');
        if (collectionId) {
            // Fetch specific collection directly
            fetchCollectionDetail(collectionId);
        }
    }, [location.search]);

    const fetchCollections = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/collections/${userId}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            if (!response.ok) throw new Error('Failed to fetch collections');
            const data = await response.json();
            setCollections(data.collections || []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const fetchCollectionDetail = async (collectionId) => {
        setCollectionDetails(null);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/collections/detail/${collectionId}`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            if (!response.ok) throw new Error('Failed to load details');
            const data = await response.json();
            setCollectionDetails(data);
            setActiveCollection({ id: collectionId, ...data });

            // Auto-save if not owner
            if (data.owner_id !== userId) {
                const formData = new FormData();
                formData.append('user_id', userId);
                await fetch(`${apiUrl}/api/collections/${collectionId}/save`, {
                    method: 'POST',
                    body: formData,
                    headers: { 'ngrok-skip-browser-warning': 'true' }
                });
                // Refresh collections list silently to include this new one
                fetchCollections();
            }
        } catch (error) {
            console.error(error);
            alert("Could not load shared collection. It might have been deleted.");
        }
    };

    const handleCreateCollection = async () => {
        if (!newCollectionName.trim()) return;
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/collections`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    name: newCollectionName,
                    owner_id: userId,
                    description: 'Created via App',
                    file_ids: []
                })
            });
            if (!response.ok) throw new Error('Failed to create collection');
            setNewCollectionName('');
            setShowCreateModal(false);
            fetchCollections();
        } catch (error) {
            alert('Error creating collection: ' + error.message);
        }
    };

    const handleDeleteCollection = async (collectionId) => {
        if (!confirm('Delete this collection?')) return;
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            await fetch(`${apiUrl}/api/collections/${collectionId}`, {
                method: 'DELETE',
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            fetchCollections();
            if (activeCollection && activeCollection.id === collectionId) {
                setActiveCollection(null);
            }
        } catch (error) {
            alert('Error deleting collection');
        }
    };

    const openCollection = (collection) => {
        setActiveCollection(collection);
        fetchCollectionDetail(collection.id);
    };

    const removeFileFromCollection = async (fileId) => {
        if (!collectionDetails) return;
        const updatedFileIds = collectionDetails.files.filter(f => f.id !== fileId).map(f => f.id);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            await fetch(`${apiUrl}/api/collections/${collectionDetails.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    file_ids: updatedFileIds
                })
            });
            // Refresh details
            fetchCollectionDetail(collectionDetails.id);
        } catch (error) {
            alert('Failed to remove file');
        }
    };

    const handleShareCollection = async () => {
        if (!collectionDetails) return;

        if (!liff.isApiAvailable('shareTargetPicker')) {
            alert("Share Target Picker is not available on this device/environment.");
            return;
        }

        const liffUrl = `https://liff.line.me/${import.meta.env.VITE_LIFF_ID}?collectionId=${collectionDetails.id}`;

        try {
            await liff.shareTargetPicker([
                {
                    type: "flex",
                    altText: `Shared Collection: ${collectionDetails.name}`,
                    contents: {
                        type: "bubble",
                        body: {
                            type: "box",
                            layout: "vertical",
                            contents: [
                                {
                                    type: "text",
                                    text: "📂 Shared Collection",
                                    weight: "bold",
                                    color: "#1DB446",
                                    size: "sm"
                                },
                                {
                                    type: "text",
                                    text: collectionDetails.name,
                                    weight: "bold",
                                    size: "xl",
                                    margin: "md",
                                    wrap: true
                                },
                                {
                                    type: "text",
                                    text: `${collectionDetails.files.length} files`,
                                    size: "xs",
                                    color: "#aaaaaa",
                                    margin: "xs"
                                }
                            ]
                        },
                        footer: {
                            type: "box",
                            layout: "vertical",
                            spacing: "sm",
                            contents: [
                                {
                                    type: "button",
                                    style: "primary",
                                    height: "sm",
                                    action: {
                                        type: "uri",
                                        label: "Open Collection",
                                        uri: liffUrl
                                    },
                                    color: "#06C755"
                                }
                            ],
                            flex: 0
                        }
                    }
                }
            ]);
            console.log("Message sent!");
        } catch (error) {
            console.log("Error sending message:", error);
            alert("Failed to share collection.");
        }
    };

    // --- Views ---

    const renderCollectionList = () => (
        <div className="pb-5">
            <div className="mb-4 mt-2 px-4">
                <h2 className="fw-bold mb-1" style={{ fontSize: '24px' }}>My Collections</h2>
                <p className="text-muted small">Organize your files into playlists</p>
            </div>

            <div className="px-4 d-flex flex-column gap-3">
                {loading ? (
                    <div className="text-center py-5 text-muted">Loading...</div>
                ) : collections.length === 0 ? (
                    <div className="text-center py-5">
                        <div className="bg-light rounded-circle p-4 d-inline-block mb-3">
                            <Folder size={32} className="text-muted" />
                        </div>
                        <h6 className="fw-bold text-secondary">No Collections Yet</h6>
                        <p className="text-muted small">Create one to start organizing!</p>
                    </div>
                ) : (
                    collections.map(col => (
                        <div key={col.id} className="card border-0 shadow-sm" style={{ borderRadius: '16px', cursor: 'pointer' }} onClick={() => openCollection(col)}>
                            <div className="card-body p-3 d-flex align-items-center">
                                <div className="bg-primary bg-opacity-10 p-3 rounded-3 me-3 text-primary">
                                    <Folder size={24} fill="currentColor" />
                                </div>
                                <div className="flex-grow-1">
                                    <h6 className="fw-bold mb-1">{col.name}</h6>
                                    <small className="text-muted">{col.file_ids ? col.file_ids.length : 0} files</small>
                                </div>
                                <button
                                    className="btn btn-link text-muted p-0"
                                    onClick={(e) => { e.stopPropagation(); handleDeleteCollection(col.id); }}
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* FAB */}
            <button
                className="fab border-0 bg-primary text-white"
                style={{ position: 'fixed', bottom: '90px', right: '20px', width: '56px', height: '56px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', zIndex: 1000 }}
                onClick={() => setShowCreateModal(true)}
            >
                <Plus size={24} />
            </button>
        </div>
    );

    const renderCollectionDetail = () => {
        if (!collectionDetails) return <div className="text-center py-5">Loading details...</div>;

        const isOwner = collectionDetails.owner_id === userId;

        return (
            <div className="pb-5">
                {/* Header */}
                <div className="px-4 pt-3 pb-3 bg-white sticky-top shadow-sm mb-3" style={{ top: 0, zIndex: 1020 }}>
                    <div className="d-flex align-items-center gap-3 mb-2">
                        <button className="btn btn-light rounded-circle p-2" onClick={() => setActiveCollection(null)}>
                            <ArrowLeft size={20} />
                        </button>
                        <div className="flex-grow-1">
                            <h5 className="fw-bold mb-0">{collectionDetails.name}</h5>
                            <small className="text-muted">{collectionDetails.files.length} files</small>
                        </div>
                        <button className="btn btn-success text-white rounded-circle p-2" onClick={handleShareCollection}>
                            <Share2 size={20} />
                        </button>
                    </div>
                </div>

                {/* File List */}
                <div className="px-4 d-flex flex-column gap-3">
                    {collectionDetails.files.length === 0 ? (
                        <div className="text-center py-5 text-muted">
                            This collection is empty. <br />
                            Go to <b>Files</b> to add items!
                        </div>
                    ) : (
                        collectionDetails.files.map(file => (
                            <div
                                key={file.id}
                                className="card border-0 shadow-sm"
                                style={{ borderRadius: '16px', cursor: 'pointer' }}
                                onClick={() => setSelectedFile(file)}
                            >
                                <div className="card-body p-3 d-flex align-items-center">
                                    <div className={`me-3 p-2 rounded-3 ${file.file_type === 'pdf' ? 'bg-danger bg-opacity-10 text-danger' : 'bg-success bg-opacity-10 text-success'}`}>
                                        {file.file_type === 'pdf' ? <FileText size={20} /> : <ImageIcon size={20} />}
                                    </div>
                                    <div className="flex-grow-1" style={{ minWidth: 0 }}>
                                        <h6 className="fw-bold mb-0 text-truncate">{file.filename}</h6>
                                        <small className="text-muted">Added {new Date(file.upload_date).toLocaleDateString()}</small>
                                    </div>
                                    {isOwner && (
                                        <button
                                            className="btn btn-link text-danger p-0 ms-2"
                                            onClick={(e) => { e.stopPropagation(); removeFileFromCollection(file.id); }}
                                        >
                                            <X size={20} />
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        );
    };

    return (
        <>
            {activeCollection ? renderCollectionDetail() : renderCollectionList()}

            {/* Create Modal */}
            {showCreateModal && (
                <>
                    <div className="modal show d-block" tabIndex="-1">
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content" style={{ borderRadius: '16px' }}>
                                <div className="modal-header border-0">
                                    <h5 className="modal-title fw-bold">New Collection</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowCreateModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <input
                                        type="text"
                                        className="form-control form-control-lg"
                                        placeholder="Collection Name (e.g., Math Homework)"
                                        value={newCollectionName}
                                        onChange={(e) => setNewCollectionName(e.target.value)}
                                        autoFocus
                                    />
                                </div>
                                <div className="modal-footer border-0">
                                    <button className="btn btn-primary w-100 rounded-3 py-2 fw-bold" onClick={handleCreateCollection}>
                                        Create
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}

            {/* File Detail Modal (Reused from FileListView) */}
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
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="modal-backdrop show"></div>
                </>
            )}
        </>
    );
};

export default ShareView;
