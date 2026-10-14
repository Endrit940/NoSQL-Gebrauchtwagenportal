from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["nosql"]


marke = "volkswagen"  
filter_ = {"brand": marke}

for name, hint in [("COLLSCAN", {"$natural": 1}), ("IXSCAN  ", "brand_1")]:
    for lauf in range(1, 4):
        exp = db.command(
            "explain",
            {"find": "autos", "filter": filter_, "hint": hint},
            verbosity="executionStats",
        )
        s = exp["executionStats"]
        print(f"{name} Lauf {lauf}: {s['executionTimeMillis']:>4} ms | "
              f"Docs geprüft: {s['totalDocsExamined']:>7} | "
              f"Keys geprüft: {s['totalKeysExamined']:>7} | Treffer: {s['nReturned']}")