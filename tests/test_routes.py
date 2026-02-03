from app.services.inference_service import InferenceError


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_classify_success_json(monkeypatch, client):
    expected = {'meta-data': {'sample_id': 'S1'}, 'results': []}

    def fake_run_inference(version, payload, features_file, config):
        assert version == '1'
        assert payload == {'meta-data': {'dmp_sample_id': 'S1'}}
        assert features_file is None
        return expected

    monkeypatch.setattr('app.routes.run_inference', fake_run_inference)

    response = client.post('/classify/1', json={'meta-data': {'dmp_sample_id': 'S1'}})
    assert response.status_code == 200
    assert response.get_json() == expected


def test_classify_validation_error(monkeypatch, client):
    def fake_run_inference(version, payload, features_file, config):
        raise InferenceError('no input provided', status_code=400)

    monkeypatch.setattr('app.routes.run_inference', fake_run_inference)

    response = client.post('/classify/1')
    assert response.status_code == 400
    assert response.get_json() == {'error': 'no input provided'}
