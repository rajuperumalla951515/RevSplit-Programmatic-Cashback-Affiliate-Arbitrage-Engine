import { Kafka } from 'kafkajs';
import pkg from 'pg';
const { Pool } = pkg;
import { config } from './config.js';

const kafka = new Kafka({
  clientId: 'revsplit-settlement-worker',
  brokers: config.kafka.brokers,
});

const consumer = kafka.consumer({ groupId: config.kafka.groupId });

const pgPool = new Pool({
  host: config.postgres.host,
  port: config.postgres.port,
  user: config.postgres.user,
  password: config.postgres.password,
  database: config.postgres.database,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

async function processPostbackMessage(payload) {
  const client = await pgPool.connect();
  try {
    const { sub_id, merchant_transaction_id, gross_sale_amount, gross_commission_amount, currency, raw_metadata } = payload;
    
    console.log(`[Kafka Settlement] Processing postback sub_id=${sub_id}, merchant_tx=${merchant_transaction_id}`);

    // Begin PostgreSQL ACID transaction
    await client.query('BEGIN');

    // Execute atomic stored procedure with FOR UPDATE row locking
    const query = `
      SELECT process_commission_postback(
        $1, $2, $3, $4, $5, $6
      ) AS transaction_id;
    `;
    const res = await client.query(query, [
      sub_id,
      merchant_transaction_id,
      gross_sale_amount,
      gross_commission_amount,
      currency || 'INR',
      JSON.stringify(raw_metadata || payload),
    ]);

    await client.query('COMMIT');
    console.log(`[Kafka Settlement SUCCESS] Transaction ID: ${res.rows[0].transaction_id}`);
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(`[Kafka Settlement ERROR] Failed to process postback: ${err.message}`);
    throw err;
  } finally {
    client.release();
  }
}

export async function startConsumer() {
  await consumer.connect();
  await consumer.subscribe({ topic: config.kafka.topicPostback, fromBeginning: false });

  console.log(`🚀 Settlement Consumer listening on Kafka topic: ${config.kafka.topicPostback}`);

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const rawValue = message.value.toString();
      try {
        const payload = JSON.parse(rawValue);
        await processPostbackMessage(payload);
      } catch (err) {
        console.error(`Error processing Kafka message on offset ${message.offset}:`, err);
      }
    },
  });
}

// Allow standalone execution
if (process.argv[1].endsWith('consumer.js')) {
  startConsumer().catch(err => {
    console.error('Fatal Kafka Consumer Error:', err);
    process.exit(1);
  });
}
