# Synology Photo Workflow – Spezifikation v7.3

**Version:** 7.3.4
**Status:** alleinige normative Bezugsquelle fuer Implementierung und Betrieb
**Zielgruppe:** KI oder Entwicklerteam, das eine bestehende Codebasis prueft, vereinfacht und erweitert
**Prioritaet:** Stabilitaet, Datensicherheit und minimale Fehlinterpretation

## 0. Normativer Vorrang

Dieses Dokument ist die **einzige normative Quelle** fuer den Synology Photo Workflow. Fruhere Fassungen, Begleittexte, Shell-Skripte, Migrationsdokumente, Baseline-Dateien und Beispiele duerfen zur Orientierung dienen, haben aber keinen Vorrang gegenueber dieser Spezifikation. Widersprueche sind zugunsten dieser Fassung zu loesen.

Historische Namen, alte Ordnerbezeichnungen und Legacy-Regeln sind nur dann gueltig, wenn sie in dieser Spezifikation explizit als Alias oder Migrationsform definiert sind.

## 1. Normative Ebenen [CON-00]

Die Spezifikation verwendet drei normative Ebenen:

- **MUSS**: zwingend verbindlich.
- **SOLL**: verbindlich als Standard; Abweichungen sind nur mit bewusster Konfiguration und gut begruendeter Fachentscheidung zulässig.
- **KANN**: optional und ohne Verpflichtungscharakter.

Alle Regeltexte, Tabellen, Beispiele und Migrationsformen muessen dieser Einordnung folgen. Wo ein Beispiel steht, ist es ohne explizite Kennzeichnung nicht normativ.

## 2. Ziel und Umfang [FR-01]

Diese Spezifikation definiert den produktiven Kern des Synology Photo Workflow als **Schnittstellenvertrag**. Sie legt fest, welche Ordner, Dateien, Zustandsuebergaenge, CLI-Befehle, validierten Artefakte und Schutzregeln gelten. Sie definiert nicht den internen Programmcode.

Das System verarbeitet Kameraordner mit JPG- und ARW-Dateien in zwei Phasen, erzeugt und prueft Steuerartefakte, schreibt Ergebnisse in Metadaten und unterstuetzt manuelle Freigaben. Der Fokus liegt auf klaren Vertrauensgrenzen, Wiederaufnahme und Datenintegritaet.

## 3. Betriebsmodell und Prioritaeten [FR-02]

Die Prioritaeten sind verbindlich: 1) Originaldaten vor Verlust schuetzen, 2) fachliche Entscheidungen nachvollziehbar halten, 3) Automatisierung nur innerhalb der freigegebenen Grenzen ermoeglichen. Sobald eine Regel mit Datenintegritaet kollidiert, hat Integritaet Vorrang.

## 4. Verbindliche Grenzen [CON-01]

Nicht Teil des Vertrags sind: konkrete Bildanalyse-Algorithmen, konkrete Modellarchitekturen, interne Heuristiken, Bibliothekswahl, Implementierungsdetails der Scoring-Logik oder detaillierte Rechenwege.

Erlaubt und verbindlich sind stattdessen: Eingaben, Ausgaben, Artefaktgrenzen, Zustandsmodelle, Sperren, Quarantaene, Wiederaufnahme, Freigabegates und Abnahmekriterien.

## 5. Fachliche Leitprinzipien [CON-02]

- Der Python-Workflow ist die operative Referenzimplementierung.
- Das historische Bash-Skript kann als Legacy-Nachweis vorhanden sein, ist aber fachlich nicht massgeblich.
- Der Workflow nutzt die Ordnersemantik `TEMP_SD`, `TEMP_IMAGES`, `TEMP_DONE` und `TEMP_ERROR`.
- Optionale Funktionen sind nur **KANN**-Funktionen und duerfen in Produktivtests oder NAS-Pruefungen eingesetzt werden, muessen aber nicht vom Systemkern zwingend implementiert sein.
- Der Standardmodus bleibt manuell kontrolliert.
- Keine personenbezogenen Daten, Modelle, Logs oder Laufzeitdaten werden in Git als Betriebszustand eingecheckt.

## 6. Struktur-, Namens- und Doku-Vertrag [FR-20]

Dieser Abschnitt definiert die kanonische Zuordnung von Namen, Rollen und lokaler Ordnerdokumentation. Abweichungen sind nur erlaubt, wenn sie explizit als Alias oder Migrationsform genannt sind.

### 6.1 Kanonische Namensformen

Die kanonischen Zustands- und Arbeitsordner fuer den NAS-Betrieb sind:

- `TEMP_SD`
- `TEMP_IMAGES`
- `TEMP_DONE`
- `TEMP_ERROR`
- `MANUALKEEP/inbox`
- `MANUALKEEP/used`
- `faces/`
- `samples/`
- `models/`
- `runtime/`

Im Repository oder in Beispielbaeumen duerfen historische oder kompaktere Schreibweisen vorkommen, sie sind aber nur dann zulaessig, wenn ihre Bedeutung eindeutig der kanonischen Form zugeordnet ist.

| Kanonisch | Alias / Migrationsform | Bedeutung | Betrieb erlaubt? | Nur Migration/Lesen? |
|---|---|---|---|---|
| `TEMP_SD` | `TEMPSD` | Eingang fuer neue Kameraordner | Nein | Ja |
| `TEMP_IMAGES` | `TEMPIMAGES` | Ergebnis aus Phase 1 zur manuellen Sichtung | Nein | Ja |
| `TEMP_DONE` | `TEMPDONE` | Manuell freigegebene Ordner fuer Phase 2 | Nein | Ja |
| `TEMP_ERROR` | `TEMPERROR` | Quarantaene fuer fehlerhafte oder unsichere Faelle | Nein | Ja |
| `runtime/run_summaries/` | `runtime/runsummaries/` | Maschinenlesbare Laufzusammenfassungen | Nein | Ja |

Die kanonische Form hat Vorrang. Aliasformen duerfen nicht als neue Fachbegriffe eingefuehrt werden.

### 6.2 Beispielstruktur und Zielzustand

`NAS_EXAMPLE/` ist der normative Beispielbaum fuer die Zielstruktur auf dem NAS. Er beschreibt die fachliche Semantik der Ordner, nicht notwendigerweise den physischen Repository-Pfad.

Die Wurzel `NAS_EXAMPLE/README.md` beschreibt den Gesamtzweck, die Datenklassen, die Zielpfade und die Zuordnung der Unterbaeume. Jeder fachlich relevante Ordner im Beispielbaum besitzt eine lokale Ordnerbeschreibung.

Die lokale Ordnerbeschreibung darf als `README.md` oder als `ORDNERBESCHREIBUNG.md` vorliegen. Beide gelten als gleichwertig, wenn sie mindestens Zweck, erlaubte Inhalte, verbotene Inhalte, typische Dateitypen, Abgrenzung, Workflow-Rolle und Sicherheitsregeln enthalten. Fuers Projekt sollen neue oder ueberarbeitete Ordner bevorzugt `README.md` verwenden; vorhandene deutsche Bezeichner duerfen als Migrationsform erhalten bleiben.

Alle Beispiele in diesem Dokument sind ohne abweichende Kennzeichnung **nicht normativ**.

### 6.3 Pflichtinhalte lokaler Ordnerdokumentation

Jede lokale Ordnerdokumentation muss mindestens enthalten:

- Zweck des Ordners.
- Zulaessige Inhalte.
- Nicht zulaessige Inhalte.
- Typische Dateitypen oder Dateinamen.
- Abgrenzung zu aehnlichen Ordnern.
- Verhalten im Workflow.
- Sicherheitsregeln.

### 6.4 Fachliche Abgrenzungen

Folgende Paare muessen in der Dokumentation explizit gegeneinander abgegrenzt werden:

- `reference/` vs. `not_used/`
- `new_faces/` vs. `reference/`
- `new_refs/` vs. `reference/`
- `TEMP_IMAGES/` vs. `TEMP_DONE/`
- `runtime/state/` vs. `runtime/run_summaries/`
- `MANUALKEEP/inbox/` vs. `MANUALKEEP/used/`
- `models/face/` vs. `models/taste/`
- `runtime/quarantine/` vs. `runtime/logs/`

## 7. Datenklassen und Schutz [FR-03]

Es gibt drei Datenklassen mit unterschiedlichen Regeln:

- **Originale:** Kamera-JPGs und ARWs.
- **Abgeleitete Medien:** Crops, Kopien, ZIP-Archive und aehnliche vom Workflow erzeugte Ableitungen.
- **Steuerdaten:** Manifeste, Zustaende, Run-Summaries, Caches, Indexe und Logs.

Originale duerfen nur nach den freigegebenen Phasen- und Archivregeln veraendert werden. Steuerdaten muessen atomar, validierbar und wiederherstellbar sein. Abgeleitete Medien duerfen nur innerhalb der dokumentierten Grenzen erstellt, verschoben oder geloescht werden.

## 8. Gemeinsame Architektur [FR-04]

Alle grossen oder dauerhaft relevanten Daten liegen auf einem persistenten NAS-Share. Der Docker-Container ist nur Ausfuehrungsumgebung und keine alleinige Datenquelle.

```text
/NAS/PhotoWorkflowData/
  faces/
    kind-1/
      reference/
      new_faces/
      not_used/
      selection.json
      candidates.json
  samples/
    reference/
    new_refs/
    not_used/
    selection.json
    candidates.json
  models/
    face/
    taste/
  runtime/
    state/
    locks/
    run_summaries/
    logs/
    quarantine/
```

Die Pfade sind konfigurierbar, muessen aber innerhalb eines erlaubten Basisverzeichnisses liegen. Pfadregeln, Namensregeln und Datenklassen duerfen nicht verletzt werden.

## 9. Legacy und Historie [CON-03]

Historische Dokumente, fruehere Spezifikationen und Shell-Skripte sind nur noch Referenzmaterial. Sie duerfen zur Migration oder fuer Altverstaendnis gelesen werden, aber keine abweichenden Betriebsregeln begruenden.

Wenn ein Legacy-Artefakt eine andere Regel beschreibt als diese Spezifikation, ist die in dieser Spezifikation beschriebene Regel massgeblich.

## 10. Aktive JPG-Regel [FR-05]

Nur JPGs im Hauptordner eines Batch-Ordners gelten als aktiv ausgewählt. JPGs in `Review/` oder `Rejected/` gelten nicht als aktiv.

Phase 2 darf ein ARW nur behalten, wenn ein aktives JPG mit demselben Basename im Hauptordner vorhanden ist. Ein Bild kann durch Rueckverschiebung in den Hauptordner wieder aktiv werden.

## 11. CLI und Betriebsarten [FR-06 / RES-02]

Verbindlicher Aufruf:

```sh
python -m app.photoworkflow --config config/config.yaml run
```

Verbindliche Befehle sind:

- `run`
- `phase1`
- `phase2`
- `rebuild_family_cache`
- `rebuild_personal_model`

Bindestrich-Varianten sind nur als deprecated Alias zulaessig. Sie muessen auf die Unterstrich-Form abgebildet werden und duerfen keine andere Semantik haben.

`workflow.phase_execution` bestimmt, welche Phasen ein Aufruf ausfuehren darf. `automation.mode` bestimmt, ob der Uebergang von Phase 1 zu Phase 2 nur manuell oder auch freigegeben automatisch erfolgen darf.

## 12. Phase 1 [FR-07]

Phase 1 verarbeitet vollstaendige Eingangsordner aus `TEMP_SD`.

### Verbindliche Phase-1-Artefakte

- verschobene ARWs im vorgesehenen Unterordner,
- ZIP-Archiv der urspruenglichen JPGs unter dem definierten Namensschema,
- Entscheidungsartefakte fuer die JPG-Bewertung,
- aktualisierte Steuerdaten fuer den Batch,
- Run-Summary-Eintrag.

### Verbindliche Phase-1-Uebergaenge

- Erfolgreiche Phase 1 geht standardmaessig nach `TEMP_IMAGES`.
- Nur wenn alle freigegebenen Voraussetzungen erfuellt sind, darf Phase 1 direkt nach `TEMP_DONE` uebergeben werden.
- Jede Abweichung oder Integritaetsunsicherheit fuehrt zu Rueckstufung oder Quarantaene.

## 13. Phase 2 [FR-08]

Phase 2 arbeitet ausschliesslich auf freigegebenen Batches in `TEMP_DONE`.

### Verbindliche Phase-2-Artefakte

- Batch-Zustand mit Fortschritt und Ergebnis,
- ZIP-Archiv der zu archivierenden ARWs,
- Pruefergebnis fuer das Archiv,
- protokollierte Bereinigung der entbehrlichen ARWs,
- Run-Summary und Abschlussstatus.

### Verbindliche Phase-2-Regeln

- Kein ARW darf entfernt werden, bevor das zugehoerige Archiv validiert und aktiviert ist.
- Bei Unterbrechung muss der naechste Lauf offen gebliebene Schritte anhand der Zustaende fortsetzen oder sauber neu pruefen.
- Fremde oder unsichere ZIP-Dateien duerfen nie still ueberschrieben oder geloescht werden.

## 14. Metadaten [FR-09]

Die Spezifikation verlangt nur den Vertragsrahmen, nicht die interne Schreiblogik. Metadaten duerfen folgende Informationen tragen, wenn die Implementierung dies unterstuetzt:

- Sternrating oder aehnliche Bewertungssignale,
- Entscheidungskennzeichen,
- Serienkennzeichen,
- Personenkennzeichen,
- Manual-Keep-Kennzeichen.

Wenn Metadaten-Schreiben nicht verfuegbar ist, muss der Lauf dennoch lauffaehig bleiben und den Fall eindeutig protokollieren.

## 15. Serienlogik [FR-10]

Die Serienlogik darf Aufnahmen innerhalb eines Batches gruppieren. Sie muss mindestens nachvollziehbar machen:

- Serienkennung,
- Seriengroesse,
- Rang in der Serie,
- Kennzeichnung als Serienbestes,
- Abstand zum Serienbesten.

Die Serienlogik darf die aktive-JPG-Regel nicht aushebeln.

## 16. Persoenlicher Geschmack [FR-11]

Das Geschmacksmodell basiert ausschließlich auf bewusst bestätigten Bildern und soll eine menschliche Auswahl ergänzen, nicht selbstverstärkend ersetzen. Trainiert wird nur mit der in `samples/selection.json` als aktiv markierten Auswahl aus `samples/reference/`; verwaltete Alternativen in `samples/not_used/` können später erneut ausgewählt, Vorschläge aus `samples/new_refs/` jedoch erst nach manueller Bestätigung berücksichtigt werden.

```text
samples/
  reference/       # aktive, manuell bestätigte Geschmackssamples
  new_refs/        # automatisch vorgeschlagene, noch nicht aktive Samples
  not_used/        # nicht aktive, workflowverwaltete Alternativen
  selection.json   # autoritative aktive Auswahl für das Training
  candidates.json  # Bewertung und Status neuer Vorschläge
```

Bei jedem Start prüft das System den Fingerprint des verwalteten Pools aus `reference/` und zulässigen verwalteten Alternativen in `not_used/`. Fehlt oder veraltet `selection.json`, wird es aus diesem Pool deterministisch neu erstellt. Ausschließlich die darin als `active` markierten Dateien bilden die Modellquelle; der physische Ordnerinhalt allein ist keine Autorität. Änderungen an der aktiven Auswahl lösen ein vollständiges, atomar aktiviertes Neutraining des kleinen lokalen Geschmacksmodells aus; der Workflow wartet bei aktivierter Funktion auf den erfolgreichen Abschluss. Das Modell, der Cache und die Manifeste verbleiben auf dem persistierenden NAS-Share.

Die Auswahl- und Ordnerlogik entspricht bewusst der Gesichtserkennung: Aktiv ist nur `reference/` mit den in `selection.json` als `active` markierten Dateien. Der verwaltete Auswahlpool umfasst `reference/` und verwaltete Alternativen in `not_used/`; `new_refs/` enthält nur menschlich zu prüfende Vorschläge. Automatisch erzeugte oder ausdrücklich verwaltbare Alternativen dürfen zwischen `reference/` und `not_used/` wechseln; Herkunft, Status und Auswahlgrund werden manifestiert. Manuell eingebrachte Referenzen sind `manual_protected`, werden nicht automatisch gelöscht und standardmäßig nicht automatisch verschoben. Grenzen, Audit-Informationen, Copy-Verify-Delete-Regeln und der sichere Nicht-Löschstandard sind gleich.

Richtwerte: `min_active: 50`, `target_active: 75`, `max_active: 100`, `max_not_used: 200`, höchstens zehn neue Vorschläge pro Lauf, höchstens 100 offene Vorschläge und keine neuen Vorschläge bei vollem `not_used/`. Eine spaetere optional freigegebene Bereinigung darf nur automatisch erzeugte Kopien nach Aufbewahrungsfrist löschen.

Ein Bild darf nach `new_refs/` kopiert werden, wenn es `keep` ist, die höchste konfigurierbare Sternklasse (standardmäßig fünf Sterne) erreicht, technisch ausreichend gut ist, kein Duplikat darstellt und Stil, Komposition, Motiv, Licht oder Farbstimmung gegenüber der aktiven Auswahl messbar erweitert. Der Nutzer bestätigt ein Sample nur durch manuelles Kopieren nach `reference/`. Nicht angenommene oder verdrängte automatisch erzeugte Kopien können nach `not_used/` verschoben werden; sie trainieren das Modell nicht.

## 17. Bekannte Gesichtserkennung [FR-12]

Die Gesichtsfunktion verarbeitet ausschließlich bekannte, manuell gepflegte Personen. Sie liefert ein moderates positives Signal für die Bildbewertung und erzeugt aus klaren Treffern prüfbare Vorschläge zur Verbesserung der Referenzbasis. Unbekannte Gesichter werden nicht gespeichert, nicht geclustert und keiner Person zugeordnet.

### Ordner und Rollen

```text
faces/
  kind-1/
    reference/       # aktive, bestätigte und ausgewählte Modellreferenzen
    new_faces/       # automatisch erzeugte, noch menschlich zu prüfende Crops
    not_used/        # nicht aktive, workflowverwaltete Alternativen
    selection.json   # autoritative aktive Auswahl
    candidates.json  # Status und Qualität der new-face-Vorschläge
```

Nur Dateien in `reference/`, die in `selection.json` den Status `active` haben, dürfen das aktive Face-Modell speisen. `new_faces/` und `not_used/` sind niemals Modellquellen. Ein Mensch aktiviert einen Vorschlag nur durch Kopieren nach `reference/`; die Anwendung verschiebt keine manuell eingeordneten Referenzbilder ohne explizite spätere Automatikfreigabe.

Der verwaltete Auswahlpool besteht aus `reference/` und aus Dateien in `not_used/`, deren Manifestherkunft `origin: generated` oder `managed: true` lautet. Daraus darf die Auswahl aktive Dateien nach `reference/` zurückholen oder inaktive verwaltete Alternativen nach `not_used/` verschieben. Dateien mit `origin: manual` sind `manual_protected`: Sie werden ohne explizite Konfigurationsfreigabe weder automatisch verschoben noch gelöscht, können aber bewusst aktiv ausgewählt werden. Jede Datei besitzt im Manifest genau einen Status: `active`, `inactive`, `pending_review`, `superseded`, `manual_protected` oder `archived`.

### Manifest, Auswahl und Rebuild

Zu Beginn **jedes** Workflow-Laufs inventarisiert das System den verwalteten Auswahlpool einer Person (`reference/` plus zulässige verwaltete Alternativen aus `not_used/`) und vergleicht dessen Fingerprint (relativer Pfad, Größe, Änderungszeit und SHA-256 soweit verfügbar) mit `selection.json`. Fehlt das Manifest, ist es ungültig oder hat sich der Pool geändert, erstellt oder aktualisiert das System `selection.json` vor der Bildverarbeitung.

Die Auswahl priorisiert in dieser Reihenfolge: lesbare und ausreichend große Crops, Mindestqualität, SHA-256-Dedupe, visuelle/Embedding-Dedupe, Gesichtsqualität und Diversitätsgewinn bei Pose, Blickrichtung, Gesichtsgröße, Licht und Aufnahmezeit. Bei Gleichstand entscheidet der relative Dateiname. Der Algorithmus muss bei identischen Eingaben und Konfigurationen dieselbe Auswahl treffen.

`selection.json` ist die autoritative Liste aktiver Referenzen. Sie enthält mindestens Schema- und Algorithmusversion, Personen-Slug und Anzeigename, Referenz-Fingerprint, Erstellungszeit, Modell-/Metrikkennung, `active`, `inactive`, Auswahlwerte, Gründe, Verschiebungen und `rebuild_required`.

Bei einer geänderten Auswahl wird der Face-Cache aus der Manifestauswahl neu aufgebaut. Ist `family_recognition.enabled: true`, wartet der Workflow vor der weiteren bildbezogenen Gesichtsauswertung auf den erfolgreichen Rebuild; er verwendet weder einen alten Cache noch deaktiviert er still die Gesichtserkennung. Scheitert der Rebuild, endet der Lauf kontrolliert mit `face_model_rebuild_failed`; der betroffene Batch wird nicht als erfolgreich abgeschlossen oder übergeben und beim nächsten Scheduler-Lauf fortgesetzt. Ist die Gesichtserkennung deaktiviert, findet weder Rebuild noch Face-Scoring statt; fehlt bei aktivierter Pflichtfunktion eine Abhängigkeit, gilt dies wie ein Rebuild-Fehler und nicht als stilles Überspringen.

Der Rebuild erfolgt in einem temporären Verzeichnis auf demselben NAS-Dateisystem: Manifest und Quellen prüfen, Merkmale erzeugen, Lesbarkeit und Dimensionen validieren, Smoke-Match ausführen, Artefakt atomar aktivieren. Bei Fehler bleibt der vorherige gültige Cache unverändert. Ein durch Zeitlimit oder Signal unterbrochener Rebuild wird als `paused` gespeichert und im nächsten Lauf fortgesetzt oder deterministisch neu erstellt.

### Aktive Menge und Speichersteuerung

Konfigurierbare Richtwerte sind `min_active: 30`, `target_active: 40` und `max_active: 50`. Unterhalb von 30 geeigneten Bildern werden alle geeigneten Bilder aktiv und ein Unterbestand wird gemeldet; zwischen 30 und 50 werden alle geeigneten Bilder aktiv; oberhalb von 50 wird eine vielfältige Auswahl bis maximal 50 getroffen.

Nicht ausgewählte, vom Workflow erzeugte oder ausdrücklich verwaltbare Referenz-Crops dürfen nach erfolgreicher Manifesterstellung atomar per Copy-Verify-Delete nach `not_used/` verschoben werden. Die Verschiebung wird im Manifest mit Quelle, Ziel, Wert und Grund protokolliert. Manuell eingebrachte Dateien werden nie automatisch gelöscht; ihre automatische Verschiebung ist standardmäßig deaktiviert und nur über eine getrennte Konfigurationsfreigabe zulässig. Jede Verschiebung ist idempotent: Nach einem Abbruch werden Quelle, Ziel, Hash, Größe und Manifeststatus geprüft. Nur ein eindeutig verifizierter Copy-Verify-Delete-Vorgang gilt als abgeschlossen; widersprüchliche Zustände werden quarantänisiert.

`not_used/` wird auf `max_not_used: 100` begrenzt. Im sicheren Standard werden bei vollem Ordner keine neuen `new_faces/`-Vorschläge erzeugt und ein sichtbarer Status `not_used_limit_exceeded` erzeugt; es findet keine automatische Löschung statt. Eine später bewusst aktivierbare Option darf ausschließlich automatisch erzeugte Crops nach definierter Aufbewahrungszeit löschen, niemals Originalbilder oder manuell eingebrachte Referenzen.

### Neue Face-Crops und menschliche Prüfung

Ein Crop darf nur fuer eine bekannte Person erzeugt werden, wenn genau ein Personenmatch eine hohe Konfidenz erreicht, der Abstand zum zweitbesten Match eine Sicherheitsmarge erfüllt, das Gesicht Mindestwerte für Größe, Schärfe und Belichtung erfüllt, das Quellbild `keep` oder Manual Keep ist und kein exaktes oder visuell nahes Duplikat zu `reference/` oder `new_faces/` besteht. Die backendunabhängige Konfiguration definiert mindestens Match-Metrik mit Richtung, `min_match_similarity`, `min_best_second_margin`, `require_single_known_match` und `min_face_size_px`; Standardwerte werden als konservative Startwerte dokumentiert und müssen getestet werden. Enthält ein Bild mehrere bekannte Personen, darf je Person höchstens ein Crop entstehen, sofern ihr eigener Treffer alle Grenzen erfüllt. Zusätzliche unbekannte Gesichter werden weder gespeichert noch als Kandidat dokumentiert.

Der Crop wird aus dem JPG mit konfigurierbarem Rand erzeugt und in `new_faces/` abgelegt. Ein lesbarer, kollisionssicherer Dateiname folgt diesem Muster: `YYYY-MM-DD__source-basename__face-01__hash8.jpg`. Die vollständige technische Herkunft steht zentral in `candidates.json`, nicht in vielen Seitendateien. Pro Kandidat werden relativer Quellpfad, voller Quell-Hash, Bounding Box, Crop-Rand, Match- und zweitbester Matchwert, Qualitätswert, Neuheitswert, Gesamtwert, Zeitstempel und Status gespeichert.

`candidate_value` kombiniert standardmäßig Gesichtsqualität (40 Prozent), Diversitätsgewinn gegenüber aktiven Referenzen und offenen Vorschlägen (35 Prozent), Erkennungssicherheit (15 Prozent) und Bildkontext wie Keep/Serienrang (10 Prozent). Nur Kandidaten oberhalb einer konfigurierten Mindestschwelle werden kopiert. Standardlimits: maximal zehn neue Vorschläge je Person und Lauf sowie maximal 100 offene Vorschläge je Person.

Ist `new_faces/` voll, gilt standardmäßig: keine neuen Crops, sichtbarer Status und keine automatische Löschung. Optional kann ein neuer Crop einen schwächeren, automatisch erzeugten Crop nach `not_used/` verdrängen, wenn sein Gesamtwert höher ist; der alte Eintrag erhält in `candidates.json` den Status `superseded`. Alle Vorschläge werden vor einer Modellaktivierung vom Menschen geprüft. Der Nutzer kopiert geeignete Crops manuell nach `reference/`; beim nächsten Start aktualisiert das System Manifest und Modell.

### Score und Metadaten

Ein eindeutiger Treffer darf einen begrenzten `family_score` liefern, ein Bild bei aktivierter Schutzregel von `reject` auf höchstens `review` anheben und Personentags für Metadaten bereitstellen. Er darf technische Mängel nicht vollständig überstimmen und keine neue Identität automatisch aktivieren.

## 18. Metadaten [FR-09]

Culling-Ergebnisse und bekannte Gesichtstreffer sollen optional mit Exiftool in JPG-Metadaten geschrieben werden. Der Workflow bleibt lauffaehig, wenn Exiftool fehlt; dann wird ein klarer Status protokolliert.

### Zu schreibende Informationen

- Sternrating aus `final_score` nach konfigurierbaren Bändern.
- Namespaced Keywords, z. B. `workflow:aicull`, `decision:keep`, `series:best`.
- Score-Bänder, nicht zwingend rohe Dezimalwerte.
- Bei bekannten Personen: `person:Kind1`, `family:match`.
- Optional `manualkeep:true` für WhatsApp-/Manual-Keep-Treffer.

Rohscores bleiben primär in `SAVE/culling_scores.csv` und der JSON-Run-Summary. Das verhindert unnötige Metadatenüberladung.

Exiftool muss ausschließlich über argumentbasierte Aufrufe mit `shell=False` gestartet werden.

## 19. WhatsApp Manual Keep [FR-13]

`MANUALKEEP/inbox/` enthält noch nicht zugeordnete Manual-Keep-Dateien. `MANUALKEEP/used/` enthält erfolgreich zugeordnete Dateien.

Eine Zuordnung darf nur im aktuellen Batch erfolgen. Bei erfolgreicher Zuordnung wird der Kandidat als `keep` behandelt und die Manual-Keep-Datei nach `used` verschoben. Mehrdeutige oder unlesbare Dateien bleiben in `inbox`.

## 20. Datenverträge und Schema-Versionen [FR-14]

Steuerdaten müssen versioniert, validierbar und atomar geschrieben sein. Dazu gehören mindestens:

- `selection.json`,
- `candidates.json`,
- `runtime/state/<batch-id>.json`,
- JSON-Run-Summary,
- optionale Batch-Records fuer Kalibrierung.

Jede dieser Dateien muss eine stabile Kennung und eine Schema-Version tragen. Ungueltige Dateien dürfen nie still überschrieben werden.

## 21. Task Scheduler, Docker und Wiederaufnahme [FR-15]

Der Scheduler startet den Container mit persistentem NAS-Mount. Pro Batch existiert genau eine Zustandsdatei unter `runtime/state/<batch-id>.json`.

Die Batch-ID muss aus Quellordner und Fingerprint ableitbar und stabil sein. Wiederaufnahme bedeutet: bereits validierte Schritte werden nicht blind wiederholt, offene Schritte werden anhand der Zustandsdateien und Artefakte fortgesetzt oder sauber neu geprüft.

## 22. Kalibrierung und lernende Gewichtung [FR-16]

Kalibrierung ist ein Vertragsbereich fuer menschlich bestaetigte Entscheidungen, nicht fuer automatische Umwidmung von Entscheidungen.

Verbindlich sind:

- ein unveraenderliches Batch-Record pro manuell freigegebenem Batch,
- ableitbare Indizes und Summaries,
- Rekonstruierbarkeit aus den Batch-Records,
- kein stiller Ersatz der menschlichen Endentscheidung durch einen Modellwert.

Solange die Freigabegates nicht erfuellt sind, darf Kalibrierung nur dokumentieren und empfehlen, nicht selbst umschalten.

## 23. Kapazitaet und Automatikstufen [FR-17]

Die Funktion darf nur innerhalb freigegebener Stufen arbeiten. Eine Freigabestufe darf den Phase-1-zu-Phase-2-Uebergang erlauben, aber nie die Datenintegritaet ueberstimmen.

Wenn ein Kapazitaetslimit erreicht ist, muessen neue Vorschlaege blockiert oder zurueckgestellt werden. Vollstaendig technische Folgen, Schwellen oder interne Strategien gehoeren nicht in den Vertragskern.

## 24. Performance fuer kleine NAS-Systeme [NFR-01]

Der Kernvertrag fordert ressourcenschonenden Betrieb, kleine Vorschauen und den Verzicht auf grosse Pflichtmodelle im Standardfall. Diese Anforderungen sind **SOLL**-Ziele fuer Produktivtests und NAS-Pruefungen; die technische Umsetzung ist **KANN** und wird vom Entwickler nachgelagert implementiert und optimiert. Andere Tests sollen so weit wie moeglich durch Testfaelle und Simulationen abgedeckt werden; auf dem Zielsystem sind nur die nicht sinnvoll simulierbaren Pruefungen auszufuehren.

## 25. Stabilitaet und Sicherheit [NFR-02 / NFR-05 / NFR-06]

Verbindlich sind:

- globaler Lock gegen parallele Laeufe,
- Path-Traversal- und Symlink-Schutz,
- atomare Schreibvorgaenge fuer Steuerdateien,
- kontrollierte Quarantaene fuer ungueltige oder unerwartete Dateien,
- Dry-Run als nicht-mutierende Betriebsform,
- keine stillen Ueberschreibungen.

Diese Vorgaben sind fuer die Spezifikation normativ; die technische Umsetzung der Pruefungen ist **KANN** und kann in Testfaellen vorab simuliert werden. Auf dem Zielsystem werden nur die verbleibenden Realweltpruefungen ausgefuehrt.

## 26. Reporting und Artefakte [FR-18]

Jeder Lauf muss klare, maschinenlesbare Ergebnisse erzeugen. Dazu gehoeren mindestens ein Run-Summary, ein klarer Ergebnisstatus und die Benennung aller offenen Nutzeraktionen, soweit vorhanden. Die konkrete Realisierung dieses Reportings ist **KANN**, die Erwartung an das Ergebnis bleibt jedoch verbindlich.

## 27. Konfiguration und Dokumentation [NFR-04]

Konfigurationen muessen lesbar, kommentiert und von der Spezifikation ableitbar sein. Die Dokumentation muss die Ordnerstruktur, die Datenklassen, die Schnittstellen und die Freigabegates erklaeren. Wie genau die Dokumentationsform umgesetzt wird, ist **KANN**; die fachliche Aussage muss jedoch pruefbar vorhanden sein.

## 28. Bedienung im Alltag [FR-19]

Der Alltagsfluss bleibt einfach: Eingang nach `TEMP_SD`, Lauf starten, Run-Summary pruefen, manuell freigeben, Phase 2 ausfuehren. Komplexere Funktionen duerfen diesen Grundfluss nicht verdecken.

## 29. Pruefung der bestehenden Codebasis

Zu pruefen sind ausschliesslich die im Vertrag definierten Schnittstellen, Artefakte, Zustaende und Schutzgrenzen. Der interne Code selbst ist nicht Teil der Spezifikation. Produktivtests und NAS-Pruefungen koennen die Umsetzung der **KANN**-Anforderungen verifizieren, aber auf dem Zielsystem sollen nur die Tests ausgefuehrt werden, die nicht sinnvoll durch Testfaelle, Stubs oder Simulationen abgedeckt werden koennen.

## 30. Mindesttests

Mindestens zu testen sind:

- Konfigurationsvalidierung,
- Datenvertraege,
- CLI-Subcommands,
- Phase-1- und Phase-2-Uebergaenge,
- Wiederaufnahme,
- Locking,
- Quarantaene,
- README-Pflicht fuer fachlich relevante Ordner,
- aktive-JPG-Regel,
- Manual Keep,
- Metadaten-Fallback,
- Run-Summary.

Die Tests pruefen das Ergebnis und die Sicherheitsgrenzen; die technische Tiefenimplementierung bleibt **KANN**-Bereich. Wo moeglich sollen diese Tests als Testfaelle, Stubs oder Simulationen formuliert werden; nur die Zielsystem-Pruefungen selbst muessen reale NAS-Tests sein.

## 31. Abnahmekriterien

1. Diese Spezifikation ist die einzige normative Quelle.
2. Die Rueckfallebene Bash ist nur noch Referenzmaterial.
3. Der Vertragsrahmen definiert Eingaben, Ausgaben, Zustaende und Schutzgrenzen, nicht den internen Code.
4. Phase 1 erzeugt die definierten Artefakte und uebergibt nur in erlaubten Modi.
5. Phase 2 veraendert ARWs nur nach validiertem Archiv und dokumentiertem Zustand.
6. Die aktive-JPG-Regel wird konsequent durchgesetzt.
7. Steuerdateien sind versioniert, validierbar und atomar geschrieben.
8. Wiederaufnahme ist idempotent und ohne stillen Datenverlust moeglich.
9. Die Selbstdokumentation von `NAS_EXAMPLE/` ist fuer fachlich relevante Ordner vorhanden.
10. Aehnliche Ordner sind in ihren README-Dateien explizit gegeneinander abgegrenzt.
11. Manual Keep, Faces und Samples sind klar voneinander getrennt.
12. Kalibrierung dokumentiert nur, schaltet nicht still um.
13. Automatikstufen koennen keine Sicherheitsgrenzen aushebeln.
14. Der Lauf bleibt lauffaehig, wenn optionale Metadaten- oder Backend-Funktionen fehlen.
15. Die Run-Summary benennt den Ergebnisstatus und offene Nutzeraktionen eindeutig.
16. Produktivtests und NAS-Pruefungen koennen **KANN**-Anforderungen verifizieren, ohne daraus einen sofortigen Implementierungszwang fuer den Kern abzuleiten.
17. Auf dem Zielsystem werden nur die Tests ausgefuehrt, die nicht sinnvoll durch Testfaelle, Stubs oder Simulationen abgedeckt werden koennen.

## 32. Anhangsrahmen

Beispiele fuer Ordner-READMEs, JSON-Strukturen und Konfigurationsmuster koennen im Anhang gezeigt werden. Sie sind beispielhaft, nicht implementierungsvorschreibend. Anhaenge duerfen keine neuen Pflichtregeln einfuehren oder bestehende Normen abschwaechen.

---

*Ende der Spezifikation v7.3.4.*
