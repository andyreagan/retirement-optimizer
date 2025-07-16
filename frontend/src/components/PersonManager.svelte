<script>
  import { createEventDispatcher } from 'svelte'
  
  const dispatch = createEventDispatcher()
  
  export let people = []
  export let startYear = new Date().getFullYear()
  
  function addPerson() {
    const newPerson = {
      name: 'New Person',
      current_age: 35,
      gender: 'male'
    }
    
    people = [...people, newPerson]
    dispatch('change', people)
  }
  
  function removePerson(index) {
    people = people.filter((_, i) => i !== index)
    dispatch('change', people)
  }
  
  function updatePerson(index, field, value) {
    people[index][field] = value
    dispatch('change', people)
  }
  
  function loadExamplePeople() {
    people = [
      {
        name: 'Alex',
        current_age: 35,
        gender: 'male'
      },
      {
        name: 'Sam',
        current_age: 33,
        gender: 'female'
      }
    ]
    dispatch('change', people)
  }
  
  // Calculate birth years for display
  $: peopleWithBirthYears = people.map(person => ({
    ...person,
    birth_year: startYear - person.current_age
  }))
</script>

<div class="person-manager">
  <div class="header">
    <h3>People in Plan</h3>
    <div class="header-actions">
      <button type="button" class="preset-btn" on:click={loadExamplePeople}>
        Load Example Couple
      </button>
    </div>
  </div>
  
  <div class="info-note">
    <p><strong>Multi-Person Planning:</strong> Add all people to be included in this retirement plan. The projection will run until the oldest person reaches age 120 and include survival probabilities.</p>
  </div>
  
  <div class="people-list">
    {#each peopleWithBirthYears as person, index}
      <div class="person-card">
        <div class="person-header">
          <input
            type="text"
            bind:value={person.name}
            on:input={(e) => updatePerson(index, 'name', e.target.value)}
            class="person-name"
            placeholder="Person's name"
          />
          <button type="button" class="remove-btn" on:click={() => removePerson(index)}>
            ×
          </button>
        </div>
        
        <div class="person-details">
          <div class="form-row">
            <div class="form-group">
              <label for="current_age_{index}">Current Age:</label>
              <input
                id="current_age_{index}"
                type="number"
                bind:value={person.current_age}
                on:input={(e) => updatePerson(index, 'current_age', parseInt(e.target.value) || 35)}
                min="18"
                max="100"
              />
            </div>
            
            <div class="form-group">
              <label for="gender_{index}">Gender:</label>
              <select 
                id="gender_{index}"
                bind:value={person.gender}
                on:change={(e) => updatePerson(index, 'gender', e.target.value)}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>
          
          <div class="birth-year-info">
            <span class="label">Born in:</span>
            <span class="value">{person.birth_year}</span>
            <span class="note">(for calendar year tracking)</span>
          </div>
        </div>
      </div>
    {/each}
    
    {#if people.length === 0}
      <div class="empty-state">
        <p>No people added yet. Add at least one person to begin planning.</p>
      </div>
    {/if}
  </div>
  
  <div class="actions">
    <button type="button" class="add-btn" on:click={addPerson}>
      + Add Person
    </button>
  </div>
  
  {#if people.length > 0}
    <div class="summary">
      <h4>Planning Summary</h4>
      <div class="summary-stats">
        <div class="stat">
          <span class="label">Number of People:</span>
          <span class="value">{people.length}</span>
        </div>
        <div class="stat">
          <span class="label">Age Range:</span>
          <span class="value">
            {Math.min(...people.map(p => p.current_age))} - {Math.max(...people.map(p => p.current_age))} years old
          </span>
        </div>
        <div class="stat">
          <span class="label">Projection End:</span>
          <span class="value">
            Year {startYear + (120 - Math.min(...people.map(p => p.current_age)))}
            (when oldest reaches 120)
          </span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .person-manager {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .header h3 {
    margin: 0;
    color: #333;
  }
  
  .preset-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .preset-btn:hover {
    background: #5a6268;
  }
  
  .info-note {
    background: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 20px;
  }
  
  .info-note p {
    margin: 0;
    color: #1565c0;
    font-size: 14px;
  }
  
  .people-list {
    margin-bottom: 20px;
  }
  
  .person-card {
    background: white;
    padding: 20px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
    margin-bottom: 15px;
    border-left: 4px solid #17a2b8;
  }
  
  .person-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .person-name {
    font-weight: bold;
    font-size: 18px;
    border: none;
    background: transparent;
    color: #333;
    flex: 1;
    padding: 5px;
    border-bottom: 1px solid transparent;
  }
  
  .person-name:focus {
    outline: none;
    border-bottom: 1px solid #17a2b8;
  }
  
  .remove-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
  }
  
  .person-details {
    display: grid;
    gap: 15px;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
  }
  
  .form-group label {
    font-size: 14px;
    color: #666;
    margin-bottom: 5px;
    font-weight: bold;
  }
  
  .form-group input,
  .form-group select {
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .birth-year-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #666;
    background: #f8f9fa;
    padding: 8px 12px;
    border-radius: 4px;
  }
  
  .birth-year-info .value {
    font-weight: bold;
    color: #333;
  }
  
  .birth-year-info .note {
    font-style: italic;
    color: #999;
  }
  
  .empty-state {
    text-align: center;
    color: #666;
    padding: 40px 20px;
    background: white;
    border-radius: 6px;
    border: 2px dashed #ddd;
  }
  
  .actions {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .add-btn {
    background: #17a2b8;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
  }
  
  .add-btn:hover {
    background: #138496;
  }
  
  .summary {
    background: white;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
  }
  
  .summary h4 {
    margin: 0 0 15px 0;
    color: #333;
  }
  
  .summary-stats {
    display: grid;
    gap: 10px;
  }
  
  .stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .stat .label {
    color: #666;
  }
  
  .stat .value {
    font-weight: bold;
    color: #333;
  }
  
  @media (max-width: 768px) {
    .form-row {
      grid-template-columns: 1fr;
    }
  }
</style>