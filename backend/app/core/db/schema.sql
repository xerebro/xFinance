-- PostgreSQL schema for xFinance normalized storage.

CREATE TABLE IF NOT EXISTS person (
  person_id UUID PRIMARY KEY,
  full_name TEXT NOT NULL,
  chamber TEXT,
  role TEXT,
  house_id TEXT,
  senate_id TEXT,
  oge_id TEXT,
  cik TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS issuer (
  issuer_id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  ticker TEXT,
  cik TEXT,
  cusip TEXT
);

CREATE TABLE IF NOT EXISTS filing_raw (
  filing_id UUID PRIMARY KEY,
  source TEXT NOT NULL,
  source_key TEXT NOT NULL,
  filed_date DATE,
  doc TEXT,
  json JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (source, source_key)
);

CREATE TABLE IF NOT EXISTS transaction (
  tx_id UUID PRIMARY KEY,
  filing_id UUID REFERENCES filing_raw(filing_id),
  person_id UUID REFERENCES person(person_id),
  issuer_id UUID REFERENCES issuer(issuer_id),
  action TEXT,
  quantity NUMERIC,
  price NUMERIC,
  amount NUMERIC,
  tx_date DATE,
  ticker TEXT,
  cik TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS position_13f (
  pos_id UUID PRIMARY KEY,
  filing_id UUID REFERENCES filing_raw(filing_id),
  manager_name TEXT,
  cik TEXT,
  cusip TEXT,
  issuer_name TEXT,
  value_usd BIGINT,
  sshPrnamt BIGINT,
  sshPrnamtType TEXT
);
