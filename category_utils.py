import re

SPECIFICITY_MARKERS = [
    # Price intent
    'under', 'below', 'within', 'budget', 'cheap', 'affordable',
    'price', 'cost',
    # Occasion
    'wedding', 'bridal', 'engagement', 'anniversary', 'gifting',
    'gift', 'birthday', 'festival', 'diwali', 'dhanteras',
    'navratri', 'puja', 'rakhi', 'eid', 'christmas', 'karwachauth',
    # Demographic
    'men', 'women', 'kids', 'baby', 'gents', 'ladies', 'boys',
    'girls', 'newborn', 'husband', 'wife', 'mother', 'daughter',
    # Style / material specificity
    'oxidised', 'antique', 'polki', 'kundan', 'solitaire', 'temple',
    'lightweight', 'daily', 'casual', 'office', 'traditional',
    'modern', 'designer', 'handmade', 'enamel', 'meenakari',
    'filigree', 'jadau', 'lakshmi', 'peacock',
    # Format
    'set', 'pair', 'combo', 'collection',
    # Collection / brand-specific
    'nakshatra', 'zoya', 'mia', 'caratlane',
]

OCCASION_CLUSTERS = {
    'Wedding':      [
        'wedding', 'bride', 'bridal', 'shaadi', 'reception',
        'sangeet', 'haldi', 'mehendi', 'trousseau', 'kanyadaan',
        'baraat', 'barat', 'vivah',
    ],
    'Engagement':   [
        'engagement', 'propose', 'proposal',
        # NOTE: 'solitaire' intentionally excluded — it is a cut
        # style searched across all occasions, not engagement-specific.
    ],
    'Anniversary':  ['anniversary', 'couple'],
    'Birthday':     ['birthday', 'bday'],
    'Festival':     [
        'festival', 'diwali', 'dhanteras', 'navratri', 'puja',
        'rakhi', 'eid', 'christmas', 'karwachauth', 'teej',
        'ugadi', 'onam', 'durga', 'ganesh chaturthi', 'baisakhi',
        'lohri', 'gudi padwa',
    ],
    'Gift':         ['gift', 'gifting', 'surprise', 'present'],
    'Baby / Kids':  [
        'baby', 'kids', 'child', 'children', 'newborn',
        'toddler', 'infant',
    ],
}

USE_CASE_CLUSTERS = {
    'Daily Wear': [
        'daily', 'everyday', 'daily use', 'office', 'casual',
        'lightweight', 'simple', 'regular', 'workwear',
        'work wear', 'everyday wear', 'daily wear', 'college',
        'minimal',
    ],
    'Price Conscious': [
        'under', 'below', 'within', 'budget', 'affordable',
        'cheap', 'low price', 'less price', 'low cost',
    ],
    'Religious / Spiritual': [
        'lakshmi', 'ganesh', 'temple', 'deity', 'pooja',
        'sacred', 'religious', 'spiritual', 'mandir', 'god',
        'goddess', 'devotional',
    ],
    "Men's": [
        'men', 'gents', 'male', ' him', 'boys', 'husband',
        'boyfriend', 'brother', "men's", 'masculine', 'groom',
    ],
    'Style / Trend': [
        'oxidised', 'boho', 'bohemian', 'statement', 'layered',
        'stack', 'trendy', 'aesthetic', 'contemporary', 'fusion',
        'antique', 'vintage', 'modern', 'designer', 'unique',
    ],
    'Material / Purity': [
        '22kt', '22k', '18kt', '18k', 'hallmark', 'bis', '916',
        'certified', 'purity', 'karat', 'karats', 'stamped',
    ],
}

def get_category(term):
    """
    Standard categorization logic for jewellery terms.
    Used across the app to group search terms and trends.
    """
    term = str(term).lower()
    
    # Precise matches first
    if any(k in term for k in ['coin', 'biscuit', 'bar', 'bullion']): return 'Coins & Bullion'
    if any(k in term for k in ['nose pin', 'nose ring', 'nosepin', 'nath']): return 'Nose Jewelry'
    
    # Earrings check (including spaced variants to prevent them matching the Rings regex check)
    if any(k in term for k in ['earring', 'earrings', 'earing', 'earings', 'ear ring', 'ear rings', 'jhumka', 'jhumkas', 'studs', 'tops', 'bali', 'hoop']): return 'Earrings'

    # Use regex for rings to avoid matching "earring"
    if re.search(r'\b(ring|rings)\b', term) or any(k in term for k in ['solitaire', 'band ring']): return 'Rings'
    
    if any(k in term for k in ['chain', 'chains']): return 'Chains'
    if any(k in term for k in ['necklace', 'necklaces', 'haar', 'haram', 'rani haar', 'choker']): return 'Necklaces'
    if any(k in term for k in ['mangalsutra', 'mangal']): return 'Mangalsutra'
    if any(k in term for k in ['bracelet', 'bracelets', 'bangle', 'bangles', 'kada', 'kangan']): return 'Bracelets & Bangles'
    if any(k in term for k in ['pendant', 'locket', 'pendent']): return 'Pendants'
    if any(k in term for k in ['anklet', 'payal']): return 'Anklets'
    
    # General material/type matches
    if 'diamond' in term: return 'Diamond'
    if 'gold' in term: return 'Gold Generic'
    if 'silver' in term: return 'Silver Generic'
    
    # Default category renamed as per requirement
    return 'General Jewellery'
