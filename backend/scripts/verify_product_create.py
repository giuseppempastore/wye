import requests

payload = {
    'barcode': '8003170082656',
    'brand_name': 'Test Brand',
    'product_name': 'Test Product',
    'category': 'food',
    'product_type': 'snack',
    'ingredients': 'water, sugar',
    'nutrition': {
        'energy_kcal': 100,
        'protein_g': 5,
        'carbs_g': 20,
        'fat_g': 2,
    },
    'source': 'debug'
}

r = requests.post('http://127.0.0.1:8000/products', json=payload, timeout=30)
print('STATUS', r.status_code)
print(r.text)
