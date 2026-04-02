import os
from boros.kernel import BorosKernel

def test_tool_use():
    k = BorosKernel()
    print("Testing terminal command...")
    res = k.registry["tool_terminal"]({"command": "echo Hello_Boros"}, k)
    assert res["status"] == "ok"
    assert "Hello_Boros" in res["stdout"]
    print("Terminal test passed.")
    
    print("Testing file diff editor...")
    with open("temp.txt", "w") as f: f.write("AAA BBB CCC")
    
    res = k.registry["tool_file_edit_diff"]({
        "target_file": "temp.txt",
        "replacement_chunks": [{"target_content": "BBB", "replacement_content": "DDD"}]
    }, k)
    
    assert res["status"] == "ok"
    with open("temp.txt", "r") as f: content = f.read()
    assert content == "AAA DDD CCC"
    print("Diff Patch test passed.")
    os.remove("temp.txt")

if __name__ == "__main__":
    test_tool_use()
