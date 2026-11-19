import React, { useState } from 'react';
import { 
  Search, 
  ShoppingBag, 
  MapPin, 
  ShoppingCart, 
  ChevronDown, 
  Zap, 
  Star, 
  ShieldCheck, 
  Link2, 
  Wallet, 
  Bot, 
  Send, 
  CheckCircle2, 
  TrendingUp, 
  Percent, 
  Copy, 
  ExternalLink, 
  ArrowRight, 
  Award, 
  Menu,
  Sparkles,
  Package,
  RotateCcw
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home', 'converter', 'ledger', 'ai_agents', 'webhook'
  const [searchCategory, setSearchCategory] = useState('All');
  const [merchantSlug, setMerchantSlug] = useState('nike');
  const [productUrl, setProductUrl] = useState('https://www.nike.com/in/t/air-revolution-running-shoes/5000');
  const [generatedLink, setGeneratedLink] = useState(null);
  const [loadingLink, setLoadingLink] = useState(false);
  const [copied, setCopied] = useState(false);

  // Financial Wallet Balances
  const [pendingBalance, setPendingBalance] = useState(350.0);
  const [availableBalance, setAvailableBalance] = useState(1450.0);
  const [platformRevenue, setPlatformRevenue] = useState(150.0);

  // Webhook Simulator State
  const [subId, setSubId] = useState('clk_nike_raju_9900');
  const [saleAmount, setSaleAmount] = useState(5000.0);
  const [commissionAmount, setCommissionAmount] = useState(500.0);
  const [webhookResult, setWebhookResult] = useState(null);

  // AI Agent Pipeline State
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentOutput, setAgentOutput] = useState(null);

  // Amazon-Style Showcase Products Catalog
  const showcaseProducts = [
    {
      id: 'prod_nike',
      title: 'Nike Air Revolution Running Shoes (Black/White)',
      merchant: 'nike',
      merchantName: 'Nike Official Store',
      image: '/assets/headphones.jpg', // User custom image fallback
      originalPrice: 5000,
      commissionRate: 10.0,
      userCashback: 350,
      platformRevenue: 150,
      effectivePrice: 4650,
      rating: 4.9,
      reviews: 2450,
      isPrime: true,
      url: 'https://www.nike.com/in/t/air-revolution-running-shoes/5000'
    },
    {
      id: 'prod_macbook',
      title: 'Apple MacBook Pro 16" M3 Max (36GB RAM, 1TB SSD)',
      merchant: 'amazon',
      merchantName: 'Amazon India',
      image: '/assets/laptop.jpg',
      originalPrice: 249900,
      commissionRate: 8.5,
      userCashback: 14869,
      platformRevenue: 6372,
      effectivePrice: 235031,
      rating: 4.9,
      reviews: 1280,
      isPrime: true,
      url: 'https://www.amazon.in/dp/B08N5WRWNW'
    },
    {
      id: 'prod_smartwatch',
      title: 'Titanium SmartWatch Ultra 2 (Cellular + GPS)',
      merchant: 'amazon',
      merchantName: 'Amazon India',
      image: '/assets/smartwatch.jpg',
      originalPrice: 89900,
      commissionRate: 8.5,
      userCashback: 5349,
      platformRevenue: 2292,
      effectivePrice: 84551,
      rating: 4.8,
      reviews: 950,
      isPrime: true,
      url: 'https://www.amazon.in/dp/B09SMARTWATCH'
    }
  ];

  // 1. Generate Monetized Affiliate Link
  const handleGenerateLink = async (e) => {
    if (e) e.preventDefault();
    setLoadingLink(true);
    setCopied(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/links/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: '8f9e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
          merchant_slug: merchantSlug,
          original_url: productUrl
        })
      });
      const data = await res.json();
      if (res.ok) {
        setGeneratedLink(data);
        setSubId(data.sub_id);
        setActiveTab('converter');
      } else {
        alert(data.detail || 'Link generation failed');
      }
    } catch (err) {
      alert(`API Error: Ensure backend is running on ${API_BASE_URL}`);
    } finally {
      setLoadingLink(false);
    }
  };

  const handleQuickShop = async (product) => {
    setMerchantSlug(product.merchant);
    setProductUrl(product.url);
    setLoadingLink(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/links/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: '8f9e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
          merchant_slug: product.merchant,
          original_url: product.url
        })
      });
      const data = await res.json();
      if (res.ok) {
        setGeneratedLink(data);
        setSubId(data.sub_id);
        window.open(`${API_BASE_URL}${data.redirect_gateway_url}`, '_blank');
      }
    } catch (err) {
      alert(`API Connection Error`);
    } finally {
      setLoadingLink(false);
    }
  };

  const handleCopyLink = () => {
    if (generatedLink) {
      navigator.clipboard.writeText(`${API_BASE_URL}${generatedLink.redirect_gateway_url}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // 2. Trigger Merchant Webhook Simulation
  const handleWebhookSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/webhooks/postback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Merchant-Signature': 'simulated_hmac_sig'
        },
        body: JSON.stringify({
          merchant_id: 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
          sub_id: subId,
          merchant_transaction_id: `TX_${Date.now()}`,
          gross_sale_amount: parseFloat(saleAmount),
          gross_commission_amount: parseFloat(commissionAmount),
          currency: 'INR'
        })
      });
      const data = await res.json();
      setWebhookResult(data);

      if (res.ok) {
        const userCashback = commissionAmount * 0.70;
        const platformMargin = commissionAmount * 0.30;
        setPendingBalance(prev => prev + userCashback);
        setPlatformRevenue(prev => prev + platformMargin);
      }
    } catch (err) {
      alert('Webhook API Error: Verify backend status');
    }
  };

  // 3. Execute Multi-Agent AI Pipeline
  const handleRunAgent = async () => {
    setAgentRunning(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/agents/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: '8f9e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
          merchant_slug: merchantSlug,
          gross_sale_amount: parseFloat(saleAmount),
          click_to_conversion_seconds: 45,
          user_ip_country: 'IND',
          thread_id: `agent_session_${Date.now()}`
        })
      });
      const data = await res.json();
      if (res.ok) {
        setAgentOutput(data);
      } else {
        alert(data.detail);
      }
    } catch (err) {
      alert('Multi-Agent API Error');
    } finally {
      setAgentRunning(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* 1. AMAZON-STYLE TOP HEADER BAR (#131921) */}
      <header style={{ background: '#131921', color: 'white', padding: '0.6rem 1.25rem' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1.25rem' }}>
          
          {/* Brand Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }} onClick={() => setActiveTab('home')}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <span style={{ fontSize: '1.6rem', fontWeight: '800', color: 'white', letterSpacing: '-0.03em' }}>RevSplit</span>
              <span style={{ fontSize: '1.2rem', fontWeight: '800', color: '#febd69' }}>.in</span>
            </div>
            <span style={{ fontSize: '0.72rem', background: '#007185', color: 'white', padding: '0.15rem 0.4rem', borderRadius: '0.2rem', fontWeight: '700' }}>PRIME</span>
          </div>

          {/* Delivery Location */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', fontSize: '0.82rem', color: '#ccc' }}>
            <MapPin size={18} color="#febd69" />
            <div>
              <div style={{ fontSize: '0.7rem', color: '#ccc' }}>Delivering to Raju</div>
              <strong style={{ color: 'white' }}>Hyderabad 500001</strong>
            </div>
          </div>

          {/* Central Search & Converter Bar */}
          <div style={{ flex: 1, maxWidth: '750px', display: 'flex', borderRadius: '0.25rem', overflow: 'hidden' }}>
            <select 
              value={searchCategory} 
              onChange={e => setSearchCategory(e.target.value)}
              style={{ background: '#f3f3f3', border: 'none', padding: '0.6rem 0.6rem', fontSize: '0.8rem', color: '#333', cursor: 'pointer', outline: 'none' }}
            >
              <option value="All">All Categories</option>
              <option value="Electronics">Electronics</option>
              <option value="Fashion">Fashion</option>
              <option value="Mobiles">Mobiles</option>
            </select>

            <input
              type="text"
              placeholder="Search products or paste merchant URL for 70% instant cashback..."
              value={productUrl}
              onChange={e => setProductUrl(e.target.value)}
              style={{ flex: 1, border: 'none', padding: '0.6rem 1rem', fontSize: '0.9rem', outline: 'none', color: '#111' }}
            />

            <button 
              onClick={handleGenerateLink} 
              style={{ background: '#febd69', border: 'none', padding: '0 1.25rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <Search size={20} color="#111" />
            </button>
          </div>

          {/* User Account & Wallet Orders */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', fontSize: '0.82rem' }}>
            <div style={{ cursor: 'pointer' }}>
              <div style={{ fontSize: '0.72rem', color: '#ccc' }}>Hello, Raju</div>
              <strong style={{ color: 'white', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                Account & Wallet <ChevronDown size={12} />
              </strong>
            </div>

            <div style={{ cursor: 'pointer' }} onClick={() => setActiveTab('ledger')}>
              <div style={{ fontSize: '0.72rem', color: '#ccc' }}>Returns &</div>
              <strong style={{ color: 'white' }}>Wallet Orders</strong>
            </div>

            {/* Cart / Wallet Balance Counter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }} onClick={() => setActiveTab('ledger')}>
              <div style={{ position: 'relative' }}>
                <ShoppingCart size={28} color="white" />
                <span style={{ position: 'absolute', top: '-4px', right: '-4px', background: '#f0c14b', color: '#111', fontWeight: '800', fontSize: '0.72rem', width: '18px', height: '18px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  3
                </span>
              </div>
              <div>
                <div style={{ fontSize: '0.7rem', color: '#febd69', fontWeight: '700' }}>CASHBACK</div>
                <strong style={{ color: '#067d62', background: '#eef2ff', padding: '0.1rem 0.4rem', borderRadius: '0.2rem' }}>₹{availableBalance.toFixed(0)}</strong>
              </div>
            </div>
          </div>

        </div>
      </header>

      {/* 2. AMAZON-STYLE SUB-HEADER NAV BAR (#232f3e) */}
      <div style={{ background: '#232f3e', color: 'white', padding: '0.4rem 1.25rem', fontSize: '0.85rem' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          
          <button style={{ background: 'transparent', border: 'none', color: 'white', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Menu size={18} /> All Categories
          </button>

          {[
            { id: 'home', label: "Amazon Storefront & Cashback Deals" },
            { id: 'converter', label: "Link Monetizer Engine" },
            { id: 'ledger', label: "ACID Financial Ledger" },
            { id: 'ai_agents', label: "LangGraph AI Inspector" },
            { id: 'webhook', label: "Webhook Simulator" }
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                background: 'transparent',
                border: 'none',
                color: activeTab === item.id ? '#febd69' : '#e2e8f0',
                fontWeight: activeTab === item.id ? '700' : '500',
                cursor: 'pointer',
                padding: '0.2rem 0.4rem',
                borderBottom: activeTab === item.id ? '2px solid #febd69' : '2px solid transparent'
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. MAIN AMAZON CONTENT AREA */}
      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '1.5rem 1.25rem', flex: 1, width: '100%' }}>

        {/* Financial Metrics Strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          
          <div className="amazon-card">
            <div style={{ fontSize: '0.8rem', color: '#565959', fontWeight: '600' }}>Available Wallet Cashback</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#0f1111', margin: '0.2rem 0' }}>₹{availableBalance.toFixed(2)}</div>
            <div style={{ fontSize: '0.75rem', color: '#067d62', fontWeight: '700' }}>70% User Split Audited by PostgreSQL</div>
          </div>

          <div className="amazon-card">
            <div style={{ fontSize: '0.8rem', color: '#565959', fontWeight: '600' }}>Pending Merchant Postbacks</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#b12704', margin: '0.2rem 0' }}>₹{pendingBalance.toFixed(2)}</div>
            <div style={{ fontSize: '0.75rem', color: '#565959' }}>Row Lock: SELECT FOR UPDATE</div>
          </div>

          <div className="amazon-card">
            <div style={{ fontSize: '0.8rem', color: '#565959', fontWeight: '600' }}>Platform Revenue (30%)</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#007185', margin: '0.2rem 0' }}>₹{platformRevenue.toFixed(2)}</div>
            <div style={{ fontSize: '0.75rem', color: '#565959' }}>Platform Margin Retained</div>
          </div>

        </div>

        {/* TAB 1: AMAZON STOREFRONT & DEALS */}
        {activeTab === 'home' && (
          <div>
            
            {/* Amazon Great Festival Banner */}
            <div style={{ background: 'linear-gradient(135deg, #232f3e 0%, #131921 100%)', color: 'white', borderRadius: '0.5rem', padding: '2rem', marginBottom: '2rem', border: '1px solid #334155' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', alignItems: 'center' }}>
                <div>
                  <span style={{ background: '#b12704', color: 'white', padding: '0.2rem 0.6rem', borderRadius: '0.2rem', fontWeight: '700', fontSize: '0.75rem' }}>
                    GREAT SHOPPING FESTIVAL
                  </span>
                  <h2 style={{ fontSize: '2rem', fontWeight: '800', marginTop: '0.75rem', marginBottom: '0.75rem' }}>
                    Get Up To 70% Real Cashback Deposited To Your Wallet
                  </h2>
                  <p style={{ color: '#cbd5e1', fontSize: '0.95rem', marginBottom: '1.25rem', lineHeight: '1.5' }}>
                    Raju bought <strong>₹5,000 Nike Shoes</strong> via RevSplit. Nike paid 10% commission (₹500). RevSplit gave <strong>₹350 (70%) to Raju</strong> and kept <strong>₹150 (30%)</strong> as platform revenue!
                  </p>

                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <button onClick={() => setActiveTab('converter')} className="btn-amazon-primary">
                      Monetize Product URL
                    </button>
                    <button onClick={() => setActiveTab('ai_agents')} className="btn-amazon-secondary">
                      Run AI Deal Finder
                    </button>
                  </div>
                </div>

                <div style={{ textAlign: 'center' }}>
                  <img src="/assets/headphones.jpg" alt="Deal Showcase" style={{ width: '100%', borderRadius: '0.5rem', border: '1px solid #475569' }} />
                </div>
              </div>
            </div>

            {/* Amazon Product Showcase Cards Grid */}
            <div style={{ marginBottom: '2.5rem' }}>
              <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#0f1111', marginBottom: '1rem' }}>
                Featured Deals with 70% Instant Cashback
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
                {showcaseProducts.map(prod => (
                  <div key={prod.id} className="amazon-card amazon-card-hover" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      {/* Image container */}
                      <div style={{ background: '#f7f7f7', borderRadius: '0.25rem', padding: '0.5rem', marginBottom: '0.85rem', textAlign: 'center' }}>
                        <img src={prod.image} alt={prod.title} style={{ height: '190px', objectFit: 'contain', maxWidth: '100%' }} />
                      </div>

                      {/* Brand & Prime */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#007185', fontWeight: '700' }}>{prod.merchantName}</span>
                        {prod.isPrime && <span style={{ background: '#007185', color: 'white', padding: '0.1rem 0.4rem', borderRadius: '0.2rem', fontWeight: '800', fontSize: '0.65rem' }}>prime</span>}
                      </div>

                      {/* Title */}
                      <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#0f1111', marginBottom: '0.5rem', lineHeight: '1.3' }}>
                        {prod.title}
                      </h4>

                      {/* Rating */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.75rem', fontSize: '0.8rem' }}>
                        <span style={{ color: '#de7921', fontWeight: '700' }}>{prod.rating}</span>
                        <div style={{ display: 'flex' }}>
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} size={12} fill="#de7921" color="#de7921" />
                          ))}
                        </div>
                        <span style={{ color: '#007185' }}>({prod.reviews.toLocaleString()})</span>
                      </div>

                      {/* Amazon Price & 70% Cashback Box */}
                      <div style={{ background: '#f7f8fa', border: '1px solid #d5d9d9', borderRadius: '0.35rem', padding: '0.75rem', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                          <span style={{ fontSize: '1.4rem', fontWeight: '800', color: '#b12704' }}>
                            ₹{prod.effectivePrice.toLocaleString('en-IN')}
                          </span>
                          <span style={{ fontSize: '0.8rem', color: '#565959', textDecoration: 'line-through' }}>
                            ₹{prod.originalPrice.toLocaleString('en-IN')}
                          </span>
                        </div>

                        <div style={{ fontSize: '0.8rem', color: '#067d62', fontWeight: '700', marginTop: '0.2rem' }}>
                          Cashback Credited: ₹{prod.userCashback.toLocaleString('en-IN')} (70% Split)
                        </div>

                        <div style={{ fontSize: '0.75rem', color: '#007185', marginTop: '0.1rem' }}>
                          Platform Margin Retained: ₹{prod.platformRevenue.toLocaleString('en-IN')} (30% Split)
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleQuickShop(prod)}
                      className="btn-amazon-primary"
                      style={{ width: '100%' }}
                    >
                      Buy Now & Claim ₹{prod.userCashback.toLocaleString('en-IN')} Cashback
                    </button>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* TAB 2: LINK MONETIZER */}
        {activeTab === 'converter' && (
          <div className="amazon-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#0f1111', marginBottom: '0.5rem' }}>
              Monetize Any Merchant Product Link
            </h3>
            <p style={{ color: '#565959', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
              Paste any product link. Our FastAPI engine generates dynamic <code>sub_id</code> tracking tokens, pairs session data in Redis, and publishes telemetry to Kafka.
            </p>

            <form onSubmit={handleGenerateLink} style={{ maxWidth: '800px' }}>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <div style={{ minWidth: '180px' }}>
                  <select className="amazon-input" value={merchantSlug} onChange={e => setMerchantSlug(e.target.value)}>
                    <option value="nike">Nike Store (10% Commission)</option>
                    <option value="amazon">Amazon India (8.5% Commission)</option>
                    <option value="flipkart">Flipkart (10% Commission)</option>
                  </select>
                </div>

                <div style={{ flex: 1, minWidth: '300px' }}>
                  <input
                    type="url"
                    className="amazon-input"
                    placeholder="Paste product link (e.g. https://www.amazon.in/dp/...)"
                    value={productUrl}
                    onChange={e => setProductUrl(e.target.value)}
                    required
                  />
                </div>

                <button type="submit" className="btn-amazon-primary" disabled={loadingLink}>
                  {loadingLink ? 'Monetizing...' : 'Monetize Link'}
                </button>
              </div>
            </form>

            {generatedLink && (
              <div style={{ marginTop: '1.5rem', background: '#f7f8fa', border: '1px solid #067d62', borderRadius: '0.35rem', padding: '1rem' }}>
                <div style={{ color: '#067d62', fontWeight: '700', marginBottom: '0.5rem' }}>Monetized Tracking Link Generated</div>
                <div><strong>Sub ID:</strong> <code>{generatedLink.sub_id}</code></div>
                <div style={{ marginTop: '0.25rem' }}>
                  <strong>Gateway Endpoint:</strong> <a href={`${API_BASE_URL}${generatedLink.redirect_gateway_url}`} target="_blank" rel="noreferrer" style={{ color: '#007185' }}>{API_BASE_URL}{generatedLink.redirect_gateway_url}</a>
                </div>

                <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
                  <button onClick={handleCopyLink} className="btn-amazon-primary">
                    {copied ? 'Copied!' : 'Copy Tracked Link'}
                  </button>
                  <a href={`${API_BASE_URL}${generatedLink.redirect_gateway_url}`} target="_blank" rel="noreferrer" className="btn-amazon-secondary" style={{ textDecoration: 'none' }}>
                    Test 302 Redirect
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: FINANCIAL LEDGER */}
        {activeTab === 'ledger' && (
          <div className="amazon-card" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#0f1111', marginBottom: '0.5rem' }}>
              Double-Entry Financial Ledger (PostgreSQL ACID Isolation)
            </h3>
            <p style={{ color: '#565959', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
              Wallet balances are derived from immutable journal entries in <code>wallet_ledger</code> protected by SQL triggers.
            </p>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #d5d9d9', color: '#565959', background: '#f7f8fa' }}>
                  <th style={{ padding: '0.75rem' }}>Entry ID</th>
                  <th style={{ padding: '0.75rem' }}>Type</th>
                  <th style={{ padding: '0.75rem' }}>Category</th>
                  <th style={{ padding: '0.75rem' }}>Amount</th>
                  <th style={{ padding: '0.75rem' }}>Balance After</th>
                  <th style={{ padding: '0.75rem' }}>Idempotency Key</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { id: 'leg_001', type: 'CREDIT', cat: 'CASHBACK_PENDING', amt: '+ ₹350.00', bal: '₹1,800.00', key: 'postback:nike:tx_nike_raju_99:pending' },
                  { id: 'leg_002', type: 'CREDIT', cat: 'CASHBACK_VERIFIED', amt: '+ ₹2,099.00', bal: '₹1,450.00', key: 'postback:flp:tx_8802:verified' },
                  { id: 'leg_003', type: 'CREDIT', cat: 'CASHBACK_PENDING', amt: '+ ₹350.00', bal: '₹1,450.00', key: 'postback:amzn:tx_7703:pending' }
                ].map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e7e7e7' }}>
                    <td style={{ padding: '0.75rem', fontFamily: 'var(--font-mono)' }}>{row.id}</td>
                    <td style={{ padding: '0.75rem', color: '#067d62', fontWeight: '700' }}>{row.type}</td>
                    <td style={{ padding: '0.75rem', color: '#007185', fontWeight: '600' }}>{row.cat}</td>
                    <td style={{ padding: '0.75rem', color: '#067d62', fontWeight: '700' }}>{row.amt}</td>
                    <td style={{ padding: '0.75rem', fontWeight: '700' }}>{row.bal}</td>
                    <td style={{ padding: '0.75rem', fontFamily: 'var(--font-mono)', color: '#565959' }}>{row.key}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 4: LANGGRAPH AI INSPECTOR */}
        {activeTab === 'ai_agents' && (
          <div className="amazon-card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#0f1111' }}>
                  Autonomous Multi-Agent AI Inspector (LangGraph Supervisor)
                </h3>
                <p style={{ color: '#565959', fontSize: '0.88rem' }}>
                  Evaluates fraud risk score, queries merchant margin paths, and generates markdown deal alerts.
                </p>
              </div>

              <button onClick={handleRunAgent} className="btn-amazon-primary" disabled={agentRunning}>
                {agentRunning ? 'Executing Graph...' : 'Execute Agent Graph'}
              </button>
            </div>

            {agentOutput ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: '#007185', marginBottom: '0.75rem' }}>Supervisor Execution Trace Timeline</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {agentOutput.execution_trace.map((tr, idx) => (
                      <div key={idx} style={{ padding: '0.75rem', background: '#f7f8fa', borderLeft: '3px solid #007185', borderRadius: '0.25rem', fontSize: '0.85rem' }}>
                        <div style={{ fontWeight: '700', color: '#0f1111' }}>Step {tr.step}: {tr.agent_name}</div>
                        <div style={{ color: '#565959' }}>{tr.action_taken}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: '#067d62', marginBottom: '0.75rem' }}>Risk Score & Generated Alert</h4>
                  <div style={{ marginBottom: '0.75rem', fontWeight: '700', color: agentOutput.risk_flagged ? '#b12704' : '#067d62' }}>
                    Risk Status: {agentOutput.risk_flagged ? 'HIGH RISK DETECTED' : 'LOW RISK (SAFE)'} (Score: {agentOutput.risk_score})
                  </div>
                  <div class="code-box" style={{ whiteSpace: 'pre-line' }}>
                    {agentOutput.personalized_message_md}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#565959' }}>
                Click <strong>"Execute Agent Graph"</strong> above to run the LangGraph supervisor workflow live.
              </div>
            )}
          </div>
        )}

        {/* TAB 5: WEBHOOK SIMULATOR */}
        {activeTab === 'webhook' && (
          <div className="amazon-card" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#0f1111', marginBottom: '0.5rem' }}>
              Merchant Webhook Ingestion Simulator
            </h3>
            <p style={{ color: '#565959', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
              Simulates e-commerce postback confirmations. Evaluates HMAC signatures, checks Redis <code>SETNX</code> deduplication locks, and executes row-level locking balance updates.
            </p>

            <form onSubmit={handleWebhookSubmit} style={{ maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.85rem', color: '#565959', marginBottom: '0.25rem', display: 'block', fontWeight: '600' }}>Tracking Token (sub_id)</label>
                <input className="amazon-input" type="text" value={subId} onChange={e => setSubId(e.target.value)} required />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#565959', marginBottom: '0.25rem', display: 'block', fontWeight: '600' }}>Sale Amount (₹)</label>
                  <input className="amazon-input" type="number" value={saleAmount} onChange={e => setSaleAmount(e.target.value)} required />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#565959', marginBottom: '0.25rem', display: 'block', fontWeight: '600' }}>Gross Commission (₹)</label>
                  <input className="amazon-input" type="number" value={commissionAmount} onChange={e => setCommissionAmount(e.target.value)} required />
                </div>
              </div>

              <button type="submit" className="btn-amazon-secondary">
                Send Webhook & Execute FOR UPDATE Settlement
              </button>
            </form>

            {webhookResult && (
              <div style={{ marginTop: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: '#067d62', marginBottom: '0.5rem' }}>Postback Processing Response</h4>
                <div class="code-box">
                  <pre>{JSON.stringify(webhookResult, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        )}

      </main>

      {/* AMAZON-STYLE FOOTER */}
      <footer style={{ background: '#131921', color: '#ddd', padding: '2rem 1.25rem', marginTop: 'auto', fontSize: '0.82rem' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', textAlign: 'center' }}>
          <div>RevSplit.in — Programmatic Cashback & Multi-Agent AI Arbitrage Engine</div>
          <div style={{ color: '#888', marginTop: '0.4rem' }}>FastAPI • LangGraph • PostgreSQL ACID Ledger • Redis • Apache Kafka • React 18</div>
        </div>
      </footer>

    </div>
  );
}
