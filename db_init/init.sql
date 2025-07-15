\c apikey
--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: apikey_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.apikey_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_key (
    id integer DEFAULT nextval('public.apikey_id_seq'::regclass) NOT NULL,
    role_id integer,
    api_key character varying(64)
);


--
-- Name: api_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_user (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    phone_number character varying(20),
    password_hash character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true,
    email_verified boolean DEFAULT false,
    phone_verified boolean DEFAULT false,
    role_id integer,
    api_key_id integer
);


--
-- Name: api_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_user_id_seq OWNED BY public.api_user.id;


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id integer DEFAULT nextval('public.roles_id_seq'::regclass) NOT NULL,
    name character varying(64)
);


--
-- Name: api_user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_user ALTER COLUMN id SET DEFAULT nextval('public.api_user_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_user api_user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_email_key UNIQUE (email);


--
-- Name: api_user api_user_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_phone_number_key UNIQUE (phone_number);


--
-- Name: api_user api_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_pkey PRIMARY KEY (id);


--
-- Name: roles idx_16511_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT idx_16511_roles_pkey PRIMARY KEY (id);


--
-- Name: api_key idx_16516_api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT idx_16516_api_key_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: ix_api_key_api_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_api_key_api_key ON public.api_key USING btree (api_key);


--
-- Name: ix_api_key_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_key_id ON public.api_key USING btree (id);


--
-- Name: ix_roles_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_roles_id ON public.roles USING btree (id);


--
-- Name: api_key api_key_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: api_user api_user_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.api_key(id);


--
-- Name: api_user api_user_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

GRANT USAGE ON SCHEMA public TO myadminuser;


--
-- Name: TABLE api_user; Type: ACL; Schema: public; Owner: -
--

GRANT SELECT ON TABLE public.api_user TO myadminuser;


--
-- PostgreSQL database dump complete
--


\c blacklist
--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: url_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.url_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: url; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.url (
    id integer DEFAULT nextval('public.url_id_seq'::regclass) NOT NULL,
    url text NOT NULL,
    category character varying(100) NOT NULL,
    date_added date NOT NULL,
    reason character varying(500) NOT NULL,
    status boolean,
    source character varying(500) NOT NULL
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: url idx_16537_url_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.url
    ADD CONSTRAINT idx_16537_url_pkey PRIMARY KEY (id);


--
-- Name: url url_url_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.url
    ADD CONSTRAINT url_url_key UNIQUE (url);


--
-- Name: ix_url_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_url_id ON public.url USING btree (id);


--
-- PostgreSQL database dump complete
--

\c shortener
--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)

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
-- Name: status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.status_enum AS ENUM (
    '0',
    'Dangerous',
    'Safe',
    'In queue for scanning',
    '-1',
    '1',
    'No conclusive information',
    'No classification'
);


--
-- Name: insert_url_to_check(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.insert_url_to_check() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO urls_to_check (url) VALUES (NEW.target_url);
    RETURN NEW;
END;
$$;


--
-- Name: notify_new_url(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.notify_new_url() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_notify('new_url', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$;


--
-- Name: notify_url_change(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.notify_url_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_notify('url_change', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num text NOT NULL
);


--
-- Name: scan_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scan_records_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scan_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scan_records (
    id integer DEFAULT nextval('public.scan_records_id_seq'::regclass) NOT NULL,
    "timestamp" timestamp with time zone,
    url character varying,
    status character varying,
    scan_type character varying,
    result character varying,
    submission_type character varying,
    scan_id character varying,
    sha256 character varying,
    threat_score integer,
    verdict text
);


--
-- Name: urls_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.urls_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: urls; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.urls (
    id integer DEFAULT nextval('public.urls_id_seq'::regclass) NOT NULL,
    key character varying,
    secret_key character varying,
    target_url character varying,
    is_active boolean,
    clicks integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone,
    api_key character varying,
    is_checked boolean DEFAULT false,
    status character varying,
    title character varying(255),
    favicon_url character varying(255)
);


--
-- Name: urls_to_check_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.urls_to_check_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: urls_to_check; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.urls_to_check (
    id integer DEFAULT nextval('public.urls_to_check_id_seq'::regclass) NOT NULL,
    url character varying
);


--
-- Name: urls idx_16455_urls_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT idx_16455_urls_pkey PRIMARY KEY (id);


--
-- Name: alembic_version idx_16462_sqlite_autoindex_alembic_version_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT idx_16462_sqlite_autoindex_alembic_version_1 PRIMARY KEY (version_num);


--
-- Name: urls_to_check idx_16467_urls_to_check_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urls_to_check
    ADD CONSTRAINT idx_16467_urls_to_check_pkey PRIMARY KEY (id);


--
-- Name: scan_records idx_16472_scan_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scan_records
    ADD CONSTRAINT idx_16472_scan_records_pkey PRIMARY KEY (id);


--
-- Name: ix_scan_records_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scan_records_id ON public.scan_records USING btree (id);


--
-- Name: ix_urls_api_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_urls_api_key ON public.urls USING btree (api_key);


--
-- Name: ix_urls_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_urls_id ON public.urls USING btree (id);


--
-- Name: ix_urls_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_urls_key ON public.urls USING btree (key);


--
-- Name: ix_urls_secret_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_urls_secret_key ON public.urls USING btree (secret_key);


--
-- Name: ix_urls_target_url; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_urls_target_url ON public.urls USING btree (target_url);


--
-- Name: ix_urls_to_check_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_urls_to_check_id ON public.urls_to_check USING btree (id);


--
-- Name: urls check_new_url; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER check_new_url AFTER INSERT ON public.urls FOR EACH ROW EXECUTE FUNCTION public.insert_url_to_check();


--
-- Name: urls new_url_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER new_url_trigger AFTER INSERT ON public.urls FOR EACH ROW EXECUTE FUNCTION public.notify_new_url();


--
-- Name: urls url_insert_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER url_insert_trigger AFTER INSERT ON public.urls FOR EACH ROW EXECUTE FUNCTION public.notify_url_change();


--
-- Name: urls url_update_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER url_update_trigger AFTER UPDATE ON public.urls FOR EACH ROW EXECUTE FUNCTION public.notify_url_change();


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA public TO myadminuser;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE myadminuser IN SCHEMA public GRANT ALL ON SEQUENCES  TO myadminuser;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE myadminuser IN SCHEMA public GRANT ALL ON TABLES  TO myadminuser;


--
-- PostgreSQL database dump complete
--

\c user
--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num text NOT NULL
);


--
-- Name: editable_html_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.editable_html_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: editable_html; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.editable_html (
    id bigint DEFAULT nextval('public.editable_html_id_seq'::regclass) NOT NULL,
    editor_name text,
    value text
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id bigint DEFAULT nextval('public.roles_id_seq'::regclass) NOT NULL,
    name text,
    index text,
    "default" boolean,
    permissions bigint
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id bigint DEFAULT nextval('public.users_id_seq'::regclass) NOT NULL,
    confirmed boolean,
    first_name text,
    last_name text,
    email text,
    password_hash text,
    role_id bigint,
    phone_number text,
    uid text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone
);


--
-- Name: roles idx_16408_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT idx_16408_roles_pkey PRIMARY KEY (id);


--
-- Name: editable_html idx_16413_editable_html_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.editable_html
    ADD CONSTRAINT idx_16413_editable_html_pkey PRIMARY KEY (id);


--
-- Name: users idx_16418_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT idx_16418_users_pkey PRIMARY KEY (id);


--
-- Name: alembic_version idx_16424_sqlite_autoindex_alembic_version_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT idx_16424_sqlite_autoindex_alembic_version_1 PRIMARY KEY (version_num);


--
-- Name: idx_16408_ix_roles_default; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_16408_ix_roles_default ON public.roles USING btree ("default");


--
-- Name: idx_16408_sqlite_autoindex_roles_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_16408_sqlite_autoindex_roles_1 ON public.roles USING btree (name);


--
-- Name: idx_16413_sqlite_autoindex_editable_html_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_16413_sqlite_autoindex_editable_html_1 ON public.editable_html USING btree (editor_name);


--
-- Name: idx_16418_ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_16418_ix_users_email ON public.users USING btree (email);


--
-- Name: idx_16418_ix_users_first_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_16418_ix_users_first_name ON public.users USING btree (first_name);


--
-- Name: idx_16418_ix_users_last_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_16418_ix_users_last_name ON public.users USING btree (last_name);


--
-- Name: idx_16418_ix_users_phone_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_16418_ix_users_phone_number ON public.users USING btree (phone_number);


--
-- Name: idx_16418_ix_users_uid; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_16418_ix_users_uid ON public.users USING btree (uid);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- PostgreSQL database dump complete
--

