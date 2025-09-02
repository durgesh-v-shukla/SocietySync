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

CREATE TABLE public.bills (
    bill_id integer NOT NULL,
    flat_number character varying(10) NOT NULL,
    bill_type character varying(50) NOT NULL,
    amount numeric(10,2) NOT NULL,
    due_date date NOT NULL,
    payment_status character varying(20) DEFAULT 'pending'::character varying,
    payment_date date,
    payment_method character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    CONSTRAINT bills_payment_status_check CHECK (payment_status IN ('pending', 'paid', 'overdue'))
);

CREATE SEQUENCE public.bills_bill_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.bills_bill_id_seq OWNED BY public.bills.bill_id;

CREATE TABLE public.complaints (
    complaint_id integer NOT NULL,
    user_id integer,
    flat_number character varying(10) NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    category character varying(50) NOT NULL,
    priority character varying(20) DEFAULT 'medium'::character varying,
    status character varying(20) DEFAULT 'open'::character varying,
    admin_response text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp without time zone,
    CONSTRAINT complaints_priority_check CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    CONSTRAINT complaints_status_check CHECK (status IN ('open', 'in_progress', 'resolved', 'closed'))
);

CREATE SEQUENCE public.complaints_complaint_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.complaints_complaint_id_seq OWNED BY public.complaints.complaint_id;

CREATE TABLE public.notification_reads (
    read_id integer NOT NULL,
    notification_id integer,
    user_id integer,
    read_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.notification_reads_read_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.notification_reads_read_id_seq OWNED BY public.notification_reads.read_id;

CREATE TABLE public.notifications (
    notification_id integer NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    created_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    priority character varying(20) DEFAULT 'normal',
    CONSTRAINT notifications_priority_check CHECK (priority IN ('low', 'normal', 'high'))
);

CREATE SEQUENCE public.notifications_notification_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.notifications_notification_id_seq OWNED BY public.notifications.notification_id;

CREATE TABLE public.owners (
    owner_id integer NOT NULL,
    user_id integer,
    flat_number character varying(10) NOT NULL,
    ownership_start_date date,
    emergency_contact character varying(15),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.owners_owner_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.owners_owner_id_seq OWNED BY public.owners.owner_id;

CREATE TABLE public.poll_options (
    option_id integer NOT NULL,
    poll_id integer,
    option_text character varying(200) NOT NULL,
    vote_count integer DEFAULT 0
);

CREATE SEQUENCE public.poll_options_option_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.poll_options_option_id_seq OWNED BY public.poll_options.option_id;

CREATE TABLE public.polls (
    poll_id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    created_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    end_date date,
    status character varying(20) DEFAULT 'active',
    CONSTRAINT polls_status_check CHECK (status IN ('active', 'closed'))
);

CREATE SEQUENCE public.polls_poll_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.polls_poll_id_seq OWNED BY public.polls.poll_id;

CREATE TABLE public.tenants (
    tenant_id integer NOT NULL,
    user_id integer,
    owner_id integer,
    flat_number character varying(10) NOT NULL,
    rent_amount numeric(10,2),
    lease_start_date date,
    lease_end_date date,
    security_deposit numeric(10,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.tenants_tenant_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.tenants_tenant_id_seq OWNED BY public.tenants.tenant_id;

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    flat_number character varying(10),
    name character varying(100) NOT NULL,
    email character varying(100),
    phone character varying(15),
    profile_picture text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone,
    password_changed boolean DEFAULT false,
    initial_password character varying(50),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'owner', 'tenant'))
);

CREATE SEQUENCE public.users_user_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;

CREATE TABLE public.visitors (
    visitor_id integer NOT NULL,
    flat_number character varying(10) NOT NULL,
    visitor_name character varying(100) NOT NULL,
    visitor_phone character varying(15),
    purpose character varying(200),
    entry_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    exit_time timestamp without time zone,
    vehicle_number character varying(20),
    logged_by integer,
    status character varying(20) DEFAULT 'in',
    CONSTRAINT visitors_status_check CHECK (status IN ('in', 'out'))
);

CREATE SEQUENCE public.visitors_visitor_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.visitors_visitor_id_seq OWNED BY public.visitors.visitor_id;

CREATE TABLE public.votes (
    vote_id integer NOT NULL,
    poll_id integer,
    option_id integer,
    user_id integer,
    voted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.votes_vote_id_seq AS integer START WITH 1 INCREMENT BY 1 CACHE 1;
ALTER SEQUENCE public.votes_vote_id_seq OWNED BY public.votes.vote_id;

ALTER TABLE ONLY public.bills ALTER COLUMN bill_id SET DEFAULT nextval('public.bills_bill_id_seq'::regclass);
ALTER TABLE ONLY public.complaints ALTER COLUMN complaint_id SET DEFAULT nextval('public.complaints_complaint_id_seq'::regclass);
ALTER TABLE ONLY public.notification_reads ALTER COLUMN read_id SET DEFAULT nextval('public.notification_reads_read_id_seq'::regclass);
ALTER TABLE ONLY public.notifications ALTER COLUMN notification_id SET DEFAULT nextval('public.notifications_notification_id_seq'::regclass);
ALTER TABLE ONLY public.owners ALTER COLUMN owner_id SET DEFAULT nextval('public.owners_owner_id_seq'::regclass);
ALTER TABLE ONLY public.poll_options ALTER COLUMN option_id SET DEFAULT nextval('public.poll_options_option_id_seq'::regclass);
ALTER TABLE ONLY public.polls ALTER COLUMN poll_id SET DEFAULT nextval('public.polls_poll_id_seq'::regclass);
ALTER TABLE ONLY public.tenants ALTER COLUMN tenant_id SET DEFAULT nextval('public.tenants_tenant_id_seq'::regclass);
ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);
ALTER TABLE ONLY public.visitors ALTER COLUMN visitor_id SET DEFAULT nextval('public.visitors_visitor_id_seq'::regclass);
ALTER TABLE ONLY public.votes ALTER COLUMN vote_id SET DEFAULT nextval('public.votes_vote_id_seq'::regclass);

ALTER TABLE ONLY public.bills ADD CONSTRAINT bills_pkey PRIMARY KEY (bill_id);
ALTER TABLE ONLY public.complaints ADD CONSTRAINT complaints_pkey PRIMARY KEY (complaint_id);
ALTER TABLE ONLY public.notification_reads ADD CONSTRAINT notification_reads_pkey PRIMARY KEY (read_id);
ALTER TABLE ONLY public.notification_reads ADD CONSTRAINT notification_reads_notification_id_user_id_key UNIQUE (notification_id, user_id);
ALTER TABLE ONLY public.notifications ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);
ALTER TABLE ONLY public.owners ADD CONSTRAINT owners_pkey PRIMARY KEY (owner_id);
ALTER TABLE ONLY public.poll_options ADD CONSTRAINT poll_options_pkey PRIMARY KEY (option_id);
ALTER TABLE ONLY public.polls ADD CONSTRAINT polls_pkey PRIMARY KEY (poll_id);
ALTER TABLE ONLY public.tenants ADD CONSTRAINT tenants_pkey PRIMARY KEY (tenant_id);
ALTER TABLE ONLY public.users ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);
ALTER TABLE ONLY public.users ADD CONSTRAINT users_username_key UNIQUE (username);
ALTER TABLE ONLY public.visitors ADD CONSTRAINT visitors_pkey PRIMARY KEY (visitor_id);
ALTER TABLE ONLY public.votes ADD CONSTRAINT votes_pkey PRIMARY KEY (vote_id);
ALTER TABLE ONLY public.votes ADD CONSTRAINT votes_poll_id_user_id_key UNIQUE (poll_id, user_id);

ALTER TABLE ONLY public.bills ADD CONSTRAINT bills_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);
ALTER TABLE ONLY public.complaints ADD CONSTRAINT complaints_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);
ALTER TABLE ONLY public.notification_reads ADD CONSTRAINT notification_reads_notification_id_fkey FOREIGN KEY (notification_id) REFERENCES public.notifications(notification_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.notification_reads ADD CONSTRAINT notification_reads_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.notifications ADD CONSTRAINT notifications_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);
ALTER TABLE ONLY public.owners ADD CONSTRAINT owners_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.poll_options ADD CONSTRAINT poll_options_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(poll_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.polls ADD CONSTRAINT polls_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);
ALTER TABLE ONLY public.tenants ADD CONSTRAINT tenants_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.owners(owner_id);
ALTER TABLE ONLY public.tenants ADD CONSTRAINT tenants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.visitors ADD CONSTRAINT visitors_logged_by_fkey FOREIGN KEY (logged_by) REFERENCES public.users(user_id);
ALTER TABLE ONLY public.votes ADD CONSTRAINT votes_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.poll_options(option_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.votes ADD CONSTRAINT votes_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(poll_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.votes ADD CONSTRAINT votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
