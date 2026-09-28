const API_BASE_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
  const linkForm = document.getElementById('linkForm');
  const webhookForm = document.getElementById('webhookForm');
  const btnRunAgent = document.getElementById('btnRunAgent');

  // 1. Link Generation Handler
  linkForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const merchant_slug = document.getElementById('merchantSelect').value;
    const original_url = document.getElementById('productUrl').value;
    const user_id = '8f9e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c';

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/links/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id, merchant_slug, original_url })
      });

      const data = await response.json();
      if (response.ok) {
        document.getElementById('resSubId').innerText = data.sub_id;
        document.getElementById('resRedirectUrl').innerText = `${API_BASE_URL}${data.redirect_gateway_url}`;
        document.getElementById('resRedirectUrl').href = `${API_BASE_URL}${data.redirect_gateway_url}`;
        document.getElementById('postbackSubId').value = data.sub_id;
        document.getElementById('linkResult').style.display = 'block';
      } else {
        alert(`Error: ${data.detail || 'Failed to generate link'}`);
      }
    } catch (err) {
      alert(`API Error: Make sure FastAPI backend is running on ${API_BASE_URL}`);
    }
  });

  // 2. Webhook Postback Simulator Handler
  webhookForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const sub_id = document.getElementById('postbackSubId').value;
    const gross_sale_amount = parseFloat(document.getElementById('saleAmount').value);
    const gross_commission_amount = parseFloat(document.getElementById('commissionAmount').value);
    const merchant_id = 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d';
    const merchant_transaction_id = `TX_${Date.now()}`;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/webhooks/postback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Merchant-Signature': 'simulated_hmac_sig'
        },
        body: JSON.stringify({
          merchant_id,
          sub_id,
          merchant_transaction_id,
          gross_sale_amount,
          gross_commission_amount,
          currency: 'INR'
        })
      });

      const data = await response.json();
      document.getElementById('resWebhookJson').innerText = JSON.stringify(data, null, 2);
      document.getElementById('webhookResult').style.display = 'block';

      // Dynamically update UI wallet balance
      const cashbackUser = gross_commission_amount * 0.70;
      const platformRev = gross_commission_amount * 0.30;
      
      const prevPending = parseFloat(document.getElementById('valPending').innerText.replace(/[^0-9.]/g, '')) || 0;
      const prevPlatform = parseFloat(document.getElementById('valPlatform').innerText.replace(/[^0-9.]/g, '')) || 0;

      document.getElementById('valPending').innerText = `₹${(prevPending + cashbackUser).toFixed(2)}`;
      document.getElementById('valPlatform').innerText = `₹${(prevPlatform + platformRev).toFixed(2)}`;
    } catch (err) {
      alert(`Webhook Error: Make sure FastAPI backend is running.`);
    }
  });

  // 3. Multi-Agent AI Pipeline Execution Handler
  btnRunAgent.addEventListener('click', async () => {
    btnRunAgent.innerText = '🤖 Executing LangGraph Multi-Agent Nodes...';
    btnRunAgent.disabled = true;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: '8f9e1d2c-3b4a-5f6e-7d8c-9b0a1f2e3d4c',
          merchant_slug: document.getElementById('merchantSelect').value,
          gross_sale_amount: parseFloat(document.getElementById('saleAmount').value),
          click_to_conversion_seconds: 45,
          user_ip_country: 'IND',
          thread_id: `thread_${Date.now()}`
        })
      });

      const data = await response.json();
      if (response.ok) {
        // Render Execution Trace Timeline
        const traceTimeline = document.getElementById('traceTimeline');
        traceTimeline.innerHTML = '';
        data.execution_trace.forEach((trace) => {
          const item = document.createElement('div');
          item.className = 'trace-item';
          item.innerHTML = `<strong>[Step ${trace.step}] ${trace.agent_name}:</strong> ${trace.action_taken}`;
          traceTimeline.appendChild(item);
        });

        // Render Risk Badge
        const riskBadge = document.getElementById('riskBadge');
        if (data.risk_flagged) {
          riskBadge.className = 'risk-badge risk-flagged';
          riskBadge.innerText = `HIGH RISK (Score: ${data.risk_score})`;
        } else {
          riskBadge.className = 'risk-badge risk-safe';
          riskBadge.innerText = `SAFE (Score: ${data.risk_score})`;
        }

        // Render Markdown Message
        document.getElementById('agentMarkdown').innerText = data.personalized_message_md || 'No markdown generated.';
        document.getElementById('agentOutput').style.display = 'grid';
      } else {
        alert(`Agent Error: ${data.detail}`);
      }
    } catch (err) {
      alert(`Agent Pipeline Error: Verify backend status.`);
    } finally {
      btnRunAgent.innerText = '🚀 Run Multi-Agent Inspection Pipeline';
      btnRunAgent.disabled = false;
    }
  });
});
