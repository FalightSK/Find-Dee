import { useState } from 'react';
import { Search, Plus, FileText, Image as ImageIcon, Share2 } from 'lucide-react';

const ShareView = () => {
    const [searchQuery, setSearchQuery] = useState('');

    const trendingItems = [
        { id: 1, title: 'Midterm Review P...', type: 'pdf', subject: 'Calculus', author: 'Art (Chula)', color: 'success' },
        { id: 2, title: 'WWII Timeline I...', type: 'image', subject: 'History', author: 'Meena (KMITL)', color: 'warning' },
        { id: 3, title: 'Physics Formula...', type: 'pdf', subject: 'Physics', author: 'Ken (KU)', color: 'primary' },
    ];

    const subjects = [
        { name: 'Calculus', icon: '⬇️', color: 'success' },
        { name: 'Physics', icon: '⚛️', color: 'primary' },
        { name: 'History', icon: '⏳', color: 'warning' },
        { name: 'Biology', icon: '🧬', color: 'danger' },
    ];

    const recentItems = [
        { id: 1, title: 'Final Exam Cram Sheet.pdf', subject: 'Calculus', author: 'Aom (TU)', type: 'pdf', date: '2h ago' },
        { id: 2, title: 'Statics Summary.pdf', subject: 'Physics', author: 'Beam (CU)', type: 'pdf', date: '5h ago' },
        { id: 3, title: 'Cell Division Diagram.png', subject: 'Biology', author: 'Cat (MU)', type: 'image', date: '1d ago' },
    ];

    return (
        <div className="pb-5">
            {/* Header Section */}
            <div className="mb-4 mt-2">
                <h2 className="fw-bold mb-3" style={{ fontSize: '24px' }}>Explore Materials</h2>

                {/* Search Bar */}
                <div className="position-relative">
                    <input
                        type="text"
                        className="form-control bg-light border-0 ps-5"
                        placeholder="Search public materials..."
                        style={{ borderRadius: '12px', height: '48px' }}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <Search className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" size={18} />
                </div>
            </div>

            {/* Trending Section */}
            <div className="mb-4">
                <h5 className="fw-bold mb-3">Trending This Week</h5>
                <div className="d-flex overflow-auto pb-2 gap-3" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                    {trendingItems.map((item) => (
                        <div key={item.id} className="card border-0 shadow-sm flex-shrink-0" style={{ width: '160px', borderRadius: '16px' }}>
                            <div className="card-body p-3">
                                <div className="d-flex align-items-center mb-2">
                                    <div className={`bg-${item.color} bg-opacity-10 p-2 rounded-3 me-2`}>
                                        {item.type === 'pdf' ? <FileText size={16} className={`text-${item.color}`} /> : <ImageIcon size={16} className={`text-${item.color}`} />}
                                    </div>
                                    <span className={`badge bg-${item.color} bg-opacity-10 text-${item.color} fw-normal`} style={{ fontSize: '10px' }}>
                                        {item.subject}
                                    </span>
                                </div>
                                <h6 className="fw-bold mb-1 text-truncate" style={{ fontSize: '14px' }}>{item.title}</h6>
                                <p className="text-muted mb-0 text-truncate" style={{ fontSize: '11px' }}>Shared by {item.author}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Browse by Subject */}
            <div className="mb-4">
                <h5 className="fw-bold mb-3">Browse by Subject</h5>
                <div className="row g-3">
                    {subjects.map((sub, idx) => (
                        <div key={idx} className="col-6">
                            <div className="card border-0 shadow-sm h-100" style={{ borderRadius: '16px' }}>
                                <div className="card-body p-3 d-flex align-items-center">
                                    <div className={`bg-${sub.color} bg-opacity-10 p-2 rounded-3 me-3 d-flex align-items-center justify-content-center`} style={{ width: '40px', height: '40px' }}>
                                        <span style={{ fontSize: '20px' }}>{sub.icon}</span>
                                    </div>
                                    <span className="fw-bold" style={{ fontSize: '14px' }}>{sub.name}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recently Added */}
            <div className="mb-4">
                <h5 className="fw-bold mb-3">Recently Added Public Materials</h5>
                <div className="d-flex flex-column gap-3">
                    {recentItems.map((item) => (
                        <div key={item.id} className="card border-0 shadow-sm" style={{ borderRadius: '16px' }}>
                            <div className="card-body p-3 d-flex align-items-center">
                                <div className={`bg-success bg-opacity-10 p-2 rounded-3 me-3`}>
                                    <FileText size={20} className="text-success" />
                                </div>
                                <div className="flex-grow-1" style={{ minWidth: 0 }}>
                                    <h6 className="fw-bold mb-1 text-truncate" style={{ fontSize: '14px' }}>{item.title}</h6>
                                    <div className="d-flex align-items-center gap-2">
                                        <span className="badge bg-success bg-opacity-10 text-success fw-normal" style={{ fontSize: '10px' }}>
                                            {item.subject}
                                        </span>
                                        <span className="text-muted small" style={{ fontSize: '11px' }}>by {item.author}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Floating Action Button */}
            <button
                className="fab border-0 bg-success text-white"
                style={{ position: 'fixed', bottom: '90px', right: '20px', width: '56px', height: '56px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', zIndex: 1000 }}
            >
                <Share2 size={24} />
            </button>
        </div>
    );
};

export default ShareView;
