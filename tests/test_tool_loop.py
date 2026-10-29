import pytest
from backend.tool_loop import tool_session
from backend.provider import ProviderError

def call(i):
    return {"id":str(i),"function":{"name":"quote","arguments":"{}"}}

def test_oversized_batch_executes_nothing_and_records_correction():
    class Model:
        def complete(self,messages,tools):
            if len(messages)==1:return {"role":"assistant","tool_calls":[call(i) for i in range(5)]}
            assert not any(m["role"]=="tool" for m in messages)
            assert "Entire batch rejected" in messages[-1]["content"]
            return {"role":"assistant","tool_calls":[call(6)]}
    executed=[];traces=[]
    def handler(name,args):
        executed.append(name);return {"decision":"decline"},True
    tool_session(Model(),[],handler,lambda *args:traces.append(args),"test")
    assert executed==["quote"]
    assert [t[2] for t in traces]==["rejected"]*5+["accepted"]

def test_duplicate_call_ids_fail_before_handlers():
    class Model:
        def complete(self,*args):return {"role":"assistant","tool_calls":[call(1),call(1)]}
    def handler(*args):raise AssertionError("must not execute")
    with pytest.raises(ProviderError,match="duplicate"):
        tool_session(Model(),[],handler,lambda *args:None,"test")

@pytest.mark.parametrize("arguments", ["{invalid", "", "[]", "null"])
def test_invalid_json_is_recorded_but_never_resent_as_function_history(arguments):
    class Model:
        def complete(self,messages,tools):
            if len(messages)==1:
                invalid=call(1);invalid["function"]["arguments"]=arguments
                return {"role":"assistant","tool_calls":[invalid]}
            assert all("tool_calls" not in m for m in messages)
            assert "valid JSON object" in messages[-1]["content"]
            return {"role":"assistant","tool_calls":[call(2)]}
    executed=[];traces=[]
    def handler(name,args):executed.append(name);return {},True
    tool_session(Model(),[],handler,lambda *args:traces.append(args),"test")
    assert executed==["quote"]
    assert [t[2] for t in traces]==["rejected","accepted"]

def test_two_conflicting_decisions_cannot_execute_the_first():
    class Model:
        def __init__(self):self.turns=0
        def complete(self,*args):
            self.turns+=1
            return {"role":"assistant","tool_calls":[call(1),call(2)]}
    def handler(*args):raise AssertionError("conflicting batch must never execute")
    traces=[]
    with pytest.raises(ProviderError,match="turn limit"):
        tool_session(Model(),[],handler,lambda *args:traces.append(args),"test")
    assert len(traces)==12 and all(t[2]=="rejected" for t in traces)
