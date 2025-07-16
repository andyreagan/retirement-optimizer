<script>
  import { onMount } from 'svelte'
  
  export let showContact = false
  export let scenarioType = 'general' // 'general', 'multi-household', 'complex'
  
  let contactForm = {
    name: '',
    email: '',
    phone: '',
    household_size: 1,
    message: '',
    preferred_contact: 'email',
    urgency: 'normal'
  }
  
  let submitting = false
  let submitted = false
  let error = null
  
  onMount(() => {
    // Pre-fill form based on scenario type
    if (scenarioType === 'multi-household') {
      contactForm.message = 'I need help with a multi-household retirement projection. I would like to discuss complex scenarios involving multiple people and their financial planning needs.'
      contactForm.household_size = 2
    } else if (scenarioType === 'complex') {
      contactForm.message = 'I have a complex retirement scenario that requires professional guidance. I would like to discuss advanced strategies and personalized planning.'
    }
  })
  
  async function submitContactForm() {
    if (!contactForm.name || !contactForm.email || !contactForm.message) {
      error = 'Please fill in all required fields'
      return
    }
    
    submitting = true
    error = null
    
    try {
      const response = await fetch('/api/contact/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          ...contactForm,
          scenario_type: scenarioType,
          submitted_at: new Date().toISOString()
        })
      })
      
      if (response.ok) {
        submitted = true
        // Track contact form submission
        trackContactSubmission()
      } else {
        const data = await response.json()
        error = data.error || 'Failed to submit contact form'
      }
    } catch (err) {
      error = 'Network error. Please try again or contact us directly.'
    } finally {
      submitting = false
    }
  }
  
  async function trackContactSubmission() {
    try {
      await fetch('/api/payments/usage/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'contact_form_submitted',
          metadata: {
            scenario_type: scenarioType,
            household_size: contactForm.household_size,
            preferred_contact: contactForm.preferred_contact
          }
        })
      })
    } catch (error) {
      console.error('Error tracking contact submission:', error)
    }
  }
  
  function closeModal() {
    showContact = false
    // Reset form after a delay to avoid flickering
    setTimeout(() => {
      if (!showContact) {
        contactForm = {
          name: '',
          email: '',
          phone: '',
          household_size: 1,
          message: '',
          preferred_contact: 'email',
          urgency: 'normal'
        }
        submitted = false
        error = null
      }
    }, 300)
  }
  
  function getServiceInfo() {
    switch (scenarioType) {
      case 'multi-household':
        return {
          title: 'Multi-Household Planning',
          description: 'Complex scenarios involving multiple families, generations, or financial interconnections.',
          features: [
            'Coordinated retirement planning across households',
            'Estate planning and wealth transfer strategies',
            'Tax optimization for multiple entities',
            'Inheritance and gift planning',
            'Family business succession planning'
          ],
          timeline: '2-3 business days',
          cost: 'Starting at $299/consultation'
        }
      case 'complex':
        return {
          title: 'Complex Scenario Planning',
          description: 'Advanced retirement strategies requiring professional expertise.',
          features: [
            'Advanced tax-loss harvesting strategies',
            'Alternative investment integration',
            'Business ownership retirement planning',
            'Multiple income stream optimization',
            'Custom withdrawal strategies'
          ],
          timeline: '1-2 business days',
          cost: 'Starting at $199/consultation'
        }
      default:
        return {
          title: 'General Retirement Planning',
          description: 'Professional guidance for your retirement planning needs.',
          features: [
            'Portfolio review and optimization',
            'Strategy refinement and validation',
            'Goal setting and milestone planning',
            'Risk assessment and management',
            'Implementation guidance'
          ],
          timeline: '1 business day',
          cost: 'Starting at $99/consultation'
        }
    }
  }
  
  $: serviceInfo = getServiceInfo()
</script>

{#if showContact}
  <div class="contact-modal">
    <div class="modal-overlay" on:click={closeModal}></div>
    <div class="modal-content">
      <div class="modal-header">
        <h2>Professional Retirement Planning</h2>
        <button class="close-btn" on:click={closeModal}>×</button>
      </div>
      
      {#if !submitted}
        <div class="modal-body">
          <div class="service-info">
            <h3>{serviceInfo.title}</h3>
            <p class="service-description">{serviceInfo.description}</p>
            
            <div class="service-details">
              <div class="detail-section">
                <h4>What's Included:</h4>
                <ul>
                  {#each serviceInfo.features as feature}
                    <li>{feature}</li>
                  {/each}
                </ul>
              </div>
              
              <div class="service-meta">
                <div class="meta-item">
                  <strong>Response Time:</strong> {serviceInfo.timeline}
                </div>
                <div class="meta-item">
                  <strong>Investment:</strong> {serviceInfo.cost}
                </div>
              </div>
            </div>
          </div>
          
          <form on:submit|preventDefault={submitContactForm}>
            <div class="form-section">
              <h4>Contact Information</h4>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="name">Full Name *</label>
                  <input
                    type="text"
                    id="name"
                    bind:value={contactForm.name}
                    required
                    disabled={submitting}
                  />
                </div>
                
                <div class="form-group">
                  <label for="email">Email Address *</label>
                  <input
                    type="email"
                    id="email"
                    bind:value={contactForm.email}
                    required
                    disabled={submitting}
                  />
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="phone">Phone Number</label>
                  <input
                    type="tel"
                    id="phone"
                    bind:value={contactForm.phone}
                    disabled={submitting}
                    placeholder="(555) 123-4567"
                  />
                </div>
                
                <div class="form-group">
                  <label for="household_size">Household Size</label>
                  <select
                    id="household_size"
                    bind:value={contactForm.household_size}
                    disabled={submitting}
                  >
                    <option value={1}>1 Person</option>
                    <option value={2}>2 People</option>
                    <option value={3}>3 People</option>
                    <option value={4}>4 People</option>
                    <option value={5}>5+ People</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="form-section">
              <h4>Contact Preferences</h4>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="preferred_contact">Preferred Contact Method</label>
                  <select
                    id="preferred_contact"
                    bind:value={contactForm.preferred_contact}
                    disabled={submitting}
                  >
                    <option value="email">Email</option>
                    <option value="phone">Phone Call</option>
                    <option value="video">Video Call</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label for="urgency">Urgency Level</label>
                  <select
                    id="urgency"
                    bind:value={contactForm.urgency}
                    disabled={submitting}
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High Priority</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="form-section">
              <h4>Your Message</h4>
              <div class="form-group">
                <label for="message">Please describe your retirement planning needs *</label>
                <textarea
                  id="message"
                  bind:value={contactForm.message}
                  rows="4"
                  required
                  disabled={submitting}
                  placeholder="Tell us about your specific situation, goals, and any challenges you're facing..."
                ></textarea>
              </div>
            </div>
            
            {#if error}
              <div class="error-message">{error}</div>
            {/if}
            
            <div class="form-actions">
              <button type="button" class="cancel-btn" on:click={closeModal}>
                Cancel
              </button>
              <button type="submit" class="submit-btn" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Request Consultation'}
              </button>
            </div>
          </form>
        </div>
      {:else}
        <div class="success-message">
          <div class="success-icon">✓</div>
          <h3>Thank You!</h3>
          <p>
            Your consultation request has been submitted successfully. 
            Our retirement planning experts will review your information and contact you within {serviceInfo.timeline}.
          </p>
          <div class="next-steps">
            <h4>What happens next:</h4>
            <ol>
              <li>We'll review your information and scenario details</li>
              <li>A qualified retirement planning professional will contact you</li>
              <li>We'll schedule a consultation at your convenience</li>
              <li>You'll receive personalized recommendations and strategies</li>
            </ol>
          </div>
          <button class="close-btn-success" on:click={closeModal}>
            Close
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .contact-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1000;
  }
  
  .modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
  }
  
  .modal-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 12px;
    max-width: 800px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #dee2e6;
    background: #f8f9fa;
    border-radius: 12px 12px 0 0;
  }
  
  .modal-header h2 {
    margin: 0;
    color: #333;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
  }
  
  .close-btn:hover {
    color: #333;
  }
  
  .modal-body {
    padding: 20px;
  }
  
  .service-info {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
    border: 1px solid #dee2e6;
  }
  
  .service-info h3 {
    margin: 0 0 10px;
    color: #007bff;
  }
  
  .service-description {
    color: #666;
    margin-bottom: 20px;
  }
  
  .service-details {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
  }
  
  .detail-section h4 {
    margin: 0 0 10px;
    color: #333;
  }
  
  .detail-section ul {
    margin: 0;
    padding-left: 20px;
  }
  
  .detail-section li {
    margin-bottom: 5px;
    color: #555;
  }
  
  .service-meta {
    display: grid;
    gap: 10px;
  }
  
  .meta-item {
    padding: 10px;
    background: white;
    border-radius: 4px;
    border: 1px solid #dee2e6;
    font-size: 14px;
  }
  
  .form-section {
    margin-bottom: 25px;
  }
  
  .form-section h4 {
    margin: 0 0 15px;
    color: #333;
    padding-bottom: 5px;
    border-bottom: 2px solid #007bff;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
  }
  
  .form-group label {
    margin-bottom: 5px;
    font-weight: 500;
    color: #555;
  }
  
  .form-group input,
  .form-group select,
  .form-group textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    transition: border-color 0.3s ease;
  }
  
  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: #007bff;
  }
  
  .form-group input:disabled,
  .form-group select:disabled,
  .form-group textarea:disabled {
    background: #f5f5f5;
    color: #666;
  }
  
  .form-group textarea {
    resize: vertical;
    min-height: 80px;
  }
  
  .error-message {
    background: #f8d7da;
    color: #721c24;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 20px;
    border: 1px solid #f5c6cb;
  }
  
  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    padding-top: 20px;
    border-top: 1px solid #dee2e6;
  }
  
  .cancel-btn,
  .submit-btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
  }
  
  .cancel-btn {
    background: #6c757d;
    color: white;
  }
  
  .cancel-btn:hover {
    background: #545b62;
  }
  
  .submit-btn {
    background: #007bff;
    color: white;
  }
  
  .submit-btn:hover:not(:disabled) {
    background: #0056b3;
  }
  
  .submit-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  .success-message {
    padding: 40px;
    text-align: center;
  }
  
  .success-icon {
    width: 60px;
    height: 60px;
    background: #28a745;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    color: white;
    font-size: 24px;
    font-weight: bold;
  }
  
  .success-message h3 {
    color: #28a745;
    margin-bottom: 15px;
  }
  
  .success-message p {
    color: #666;
    margin-bottom: 25px;
    line-height: 1.5;
  }
  
  .next-steps {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
    text-align: left;
  }
  
  .next-steps h4 {
    margin: 0 0 15px;
    color: #333;
  }
  
  .next-steps ol {
    margin: 0;
    padding-left: 20px;
  }
  
  .next-steps li {
    margin-bottom: 8px;
    color: #555;
  }
  
  .close-btn-success {
    background: #007bff;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }
  
  .close-btn-success:hover {
    background: #0056b3;
  }
  
  @media (max-width: 768px) {
    .modal-content {
      width: 95%;
      max-height: 95vh;
    }
    
    .service-details {
      grid-template-columns: 1fr;
    }
    
    .form-row {
      grid-template-columns: 1fr;
    }
    
    .form-actions {
      flex-direction: column;
    }
  }
</style>