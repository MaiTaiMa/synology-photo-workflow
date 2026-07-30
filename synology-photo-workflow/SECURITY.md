# Security

## Sicherheitsmodell

Der Workflow verarbeitet private Fotos nur unter `paths.basedir`. Alle Pfade werden normalisiert und gegen diese Grenze geprüft; Symlinks und ZIP-Traversal werden abgewiesen. Der Standardmodus ist `assisted_review`, automatische Referenzaktivierung ist verboten.

## Betrieb

Nutze einen dedizierten DSM-Benutzer mit Minimalrechten und einen persistenten Mount. `config/config.yaml`, Bilder, Modelle, Caches, Logs und Laufzeitdaten gehören nicht in Git. Vor Updates: Archive und `WORKFLOW_DATA` sichern, `validate_config` sowie Tests ausführen.

## Meldungen

Keine privaten Bilder, Embeddings, NAS-Pfade oder Geheimnisse in Tickets veröffentlichen. Sicherheitsprobleme zunächst vertraulich an den Betreiber melden.
