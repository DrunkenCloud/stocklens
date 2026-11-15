-- Starter watchlist: well-known NSE (NIFTY-50-ish) symbols. Applied by
-- `python db/migrate.py --seed`; idempotent. breeze_code/isin get filled in by
-- the refresh_securities job.

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
    -- TATAMOTORS demerged (2025) into two separately-listed NSE symbols;
    -- the old ticker is gone, confirmed by both Breeze and Yahoo Finance
    -- returning "not found" for it.
    ('TMCV',       'Tata Motors Ltd (Commercial Vehicles)', 'Automobile'),
    ('TMPV',       'Tata Motors Passenger Vehicles Ltd',    'Automobile'),
    ('ADANIENT',   'Adani Enterprises Ltd',             'Diversified'),
    ('HCLTECH',    'HCL Technologies Ltd',              'IT'),
    ('JSWSTEEL',   'JSW Steel Ltd',                      'Metals'),
    ('BAJAJFINSV', 'Bajaj Finserv Ltd',                 'Financials')
ON CONFLICT (symbol) DO NOTHING;

