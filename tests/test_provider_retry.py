import httpx,json

def test_provider_retries_only_rejected_transient_requests(monkeypatch):
    from backend.provider import NebiusModel,ProviderError
    import pytest
    monkeypatch.setenv('NEBIUS_API_KEY','not-a-real-provider-key');monkeypatch.setenv('NEBIUS_MODEL','test-Nemotron')
    monkeypatch.setattr('backend.provider.time.sleep',lambda seconds:None)
    original=httpx.Client;statuses=[529,503,200];seen=[]
    def handle(request):
        seen.append(json.loads(request.content));status=statuses.pop(0)
        return httpx.Response(status,headers={'Retry-After':'0'},json={'choices':[{'message':{'tool_calls':[{'id':'a','function':{'name':'inspect','arguments':'{}'}}]}}]})
    monkeypatch.setattr('backend.provider.httpx.Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    assert NebiusModel().complete([],[])['tool_calls'];assert len(seen)==3
    assert all(r['parallel_tool_calls'] is False for r in seen)
    statuses[:]=[401];seen.clear()
    with pytest.raises(ProviderError,match='401'):NebiusModel().complete([],[])
    assert len(seen)==1
    statuses[:]=[529,529,529];seen.clear()
    with pytest.raises(ProviderError,match='529'):NebiusModel().complete([],[])
    assert len(seen)==3
