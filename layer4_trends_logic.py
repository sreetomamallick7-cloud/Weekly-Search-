"""
Layer 4 — Google Trends Intelligence (SerpApi Version)
Calls SerpApi for Google Trends data instead of Pytrends.
"""
import os
import requests
import logging
import time

log = logging.getLogger(__name__)
_ERRORS = []

def _err(msg):
    log.warning(msg)
    _ERRORS.append(msg)

def _get_api_key():
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        _err("SERPAPI_KEY not configured in environment")
    return key

def _fetch_serp(params):
    api_key = _get_api_key()
    if not api_key:
        return None
    
    base_url = "https://serpapi.com/search"
    params["api_key"] = api_key
    params["engine"] = "google_trends"
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        if response.status_code != 200:
            _err(f"SerpApi error ({response.status_code}): {response.text}")
            return None
        return response.json()
    except Exception as e:
        _err(f"SerpApi request failed: {str(e)}")
        return None

def _get_iot_score(keyword, geo='IN', date='today 3-m'):
    """Fetch interest over time and return the average score."""
    data = _fetch_serp({"q": keyword, "geo": geo, "date": date})
    if not data:
        return None
    
    # SerpApi structure: interest_over_time -> timeline_data -> [ { values: [ { value: "100", ... } ] } ]
    iot = data.get("interest_over_time", {})
    timeline = iot.get("timeline_data", [])
    if not timeline:
        return 0.0
    
    scores = []
    for entry in timeline:
        vals = entry.get("values", [])
        if vals:
            # Usually only one value if single keyword
            val = vals[0].get("extracted_value", 0)
            scores.append(float(val))
    
    return round(sum(scores) / len(scores), 1) if scores else 0.0

def _get_iot_series(keyword, geo='IN', date='today 3-m'):
    """Fetch full interest over time series."""
    data = _fetch_serp({"q": keyword, "geo": geo, "date": date})
    if not data:
        return []
    
    iot = data.get("interest_over_time", {})
    timeline = iot.get("timeline_data", [])
    series = []
    for entry in timeline:
        # Date can be "Oct 15 – Oct 21, 2023" or similar. SerpApi usually provides timestamp.
        # We'll use the formatted date if available.
        date_str = entry.get("date", "")
        vals = entry.get("values", [])
        if vals:
            val = vals[0].get("extracted_value", 0)
            series.append({"date": date_str, "value": int(val)})
    return series

def _get_rising_queries(keyword, geo='IN', date='today 3-m'):
    """Fetch rising related queries."""
    data = _fetch_serp({"q": keyword, "geo": geo, "date": date, "data_type": "RELATED_QUERIES"})
    if not data:
        return []
    
    # SerpApi structure: related_queries -> rising -> [ { query: "...", value: "...", extracted_value: 123 } ]
    rq = data.get("related_queries", {})
    rising = rq.get("rising", [])
    result = []
    for r in rising:
        result.append({
            "query": r.get("query", ""),
            "value": r.get("extracted_value", 0) # This is the breakout/percentage
        })
    return result

def _get_regional_interest(keyword, geo='IN', date='today 3-m'):
    """Fetch regional interest."""
    data = _fetch_serp({"q": keyword, "geo": geo, "date": date, "data_type": "GEO_MAP"})
    if not data:
        return []
    
    # SerpApi structure: interest_by_region -> [ { name: "...", value: "...", extracted_value: 100 } ]
    reg = data.get("interest_by_region", [])
    result = []
    for r in reg:
        name = r.get("name", "")
        val = r.get("extracted_value", 0)
        if val:
            result.append({"region": name, "value": int(val)})
    return sorted(result, key=lambda x: -x["value"])

from category_utils import get_category

JEWELLERY_WHITELIST = [
    "gold", "silver", "diamond", "platinum", "ring", "rings", "necklace",
    "earring", "earrings", "jhumka", "chain", "chains", "bangle", "bangles",
    "bracelet", "pendant", "locket", "mangalsutra", "anklet", "payal",
    "nose pin", "nosepin", "nath", "haar", "choker", "kada", "jewel",
    "jewellery", "jewelry", "ornament", "coin", "biscuit", "solitaire",
    "polki", "kundan", "ruby", "emerald", "sapphire", "pearl", "stud",
    "tops", "bali", "hoop", "tanishq", "malabar", "kalyan", "caratlane",
    "bluestone", "orra", "nakshatra", "zoya", "temple jewellery",
    "antique", "bridal", "wedding jewellery", "imitation", "artificial"
]

def run_layer4_trends(top_terms, top_categories, zero_a2c_terms, zero_conv_terms):
    global _ERRORS
    _ERRORS = []
    
    res = {}
    
    # ── 4.1 Internal vs GT Alignment ──────────────────────────────────────────
    alignment_rows = []
    for i, t in enumerate(top_terms[:15]): # Reduced top count for SerpApi credits efficiency
        term = t.get('term_norm', '')
        gt = _get_iot_score(term)
        rank = i + 1
        srch = int(t.get('searches', 0))
        
        if gt is None: aln = 'No GT data (SerpApi error)'
        elif gt > 40 and rank <= 10: aln = 'Healthy — capturing national demand'
        elif gt > 40 and rank > 10: aln = 'SEO / Catalog Gap — national demand not fully captured'
        elif gt <= 10 and rank <= 10: aln = 'Platform-specific brand intent — protect it'
        else: aln = 'Niche or declining demand'
        
        alignment_rows.append({
            'term_norm': term, 'internal_rank': rank, 'searches': srch,
            'gt_score': gt, 'alignment': aln, 'category': t.get('category', ''),
        })
    
    res['4.1'] = {
        'rows': alignment_rows,
        'insight': f"Processed {len(alignment_rows)} terms via SerpApi. Check alignment of national vs internal intent."
    }

    # ── 4.2 Rising Queries (per top category) ───────────────────────────
    internal_map = {t['term_norm'].lower(): t for t in top_terms if t.get('term_norm')}
    zero_a2c_set = {t['term_norm'].lower() for t in zero_a2c_terms if t.get('term_norm')}
    
    all_rising_cat = []
    top_5_cats = [c for c in top_categories[:3] if c] # Reduced to 3 cats for efficiency
    for cat in top_5_cats:
        rising_list = _get_rising_queries(cat)
        for r in rising_list:
            query = r.get('query', '').lower()
            match = internal_map.get(query)
            in_int = bool(match)
            is_z = query in zero_a2c_set
            all_rising_cat.append({
                'query': query, 'gt_value': int(r.get('value', 0)), 'category': cat,
                'in_internal_data': in_int, 'is_zero_a2c': is_z,
                'internal_searches': int(match.get('searches', 0)) if match else 0,
                'internal_a2c':      int(match.get('a2c_count', 0)) if match else 0,
                'status': 'Zero A2C' if is_z else ('In catalog' if in_int else 'Missing')
            })
            
    rising_zero = [r for r in all_rising_cat if r['is_zero_a2c']]
    res['4.2'] = {
        'rows': rising_zero, 'count': len(rising_zero),
        'insight': f"Found {len(rising_zero)} rising terms with zero A2C."
    }

    # ── 4.3 GT Breakout Terms (Broad Seeds + Whitelist + Exclusion) ───────────
    # Step 1: Broad fetching from 5 seeds
    seeds = ["jewellery", "gold jewellery", "diamond jewellery", "silver jewellery", "bridal jewellery"]
    combined_rising = []
    seen_queries = set()
    
    for seed in seeds:
        queries = _get_rising_queries(seed)
        for q in queries:
            query_text = q.get('query', '').lower().strip()
            if query_text and query_text not in seen_queries:
                seen_queries.add(query_text)
                combined_rising.append(q)
    
    # Step 2: Whitelist Filter
    def is_relevant(q_text):
        return any(w in q_text for w in JEWELLERY_WHITELIST)
        
    relevant_terms = [q for q in combined_rising if is_relevant(q.get('query', '').lower())]
    
    # Step 3: Internal Exclusion (only show truly MISSING terms)
    # We use internal_map which has all terms from df_curr uploaded by user
    missing_breakouts = []
    for q in relevant_terms:
        q_text = q.get('query', '').lower().strip()
        if q_text not in internal_map:
            # Step 4: Auto-categorize
            cat = get_category(q_text)
            missing_breakouts.append({
                'query': q_text,
                'gt_value': int(q.get('value', 0)),
                'category': cat,
                'in_internal_data': False,
                'status': 'Missing from data'
            })
            
    # Step 5: Group and finalize
    # Get unique cats from current results to build grouped structure
    res_cats = sorted(list(set(r['category'] for r in missing_breakouts)))
    res['4.3'] = {
        'rows': missing_breakouts,
        'by_category': {c: [r for r in missing_breakouts if r['category'] == c] for c in res_cats},
        'count': len(missing_breakouts),
        'insight': f"Identified {len(missing_breakouts)} jewellery-relevant breakout terms currently missing from your search data."
    }

    # ── 4.4 Seasonal Trend ────────────────────────────────────────────────────
    series_list = []
    for i, t in enumerate(top_terms[:5]): # Top 5 terms for time series
        term = t.get('term_norm', '')
        data = _get_iot_series(term)
        if data:
            series_list.append({
                'term': term, 
                'category': t.get('category', ''), 
                'data': data
            })
    res['4.4'] = {
        'series': series_list,
        'insight': "Google Trends seasonality indices for top performers."
    }

    # ── 4.5 Regional Interest ──────────────────────────────────────────────────
    regional_data = {}
    terms_3 = [t['term_norm'] for t in top_terms[:3] if t.get('term_norm')]
    for t in terms_3:
        reg = _get_regional_interest(t)
        if reg:
            regional_data[t] = reg
            
    res['4.5'] = {
        'by_term': regional_data, 'terms': terms_3,
        'insight': "State-wise demand distribution in India for top terms."
    }

    # ── 4.6 Zero-conv terms GT score ──────────────────────────────────────────
    zc_rows = []
    for t in zero_conv_terms[:10]: # Top 10 zero-conv
        term = t.get('term_norm', '')
        gt = _get_iot_score(term)
        srch = int(t.get('searches', 0))
        if gt is None: gap = 'No data'
        elif gt > 40: gap = '🔴 CRITICAL — Broken Funnel'
        elif gt > 15: gap = '🟡 Moderate Gap'
        else: gap = '🔵 Platform-specific'
        
        zc_rows.append({
            'term_norm': term, 'searches': srch, 'gt_score': gt,
            'gap_type': gap, 'category': t.get('category', ''),
        })
    
    critical = sum(1 for r in zc_rows if 'CRITICAL' in r['gap_type'])
    res['4.6'] = {
        'rows': zc_rows, 'critical_count': critical,
        'insight': f"Identified {critical} high-intent terms with funnel breakage."
    }

    # ── 4.7 Trending Related Queries (Category level) ────────────────────────
    by_cat = {}
    for cat in top_5_cats:
        rising = _get_rising_queries(cat)
        enriched = []
        for r in rising:
            q = r.get('query', '').lower()
            m = internal_map.get(q)
            enriched.append({
                'query': q, 'gt_value': int(r.get('value', 0)),
                'in_internal': bool(m),
                'internal_searches': int(m.get('searches', 0)) if m else 0,
                'internal_a2c':      int(m.get('a2c_count', 0)) if m else 0,
            })
        by_cat[cat] = sorted(enriched, key=lambda x: -x['gt_value'])
        
    res['4.7'] = {
        'by_category': by_cat,
        'insight': "Market-wide rising queries forecast for your top categories."
    }

    if _ERRORS:
        res['_errors'] = _ERRORS
    
    # Sentinel for total failure
    if not any(res.get(k, {}).get('rows') or res.get(k, {}).get('series') or res.get(k, {}).get('by_term') for k in res):
        res['_no_data'] = "SerpApi returned no results for any query. Check API key or query volume."

    return res
