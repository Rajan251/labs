import React, { useState, useEffect } from 'react';
import './App.css';
import VideoPlayer from './VideoPlayer';

function App() {
  const [videos, setVideos] = useState([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await fetch('http://localhost:80/api/videos');
      const data = await res.json();
      setVideos(data);
    } catch (err) {
      console.error("Failed to fetch videos", err);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = e.target.file.files[0];
    const title = e.target.title.value;
    
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    setUploading(true);
    try {
      await fetch('http://localhost:80/api/upload', {
        method: 'POST',
        body: formData
      });
      alert('Upload started!');
      fetchVideos(); // Refresh list
    } catch (err) {
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Platform MVP</h1>
      </header>
      
      <div className="container">
        <section className="upload-section">
          <h2>Upload Video</h2>
          <form onSubmit={handleUpload}>
            <input type="text" name="title" placeholder="Video Title" required />
            <input type="file" name="file" accept="video/*" required />
            <button type="submit" disabled={uploading}>
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </form>
        </section>

        <section className="video-list">
          <h2>Recent Videos</h2>
          <div className="grid">
            {videos.map(video => (
              <div key={video.id} className="video-card">
                <h3>{video.title}</h3>
                <p>Status: {video.status}</p>
                {video.status === 'ready' && (
                  <VideoPlayer src={`http://localhost:80${video.hls_url}`} />
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
