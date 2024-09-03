--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Ubuntu 16.4-1.pgdg22.04+1)
-- Dumped by pg_dump version 16.4 (Ubuntu 16.4-1.pgdg22.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: sincroni_blacklist; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sincroni_blacklist (
    id integer NOT NULL,
    server_id bigint NOT NULL,
    entity_id bigint NOT NULL,
    pub boolean DEFAULT false,
    dev boolean DEFAULT false,
    private boolean DEFAULT false,
    blacklist_type smallint DEFAULT 0,
    reason text,
    repeat boolean DEFAULT false
);


--
-- Name: sincroni_blacklist_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sincroni_blacklist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sincroni_blacklist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sincroni_blacklist_id_seq OWNED BY public.sincroni_blacklist.id;


--
-- Name: sincroni_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sincroni_config (
    server_id bigint NOT NULL,
    webhook_embed boolean DEFAULT true,
    censor_messages boolean DEFAULT false,
    censor_links boolean DEFAULT false,
    censor_invites boolean DEFAULT false,
    chat_type smallint DEFAULT 0
);


--
-- Name: sincroni_embed_color; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sincroni_embed_color (
    server_id bigint NOT NULL,
    chat_type smallint DEFAULT 0 NOT NULL,
    custom_color integer NOT NULL
);


--
-- Name: sincroni_global_chat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sincroni_global_chat (
    server_id bigint NOT NULL,
    channel_id bigint NOT NULL,
    webhook_url text,
    chat_type smallint DEFAULT 0 NOT NULL
);


--
-- Name: sincroni_linked_channels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sincroni_linked_channels (
    id integer NOT NULL,
    origin_channel_id bigint NOT NULL,
    origin_webhook_url text,
    destination_channel_id bigint NOT NULL,
    destination_webhook_url text
);


--
-- Name: sincroni_linked_channels_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sincroni_linked_channels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sincroni_linked_channels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sincroni_linked_channels_id_seq OWNED BY public.sincroni_linked_channels.id;


--
-- Name: sincroni_whitelist; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sincroni_whitelist (
    id integer NOT NULL,
    entity_id bigint NOT NULL,
    whitelist_type smallint DEFAULT 0,
    reason text
);


--
-- Name: sincroni_whitelist_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sincroni_whitelist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sincroni_whitelist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sincroni_whitelist_id_seq OWNED BY public.sincroni_whitelist.id;


--
-- Name: sincroni_blacklist id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_blacklist ALTER COLUMN id SET DEFAULT nextval('public.sincroni_blacklist_id_seq'::regclass);


--
-- Name: sincroni_linked_channels id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_linked_channels ALTER COLUMN id SET DEFAULT nextval('public.sincroni_linked_channels_id_seq'::regclass);


--
-- Name: sincroni_whitelist id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_whitelist ALTER COLUMN id SET DEFAULT nextval('public.sincroni_whitelist_id_seq'::regclass);


--
-- Name: sincroni_global_chat sicroni_global_chat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_global_chat
    ADD CONSTRAINT sicroni_global_chat_pkey PRIMARY KEY (server_id, chat_type);


--
-- Name: sincroni_global_chat sicroni_global_chat_server_id_channel_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_global_chat
    ADD CONSTRAINT sicroni_global_chat_server_id_channel_id_key UNIQUE (server_id, channel_id);


--
-- Name: sincroni_config sincroni_config_server_id_chat_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_config
    ADD CONSTRAINT sincroni_config_server_id_chat_type_key UNIQUE (server_id, chat_type);


--
-- Name: sincroni_embed_color sincroni_embed_color_server_id_chat_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sincroni_embed_color
    ADD CONSTRAINT sincroni_embed_color_server_id_chat_type_key UNIQUE (server_id, chat_type);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

