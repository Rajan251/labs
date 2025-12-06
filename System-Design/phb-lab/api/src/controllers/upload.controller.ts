import { Request, Response } from 'express';
import * as Minio from 'minio';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/db';
import amqp from 'amqplib';

const minioClient = new Minio.Client({
    endPoint: 'localhost',
    port: 9000,
    useSSL: false,
    accessKey: process.env.MINIO_ROOT_USER || 'minioadmin',
    secretKey: process.env.MINIO_ROOT_PASSWORD || 'minioadmin',
});

// Ensure bucket exists
const BUCKET_NAME = 'videos';
minioClient.bucketExists(BUCKET_NAME, (err, exists) => {
    if (err) return console.log(err);
    if (!exists) {
        minioClient.makeBucket(BUCKET_NAME, 'us-east-1', (err) => {
            if (err) return console.log('Error creating bucket.', err);
            console.log('Bucket created successfully.');
        });
    }
});

export const getUploadUrl = async (req: Request, res: Response) => {
    try {
        const videoId = uuidv4();
        const { title } = req.body;
        const objectName = `${videoId}/raw.mp4`;

        // 1. Generate Presigned URL
        const presignedUrl = await minioClient.presignedPutObject(BUCKET_NAME, objectName, 24 * 60 * 60);

        // 2. Save metadata to DB
        await pool.query(
            'INSERT INTO videos (id, title, s3_key, status) VALUES ($1, $2, $3, $4)',
            [videoId, title, objectName, 'UPLOADING']
        );

        res.json({ videoId, url: presignedUrl });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
};

export const completeUpload = async (req: Request, res: Response) => {
    try {
        const { videoId } = req.params;

        // 1. Update DB status
        await pool.query('UPDATE videos SET status = $1 WHERE id = $2', ['PROCESSING', videoId]);

        // 2. Push to RabbitMQ
        const connection = await amqp.connect(process.env.RABBITMQ_URL || 'amqp://localhost');
        const channel = await connection.createChannel();
        const queue = 'video_transcode';

        await channel.assertQueue(queue, { durable: true });
        const msg = JSON.stringify({ videoId });
        channel.sendToQueue(queue, Buffer.from(msg));

        console.log(`[x] Sent ${msg}`);
        setTimeout(() => connection.close(), 500);

        res.json({ status: 'Processing started' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
};
