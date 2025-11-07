import React, { useState, useEffect } from 'react';
import { getUserTokens, purchaseTokens } from '../services/api';

interface TokenBalanceProps {
  userId: string;
  onTokenUpdate?: (tokens: number) => void;
}

interface TokenData {
  user_id: string;
  tokens: number;
  total_used: number;
  created_at: string;
  updated_at: string;
}

const TokenBalance: React.FC<TokenBalanceProps> = ({ userId, onTokenUpdate }) => {
  const [tokenData, setTokenData] = useState<TokenData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [purchasing, setPurchasing] = useState(false);

  const tokenPackages = [
    { id: 'standard', name: 'Standard Pack', tokens: 100, price: 0, popular: false }
  ];

  useEffect(() => {
    fetchTokenBalance();
  }, [userId]);

  const fetchTokenBalance = async () => {
    try {
      setLoading(true);
      const data = await getUserTokens(userId);
      setTokenData(data);
      if (onTokenUpdate) {
        onTokenUpdate(data.tokens);
      }
    } catch (error) {
      console.error('Error fetching token balance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (packageId: string) => {
    try {
      setPurchasing(true);
      console.log('Attempting to purchase tokens:', { userId, packageId });
      const response = await purchaseTokens(userId, packageId, 'free');
      console.log('Purchase successful:', response);
      await fetchTokenBalance(); // Refresh token balance
      setShowPurchaseModal(false);
    } catch (error: any) {
      console.error('Error purchasing tokens:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to purchase tokens. Please try again.';
      alert(errorMessage);
    } finally {
      setPurchasing(false);
    }
  };

  if (loading) {
    return (
      <div className="token-balance loading">
        <div className="token-spinner"></div>
        <span>Loading resume screening tokens...</span>
      </div>
    );
  }

  if (!tokenData) {
    return (
      <div className="token-balance error">
        <span>Unable to load token balance</span>
      </div>
    );
  }

  const isLowTokens = tokenData.tokens < 10;
  const isOutOfTokens = tokenData.tokens === 0;

  return (
    <div className={`token-balance ${isOutOfTokens ? 'out-of-tokens' : isLowTokens ? 'low-tokens' : ''}`}>
      <div className="token-info">
        <div className="token-icon">🪙</div>
        <div className="token-details">
          <div className="token-count">
            <span className="token-number">{tokenData.tokens}</span>
            <span className="token-label">resume screening tokens</span>
          </div>
          <div className="token-used">
            {tokenData.total_used} used
          </div>
        </div>
      </div>
      
      {isOutOfTokens && (
        <div className="token-warning">
          <span>⚠️ No resume screening tokens remaining</span>
        </div>
      )}
      
      {isLowTokens && !isOutOfTokens && (
        <div className="token-warning">
          <span>⚠️ Low resume screening tokens</span>
        </div>
      )}

      <button 
        className="btn btn-primary token-purchase-btn"
        onClick={() => setShowPurchaseModal(true)}
      >
        {isOutOfTokens ? 'Buy Tokens' : 'Add Tokens'}
      </button>

      {showPurchaseModal && (
        <div className="token-purchase-modal">
          <div className="token-purchase-content">
            <div className="token-purchase-header">
              <h3>Get Free Resume Screening Tokens</h3>
              <button 
                className="close-btn"
                onClick={() => setShowPurchaseModal(false)}
              >
                ✕
              </button>
            </div>
            
            <div className="token-packages">
              {tokenPackages.map((pkg) => (
                <div key={pkg.id} className={`token-package ${pkg.popular ? 'popular' : ''}`}>
                  {pkg.popular && <div className="popular-badge">Most Popular</div>}
                  <div className="package-name">{pkg.name}</div>
                  <div className="package-tokens">{pkg.tokens} resume screening tokens</div>
                  <div className="package-price">{pkg.price === 0 ? 'Free' : `$${pkg.price}`}</div>
                  <button 
                    className="btn btn-primary package-btn"
                    onClick={() => handlePurchase(pkg.id)}
                    disabled={purchasing}
                  >
                    {purchasing ? 'Processing...' : (pkg.price === 0 ? 'Get Free Tokens' : 'Purchase')}
                  </button>
                </div>
              ))}
            </div>
            
            <div className="token-info-text">
              <p>💡 <strong>How it works:</strong></p>
              <ul>
                <li>1 resume screening token = 1 resume screening</li>
                <li>You get 100 free resume screening tokens when you sign up</li>
                <li>Get an additional 100 free tokens with this offer</li>
                <li>Resume screening tokens never expire</li>
                <li>No payment required - completely free!</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenBalance;
