from app.rag.index import store
store.build()
print(f"Indexed {len(store.records)} chunks")
