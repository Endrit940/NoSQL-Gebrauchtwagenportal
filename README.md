# NoSQL-Gebrauchtwagenportal

## Anleitung zum Starten der Anwendung

**1. Projekt herunterladen**

Auf GitHub auf **Code → Download ZIP** klicken und die ZIP-Datei entpacken.

**2. Voraussetzungen**

Folgende Programme müssen installiert sein:
- Python
- Docker Desktop

**3. Python-Bibliotheken installieren**

Im Terminal im Projektordner folgenden Befehl ausführen:

`pip install -r requirements.txt`

**4. MongoDB starten**

Docker Desktop öffnen und folgenden Befehl ausführen:

`docker run -d --name nosql_mongo -p 27017:27017 mongo`

Falls der Container bereits vorhanden, aber gestoppt ist:

`docker start nosql_mongo`

**5. Datensatz importieren**

Im Projektordner folgende Befehle nacheinander ausführen:

`docker cp data.csv nosql_mongo:/data.csv`

`docker exec nosql_mongo mongoimport --db nosql --collection autos --type csv --headerline --file /data.csv`

**6. Anwendung starten**

Im Terminal folgenden Befehl ausführen:

`streamlit run app.py`

Anschließend im Browser öffnen:

http://localhost:8501

**7. Performance-Test (optional)**

Für den Vergleich zwischen COLLSCAN und IXSCAN zunächst den Index anlegen:

`docker exec nosql_mongo mongosh nosql --eval "db.autos.createIndex({brand: 1})"`

Anschließend den Performance-Test ausführen:

`python test_scan.py`

**Hinweis:** Docker Desktop und der MongoDB-Container müssen während der Nutzung der Anwendung laufen. Der Datensatz muss nur einmal importiert werden.