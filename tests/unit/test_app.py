def test_home_page_return_200(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "MONOENROLL".encode("utf-8") in response.data