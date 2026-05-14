import { useState } from 'react'

function App() {
  const [topic, setTopic] = useState('');
  const [speakerCount, setSpeakerCount] = useState(2);
  const [language, setLanguage] = useState('English');
  const [bgMusic, setBgMusic] = useState('Automated');
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setAudioUrl(null);

    try {
      const response = await fetch('http://localhost:5050/api/generate_podcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, speakerCount, language, bgMusic }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to generate podcast');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <h1>Dextora Podcast</h1>
        <p className="subtitle">AI-Powered Personalized Audio Experiences</p>

        {!loading && !audioUrl && (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="topic">What should the podcast be about?</label>
              <input
                type="text"
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., The History of the Roman Empire"
                required
              />
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label htmlFor="speakers">Speaker Count</label>
                <select
                  id="speakers"
                  value={speakerCount}
                  onChange={(e) => setSpeakerCount(Number(e.target.value))}
                >
                  <option value={1}>1 Speaker (Monologue)</option>
                  <option value={2}>2 Speakers (Interview)</option>
                  <option value={3}>3 Speakers (Panel)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="language">Output Language</label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi (हिन्दी)</option>
                  <option value="Telugu">Telugu (తెలుగు)</option>
                </select>
              </div>
              
              <div className="form-group" style={{ gridColumn: "span 2" }}>
                <label htmlFor="bgMusic">Background Music</label>
                <select
                  id="bgMusic"
                  value={bgMusic}
                  onChange={(e) => setBgMusic(e.target.value)}
                >
                  <option value="Automated">Automated (AI Chooses)</option>
                  <option value="None">None</option>
                  <option value="Subtle">Subtle Professional</option>
                  <option value="Ambient">Ambient Inspired</option>
                  <option value="Energetic">Energetic</option>
                  <option value="Mysterious">Mysterious</option>
                  <option value="Cinematic">Cinematic</option>
                  <option value="Lofi">Lofi / Chill</option>
                </select>
              </div>
            </div>

            {error && <p style={{ color: '#ef4444', marginBottom: '1rem', textAlign: 'center' }}>{error}</p>}

            <button type="submit" className="btn-primary" disabled={!topic.trim()}>
              Generate Podcast
            </button>
          </form>
        )}

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p className="loading-text">Writing script & generating audio...</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
              This usually takes 1-2 minutes.
            </p>
          </div>
        )}

        {audioUrl && !loading && (
          <div className="result-container">
            <div className="success-icon">✓</div>
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem' }}>Your Podcast is Ready!</h2>
            
            <audio controls src={audioUrl}>
              Your browser does not support the audio element.
            </audio>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <a href={audioUrl} download="podcast.mp3" className="btn-primary" style={{ flex: 1, textDecoration: 'none' }}>
                Download MP3
              </a>
              <button 
                onClick={() => setAudioUrl(null)} 
                className="btn-secondary" 
                style={{ flex: 1 }}
              >
                Create Another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
