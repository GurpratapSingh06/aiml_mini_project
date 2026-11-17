import pickle

with open('data/indexes/chunk_lookup.pkl', 'rb') as f:
    lookup = pickle.load(f)

print('Total chunks:', len(lookup))
for i, (k, v) in enumerate(list(lookup.items())[:10]):
    print(f"--- Chunk {i} ---")
    print("ID:", k)
    print("URL:", v.get("source_url"))
    print("Title:", v.get("source_title"))
    print("Academic Year:", v.get("academic_year"))
    text = v.get("text", "")
    print("Text snippet:", text[:150].replace('\n', ' '))
