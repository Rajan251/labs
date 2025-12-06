import { useState, useEffect, useRef } from 'react';
import Hls from 'hls.js';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:3000/api/v1';

function App() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [videoId, setVideoId] = useState<string | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);

        try {
            // 1. Get Presigned URL
            const { data: initData } = await axios.post(`${API_URL}/upload/init`, {
                title: file.name
            });

            // 2. Upload to S3/MinIO
            await axios.put(initData.url, file, {
                headers: { 'Content-Type': file.type }
            });

            // 3. Notify Complete
            await axios.post(`${API_URL}/upload/${initData.videoId}/complete`);

            setVideoId(initData.videoId);
            alert('Upload Complete! Processing started.');
        } catch (error) {
            console.error(error);
            alert('Upload Failed');
        } finally {
            setUploading(false);
        }
    };

    useEffect(() => {
        if (videoId && videoRef.current) {
            const hlsUrl = `http://localhost:9000/videos/${videoId}/hls/playlist.m3u8`;

            if (Hls.isSupported()) {
                const hls = new Hls();
                hls.loadSource(hlsUrl);
                hls.attachMedia(videoRef.current);
            } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
                videoRef.current.src = hlsUrl;
            }
        }
    }, [videoId]);

    return (
        <div className="container">
            <h1>Video Streaming Platform</h1>

            <div className="upload-section">
                <input type="file" onChange={handleFileChange} accept="video/*" />
                <button onClick={handleUpload} disabled={!file || uploading}>
                    {uploading ? 'Uploading...' : 'Upload Video'}
                </button>
            </div>

            {videoId && (
                <div className="video-player">
                    <h2>Now Playing</h2>
                    <video ref={videoRef} controls style={{ width: '100%', maxWidth: '800px' }} />
                    <p>Video ID: {videoId}</p>
                </div>
            )}
        </div>
    );
}

export default App;
