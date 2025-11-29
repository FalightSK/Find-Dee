import { useState, useContext } from 'react';
import { UserContext } from '../App';
import { Check, Star, Shield, Zap } from 'lucide-react';

const SettingsView = () => {
    const userId = useContext(UserContext);
    const [currentPlan, setCurrentPlan] = useState('free');

    const plans = [
        {
            id: 'free',
            name: 'Free',
            price: '฿0',
            period: '/month',
            features: ['5GB Storage', 'Basic Search', 'Standard Support'],
            icon: Star,
            color: 'text-secondary',
            bgColor: 'bg-secondary'
        },
        {
            id: 'pro',
            name: 'Pro',
            price: '฿99',
            period: '/month',
            features: ['50GB Storage', 'AI Smart Search', 'Priority Support', 'No Ads'],
            icon: Zap,
            color: 'text-warning',
            bgColor: 'bg-warning'
        },
        {
            id: 'enterprise',
            name: 'Enterprise',
            price: '฿299',
            period: '/month',
            features: ['Unlimited Storage', 'Advanced AI Analysis', '24/7 Dedicated Support', 'Team Collaboration'],
            icon: Shield,
            color: 'text-success',
            bgColor: 'bg-success'
        }
    ];

    return (
        <div className="container py-4">
            {/* User Profile Section */}
            <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '16px' }}>
                <div className="card-body p-4 d-flex align-items-center">
                    <div className="bg-primary bg-opacity-10 rounded-circle p-3 me-3 text-primary">
                        <span className="fw-bold" style={{ fontSize: '20px' }}>
                            {userId ? userId.substring(0, 2).toUpperCase() : 'Guest'}
                        </span>
                    </div>
                    <div>
                        <h6 className="fw-bold mb-1">Current User</h6>
                        <p className="text-muted mb-0 small text-truncate" style={{ maxWidth: '200px' }}>
                            {userId || 'Not logged in'}
                        </p>
                    </div>
                </div>
            </div>

            <h5 className="fw-bold mb-3">Subscription Plans</h5>

            {/* Plans List */}
            <div className="d-flex flex-column gap-3">
                {plans.map((plan) => {
                    const Icon = plan.icon;
                    const isCurrent = currentPlan === plan.id;

                    return (
                        <div
                            key={plan.id}
                            className={`card border-0 shadow-sm ${isCurrent ? 'ring-2 ring-success' : ''}`}
                            style={{
                                borderRadius: '16px',
                                border: isCurrent ? '2px solid #06c755' : 'none'
                            }}
                        >
                            <div className="card-body p-4">
                                <div className="d-flex justify-content-between align-items-start mb-3">
                                    <div className="d-flex align-items-center gap-3">
                                        <div className={`${plan.bgColor} bg-opacity-10 p-2 rounded-circle ${plan.color}`}>
                                            <Icon size={24} />
                                        </div>
                                        <div>
                                            <h6 className="fw-bold mb-0">{plan.name}</h6>
                                            <div className="d-flex align-items-baseline">
                                                <span className="fw-bold fs-5">{plan.price}</span>
                                                <span className="text-muted small">{plan.period}</span>
                                            </div>
                                        </div>
                                    </div>
                                    {isCurrent && (
                                        <span className="badge bg-success bg-opacity-10 text-success px-3 py-2 rounded-pill">
                                            Current
                                        </span>
                                    )}
                                </div>

                                <div className="d-flex flex-column gap-2 mb-3">
                                    {plan.features.map((feature, idx) => (
                                        <div key={idx} className="d-flex align-items-center gap-2 text-muted small">
                                            <Check size={14} className="text-success" />
                                            {feature}
                                        </div>
                                    ))}
                                </div>

                                {!isCurrent && (
                                    <button className="btn btn-outline-success w-100 rounded-3 fw-bold py-2">
                                        Upgrade
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="text-center mt-4 text-muted small">
                <p>Need help? Contact Support</p>
                <p>Version 1.0.0</p>
            </div>
        </div>
    );
};

export default SettingsView;
