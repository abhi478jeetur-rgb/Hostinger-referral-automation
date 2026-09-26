-- ====================================================================
-- HOSTINGER AUTO-AGENT SUPABASE SCHEMA
-- Run this in the Supabase Dashboard -> SQL Editor -> New Query -> Run
-- ====================================================================

-- 1. Leads Table (stores all harvested Tier-1 US/UK businesses)
CREATE TABLE IF NOT EXISTS public.leads (
    id BIGINT PRIMARY KEY,
    business_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    website TEXT,
    domain TEXT,
    phone TEXT,
    location TEXT,
    category TEXT,
    rating NUMERIC DEFAULT 0.0,
    reviews_count INTEGER DEFAULT 0,
    ttfb_seconds NUMERIC DEFAULT 0.0,
    status TEXT DEFAULT 'NEW',  -- 'NEW', 'SENT_1', 'REPLIED', 'SENT_2', 'CONVERTED'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supabase_leads_email ON public.leads(email);
CREATE INDEX IF NOT EXISTS idx_supabase_leads_domain ON public.leads(domain);
CREATE INDEX IF NOT EXISTS idx_supabase_leads_status ON public.leads(status);

-- 2. Email Logs Table (tracks Step 1 hook and Step 2 Hostinger pitch emails)
CREATE TABLE IF NOT EXISTS public.email_logs (
    id BIGSERIAL PRIMARY KEY,
    lead_id BIGINT REFERENCES public.leads(id) ON DELETE CASCADE,
    account_used TEXT NOT NULL,
    step INTEGER NOT NULL, -- 1 for Hook, 2 for Referral Pitch
    message_id TEXT,
    thread_id TEXT,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    open_status INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_supabase_logs_lead ON public.email_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_supabase_logs_thread ON public.email_logs(thread_id);

-- 3. Replies Table (tracks client incoming responses & AI follow-up drafts)
CREATE TABLE IF NOT EXISTS public.replies (
    id BIGSERIAL PRIMARY KEY,
    lead_id BIGINT REFERENCES public.leads(id) ON DELETE CASCADE,
    raw_reply_text TEXT NOT NULL,
    ai_reply_text TEXT,
    replied_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supabase_replies_lead ON public.replies(lead_id);

-- 4. Enable Row Level Security (RLS) & Allow Anon/Authenticated Access
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.replies ENABLE ROW LEVEL SECURITY;

-- Permissive policies for anon API Key synchronization
DROP POLICY IF EXISTS "Allow anon all on leads" ON public.leads;
CREATE POLICY "Allow anon all on leads" ON public.leads
    FOR ALL TO anon, authenticated
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon all on email_logs" ON public.email_logs;
CREATE POLICY "Allow anon all on email_logs" ON public.email_logs
    FOR ALL TO anon, authenticated
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon all on replies" ON public.replies;
CREATE POLICY "Allow anon all on replies" ON public.replies
    FOR ALL TO anon, authenticated
    USING (true)
    WITH CHECK (true);
