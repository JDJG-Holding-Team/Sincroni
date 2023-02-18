CREATE TABLE SICRONI_GLOBAL_CHAT(
   "server_id" BIGINT NOT NULL,
   "channel_id" BIGINT NOT NULL,
   "webhook_url" TEXT,
   "chat_type" SMALLINT DEFAULT 0 NOT NULL,
   UNIQUE ("server_id", "channel_id"),
   PRIMARY KEY ("server_id", "chat_type")
)