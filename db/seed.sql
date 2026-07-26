-- Seed companies: a starter set of well-known NSE (NIFTY-50-ish) symbols.
-- Real universe comes from the refresh_universe pipeline job later (M1+).
-- breeze_code left NULL; mapped when the Breeze client is built.

INSERT INTO companies (symbol, name, sector) VALUES
    ('RELIANCE',   'Reliance Industries Ltd',          'Energy'),
    ('TCS',        'Tata Consultancy Services Ltd',    'IT'),
    ('HDFCBANK',   'HDFC Bank Ltd',                     'Financials'),
    ('ICICIBANK',  'ICICI Bank Ltd',                    'Financials'),
    ('INFY',       'Infosys Ltd',                       'IT'),
    ('HINDUNILVR', 'Hindustan Unilever Ltd',            'FMCG'),
    ('ITC',        'ITC Ltd',                           'FMCG'),
    ('SBIN',       'State Bank of India',                'Financials'),
    ('BHARTIARTL', 'Bharti Airtel Ltd',                 'Telecom'),
    ('KOTAKBANK',  'Kotak Mahindra Bank Ltd',           'Financials'),
    ('LT',         'Larsen & Toubro Ltd',               'Infrastructure'),
    ('AXISBANK',   'Axis Bank Ltd',                     'Financials'),
    ('BAJFINANCE', 'Bajaj Finance Ltd',                 'Financials'),
    ('ASIANPAINT', 'Asian Paints Ltd',                  'Consumer Durables'),
    ('MARUTI',     'Maruti Suzuki India Ltd',           'Automobile'),
    ('TITAN',      'Titan Company Ltd',                 'Consumer Durables'),
    ('SUNPHARMA',  'Sun Pharmaceutical Industries Ltd', 'Pharma'),
    ('ULTRACEMCO', 'UltraTech Cement Ltd',              'Cement'),
    ('WIPRO',      'Wipro Ltd',                         'IT'),
    ('NESTLEIND',  'Nestle India Ltd',                  'FMCG'),
    ('ONGC',       'Oil & Natural Gas Corporation Ltd', 'Energy'),
    ('NTPC',       'NTPC Ltd',                          'Power'),
    ('POWERGRID',  'Power Grid Corporation of India Ltd','Power'),
    ('M&M',        'Mahindra & Mahindra Ltd',           'Automobile'),
    ('TATASTEEL',  'Tata Steel Ltd',                     'Metals'),
    ('TATAMOTORS', 'Tata Motors Ltd',                   'Automobile'),
    ('ADANIENT',   'Adani Enterprises Ltd',             'Diversified'),
    ('HCLTECH',    'HCL Technologies Ltd',              'IT'),
    ('JSWSTEEL',   'JSW Steel Ltd',                      'Metals'),
    ('BAJAJFINSV', 'Bajaj Finserv Ltd',                 'Financials')
ON CONFLICT (symbol) DO NOTHING;

-- Single default user (v1 is single-user, no auth - see 06_DECISIONS.md).
-- Fixed id so the backend can reference it without a lookup.
INSERT INTO users (id) VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;
