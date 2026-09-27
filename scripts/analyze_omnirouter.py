import json
from collections import Counter

def main():
    with open('workspace/omnirouter_models.json', 'r', encoding='utf-8') as f:
        models = json.load(f)

    print(f"Total models: {len(models)}")

    # Group by provider prefix or family
    prefixes = Counter()
    for m in models:
        if '/' in m:
            prefixes[m.split('/')[0]] += 1
        else:
            prefixes['(no-slash)'] += 1

    print("\nTop prefixes / namespaces:")
    for p, c in prefixes.most_common(25):
        print(f"  {p}: {c}")

    keywords = ['gemini', 'claude', 'gpt-4', 'o1', 'o3', 'deepseek', 'qwen', 'llama-3', 'mistral', 'sonnet', 'opus']
    print("\nKey model categories:")
    for kw in keywords:
        matched = [m for m in models if kw in m.lower()]
        print(f"\n--- Matches for '{kw}' (showing up to 10 of {len(matched)}) ---")
        for m in matched[:10]:
            print(f"  {m}")

if __name__ == '__main__':
    main()
