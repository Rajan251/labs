// ============================================
// MongoDB Connection Example using Environment Variables
// Node.js with dotenv
// ============================================

require('dotenv').config();
const { MongoClient } = require('mongodb');

class MongoDBConfig {
    constructor() {
        // Option 1: Use full connection string (RECOMMENDED)
        this.uri = process.env.MONGODB_URI;

        // Option 2: Build connection string from components
        if (!this.uri) {
            this.uri = this._buildConnectionString();
        }

        // Connection pool settings
        this.maxPoolSize = parseInt(process.env.MONGODB_MAX_POOL_SIZE || '100');
        this.minPoolSize = parseInt(process.env.MONGODB_MIN_POOL_SIZE || '10');
        this.maxIdleTimeMS = parseInt(process.env.MONGODB_MAX_IDLE_TIME_MS || '30000');

        // Write concern settings
        this.writeConcern = process.env.MONGODB_WRITE_CONCERN || 'majority';
        this.writeTimeoutMS = parseInt(process.env.MONGODB_WRITE_TIMEOUT_MS || '5000');
        this.journal = process.env.MONGODB_JOURNAL === 'true';

        // Read preference settings
        this.readPreference = process.env.MONGODB_READ_PREFERENCE || 'primary';
        this.maxStalenessSeconds = parseInt(process.env.MONGODB_MAX_STALENESS_SECONDS || '90');

        // Timeout settings
        this.serverSelectionTimeoutMS = parseInt(process.env.MONGODB_SERVER_SELECTION_TIMEOUT_MS || '5000');
        this.connectTimeoutMS = parseInt(process.env.MONGODB_CONNECT_TIMEOUT_MS || '10000');
        this.socketTimeoutMS = parseInt(process.env.MONGODB_SOCKET_TIMEOUT_MS || '10000');

        // Retry settings
        this.retryWrites = process.env.MONGODB_RETRY_WRITES === 'true';
        this.retryReads = process.env.MONGODB_RETRY_READS === 'true';

        // TLS settings
        this.tlsEnabled = process.env.MONGODB_TLS_ENABLED === 'true';
        this.tlsCAFile = process.env.MONGODB_TLS_CA_FILE;
        this.tlsCertFile = process.env.MONGODB_TLS_CERT_FILE;

        // Application settings
        this.appName = process.env.APP_NAME || 'MyApplication';
        this.appEnv = process.env.APP_ENV || 'development';
    }

    _buildConnectionString() {
        const username = process.env.MONGODB_USERNAME;
        const password = process.env.MONGODB_PASSWORD;
        const hosts = process.env.MONGODB_HOSTS || 'localhost:27017';
        const database = process.env.MONGODB_DATABASE || 'test';
        const replicaSet = process.env.MONGODB_REPLICA_SET;
        const authSource = process.env.MONGODB_AUTH_SOURCE || 'admin';

        // Build base URI
        let uri;
        if (username && password) {
            uri = `mongodb://${username}:${password}@${hosts}/${database}`;
        } else {
            uri = `mongodb://${hosts}/${database}`;
        }

        // Add query parameters
        const params = [];
        if (replicaSet) params.push(`replicaSet=${replicaSet}`);
        if (authSource) params.push(`authSource=${authSource}`);
        params.push(`w=${this.writeConcern}`);
        params.push(`wtimeout=${this.writeTimeoutMS}`);
        params.push(`readPreference=${this.readPreference}`);
        params.push(`maxPoolSize=${this.maxPoolSize}`);
        params.push(`minPoolSize=${this.minPoolSize}`);
        if (this.retryWrites) params.push('retryWrites=true');

        if (params.length > 0) {
            uri += '?' + params.join('&');
        }

        return uri;
    }
}

class MongoDBConnection {
    constructor() {
        this.config = new MongoDBConfig();
        this.client = null;
        this.db = null;
    }

    async connect() {
        try {
            console.log(`Connecting to MongoDB (${this.config.appEnv})...`);
            console.log(`App Name: ${this.config.appName}`);

            // Create MongoDB client
            this.client = new MongoClient(this.config.uri, {
                serverSelectionTimeoutMS: this.config.serverSelectionTimeoutMS,
                connectTimeoutMS: this.config.connectTimeoutMS,
                socketTimeoutMS: this.config.socketTimeoutMS,
                maxPoolSize: this.config.maxPoolSize,
                minPoolSize: this.config.minPoolSize,
                maxIdleTimeMS: this.config.maxIdleTimeMS,
                retryWrites: this.config.retryWrites,
                retryReads: this.config.retryReads,
                appName: this.config.appName
            });

            // Connect to MongoDB
            await this.client.connect();

            // Test connection
            await this.client.db('admin').command({ ping: 1 });
            console.log('✅ Connected to MongoDB successfully');

            // Get database
            const databaseName = process.env.MONGODB_DATABASE || 'test';
            this.db = this.client.db(databaseName);

            // Log connection info
            await this._logConnectionInfo();

            return this.db;

        } catch (error) {
            console.error('❌ Failed to connect to MongoDB:', error);
            throw error;
        }
    }

    async _logConnectionInfo() {
        try {
            // Get server info
            const serverInfo = await this.client.db('admin').admin().serverInfo();
            console.log(`MongoDB Version: ${serverInfo.version}`);

            // Check if replica set
            const isMaster = await this.client.db('admin').admin().command({ isMaster: 1 });
            if (isMaster.setName) {
                console.log(`Replica Set: ${isMaster.setName}`);
                console.log(`Primary: ${isMaster.primary || 'Unknown'}`);
            } else {
                console.log('Running in standalone mode');
            }

            // Log configuration
            console.log(`Write Concern: ${this.config.writeConcern}`);
            console.log(`Read Preference: ${this.config.readPreference}`);
            console.log(`Connection Pool: ${this.config.minPoolSize}-${this.config.maxPoolSize}`);

        } catch (error) {
            console.warn('Could not retrieve connection info:', error.message);
        }
    }

    async close() {
        if (this.client) {
            await this.client.close();
            console.log('✅ MongoDB connection closed');
        }
    }

    async insertDocument(collectionName, document) {
        try {
            const collection = this.db.collection(collectionName);

            const result = await collection.insertOne(document, {
                writeConcern: {
                    w: this.config.writeConcern,
                    wtimeout: this.config.writeTimeoutMS,
                    j: this.config.journal
                }
            });

            console.log(`✅ Inserted document: ${result.insertedId}`);
            return result.insertedId;

        } catch (error) {
            console.error('❌ Insert failed:', error);
            throw error;
        }
    }

    async findDocuments(collectionName, query = {}) {
        try {
            const collection = this.db.collection(collectionName);
            const documents = await collection.find(query).toArray();

            console.log(`✅ Found ${documents.length} documents`);
            return documents;

        } catch (error) {
            console.error('❌ Find failed:', error);
            throw error;
        }
    }
}

// Example usage
async function main() {
    const mongo = new MongoDBConnection();

    try {
        await mongo.connect();

        console.log('\n' + '='.repeat(60));
        console.log('MongoDB Connection Test');
        console.log('='.repeat(60) + '\n');

        // Insert test document
        console.log('📝 Inserting test document...');
        const docId = await mongo.insertDocument('test_collection', {
            message: 'Hello from .env configuration!',
            timestamp: new Date(),
            environment: process.env.APP_ENV || 'unknown'
        });
        console.log(`   Document ID: ${docId}\n`);

        // Find documents
        console.log('📖 Reading documents...');
        const documents = await mongo.findDocuments('test_collection');
        documents.forEach(doc => {
            console.log(`   - ${doc.message} (${doc.environment})`);
        });

        console.log('\n' + '='.repeat(60));
        console.log('✅ Test completed successfully!');
        console.log('='.repeat(60) + '\n');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        await mongo.close();
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = { MongoDBConnection, MongoDBConfig };
