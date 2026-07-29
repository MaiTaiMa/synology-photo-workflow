<!--
photo-workflow
Datei: Synology-Photo-Workflow_Spezifikation_v7-7.md
Mitentwickler: MaiTai
Erstellt: 2026-07-29
Projektversion: 7.7
Funktion: Alleinige normative Spezifikation fuer den sicheren, wiederaufnehmbaren
          Synology-Photo-Workflow.
-->

# Synology Photo Workflow – Spezifikation v7.7

**Status:** Alleinige normative Bezugsquelle fuer Entwicklung, Betrieb, Test und Aenderungen.
Diese Fassung loest alle frueheren Versionen dieser Spezifikation vollstaendig ab; abweichende
aeltere Fassungen oder Teildokumente sind nicht mehr gueltig.

## 0. Lesart und Vorrang

Die Schluesselwoerter **MUSS**, **DARF NICHT**, **SOLL** und **KANN** sind normativ.
Bei Widerspruch gilt in dieser Reihenfolge: (1) Datenintegritaet, Schutz von Originalen,
Datenschutz und Sicherheitsgrenzen; (2) ausdrueckliche Verbote; (3) Haupttext; (4)
normative Anhaenge; (5) nichtnormative Referenzwerte.

Ein Entwickler darf interne Algorithmen austauschen, wenn alle externen Vertraege,
Artefaktformate, Sicherheitsgrenzen und Abnahmekriterien erhalten bleiben. Ein Anhang
mit dem Status **normativ** ist Teil dieser Spezifikation; ein Anhang mit dem Status
**Referenz** gibt sichere Standardwerte vor, sofern die Konfiguration keinen dokumentierten
Ersatz setzt.

## 1. Ziel und Schutzgrenzen

Der Workflow verarbeitet Foto-Batches auf einem Synology-NAS in zwei Phasen: Phase 1
analysiert, bewertet und bereitet die menschliche Pruefung vor; Phase 2 archiviert und
bereinigt ARWs erst nach einer nachweislich sicheren Endentscheidung. Original-JPGs und
ARWs duerfen weder still ueberschrieben noch geloescht werden.

Bekannte Gesichtserkennung verarbeitet nur bewusst gepflegte bekannte Personen.
Unbekannte Gesichter duerfen nicht gespeichert, geclustert, indexiert, getaggt, als
Kandidat protokolliert oder als Referenz aktiviert werden. Ein Gesichtstreffer darf
technische Mindestqualitaet, Manual Keep oder Schutzregeln niemals ueberstimmen.

## 2. Ordner, Namen und Datenklassen

Kanonische Arbeitsordner sind `TEMP_SD`, `TEMP_IMAGES`, `TEMP_DONE`, `TEMP_ERROR`,
`WORKFLOW_DATA/{faces,models,runtime,samples}` und `MANUAL_KEEP/{inbox,used}`.
Ein Batch enthaelt verbindlich die Unterordner `ARW`, `SAVE`, `Review`, `Rejected`.
Nur JPGs im Batch-Hauptordner gelten als aktiv. Ein aus `Review` oder `Rejected` in den
Hauptordner zurueckgelegtes JPG ist wieder aktiv und schuetzt sein passendes ARW.

| Klasse | Inhalt | Schutzregel |
|---|---|---|
| Originale | Kamera-JPGs und ARWs | Nur im geregelten Phasenablauf veraenderbar |
| Abgeleitete Medien | Crops, ZIPs, Vorschauen, Kopien | Nur mit Herkunft, Hash und dokumentierter Aktion |
| Steuerdaten | Manifeste, Zustaende, Logs, Indizes, Caches | Schema-validiert, atomar, rekonstruierbar |

Abweichende Schreibweisen (z. B. `TEMPIMAGES`, `TEMPDONE`, `TEMPERROR`, `WORKFLOWDATA`, `faces/kind-1`, `new_refs`, `not_used`, historisches `culling_scores.csv`) duerfen ausschliesslich lesend fuer die Migration akzeptiert werden. Sie duerfen weder neu erzeugt noch in Summaries, Manifesten, Dokumentation, Beispielkonfiguration oder Scheduler-Befehlen ausgegeben werden. Neue Artefakte verwenden nur die oben genannten kanonischen Namen.

Eine Migration inventarisiert Quelle und Ziel, prueft Pfad und Fingerprint, schreibt ein Auditprotokoll und erzeugt keine stillen Ueberschreibungen. Ein Batch darf nicht gleichzeitig unter Alias- und kanonischem Pfad aktiv sein.

## 3. Batch-, Phasen- und Transaktionsvertrag

Die unveraenderliche `batch_id` lautet `source-folder-name_fingerprint8` und bleibt beim
Wechsel zwischen allen Arbeitsordnern gleich. Pro Batch gibt es genau eine zentrale
Zustandsdatei `WORKFLOW_DATA/runtime/state/<batch_id>.json`; globale Zustandsdateien
sind unzulaessig. Ihr Mindestvertrag steht in Anhang A.

Phase 1 MUSS in dieser Reihenfolge arbeiten: Stabilitaets-, Namens-, Lock- und
Symlink-Pruefung; Datumsnormalisierung; ARW-Ablage nach `ARW`; validiertes JPG-Archiv;
Feature- und Score-Ermittlung einschliesslich Manual Keep und Serienlogik; eingebettete
Metadaten, CSV und Phase-1-Manifest; sichtbare Ablage in Hauptordner, `Review` oder
`Rejected`; atomare Uebergabe nach `TEMP_IMAGES`.

Fuer manuell freigegebene Batches lautet der Zustandsautomat zwingend:
`phase1_completed -> review_comparison_pending -> review_record_committed ->
calibration_index_committed -> phase2_archiving -> phase2_completed`.
Der manuelle Move nach `TEMP_DONE` ist das alleinige Freigabesignal. Bei einer explizit
zugelassenen automatischen Uebergabe lautet er `phase1_completed -> automatic_handoff ->
phase2_archiving -> phase2_completed`; es entsteht kein Trainingslabel.

Phase 2 MUSS zuerst Phase-1-Manifest und Endentscheidungen validieren, bei manueller
Freigabe den unveraenderlichen Review-Record schreiben und erst danach archivieren.
Ein ARW darf nur geloescht werden, nachdem ein vollstaendiges Archiv erzeugt, geprueft,
auf demselben Dateisystem atomar aktiviert und mit Hash protokolliert wurde. Bei jedem
Fehler bleibt das ARW erhalten; `ARW` darf erst nach vollstaendig dokumentierter
Bereinigung entfernt werden.

## 4. Aktives JPG, Endentscheidung und Manual Keep

Ein ARW ist geschuetzt, wenn ein aktives JPG mit demselben eindeutig normalisierten
Basename existiert. Mehrdeutige Paarungen, mehrere wirksame JPG-Kopien, fehlende
Quellhashes oder widerspruechliche Ordnerzustaende blockieren Phase 2 mit
`review_state_invalid`; es darf keine ARW-Aktion stattfinden.

Die Endentscheidung wird ohne Neuberechnung von Scores ausschliesslich aus dem
vorgefundenen Batch-Zustand abgeleitet: (1) ein valides Manual-Keep-Signal ergibt
`keep`; (2) `Rejected` ergibt `reject`; (3) `Review` ergibt `review`; (4) Hauptordner
ergibt `keep`. Fehlt ein Bild oder ist die Zuordnung nicht eindeutig, ist der ganze
Batch blockiert. Die genaue Datenform steht in Anhang A.

Manual Keep liest `MANUAL_KEEP/inbox` nur fuer den aktuellen Batch. Die Standardmetrik ist
Kosinusaehnlichkeit (`higher_is_better`, Bereich 0 bis 1) mit Schwelle 0,95 und Mindestmarge
0,03 zum zweitbesten Treffer; ein eindeutiger Treffer erzwingt `keep` mit Grund
`manual_keep_match`. Eine andere Metrik ist nur zulaessig, wenn Richtung, Wertebereich,
aequivalente Schwelle und Marge vollstaendig konfiguriert und dokumentiert sind. Der
zugeordnete Kandidat durchlaeuft weiterhin normales Scoring, Serienanalyse und
Metadatenschreiben. Erst nach erfolgreicher Zuordnung wird die Quelldatei nach `used`
verschoben. Mehrdeutige, nicht lesbare oder nicht zuordenbare Dateien bleiben in `inbox`,
werden geloggt und in der Run-Summary gezaehlt. Referenzwerte stehen in Anhang D.

## 5. Scoring, Serien und Metadaten

Alle Score-Komponenten liegen in `[0,1]` oder sind `null` (unbekannt, nicht Nullpunkt).
Fehlende Komponenten fuehren zur proportionalen Renormierung aller verbleibenden aktiven
Gewichte auf 1,0. Eine Information darf nicht doppelt gewichtet werden; insbesondere ist
`eye_score` entweder eine eigene finale Komponente oder kein Bestandteil von `base_score`.

Die Standardkomponenten sind `base_score`, `eye_score`, `personal_score` und
`family_score`. Scoring erzeugt `predicted_decision`; die manuelle Endentscheidung ist
davon getrennt. Serienlogik erzeugt deterministisch Serien-ID, Groesse, Rang und
Bestbild. Das Bestbild darf hoechstens um eine Klasse aufgewertet werden; Abwertungen
anderer Bilder brauchen eine geloggte Distanz zum Bestbild. Standardwerte befinden sich
in Anhang D und sind Referenz, nicht Sicherheitsgrenze.

Metadaten werden im Normalweg eingebettet mit Exiftool geschrieben; der Prozess wird
nur argumentbasiert mit `shell=False` gestartet. Vor dem Schreiben wird die Quelle
inventarisiert, danach werden die verwalteten Felder zurueckgelesen. Eine Abweichung
setzt `failed_metadata` und blockiert den Metadatenabschluss. Sidecars sind nur ein
explizit aktivierter Recovery-Modus. Rohscores gehoeren in CSV und JSON, nicht zwingend
in Bildmetadaten.

Der feste minimale Tag-Satz umfasst: Sternrating aus konfiguriertem Scoreband,
`workflow:ai_cull`, `decision:<keep|review|reject>`, optional `series:best`,
`family:match`, `person:<slug>` ausschliesslich bei bekanntem validem Treffer sowie
`manual_keep:true`. Fehlendes Exiftool blockiert den Kernworkflow nicht, muss aber klar
als `disabled` oder `failed` berichtet werden. Der normative Tag- und CSV-Vertrag steht
in Anhang B.

## 6. Bekannte Gesichter und Face-Backends

Nur Dateien in `WORKFLOW_DATA/faces/<person>/reference`, die in `selection.json` den
Status `active` tragen, speisen das Modell. `newfaces` und `notused` sind niemals
Modellquellen. Dateien mit `origin: manual` oder Status `manual_protected` duerfen ohne
ausdrueckliche separate Freigabe weder verschoben noch geloescht werden.

Vor jedem Lauf wird der Referenzpool mit `selection.json` abgeglichen. Fehlt das
Manifest, ist es ungueltig oder aendert sich sein Fingerprint, MUSS die Auswahl
atomar aktualisiert und der Cache neu aufgebaut werden. Bei aktivierter Face-Funktion
blockieren ein fehlender Pflicht-Rebuild, eine fehlende Abhaengigkeit oder ein unbereites
Backend den betroffenen Batch kontrolliert; es gibt keinen stillen Fallback.

Backends werden ausschliesslich durch eine explizite Registry und Adapter ausgewahlt.
`app.family_recognition` DARF KEINE ML-Bibliothek direkt importieren. Backend, Adapter,
Modellhash, Provider, Vorverarbeitung, Metrik und Auswahlfingerprint sind Teil des
Cache-Fingerprints; unterschiedliche Fingerprints duerfen nie gemischt werden. Die
Schnittstelle, Diagnosepflicht und Metrikregeln stehen in Anhang C.

Ein neuer Face-Crop ist nur fuer genau einen sicheren bekannten Personenmatch zulaessig:
Metrikschwelle und Best-zweitbest-Marge erfuellt, Mindestgroesse/Qualitaet erreicht,
Quelle `keep` oder Manual Keep und kein exaktes bzw. visuell nahes Duplikat. Er wird als
Vorschlag in `newfaces` gespeichert und braucht Herkunft, Hash, Bounding Box,
Qualitaet, Neuheit, Konfidenz und Status in `candidates.json`. Ein Mensch aktiviert ihn
nur durch bewusstes Kopieren nach `reference`.

## 7. Steuerdaten, Kalibrierung und Lernen

Jede Steuerdatei MUSS `schema_version`, `created_at`, `updated_at`, `producer_version`
und eine stabile Bereichskennung enthalten. Vor jeder Nutzung werden Version und
Pflichtfelder validiert. Unbekannte zukuenftige, ungueltige oder unlesbare Dateien
duerfen nicht still ueberschrieben werden: Sie werden mit Grund, Zeit und Hash nach
`WORKFLOW_DATA/runtime/quarantine` kopiert, als blockierend gemeldet und erfordern
sichere Neuerstellung oder menschliche Pruefung.

Schreiben erfolgt immer: Inhalt erzeugen, gegen Schema validieren, temporaer auf
demselben Dateisystem schreiben, erneut lesen und validieren, dann atomar ersetzen.
Die vorherige gueltige Version bleibt bis zur erfolgreichen Aktivierung erhalten.

Vor jeder ARW-Aktion eines manuell freigegebenen Batches MUSS ein unveraenderliches
`review_decision_record.json` entstehen. Es ist die fachliche Wahrheit; globale Indizes
und `calibration_summary.json` sind daraus vollstaendig rekonstruierbar. Der Record
darf keine Bilddateien, Vorschaubilder, Roh-Embeddings oder absolute NAS-Pfade enthalten.
Schema, Kennzahlen und Transaktionsfolge stehen normativ in Anhang A.

Ein Lernmodell ist optional und arbeitet nur im Schattenmodus. Es darf nur bestaetigte
menschliche Entscheidungen und bereits gespeicherte Merkmale nutzen; transparente
Basisgewichte sowie Hard-Safety-Regeln bleiben aktiv. Eine Aktivierung erfordert eine
bewusste Nutzerfreigabe, versionierte Kennzahlen, kompatiblen Datenfingerprint und
einen sofortigen Rollback. Das System schaltet einen Automatikmodus niemals selbst ein.

## 8. Betrieb, Sicherheit und Wiederaufnahme

Ein globaler Lock verhindert parallele produktive Laeufe. Alle produktiven Pfade muessen
unter dem erlaubten Basisverzeichnis liegen; Path Traversal und Symlink-Ausbrueche sind
abzulehnen. Der Dry Run veraendert weder Namen, Dateien, Metadaten, Archive noch Caches.
ZIPs werden vor Nutzung auf Lesbarkeit, Traversal, Groessenlimits und Kompressionsverhaeltnis
geprueft. Stille Ueberschreibungen sind verboten.

Der Synology Task Scheduler startet einen Container mit persistentem NAS-Mount; alle
Zustaende, Logs, Konfigurationen, Caches und Summaries liegen auf dem NAS und nicht im
beschreibbaren Container-Dateisystem. Der Container beendet sich nach einem Lauf
kontrolliert. UID/GID, Mounts, Startbefehl, Restore- und Abbruchtest sind vor
Produktivfreigabe auf dem Ziel-NAS abzunehmen.

Bei Start werden Lock und Zustandsdateien zuerst geprueft; der aelteste pausierte oder
unterbrochene Batch hat Vorrang. Bestaetigte atomare Schritte werden nicht wiederholt.
Unvollstaendige Schritte werden anhand von Quelle, Ziel, Hash, Groesse und Marker sicher
fortgesetzt oder neu ausgefuehrt; bei Widerspruch wird quarantanisiert. Nach Zeitbudget
oder SIGTERM wird kein neuer teurer Schritt begonnen, der sichere aktuelle Schritt wird
abgeschlossen, der Status `paused` atomar geschrieben und kontrolliert beendet.

Die Implementierung SOLL fuer kleine NAS optimiert sein: ARWs werden im MVP nicht dekodiert;
technische Vorschauen haben 256 bis 512 Pixel laengste Kante, Aehnlichkeitsvektoren 32 bis 64
Pixel, Standard-Workerzahl ist 1, Bilder werden unmittelbar geschlossen und es erfolgt keine
Vollbatch-Haltung im RAM. Referenzprofile, Geschmacksmodell und Face-Merkmale werden
persistent gecacht und nur bei Eingabeaenderung neu aufgebaut; Fehler und Timeouts eines
Bildes duerfen den Batch nicht abstuerzen lassen. Diese Werte sind konfigurierbar und duerfen
die Sicherheitsvertraege nicht abschwaechen.

Testebenen sind getrennt zu fuehren: Unit-Tests pruefen reine Fachlogik, Schema, Score und
Zustaende; Integrationstests pruefen CLI, Dateisystem-Stubs, ZIP und Adapterfehler;
Sicherheits-Simulationen pruefen Path Traversal, Symlink, Locks, Quarantaene und
Abbruchpunkte; ein Ziel-NAS-Pilot misst Laufzeit, Peak-RAM, CPU-Auslastung, freie Kapazitaet,
Cache-Rebuildzeit, Fehler-/Pause-Rate und erfolgreiche Wiederaufnahme auf realer Hardware.
Stufe 2 oder 3 der Automatik ist erst zulaessig, wenn der NAS-Pilot diese Werte fuer die
Zielhardware und einen repraesentativen Zeitraum akzeptiert und Anhang E vollstaendig
erfuellt ist.

## 9. Reporting, Konfiguration und Dokumentation

Jeder Lauf erzeugt kurze Scheduler-Ausgabe, strukturierte JSON-Run-Summary, Batch-CSV
`SAVE/culling_scores.csv` und persistente Logs. Die Summary MUSS Run-/Batch-ID,
Konfigurationsfingerprint, angeforderten und wirksamen Automatikmodus, Ergebnisstatus,
Keep/Review/Reject-Zaehler, Cache-/Metadatenstatus, ZIP-Konflikte, Kalibrierungsstatus
und priorisierte `user_actions_required` enthalten. Jede Aktion enthaelt Severity
`info`, `warning` oder `blocking`, Bereich, menschenlesbare Handlung und optionalen
Handbuchanker.

Die Beispielkonfiguration ist vollstaendig kommentiert: Zweck, Typ bzw. Wertebereich,
Standardverhalten, Sicherheits-/Performancewirkung und Status `stable`, `advanced` oder
`experimental`. Unbekannte Schluessel, ungueltige Enum-Werte und widerspruechliche
Kombinationen sind Konfigurationsfehler. Die effektive Konfiguration wird mit
Fingerprint im Run dokumentiert; Geheimnisse und Produktionspfade gelangen nicht in Git.

Jeder fachliche Ordner besitzt eine README mit Zweck, erlaubten/verbotenen Inhalten,
Dateitypen, Abgrenzung, Workflow-Verhalten und Sicherheitsregeln. Pflichtdokumente sind
`README.md`, `docs/MANUAL_DE.md`, `docs/CONFIGURATION.md`, `docs/INSTALLATION.md`,
`docs/BETRIEB.md`, `docs/TESTING.md`, `docs/ARCHITEKTUR.md`, `SECURITY.md` und
`CHANGELOG.md`.

Aktive projektgepflegte Text- und Codedateien ausserhalb `legacy/` tragen einen nativen
Header mit Projektname, relativem Dateinamen, Mitentwickler, ISO-Erstelldatum,
Projektversion und Kurzfunktion. Oeffentliche APIs brauchen zusaetzlich Docstrings.
CI prueft Header, Pflichtfelder, Versionskonsistenz und Konfigurationsschema. Binaer-,
Modell-, Bild-, ZIP-, Lock- und Drittanbieterdateien sind ausgenommen.

Das historische Bash-Skript bleibt unveraendert als dokumentierte Notfall-Rueckfallebene
erhalten. Es ist nicht Teil der aktiven Python-/Docker-Weiterentwicklung und darf nicht
innerhalb eines laufenden, pausierten, fehlgeschlagenen oder unvollstaendigen Python-Batches
verwendet werden. Ein Einsatz ist erst nach dokumentierter Sicherung, Lock-Pruefung und
bewusster manueller Recovery-Entscheidung zulaessig; Python-Teilzustaende werden dabei
niemals durch Bash interpretiert oder fortgeschrieben.

## 10. Automatikstufen

| Stufe | Modus | System darf | Mensch muss |
|---|---|---|---|
| 1 | assisted_review | Phase 1, Reporting, Vorschlaege | Phase-2-Uebergabe und Referenzaktivierung |
| 2 | automatic_phase2 | Phase 2 nach expliziten Gates | Referenzaktivierung |
| 3 | automatic_candidates | Kandidaten priorisieren/verwalten | Referenzaktivierung |
| 4 | reference_activation | Nur spaeterer Erweiterungspunkt | Audit und explizite Freigabe |

Stufe 1 ist Standard. Stufe 2 erfordert gleichzeitig `automation.mode`,
`automatic_phase2_enabled: true`, `workflow.phase_execution: phase1_then_phase2`
sowie dokumentierte NAS-Abnahme und Kalibrierungsbereitschaft. Stufe 3 erfordert
zusaetzlich `automatic_candidates_enabled: true`; sie darf manuelle Referenzen nie
verschieben oder loeschen. Stufe 4 ist experimental, standardmaessig verboten und
braucht eine eigene spaetere Anforderung.

Kritische Fehler – insbesondere ungueltige Steuerdaten, fehlender oder pausierter
Pflicht-Rebuild, unaufloesbarer Dateikonflikt, Integritaets- oder Sicherheitsfehler –
stoppen den Batch. Bei `rollback_on_error: true` fallen nachfolgende Batches auf
`assisted_review` zurueck; bereits erfolgreich atomare Aktionen werden nicht rueckgaengig
gemacht. Volle Pools blockieren Vorschlaege, loeschen aber nichts automatisch.

## 11. Abnahme und Aenderungen

Die Abnahme ist erst erfuellt, wenn alle Faelle in Anhang E automatisiert reproduzierbar
bestehen und der Ziel-NAS-Pilot dokumentiert ist. Unit- oder Containertests ersetzen den
NAS-Piloten nicht. Eine Aenderung an Gewichten, Schwellen, Feature-Logik, Referenzbasis,
Backend, Modell oder Metadatenvertrag MUSS Versions-, Konfigurations- und gegebenenfalls
Cache-/Kalibrierungsfingerprint aendern und Migrationshinweise im CHANGELOG enthalten.

---

# Anhang A – Normative Datenvertraege

## A.1 Gemeinsame Regeln

JSON ist UTF-8; Zeitstempel sind UTC nach ISO-8601 mit `Z`; `schema_version` ist positive
Ganzzahl. Unbekannte Schema-Versionen oder Enum-Werte blockieren. Zusaetzliche Felder
sind nur erlaubt, wenn sie keine bestehende Semantik aendern.

## A.2 Batch-Zustand (MUSS)

`<batch_id>.json` enthaelt mindestens: `schema_version`, `batch_id`, urspruenglicher
Ordnername, relativer aktueller Pfad, vollstaendiger Quellfingerprint, Phase, Status
(`pending`, `running`, `paused`, `completed`, `failed`), Start-/Aktualisierungszeit,
Konfigurationsfingerprint, abgeschlossene Schritte, aktuellen Schritt,
Fortschrittszeiger, Zaehler, Fehler und Pausen-/Abbruchgrund. Uebergaenge sind nur
vorwaerts zulaessig. Ein Status `completed` ist nur mit allen erwarteten Artefakten und
erfolgreichen Integritaetspruefungen gueltig.

## A.3 Auswahl- und Kandidatendaten (MUSS)

`selection.json` enthaelt Pool-Fingerprint, Modell-/Algorithmus-/Metrikkennung,
Personen-Slug und Anzeigename sowie pro Datei relativen Pfad, Herkunft, Status,
Auswahlwert und Auswahlgrund. Zulaessige Status sind `active`, `inactive`,
`pending_review`, `superseded`, `manual_protected`, `archived`. `candidates.json`
enthaelt pro Vorschlag Quellpfad/-hash, Bounding Box, Crop-Rand, Match-/zweiten Wert,
Qualitaet, Neuheit, Konfidenz, Dedupe-Bezug, Zeit und Status.

## A.4 Review-Record (MUSS)

`review_decision_record.json` liegt unter
`WORKFLOW_DATA/runtime/calibration/batches/<batch_id>/`. Es enthaelt `record_id`,
`batch_id`, `handoff_source` (`manual_review` oder `automatic`), Phase-1- und
Review-Zeit, `config_fingerprint`, `model_version`, Integritaetshashes und je Bild:
`image_id` (SHA-256), relativen Phase-1-Pfad, `predicted_decision`, optionale
Wahrscheinlichkeiten, `final_decision`, `correction_type`, `final_score`, normierte
Features, Quelle der Endentscheidung und finalen relativen Pfad. Entscheidungen sind
nur `keep`, `review`, `reject`; Korrekturen nur `confirmed`, `promoted`, `demoted`,
`manual_keep`. Nicht verfuegbare Scores sind `null`.

Transaktion: Phase-1-Manifest validieren; alle Endentscheidungen vollstaendig ermitteln;
Record bauen und validieren; temporaer schreiben, erneut lesen und atomar aktivieren;
ableitbaren Index und Summary aktualisieren; erst dann archivieren. Fehlt die
Phase-1-Grundlage oder passen Fingerprints nicht, blockiert `review_state_invalid`.

## A.5 Kennzahlen und Freigabe (MUSS)

`calibration_summary.json` enthaelt Anzahl Records/Bilder, Fenster, aktiven Fingerprint,
terminale Uebereinstimmung, Gesamtuebereinstimmung, `reject_to_keep_rate`,
`reject_to_review_rate`, `keep_to_reject_rate`, Review-Rate, Trend, Status,
Begruendung, naechste Aktion und Hash der genutzten Record-IDs. Terminale Uebereinstimmung
ist der Anteil bestaetigter direkter Keep-/Reject-Vorhersagen an allen direkten
Keep-/Reject-Vorhersagen; ein Nenner von null wird als nicht auswertbar, nicht als 100 %
berichtet. Unterschiedliche Fingerprints duerfen nicht gemischt werden.

Referenz-Gate fuer `eligible_automatic_phase2`: mindestens drei repraesentative manuell
gepruefte Batches, 300 Bilder im kompatiblen Fenster, mindestens 90 % terminale
Uebereinstimmung, 0 % `reject_to_keep_rate` und keine blockierende technische Stoerung.
Die Empfehlung aktiviert nichts selbst.

---

# Anhang B – Normative Metadaten-, CSV- und Archivvertraege

## B.1 Metadaten

`XMP:Rating` wird mit 0–5 ersetzt. In `XMP-dc:Subject` duerfen nur eigene Praefixe
ersetzt werden; fremde Keywords bleiben erhalten. Zulaessige neue Tags sind
`workflow:ai_cull`, `workflow:model:<id>`, `decision:predicted:<wert>`,
`decision:final:<wert>`, `series:id:<id>`, `series:role:best_member`,
`family:match:<true|false>`, `person:<slug>`, `score_band:final:<0..5>` und
`whatsapp:manual_keep`. Alte Grossschreibungsformen sind nur lesende Migrationsaliase.

## B.2 CSV und Archive

Der kanonische Name ist `SAVE/culling_scores.csv`. Er enthaelt mindestens `image_id`,
`relative_path`, vier Komponentenscores, `final_score`, `star_rating`,
`predicted_decision`, `final_decision`, `decision_reason`, Serienfelder,
`model_version` und `config_fingerprint`. Der historische Name darf nur gelesen werden.

JPG- und ARW-ZIPs werden vor Aktivierung vollstaendig gelesen/geprueft. Der finale
Name wird nie ueberschrieben; bei Kollision folgt `stem_EXTRA<n>.zip`. Quelle, Ziel,
Kollisionsgrund, Archivhash und Aktivierungszeit sind in Log und Summary zu speichern.

---

# Anhang C – Normativer Face-Backend-Vertrag

Die Registry ist explizit und deterministisch. Zulassige Referenz-IDs sind
`opencv_yunet_sface_cpu` (stable, Standard), `onnx_face_cpu` (advanced),
`onnx_face_cuda` (advanced), `face_recognition_dlib_cpu` (experimental) und
`insightface_onnx` (experimental). Optionale Backends liegen in getrennten Images oder
Dependency-Gruppen; CUDA ist nur in einem expliziten GPU-Image mit validierter Laufzeit
zulaessig.

```python
class FaceBackendProtocol:
    name: str
    adapter_version: str
    metric: MatchMetric
    def diagnose(self) -> FaceBackendDiagnosis: ...
    def detect_and_embed(self, image_path: Path) -> list[FaceEmbedding]: ...
    def compare(self, embedding, references) -> FaceMatch: ...
```

`FaceEmbedding` enthaelt Vektor, Backend, Modellfingerprint, Dimension und Bounding Box;
diese Rohdaten duerfen nie in Metadaten, CSV, Kandidatenlisten, Summaries oder Logs.
`FaceMatch` nutzt `matched`, `unmatched`, `ambiguous`, `no_face`, `error` sowie optional
Personen-Slug, Score, Metrik und zweitbesten Score.

Die Metrik hat Name, Richtung und Schwelle. Bei `higher_is_better` gilt Match nur bei
`score >= threshold` und `score - second_best >= margin`; bei `lower_is_better` nur bei
`score <= threshold` und `second_best - score >= margin`. Fehlen eindeutige Werte,
resultiert konservativ `unmatched` oder `ambiguous`. `diagnose_face_backend` veraendert
keine Caches oder Bilder und liefert bei unbereitem Backend einen Nicht-Null-Exit-Code.

---

# Anhang D – Referenzkonfiguration und Werte (nichtnormativ, sichere Defaults)

```yaml
workflow:
  phase_execution: phase1_then_phase2
  batch_limit: 1
  batch_sort: oldest_first
  max_run_hours: 10
  resume_incomplete_batches: true
culling:
  keep_threshold: 0.65
  reject_threshold: 0.35
  auto_keep_min_rating: 2
  final_component_weights: {base_score: 0.55, eye_score: 0.10, personal_score: 0.20, family_score: 0.15}
  base_weights: {sharpness: 0.35, aesthetic: 0.35, exposure: 0.20, reference_score: 0.10}
family_recognition:
  enabled: false
  backend: opencv_yunet_sface_cpu
  match_threshold: null
  min_best_second_margin: null
automation:
  mode: assisted_review
  automatic_phase2_enabled: false
  automatic_candidates_enabled: false
  automatic_reference_activation: false
  rollback_on_error: true
```

Referenzwerte fuer Manual Keep mit Cosine Similarity sind `similarity >= 0.95` und
`best - second_best >= 0.03`. Face-Pool-Richtwerte sind `min_active: 30`,
`target_active: 40`, `max_active: 50`, `max_notused: 100`, hoechstens zehn neue
Vorschlaege je Person und Lauf sowie hoechstens 100 offene Vorschlaege. Bei vollem Pool
werden keine neuen Vorschlaege erzeugt; es findet keine automatische Loeschung statt.

Sternbaender: 0.00–0.19 = 0, 0.20–0.39 = 1, 0.40–0.59 = 2, 0.60–0.74 = 3,
0.75–0.89 = 4, 0.90–1.00 = 5. Standardwerte fuer einen Crop-Wert sind
Gesichtsqualitaet 40 %, Diversitaetsgewinn 35 %, Erkennungssicherheit 15 % und
Bildkontext 10 %. Alle Werte sind vor produktiver Aenderung auf NAS-Testdaten zu pruefen.

---

# Anhang E – Normative Abnahme ACC-01 bis ACC-15

| ID | Szenario | Verbindliches Sollresultat |
|---|---|---|
| ACC-01 | Stabiler Eingang | Phase 1 erzeugt Manifest, JPG-Archiv, CSV und atomare Uebergabe |
| ACC-02 | Wachsender/gesperrter Eingang | Keine Mutation; sichtbarer Blocker |
| ACC-03 | Rejected-JPG zurueck im Hauptordner | Finale Entscheidung keep; ARW bleibt geschuetzt |
| ACC-04 | Metadaten-/Archivpruefung fehlschlaegt | Kein erfolgreicher Abschluss und keine ARW-Loeschung |
| ACC-05 | Absturz vor/nach Archivaktivierung | Idempotente Wiederaufnahme, kein ARW-Verlust |
| ACC-06 | Ungueltige Steuerdatei | Quarantaene, Blockierung, kein Ueberschreiben |
| ACC-07 | Face deaktiviert | Keine Face-Artefakte und keine Personentags |
| ACC-08 | Unzulaessiges Face-Backend | Kontrollierter Fehler, kein Fallback |
| ACC-09 | Backend/Modell/Metrikwechsel | Neuer Fingerprint, keine Cache-Mischung |
| ACC-10 | Richtungsverschiedene Metriken | Schwelle und Margin korrekt angewandt |
| ACC-11 | CUDA ohne GPU | Diagnosefehler, kein CPU-Fallback |
| ACC-12 | Defekter Kalibrierungsindex | Vollstaendiger Rebuild aus Batch-Records |
| ACC-13 | Automatik ohne Readiness | Sicherer Hold, keine riskante Uebergabe |
| ACC-14 | Header/Schema-Check | CI erkennt fehlende, falsche, inkonsistente Angaben |
| ACC-15 | Ziel-NAS-Pilot | Mounts, UID/GID, Scheduler, Restore, Abbruch und Wiederaufnahme bestanden |

# Anhang F – Normativer CLI-, Exit-Code- und Modulvertrag

## F.1 Aufruf und Befehle

Der kanonische Einstiegspunkt lautet:

```sh
python -m app.photoworkflow --config config/config.yaml <command>
```

| Befehl | Wirkung | Seiteneffekte |
|---|---|---|
| `run` | Fuehrt den durch `workflow.phase_execution` erlaubten Ablauf aus | Ja, nach Modus und Gates |
| `phase1` | Fuehrt ausschliesslich Phase 1 aus | Ja |
| `phase2` | Fuehrt ausschliesslich Phase 2 aus | Ja; niemals ohne Freigabe und Validierung |
| `rebuild_family_cache` | Baut den Face-Cache des explizit gewaehlten Backends atomar neu | Ja, nur Cache-Artefakte |
| `rebuild_personal_model` | Baut das persoenliche Modell aus aktiven Samples neu | Ja, nur Modell-/Cache-Artefakte |
| `diagnose_face_backend` | Prueft Backend, Modelle, Hashes, Provider und Metrik | Nein |
| `validate_config` | Prueft Schema, Pfade, Abhaengigkeiten und Widersprueche | Nein |
| `print_effective_config` | Gibt die effektive Konfiguration ohne Secrets aus | Nein |
| `rebuild_calibration_index` | Baut Index und Summary nur aus validen Batch-Records neu | Ja, nur abgeleitete Artefakte |
| `recover_batch <batch_id>` | Setzt einen vorhandenen validen Batch sicher fort | Ja, nur offene, validierte Schritte |
| `reopen_review <batch_id>` | Privilegierter Korrekturbefehl; standardmaessig deaktiviert | Ja, nur mit Audit-Eintrag |

Explizite Phasenbefehle uebersteuern `workflow.phase_execution`, niemals jedoch Lock-,
Pfad-, Integritaets-, Archiv- oder Automatikpruefungen. Bindestrichformen sind ausschliesslich
lesende/deprecated CLI-Aliase; Hilfe, Tests, Dokumentation und neue Automatisierung verwenden
nur die Unterstrichformen. `recover_batch` darf ohne vorhandenes valides Batch-Manifest keine
ARWs loeschen und keine neue Bildbewertung starten.

## F.2 Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Vollstaendig erfolgreich, kein Blocker |
| 2 | Mindestens ein Batch wegen Validierung nicht ausgefuehrt |
| 3 | Wiederherstellbarer Fehler ohne ARW-Loeschung |
| 4 | Mindestens ein Batch in `recovery_required` oder `failed_delete` |
| 5 | Konfigurations- oder Abhaengigkeitsfehler |
| 6 | Unerwartete interne Ausnahme |

Ein Fehler eines Batches darf unabhängige Batches nicht gefaehrden. Er MUSS jedoch im
Gesamtergebnis, in der JSON-Run-Summary und in der Scheduler-Ausgabe erscheinen.

## F.3 Modulgrenzen

| Modul | Exklusive Verantwortung |
|---|---|
| `app.cli` | Argumente, Konfiguration laden, Dispatch, Exit-Codes |
| `app.configuration` | YAML-Schema, Alias-Migration, Validierung, Pfadauflösung, Fingerprint |
| `app.inventory` | Eingangsstaerke, Inventar, Fingerprints, JPG-ARW-Paarbildung |
| `app.phases` | Orchestrierung und Reihenfolge der Phasen |
| `app.culling` | Merkmale, Score-Komposition, Sterne, Serienentscheidung |
| `app.manual_keep` | Inbox-Zuordnung und Verschiebung nach `used` |
| `app.metadata` | Exiftool, Keyword-Merge, Ruecklesepruefung |
| `app.archives` | ZIP-Erstellung, Validierung, Hash, Aktivierung, Kollisionen |
| `app.batch_state` | Zustandsautomat, atomare Updates, Wiederaufnahme |
| `app.calibration` | Records, Indizes, Kennzahlen, Readiness, Schattenmodell |
| `app.face_backend*` | Modellneutrale Typen, Registry, Diagnose und einzelne Adapter |
| `app.family_recognition` | Referenzen, Cache, Match- und Kandidatenfachlogik ohne ML-Import |
| `app.reporting` | Logs, Scheduler-Ausgabe, JSON-Run-Summaries |
| `app.locks` | Lauf-/Batch-Locks und Stale-Lock-Pruefung |

Fachlogik darf nicht in `app.cli` dupliziert werden. Dateisystemmutationen erfolgen nur
ueber die vorgesehenen Fachmodule und kontrollierte Phasenoperationen. Funktionen mit
Seiteneffekt validieren ihre Eingaben und geben ein testbares Ergebnisobjekt zurueck.

---

# Anhang G – Normativer Konfigurations- und Validierungsvertrag

## G.1 Quellen und Geheimnisse

`config/config.example.yaml` ist die vollstaendig kommentierte, versionierte Vorlage.
Lokale Produktionswerte liegen getrennt in `config/config.yaml` und gehoeren nicht in Git.
Auch Debug-Konfigurationen sind als Beispiele zu kennzeichnen und secrets-frei zu halten.
Relative Pfade werden gegen `paths.basedir` aufgeloest und duerfen nach Normalisierung
niemals dieses Basisverzeichnis verlassen.

Jeder Abschnitt besitzt einen Kommentar zu Zweck, Abhaengigkeiten, Betriebswirkung und
sicherer Empfehlung. Jede Variable dokumentiert Zweck, Typ/Wertebereich, Einheit soweit
relevant, Standardverhalten, Sicherheits-/Performancewirkung und Stabilitaetsstatus.
Eine Standardkonfiguration aktiviert nur `stable`-Werte.

## G.2 Kanonische Schluessel

| Bereich | Verbindliche Schluessel |
|---|---|
| `paths` | `basedir`, `temp_sd`, `temp_images`, `temp_done`, `temp_error`, `workflow_data` |
| `workflow` | `phase_execution`, `batch_limit`, `batch_sort`, `skip_incomplete_batches`, `max_run_hours`, `resume_incomplete_batches` |
| `culling` | `enabled`, Schwellwerte, Gewichte, Sternbaender |
| `phase2` | `delete_unneeded_arws_after_verified_archive`, `allow_automatic_handoff` |
| `metadata` | `write_mode`, `verify_after_write`, `create_exiftool_backups`, `sidecar_recovery_enabled` |
| `family_recognition` | `enabled`, `backend`, `execution_profile`, `metric`, `match_threshold`, `min_best_second_margin`, `backends` |
| `automation` | `mode`, `automatic_phase2_enabled`, `automatic_candidates_enabled`, `automatic_reference_activation`, `automatic_sample_activation`, `rollback_on_error` |
| `calibration` | Aktivierung, Records-Pfad, Auswertungsfenster, Mindestmengen, Readiness- und Schattenmodusgrenzen |

`culling.decision_mode` und `similarity_metric` sind nur lesende Migrationsaliase.
Sind Alias und kanonischer Wert zugleich abweichend gesetzt, scheitert die Validierung.
Unbekannte Schluessel sind Fehler, ausserhalb eines explizit dokumentierten `extensions`
Blocks. Nicht ausgewaehlte Backend-Bloecke duerfen unvollstaendig sein, vorhandene Werte
muessen aber syntaktisch gueltig bleiben.

## G.3 Mindestvalidierung

Die Validierung prueft mindestens: erlaubte Enum-Werte; `0 <= reject_threshold <
keep_threshold <= 1`; nichtnegative Gewichte mit Summe 1,0 bei voller Verfuegbarkeit;
lueckenlose, nicht ueberlappende Sternbaender fuer `[0,1]`; `auto_keep_min_rating` im
Bereich 0–5; nur `oldest_first` als Batch-Reihenfolge; Pfade innerhalb `basedir`;
Automatikgates; Limits gegen Zielwerte; Bereinigungsrechte gegen Herkunft; Zeitbudget
gegen Wiederaufnahme; Pflichtfunktionen gegen Abhaengigkeiten und Backend-Profil gegen
Container-Profil.

`match_threshold: null` bedeutet unkalibriert: keine automatische Personen-Zuordnung,
kein Family-Score und keine Personentags. Ein CUDA-Profil verlangt CUDA-Provider,
GPU-Image und bewusste GPU-Containerkonfiguration; ein CPU-Profil darf keine GPU
voraussetzen. Vor Produktivbetrieb muessen `validate_config` und bei aktivierter
Gesichtsfunktion `diagnose_face_backend` erfolgreich sein.

---

# Anhang H – Normativer Archiv-, Datei- und Wiederaufnahmevertrag

## H.1 Formate und Paarbildung

Im MVP sind nur `.jpg`, `.jpeg` und `.arw` unterstuetzt; Erweiterungen werden
ASCII-case-insensitiv verglichen. Die Paarbildung nutzt ausschliesslich den vollstaendigen
Dateinamen ohne letzte Erweiterung. Teilstrings und Aehnlichkeitssuchen sind unzulaessig.
Mehrere ARWs mit gleichem Basename, nicht normalisierbare Unicode-Namen, mehrere aktive
JPGs, unklare Inventare oder nicht dokumentierte Umbenennungen blockieren Phase 2.

Eine bewusst unterstuetzte Umbenennung braucht im Phase-1-Manifest ein `arw_binding` mit
altem Basename, neuem JPG-Pfad, JPG-Hash und urspruenglichem ARW-Fingerprint. Ohne diesen
Nachweis schuetzt ein umbenanntes JPG kein ARW. Symlinks, nicht erlaubte Hardlink-Sonderfaelle
und Pfade ausserhalb `basedir` werden abgewiesen.

## H.2 Archivplan und Aktivierung

Vor der Bereinigung erzeugt Phase 2 einen unveraenderlichen Archivplan. Das temporaere
ARW-Archiv enthaelt fuer jeden Eintrag relativen Pfad, Groesse und SHA-256. Vor Aktivierung
werden ZIP-Lesbarkeit, sichere Memberpfade, erwartete Dateiliste, Groesse und Hash jedes
Eintrags geprueft. Erst dann wird das Archiv atomar aktiviert und `archive_manifest.json`
persistiert.

Existiert ein Zielarchiv mit exakt passendem Plan, Entry-Hashes und Konfigurationsfingerprint,
darf es wiederverwendet werden. Existiert es, ist aber abweichend oder nicht vertrauenswuerdig,
folgt der erste freie Kollisionsname `..._EXTRA<n>.zip`; `zip_target_collision` ist dann in
Log, Summary und Konfliktliste Pflicht. Fremde oder unsichere ZIPs duerfen weder ersetzt noch
entfernt werden.

## H.3 Bereinigung und Recovery

Nach `archive_verified` darf die Wiederaufnahme nur noch vorhandene ARWs loeschen, die exakt
im verifizierten Archivmanifest stehen. Jede Loeschung protokolliert ARW-Fingerprint,
Archivpfad, Archivhash und Zeit. Jede Abweichung erzeugt `recovery_required`; es findet
keine heuristische Bereinigung statt. Ein leerer `ARW`-Ordner wird erst nach vollstaendiger,
dokumentierter Loeschung entfernt.

Der Zustand wird – soweit vom Dateisystem unterstuetzt – per temporärer Datei, `fsync`,
atomarem Rename und anschließendem Directory-`fsync` persistiert. Ein Lock enthält `run_id`,
Eigentuemer, Host/PID und Zeit. Ein abgelaufener Lock darf nur nach dokumentierter
Besitzer-, PID/Host- und Zeitpruefung als stale gelten, niemals blind geloescht werden.

---

# Anhang I – Normativer Sample-, Kapazitaets- und Rebuildvertrag

## I.1 Persoenliche Geschmackssamples

`WORKFLOW_DATA/samples/{reference,newrefs,notused}` verwendet dieselbe Blaupause wie
Face-Referenzen. Nur in `samples/selection.json` als `active` markierte Dateien aus
`reference` sind Modellquelle. `newrefs` sind ausschliesslich Vorschlaege; der Mensch
aktiviert sie durch Kopieren nach `reference`. Manuelle Dateien sind `manual_protected`
und duerfen nicht automatisch verschoben oder geloescht werden.

Aenderungen am aktiven Poolfingerprint erzwingen ein atomar aktiviertes Rebuild des
kleinen lokalen Geschmacksmodells. Ein Vorschlag nach `newrefs` braucht `keep`, die
hoechste konfigurierte Sternklasse, ausreichende technische Qualitaet, Dedupe-Freiheit
und messbaren Diversitaetsgewinn in Stil, Komposition, Motiv, Licht oder Farbstimmung.
Er trainiert nicht vor der manuellen Aktivierung.

Referenzlimits sind `min_active: 50`, `target_active: 75`, `max_active: 100`,
`max_notused: 200`, hoechstens zehn neue Vorschlaege pro Lauf und 100 offene Vorschlaege.

## I.2 Gemeinsame Auswahl- und Verschieberegeln

Die Auswahl ist bei gleichen Eingaben und Konfigurationen deterministisch. Sie priorisiert
Lesbarkeit, Mindestqualitaet, SHA-256-Dedupe, visuellen Dedupe, Fachqualitaet und
Diversitaetsgewinn; Gleichstand entscheidet der relative Dateiname. Verwaltete,
automatisch erzeugte Dateien duerfen nur per Copy-Verify-Delete zwischen `reference`
und `notused` wechseln. Quelle, Ziel, Hash, Groesse, alter/neuer Status, Wert, Grund und
Zeit werden manifestiert. Widersprueche werden quarantanisiert.

| Kapazitaet | Bedingung | Verhalten |
|---|---|---|
| `normal` | unter 80 % | Vorschlaege normal erzeugen |
| `warning` | 80 % bis unter Limit | erzeugen, Warnung protokollieren |
| `full` | Vorschlagslimit erreicht | keine neuen Vorschlaege |
| `blocked` | `notused`-Limit erreicht | keine Verdraengung, keine neuen Vorschlaege |

Die Kapazitaetsampel mit `active_count`, `pending_count`, `inactive_count`, Limit,
Status und `new_candidates_skipped` ist in Manifest, Log und Run-Summary abzulegen.
Volle Pools loeschen nie automatisch. Eine spaetere Bereinigung ist nur fuer automatisch
erzeugte Kopien, nur nach konfigurierter Aufbewahrung, nur mit vorherigem Audit und nur
bei expliziter Aktivierung zulaessig.

## I.3 Rebuild-Transaktion

Ein Rebuild erfolgt im temporaeren Verzeichnis auf demselben NAS-Dateisystem: Manifest
und Quellen pruefen, Merkmale erzeugen, Lesbarkeit/Dimensionen pruefen, Smoke-Test,
Artefakt atomar aktivieren. Bei Fehler bleibt der vorherige valide Cache erhalten; fuer
einen geaenderten Fingerprint darf er jedoch nicht weiterverwendet werden. Ein durch
Zeitlimit oder Signal unterbrochener Rebuild wird `paused` und beim naechsten Lauf
fortgesetzt oder deterministisch neu erstellt.

---

# Anhang J – Normativer Reporting-, Betrieb- und Deploymentvertrag

## J.1 Run-Summary

Die Run-Summary liegt persistent unter `WORKFLOW_DATA/runtime/run_summaries/<run_id>.json`.
Sie enthaelt mindestens Run-ID, Batch-ID, Zeitfenster, Ergebnisstatus, Konfigurations-
fingerprint, angeforderten und wirksamen Automatikmodus, gefundene/verarbeitete/
uebersprungene/fehlerhafte Batches, Keep/Review/Reject-Zahlen, Manual-Keep-Ergebnisse,
Cache- und Metadatenstatus, ZIP-Kollisionen und `user_actions_required`.

`user_actions_required` enthaelt `severity` (`info`, `warning`, `blocking`), `scope`
(Batch, Person oder Sample-Pool), eine kurze Handlung und optionalen Handbuchanker.
Scheduler-stdout zeigt mindestens Warnungen und Blocker. `automation_readiness` berichtet
Status, kompatible Batches/Bilder, terminale Uebereinstimmung, kritische Fehlerraten,
Review-Rate, Trend, Fingerprint, Empfehlung und naechste Aktion; es aendert nie
Konfiguration oder Automatikstufe.

## J.2 Deployment-Gates

Container und DSM Task Scheduler verwenden einen persistent gemounteten `basedir`, einen
dedizierten Least-Privilege-Benutzer und nachvollziehbare UID/GID. Modelle, Referenzen,
Caches, Logs, Zustaende, Summaries und Archive liegen ausserhalb des Container-Images.
Private Bilder, Modelle, Caches, Logs, Laufzeitdaten, lokale Konfigurationen und Secrets
sind in `.gitignore` und duerfen nicht in Git gelangen.

Vor der Produktivfreigabe sind nachzuweisen: Konfigurationsvalidierung, CLI-Hilfe,
Unit-/Integrationstests, Pfad- und ZIP-Sicherheitstests, Dependency-Scan,
Wiederherstellung eines validierten ARW-Archivs, paralleler Scheduler-Start,
Abbruchtest vor/nach jeder Phase-2-Transaktion und Ressourcenverhalten auf Ziel-NAS.
Docker- und optionale GPU-Images werden getrennt dokumentiert; nicht-root-Ausfuehrung
ist anzustreben.

## J.3 Historisches Bash-Skript

Der verbindliche Vertrag zum historischen Bash-Skript steht in Kapitel 9. Diese Anlage
enthaelt dazu keine abweichende Regel.

---

# Anhang K – Normativer Qualitaets-, Dokumentations- und CI-Vertrag

## K.1 Codequalitaet

Aktive Python-Dateien beginnen mit Modul-Docstring: Verantwortung, wesentliche Ein-/
Ausgaben, Sicherheitsgrenzen und optionale Abhaengigkeiten. Oeffentliche Klassen,
Funktionen und CLI-Implementierungen dokumentieren Zweck, Parameter, Rueckgabe und
fachliche Fehler. Nichttriviale Zustands-, Transaktions-, Loesch-, Cache- und
Bewertungslogik erklaert das Warum; sicherheits- bzw. datenintegritaetsrelevante Stellen
sind mit `SICHERHEIT` bzw. `DATENINTEGRITAET` markiert.

Breite Ausnahmebehandlung, globale mutable Zustaende, stille Fehlerunterdrueckung und
unkommentierte magische Grenzwerte sind verboten. Fachentscheidung und Seiteneffekt
werden getrennt. Konfigurierbare Grenzen stehen in der Konfiguration; technische
Konstanten brauchen Begruendung und Test.

## K.2 Repository-Dokumente

| Datei | Mindestinhalt |
|---|---|
| `README.md` | Umfang, Voraussetzungen, Schnellstart, sicherer Ablauf |
| `docs/MANUAL_DE.md` | Bedienung, Ordner, Phasen, Fehler, Wiederherstellung, Backends |
| `docs/CONFIGURATION.md` | Alle Variablen, Werte, Wirkungen, Empfehlungen |
| `docs/INSTALLATION.md` | NAS/Python/Docker, Rechte, Dry Run, Exiftool |
| `docs/BETRIEB.md` | Scheduler, Locks, Logs, Backup, Update, Rollback, Bash-Fallback |
| `docs/TESTING.md` | Tests, Testdaten, Dry Run, NAS-Abnahme |
| `docs/ARCHITEKTUR.md` | Module, Datenfluesse, Abhaengigkeiten, Cache-Invalidierung |
| `SECURITY.md` | Rechte, private Fotos/Secrets, Meldung von Schwachstellen |
| `CHANGELOG.md` | Versionen, Migrationen, Fehler, inkompatible Aenderungen |

Jede Ordner-README grenzt mindestens `reference/notused`, `newrefs/reference`,
`TEMP_IMAGES/TEMP_DONE`, `runtime/state/runtime/run_summaries`, `inbox/used`,
`models/family/models/taste` und `quarantine/logs` voneinander ab.

## K.3 CI und Aenderungsdisziplin

CI prueft mindestens Header, Projektversion, Konfigurationsvalidierung, Syntax,
Format/Lint, Unit-/Integrationstests sowie Konsistenz von CLI-Namen, Backend-IDs und
Konfigurationsschluesseln zwischen Code, Konfiguration und Dokumentation. Testdaten sind
anonymisiert, synthetisch oder ausdruecklich freigegeben; private Originalbilder sind
verboten.

Jede Aenderung an Verhalten, Konfiguration, CLI, Artefaktschema oder Backend-Registry
aktualisiert im selben Aenderungssatz Code, kommentierte Beispielkonfiguration,
Handbuch, Konfigurations-, Architektur- und Betriebsdokumentation, Changelog und Tests.
Eine Funktion gilt erst als umgesetzt, wenn sie aufgerufen wird, konfigurierbar ist,
dokumentiert ist und mindestens einen automatisierten Test besitzt.

---

# Anhang L – Migration, Begriffe und Nichtumfang

## L.1 Begriffe

| Begriff | Verbindliche Bedeutung |
|---|---|
| Batch | Kameraordner mit stabiler `batch_id`, Manifest und Zustandsdatei |
| Aktives JPG | JPG im Batch-Hauptordner, das ein exakt passendes ARW schuetzt |
| Score-Entscheidung | Phase-1-Klasse `keep`, `review` oder `reject` |
| Finale Entscheidung | Deterministische Endentscheidung aus validiertem Phase-2-Ordnerzustand |
| Archivaktivierung | Atomarer Wechsel einer vollstaendig validierten ZIP in ihren finalen Namen |
| Wiederaufnahme | Idempotentes Fortsetzen anhand von Zustand, Hashes und Artefakten |
| Blockierender Fehler | Fehler, der eine sicherheitsrelevante Batch-Aktion verhindert |
| Face-Cache-Fingerprint | Fingerprint aus Backend, Adapter, Modellen, Provider, Vorverarbeitung, Metrik und Auswahl |

Neue JSON-Felder, Konfigurationsschluessel, Python-Namen, Statuswerte und CLI-Befehle
verwenden `snake_case`. Sichtbare Arbeitsordner und festgelegte Keyword-Praefixe sind
Ausnahmen.

## L.2 Nichtumfang

Nicht Bestandteil des Projekts sind Unknown-Clustering, Unknown-to-Known-Zuordnung,
Gesichtsreview-UI, Vektorindex-Infrastruktur, kuenstliche Bild-/Gesichtsgenerierung,
Cloud-Zwang, dauerhafte Online-Dienste, GPU-Pflicht im NAS-Standardbetrieb und komplexe
mehrstufige Face-Learning-Pipelines. Die Auswahl eines optionalen GPU-Backends aendert
weder diese Grenzen noch die Sicherheitsanforderungen.

## L.3 Migrationsregel

Historische Pfade, Namen, Konfigurationsschluessel, Backend-IDs und Metadaten-Tags sind
nur lesende Kompatibilitaetsoptionen, wenn diese Spezifikation sie ausdruecklich nennt.
Sie definieren keinen neuen Produktivvertrag. Migrationen muessen inventarisiert,
protokolliert, wiederholbar und ohne stilles Ueberschreiben erfolgen.

---

# Anhang M – Vollstaendige Mindesttestliste

Neben ACC-01 bis ACC-15 decken Unit- und Integrationstests mindestens ab:

- Konfiguration: Wertebereiche, unbekannte Schluessel, Alias-Konflikte, effektive Konfiguration und Pfadgrenzen
- Steuerdaten: Schema, Pflichtfelder, atomisches Schreiben, Quarantaene und Herkunftsschutz
- CLI: alle kanonischen Befehle, Seiteneffektfreiheit von Diagnose/Validierung und Exit-Codes
- Phase 1: stabile/instabile Eingaenge, Datum, ARW-Ablage, JPG-ZIP, Metadaten und Uebergabe
- Phase 2: Paarbildung, Archivplan, temporäres Archiv, Aktivierung, Kollision, Loeschung und Wiederaufnahme
- Kalibrierung: manueller Move, unveraenderlicher Record, Index-Rebuild, Fingerprint-Trennung und Schattenmodus
- Scoring: Normierung, Schwellwerte, keine Doppelgewichtung, Seriengrenzen und fehlende Komponenten
- Referenzpools: Auswahl, Dedupe, Copy-Verify-Delete, Kapazitaet, manueller Schutz und Rebuild-Unterbrechung
- Faces: bekannte Treffer, Metrikrichtung, Margin, Backendfehler, Cache-Fingerprint und Ausschluss unbekannter Gesichter
- Manual Keep: aktueller Batch, Schwelle, Marge, Keep-Vorrang, `used` und unklare Dateien in `inbox`
- Sicherheit: Lock, Stale-Lock-Pruefung, Dry Run, Pfadausbruch, Symlink, ZIP-Traversal und keine stillen Ueberschreibungen
- Nutzbarkeit: Jede blockierende Lage erzeugt eine konkrete, umsetzbare `user_actions_required`-Meldung

--- Ende der Spezifikation v7.7. ---
