# AI Responder


Diese Applikation dient zur Beantwortung von Fragen mit Hilfe von Kontext, der aus verschiedenen Quellen stammt.

- Aufbau der Applikation

Wo ist was:
Chat: Konfiguration von Chatbots, Prompts, Model, ..

Context: Verwaltung von Collections mit Dokumenten, Anbindung von qdrant als Vector store, Suchfunktion

Crawler: Websiten rekursiv scrapen und Context aktualisieren.

## How to run

docker compose up

## How does it work

Websiten werden gescraped, über requests oder selenium, je nach Konfiguration.

Inhalte werden in Datenbank gespeichert, beim Indexieren werden Embeddings generiert und in qdrant gespeichert.
