from pathlib import Path
b=Path('cpp_core/build/Release/game_core.dll').read_bytes()
for name in [b'create_engine', b'guess_letter', b'guess_word', b'get_state', b'get_last_error']:
    idx=b.find(name)
    print(name.decode(), idx)
    if idx!=-1:
        s=max(0,idx-30); e=idx+len(name)+30
        print(b[s:e])
