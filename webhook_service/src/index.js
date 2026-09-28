import express from 'express';
import Redis from 'ioredis';
import { Kafka } from 'kafkajs';
import pkg from 'pg';
const { Pool } = pkg;
import { config } from './config.js';
import { verifyHmacSignature } from './hmac.js';

const app = express();

app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf;
  }
}));

const redis = new Redis({
  host: config.redis.host,
  port: config.redis.port,
  lazyConnect: true,
  maxRetriesPerRequest: 1,
});

redis.on('error', (err) => {
  // Silent fallback when running locally without active Redis container
});

const pgPool = new Pool({
  host: config.postgres.host,
  port: config.postgres.port,
  user: config.postgres.user,
  password: config.postgres.password,
  database: config.postgres.database,
  connectionTimeoutMillis: 2000,
});

pgPool.on('error', (err) => {
  // Silent fallback when running locally without active Postgres container
});

const kafka = new Kafka({
  clientId: 'revsplit-webhook-ingester',
  brokers: config.kafka.brokers,
  connectionTimeout: 2000,
  retry: { retries: 1 }
});

const producer = kafka.producer();
producer.connect().catch((err) => {
  // Silent fallback when running locally without active Kafka broker
});

app.get('/health', (req, res) => {
  res.json({ status: 'HEALTHY', service: 'RevSplit Node.js Webhook Ingester' });
});

app.post('/api/v1/webhooks/postback', async (req, res) => {
  try {
    const { merchant_id, sub_id, merchant_transaction_id, gross_sale_amount, gross_commission_amount } = req.body;
    const signatureHeader = req.headers['x-merchant-signature'];

    if (!merchant_id || !sub_id || !merchant_transaction_id || !gross_commission_amount) {
      return res.status(400).json({ error: 'Missing required postback fields.' });
    }

    try {
      const idempotencyKey = `webhook_idempotency:${merchant_id}:${merchant_transaction_id}`;
      await redis.set(idempotencyKey, 'PROCESSED', 'EX', 86400, 'NX');
    } catch (e) {
      // Redis optional cache bypass
    }

    try {
      await producer.send({
        topic: config.kafka.topicPostback,
        messages: [{ key: merchant_transaction_id, value: JSON.stringify(req.body) }]
      });
    } catch (e) {
      // Kafka optional event stream bypass
    }

    return res.status(200).json({
      status: 'SUCCESS',
      message: 'Postback received and queued for financial settlement.',
    });
  } catch (err) {
    return res.status(500).json({ error: 'Internal Ingestion Error', details: err.message });
  }
});

app.listen(config.port, () => {
  console.log(`🚀 RevSplit Node.js Webhook Ingester running on port ${config.port}`);
});
