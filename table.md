
# Table Design

That's Right, this guide will be on the table designs I use.
This way you can set it up yourself.

## Table 1

Global Chat

```postgresql
CREATE TABLE  SINCRONI_GLOBAL_CHAT(
   server_id BIGINT NOT NULL,
   channel_id BIGINT NOT NULL,
   webhook text, chat_type SMALLINT
)
```
