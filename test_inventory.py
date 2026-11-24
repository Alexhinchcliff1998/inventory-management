from fastapi.testclient import TestClient
from inventory import create_app

def test_inventory_lifecycle(tmp_path):
    c=TestClient(create_app(tmp_path/'test.db'))
    item={'sku':'BOX-01','name':'Shipping box','reorder_point':5}
    assert c.post('/api/items',json=item).status_code==201
    assert c.post('/api/items',json=item).status_code==409
    assert c.post('/api/items/BOX-01/movements',json={'quantity':10,'reason':'receipt'}).status_code==201
    assert c.post('/api/items/BOX-01/movements',json={'quantity':-11,'reason':'issue'}).status_code==409
    assert c.post('/api/items/BOX-01/movements',json={'quantity':-6,'reason':'issue'}).status_code==201
    row=c.get('/api/items').json()[0]
    assert row['on_hand']==4 and row['needs_reorder']==1
    assert len(c.get('/api/movements').json())==2

def test_bad_requests(tmp_path):
    c=TestClient(create_app(tmp_path/'test.db'))
    assert c.post('/api/items',json={'sku':'!', 'name':'x','reorder_point':-1}).status_code==422
    assert c.post('/api/items/missing/movements',json={'quantity':1,'reason':'receipt'}).status_code==404
