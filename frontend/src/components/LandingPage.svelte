<script>
  export let onShowAuth

  const features = [
    {
      title: "FIRE-Focused Planning",
      description: "Built specifically for high-savings rates and early retirement timelines that the FIRE community demands"
    },
    {
      title: "Advanced Monte Carlo",
      description: "Run 10,000+ market scenarios with sequence of returns risk analysis - critical for early retirees"
    },
    {
      title: "Tax Optimization Ladder",
      description: "Sophisticated Roth conversion ladders and withdrawal sequencing for tax-efficient early retirement"
    },
    {
      title: "Multi-Account Mastery",
      description: "Optimize across 401k, Roth IRA, HSA, and taxable accounts with proper asset location strategies"
    }
  ]

  const subscriptionTiers = [
    {
      name: "Free",
      price: "$0",
      features: [
        "Basic FIRE projections",
        "Simple Monte Carlo (100 runs)",
        "1 saved scenario",
        "Essential withdrawal strategies"
      ]
    },
    {
      name: "Premium",
      price: "$9.99/month",
      features: [
        "Unlimited FIRE projections",
        "Full Monte Carlo (10,000 runs)",
        "Unlimited saved scenarios",
        "Excel export",
        "Advanced Roth ladders",
        "Sequence of returns analysis",
        "Geographic arbitrage planning"
      ]
    }
  ]
</script>

<div class="landing-page">
  <div class="hero-section">
    <div class="hero-content">
      <h1>FIREsim</h1>
      <p class="hero-subtitle">
        The ultimate retirement optimization simulator for the FIRE community. 
        Achieve Financial Independence, Retire Early with advanced Monte Carlo simulation, 
        multi-account optimization, and tax-aware strategies designed for aggressive savers.
      </p>
      <div class="hero-actions">
        <button class="cta-button" on:click={() => onShowAuth()}>
          Get Started Free
        </button>
        <button class="demo-button" on:click={() => onShowAuth()}>
          View Demo
        </button>
      </div>
    </div>
    <div class="hero-visual">
      <div class="chart-placeholder">
        <div class="chart-bars">
          <div class="bar" style="height: 60%"></div>
          <div class="bar" style="height: 75%"></div>
          <div class="bar" style="height: 90%"></div>
          <div class="bar" style="height: 85%"></div>
          <div class="bar" style="height: 95%"></div>
        </div>
        <p class="chart-label">Retirement Portfolio Growth</p>
      </div>
    </div>
  </div>

  <div class="features-section">
    <h2>Why FIREsim is Different</h2>
    <p class="features-intro">Unlike generic retirement calculators, FIREsim is built from the ground up for the FIRE community's unique needs:</p>
    <div class="features-grid">
      {#each features as feature}
        <div class="feature-card">
          <h3>{feature.title}</h3>
          <p>{feature.description}</p>
        </div>
      {/each}
    </div>
  </div>

  <div class="pricing-section">
    <h2>Choose Your Plan</h2>
    <div class="pricing-grid">
      {#each subscriptionTiers as tier}
        <div class="pricing-card" class:featured={tier.name === 'Premium'}>
          <h3>{tier.name}</h3>
          <div class="price">{tier.price}</div>
          <ul class="features-list">
            {#each tier.features as feature}
              <li>{feature}</li>
            {/each}
          </ul>
          <button class="tier-button" on:click={() => onShowAuth()}>
            {tier.name === 'Free' ? 'Start Free' : 'Upgrade Now'}
          </button>
        </div>
      {/each}
    </div>
  </div>

  <div class="cta-section">
    <h2>Ready to Achieve Financial Independence?</h2>
    <p>Join the FIRE community and start your journey to early retirement with data-driven planning.</p>
    <button class="cta-button" on:click={() => onShowAuth()}>
      Start Planning Today
    </button>
  </div>
</div>

<style>
  .landing-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
  }

  .hero-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 60px;
    align-items: center;
    padding: 80px 0;
    min-height: 500px;
  }

  .hero-content h1 {
    font-size: 3rem;
    margin-bottom: 20px;
    color: #2c3e50;
    line-height: 1.2;
  }

  .hero-subtitle {
    font-size: 1.25rem;
    color: #666;
    margin-bottom: 40px;
    line-height: 1.5;
  }

  .hero-actions {
    display: flex;
    gap: 20px;
  }

  .cta-button {
    padding: 15px 30px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .cta-button:hover {
    background: #0056b3;
    transform: translateY(-2px);
  }

  .demo-button {
    padding: 15px 30px;
    background: transparent;
    color: #007bff;
    border: 2px solid #007bff;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .demo-button:hover {
    background: #007bff;
    color: white;
  }

  .hero-visual {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .chart-placeholder {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    width: 100%;
    max-width: 300px;
  }

  .chart-bars {
    display: flex;
    justify-content: space-between;
    align-items: end;
    height: 120px;
    margin-bottom: 20px;
    gap: 10px;
  }

  .bar {
    background: linear-gradient(to top, #007bff, #0056b3);
    border-radius: 4px 4px 0 0;
    flex: 1;
    min-height: 20px;
    transition: all 0.3s ease;
  }

  .chart-label {
    color: #666;
    font-size: 0.9rem;
    margin: 0;
  }

  .features-section {
    padding: 80px 0;
    text-align: center;
  }

  .features-section h2 {
    font-size: 2.5rem;
    margin-bottom: 20px;
    color: #2c3e50;
  }

  .features-intro {
    font-size: 1.1rem;
    color: #666;
    margin-bottom: 60px;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 40px;
  }

  .feature-card {
    background: white;
    padding: 40px 30px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
  }

  .feature-card:hover {
    transform: translateY(-5px);
  }

  .feature-card h3 {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: #2c3e50;
  }

  .feature-card p {
    color: #666;
    line-height: 1.6;
  }

  .pricing-section {
    padding: 80px 0;
    text-align: center;
    background: #f8f9fa;
    margin: 0 -20px;
    padding-left: 20px;
    padding-right: 20px;
  }

  .pricing-section h2 {
    font-size: 2.5rem;
    margin-bottom: 60px;
    color: #2c3e50;
  }

  .pricing-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 40px;
    max-width: 800px;
    margin: 0 auto;
  }

  .pricing-card {
    background: white;
    padding: 40px 30px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
  }

  .pricing-card.featured {
    border: 3px solid #007bff;
    transform: scale(1.05);
  }

  .pricing-card h3 {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: #2c3e50;
  }

  .price {
    font-size: 2.5rem;
    font-weight: 700;
    color: #007bff;
    margin-bottom: 30px;
  }

  .features-list {
    list-style: none;
    padding: 0;
    margin: 0 0 30px 0;
  }

  .features-list li {
    padding: 10px 0;
    color: #666;
    border-bottom: 1px solid #eee;
  }

  .features-list li:last-child {
    border-bottom: none;
  }

  .tier-button {
    width: 100%;
    padding: 15px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .tier-button:hover {
    background: #0056b3;
  }

  .cta-section {
    padding: 80px 0;
    text-align: center;
  }

  .cta-section h2 {
    font-size: 2.5rem;
    margin-bottom: 20px;
    color: #2c3e50;
  }

  .cta-section p {
    font-size: 1.25rem;
    color: #666;
    margin-bottom: 40px;
  }

  @media (max-width: 768px) {
    .hero-section {
      grid-template-columns: 1fr;
      gap: 40px;
      padding: 60px 0;
    }

    .hero-content h1 {
      font-size: 2.5rem;
    }

    .hero-actions {
      flex-direction: column;
      align-items: center;
    }

    .cta-button,
    .demo-button {
      width: 100%;
      max-width: 300px;
    }

    .features-section,
    .pricing-section,
    .cta-section {
      padding: 60px 0;
    }

    .features-section h2,
    .pricing-section h2,
    .cta-section h2 {
      font-size: 2rem;
    }
  }
</style>