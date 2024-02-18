CREATE TABLE IF NOT EXISTS SINCRONI_GLOBAL_CHAT(
   "server_id" BIGINT NOT NULL,
   "channel_id" BIGINT NOT NULL,
   "webhook_url" TEXT,
   "chat_type" SMALLINT DEFAULT 0 NOT NULL,
   UNIQUE ("server_id", "channel_id"),
   PRIMARY KEY ("server_id", "chat_type")
)

CREATE TABLE IF NOT EXISTS SINCRONI_BLACKLIST(
   id SERIAL NOT NULL,
   server_id BIGINT NOT NULL,
   entity_id BIGINT NOT NULL,
   pub BOOLEAN DEFAULT FALSE,
   dev BOOLEAN DEFAULT FALSE,
   private BOOLEAN DEFAULT FALSE,
   blacklist_type SMALLINT DEFAULT 0,
   reason TEXT DEFAULT "No reason provided"
   repeat BOOLEAN DEFAULT FALSE,
)

CREATE TABLE IF NOT EXISTS SINCRONI_WHITELIST(
  id SERIAL NOT NULL,
  entity_id BIGINT NOT NULL,
  whitelist_type smallint DEFAULT 0,
  reason TEXT DEFAULT "No reason provided"
)


CREATE TABLE IF NOT EXISTS SINCRONI_LINKED_CHANNELS(
  id SERIAL NOT NULL,
  origin_channel_id BIGINT NOT NULL,
  destination_channel_id BIGINT NOT NULL
)

CREATE TABLE IF NOT EXISTS SINCRONI_EMBED_COLOR(
server_id BIGINT NOT NULL,
chat_type SMALLINT DEFAULT 0 NOT NULL,
custom_color INTEGER NOT NULL,
UNIQUE (server_id, chat_type)
)
