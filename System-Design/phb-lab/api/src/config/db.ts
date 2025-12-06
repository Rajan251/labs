import { Pool } from 'pg';

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER || 'user',
    password: process.env.DB_PASSWORD || 'password',
    database: process.env.DB_NAME || 'video_db',
});

export const initDB = async () => {
    const client = await pool.connect();
    try {
        console.log('Connected to Database');
        await client.query(`
      CREATE TABLE IF NOT EXISTS videos (
        id UUID PRIMARY KEY,
        title VARCHAR(255),
        status VARCHAR(50) DEFAULT 'PENDING',
        s3_key VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    } finally {
        client.release();
    }
};

export default pool;
