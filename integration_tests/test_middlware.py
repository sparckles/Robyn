import requests



BASE_URL = "http://127.0.0.1:5000"



def test_post_with_middleware(session):
    
    res = requests.post(f"{BASE_URL}/post_with_body", data = {
        "hello": "world"
    })


    
    assert res.text=="hello=world"
    assert (res.status_code == 200)
    



