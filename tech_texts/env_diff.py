import os
from pathlib import Path

EXAMPLE = Path("../env.example")
LOCAL = Path("../env.local")

def parse_env(path):
    env = {}
    if not path.exists():
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def main():
    example_env = parse_env(EXAMPLE.resolve())
    local_env = parse_env(LOCAL.resolve())
    all_keys = set(example_env) | set(local_env)
    print("=== ENV DIFF (env.example vs env.local) ===\n")
    for key in sorted(all_keys):
        ex = example_env.get(key)
        lo = local_env.get(key)
        if ex == lo:
            continue
        if ex is None:
            print(f"[ONLY IN LOCAL]   {key} = {lo}")
        elif lo is None:
            print(f"[ONLY IN EXAMPLE] {key} = {ex}")
        else:
            print(f"[DIFF]            {key}: example='{ex}' | local='{lo}'")
    print("\n=== END ===")

if __name__ == "__main__":
    main() 