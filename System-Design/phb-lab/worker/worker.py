import os
import json
import pika
import ffmpeg
from minio import Minio
import psycopg2
from dotenv import load_dotenv
import shutil

load_dotenv('../.env')

# Configuration
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672')
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = os.getenv('MINIO_ROOT_USER', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
BUCKET_NAME = 'videos'

# Database Connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'video_db'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

# MinIO Client
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def process_video(ch, method, properties, body):
    data = json.loads(body)
    video_id = data['videoId']
    print(f" [x] Received video task: {video_id}")

    local_input = f"/tmp/{video_id}_raw.mp4"
    output_dir = f"/tmp/{video_id}_hls"

    try:
        # 1. Download Video
        object_name = f"{video_id}/raw.mp4"
        print(f"Downloading {object_name}...")
        client.fget_object(BUCKET_NAME, object_name, local_input)
        
        # 2. Transcode to HLS
        os.makedirs(output_dir, exist_ok=True)
        print("Transcoding...")
        
        # Generate HLS playlist and segments
        # We create a simple single-bitrate HLS for MVP
        (
            ffmpeg
            .input(local_input)
            .output(f"{output_dir}/playlist.m3u8", format='hls', hls_time=10, hls_list_size=0)
            .run(overwrite_output=True, quiet=True)
        )
        print("Transcoding complete")

        # 3. Upload HLS files to MinIO
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # s3_key structure: {uuid}/hls/{filename}
                s3_key = f"{video_id}/hls/{file}"
                client.fput_object(BUCKET_NAME, s3_key, file_path)
                print(f"Uploaded {s3_key}")

        # 4. Update DB Status
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE videos SET status = 'READY' WHERE id = %s", (video_id,))
        conn.commit()
        cur.close()
        conn.close()

        print(f" [x] Done processing {video_id}")

    except Exception as e:
        print(f"Error processing {video_id}: {e}")
        # Ideally update DB to FAILED here

    finally:
        # Cleanup
        if os.path.exists(local_input):
            os.remove(local_input)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print("Starting worker...")
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    queue_name = 'video_transcode'
    channel.queue_declare(queue=queue_name, durable=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=process_video)

    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
