# Synology Photo Workflow – Spezifikation

**Status:** verbindliche, bewusst schlanke Anforderungs- und Funktionsbeschreibung  
**Zielgruppe:** KI oder Entwicklerteam, das eine bestehende Codebasis prüft, vereinfacht und erweitert  
**Priorität:** Stabilität, Datensicherheit und gute Laufzeit auf kleinen Synology-NAS-Systemen

## Ziel und Umfang

Dieses Dokument definiert den **kleinen, produktiv sinnvollen Kern** des Synology Photo Workflow. Die Implementierung soll eine vorhandene Codebasis gezielt prüfen und nur die hier beschriebenen Funktionen ergänzen oder reparieren. Sie soll nicht zu einer großen allgemeinen Foto- oder Gesichtsdatenplattform ausgebaut werden.

Das System verarbeitet Kameraordner mit JPG- und ARW-Dateien in zwei Phasen. Es bewertet JPGs technisch und nach persönlichem Geschmack, berücksichtigt bekannte Familiengesichter als moderates positives Signal, schreibt Ergebnisse in Bildmetadaten und schützt die historische Ablauflogik vor Datenverlust.


## Betriebsmodell und Prioritäten

Der Workflow verfolgt drei gleichrangige Ziele: Originaldaten vor Verlust schützen, den wiederkehrenden manuellen Aufwand klein halten und die Qualität der Entscheidungen über nachvollziehbare Lernbeispiele verbessern. Bei Zielkonflikten gilt diese Reihenfolge: Datenintegrität und Sicherheitsgrenzen vor Automatisierungsgrad, Automatisierungsgrad vor kosmetischer Optimierung.

Der normale Nutzerablauf soll kurz bleiben: Kameraordner bereitstellen, Run-Summary prüfen, nur bei `review`, `warning`, `full`, `blocked`, `paused` oder `failed` tätig werden und neue Gesichts- oder Geschmacksvorschläge gesammelt statt pro Lauf prüfen. Die Anwendung übernimmt Inventar, Bewertung, Dedupe, Kandidatenpriorisierung, Limits, Modell-Rebuild, Wiederaufnahme, Reporting und – nach Freigabe – die sichere Ausführung von Phase 2.

Es gibt drei Datenklassen mit unterschiedlichen Regeln: **Originale** (Kamera-JPGs und ARWs) werden nur nach den Phase-2- und Archivregeln behandelt; **abgeleitete Medien** (Face-Crops und Sample-Kopien) dürfen nach dokumentierten Regeln verwaltet werden; **Steuerdaten** (Manifeste, Zustände, Caches und Logs) werden atomar geschrieben und sind wiederherstellbar. Kein abgeleitetes Artefakt darf eine Aktion an einem Original auslösen, die nicht bereits durch die aktive-JPG-Regel und die jeweilige Automatikstufe erlaubt ist.


## Verbindliche Grenzen

Folgende Funktionen gehören ausdrücklich **nicht** zum Projektumfang:

- Lernen, Clustern oder automatisches Zusammenführen unbekannter Gesichter.
- Unknown-to-Known-Zuordnungen, Gesichtsreview-UI, Face-Crop-Datenbanken oder Vektorindex-Infrastruktur.
- Generierung künstlicher Bilder oder Gesichter.
- Cloud-Zwang, dauerhafte Online-Dienste oder große GPU-Modelle.
- Komplexe, mehrstufige Face-Learning-Pipelines.

Die Gesichtsfunktion beschränkt sich auf den Abgleich gegen **manuell gepflegte, bekannte Personen**. Die Geschmacksfunktion beschränkt sich auf einen kleinen, lokal gespeicherten Modell-/Referenzbestand.

## Fachliche Leitprinzipien

- Das historische Bash-Skript bleibt unverändert als Notfall-Rückfallebene erhalten, ist aber nicht Teil der aktiven Python-/Docker-Weiterentwicklung.
- Der Python-Workflow wahrt die bewährte Ordnersemantik von Bash (`TEMP_SD`, `TEMP_IMAGES`, `TEMP_DONE`), übernimmt aber die alleinige fachliche Verantwortung für Culling, Metadaten, Referenzen, Kalibrierung und Modelle.
- Sicherheit vor Datenverlust ist wichtiger als aggressives Aussortieren.
- Der Standardmodus bleibt manuell kontrolliert; Vollautomatik ist eine spätere, explizite Option.
- Alle optionalen KI-Funktionen müssen bei fehlenden Bibliotheken kontrolliert ausfallen. Der Kernworkflow bleibt lauffähig.
- Keine personenbezogenen Bilder, Modelle, Caches, Logs oder Laufzeitdaten werden in Git eingecheckt.


## Gemeinsame Architektur

Alle großen, personenbezogenen oder dauerhaft relevanten Daten liegen auf einem persistenten NAS-Share. Der Docker-Container ist ausschließlich die austauschbare Ausführungsumgebung: Er enthält Code und Abhängigkeiten, aber keine alleinige Quelle für Referenzbilder, Vorschläge, Modelle, Caches, Manifeste, Checkpoints oder Logs. Diese Daten müssen als persistenter bind mount eingebunden werden, damit Container-Neubau, Update oder Austausch keinen Arbeits- oder Lernstand verlieren.

```text
/NAS/PhotoWorkflowData/
  faces/
    kind-1/
      reference/
      new_faces/
      not_used/
      selection.json
      candidates.json
    person-2/
      ...
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
```

Namen für Verzeichnisse und Dateien verwenden portablen, GitHub- und Python-konformen Stil: Kleinbuchstaben, ASCII, Ziffern, Bindestriche für stabile Slugs und Unterstriche für mehrteilige technische Begriffe, etwa `kind-1`, `new_faces`, `not_used` und `run_summaries`. Ein Personen-Slug ist stabil und technisch; ein frei lesbarer Anzeigename gehört in `selection.json` und Metadaten, nicht zwingend in den Pfad.

Die Ordnerstruktur ist eine wiederverwendbare Blaupause: `reference/` enthält die aktive, vom Modell verwendete Auswahl; `new_faces/` beziehungsweise `new_refs/` enthält automatisch erzeugte Vorschläge zur menschlichen Prüfung; `not_used/` enthält nicht aktive, vom Workflow verwaltete Alternativen; Manifest und Kandidatenliste dokumentieren jede Auswahl. Die Automatisierung bereitet vor, bewertet, begrenzt und protokolliert. Der Mensch bestätigt die fachlich entscheidenden Übergänge in `reference/`. Dadurch kann die Automatik später aktiviert werden, ohne diese Sicherheitsgrenze in der Implementierung neu schaffen zu müssen.


## Begriffe und Ordner

| Bereich | Bedeutung |
|---|---|
| `TEMP_SD` | Eingang für neue Kameraordner |
| `TEMP_IMAGES` | Ergebnis aus Phase 1 zur manuellen Sichtung |
| `TEMP_DONE` | Manuell freigegebene Ordner für Phase 2 |
| `TEMP_ERROR` | Quarantäne für fehlerhafte oder unsichere Fälle |
| `MANUALKEEP/inbox` | Vorab ausgewählte, z. B. über WhatsApp erhaltene kleinere JPGs |
| `MANUALKEEP/used` | Bereits erfolgreich zugeordnete Manual-Keep-Dateien |
| `faces/<person-slug>` | Aktive und verwaltete Referenz-Crops bekannter Personen |
| `samples/` | Aktive und verwaltete Referenzen für das persönliche Geschmacksmodell |
| `models/` | Persistente lokale Modellartefakte und Caches mit Manifest-/Modellversion, nicht in Git |
| `runtime/state/` | Eine atomare Zustandsdatei je Batch zur Wiederaufnahme |
| `runtime/run_summaries/` | Maschinenlesbare Laufzusammenfassungen |

Die tatsächlichen Pfade sind konfigurierbar, müssen aber innerhalb eines erlaubten Basisverzeichnisses liegen.

## Rückfallebene Bash

Das historische Bash-Skript bleibt Bestandteil des Projekts und wird nicht entfernt oder fachlich umdefiniert. Es ist die dokumentierte Rückfallebene, wenn Python, ein Modell, Exiftool oder eine optionale Abhängigkeit nicht verfügbar ist.

Die Python-Implementierung muss insbesondere diese fachliche Altlogik beibehalten:

1. Neue Kameraordner kommen nach `TEMP_SD`.
2. Phase 1 prüft und verarbeitet sie, verschiebt ARWs nach `ARW/` und sichert die ursprünglichen JPGs als ZIP in `SAVE/`.
3. Phase 1 bewertet JPGs und übergibt den Ordner standardmäßig an `TEMP_IMAGES`.
4. Der Nutzer prüft dort das Ergebnis und verschiebt einen freigegebenen Ordner nach `TEMP_DONE`.
5. Phase 2 behält nur ARWs, deren gleichnamige JPGs im Hauptordner aktiv ausgewählt sind; sie archiviert die übrigen relevanten ARWs sicher und bereinigt `ARW/`.

Das Bash-Skript kennt nicht zwingend alle Python-Zusatzfunktionen wie Scores oder Metadaten. Es muss aber weiterhin für den sicheren Grundfluss nutzbar bleiben.

## Aktive JPG-Regel

Nur JPGs im Hauptordner eines Batch-Ordners gelten als **aktiv ausgewählt**. JPGs in `Review/` oder `Rejected/` gelten nicht als aktiv.

Phase 2 darf ein ARW nur behalten, wenn ein aktives JPG mit demselben Basename im Hauptordner vorhanden ist. Ein Nutzer kann ein Bild vor der Freigabe aus `Review/` oder `Rejected/` zurück in den Hauptordner legen; dann wird es wieder aktiv.

## CLI und Betriebsarten

Der stabile Python-Aufruf soll paketbasiert sein:

```sh
python -m app.photoworkflow --config config/config.yaml run
```

Mindestens erforderlich sind:

- `run`: folgt dem konfigurierten Ausführungsmodus.
- `phase1`: führt nur Phase 1 aus.
- `phase2`: führt nur Phase 2 aus.
- `rebuild-family-cache`: baut den optionalen Cache bekannter Gesichter neu auf.
- `rebuild-personal-model`: baut das optionale Geschmacksmodell neu auf.

`run` unterstützt:

- `phase1thenphase2`
- `phase1only`
- `phase2only`

Explizite CLI-Kommandos übersteuern die Konfiguration. `workflow.phase_execution` steuert, welche Phasen ein Aufruf ausführen darf; die Freigabeentscheidung für den Übergang von Phase 1 zu Phase 2 steuert ausschließlich `automation.mode`. `automation.mode: assisted_review` ist der sichere Standard und die fachliche Autorität. Der ältere Culling-Wert `culling.decision_mode` darf nur als Kompatibilitätsalias existieren, wird beim Laden eindeutig in `automation.mode` übersetzt und darf keinen abweichenden Wert setzen. Widersprüchliche Werte brechen die Konfigurationsvalidierung mit verständlicher Fehlermeldung ab.

## Phase 1

Phase 1 verarbeitet vollständige und stabile Eingangsordner aus `TEMP_SD`.

### Ablauf

1. Ordner prüfen: zulässiger Name, vollständige Übertragung, keine aktive Sperre.
2. Datum gemäß konfigurierbarer Legacy-Logik oder echtem Volljahresmodus bestimmen.
3. ARWs nach `ARW/` verschieben.
4. Ursprüngliche JPGs sicher als `SAVE/<Ordner>_ALLJPG.zip` archivieren.
5. JPGs bewerten.
6. Manual-Keep-Zuordnungen anwenden.
7. Serienlogik anwenden, falls aktiviert.
8. Culling-Entscheidung `keep`, `review` oder `reject` treffen.
9. Optional Bewertungen und bekannte Personentreffer in die Bildmetadaten schreiben.
10. Der Ordner geht im Standardmodus nach `TEMP_IMAGES`.

### Übergabemodi

Der Standard ist `automation.mode: assisted_review`. Dann geht Phase 1 ausschließlich nach `TEMP_IMAGES`; der Nutzer gibt bewusst frei, indem er den Ordner nach `TEMP_DONE` verschiebt.

Für die freigegebene Stufe `automatic_phase2` müssen `automation.mode`, `automation.automatic_phase2_enabled: true` und `workflow.phase_execution: phase1thenphase2` gemeinsam gesetzt sein. Dann darf Phase 1 den vollständig erfolgreichen Batch direkt nach `TEMP_DONE` übergeben, sodass derselbe `run` Phase 2 abschließen kann. Fehlt eine dieser Voraussetzungen oder schlägt eine Integritätsprüfung fehl, bleibt der Batch in `TEMP_IMAGES`. Der frühere Schlüssel `culling.decision_mode` ist nur ein validierter Kompatibilitätsalias und darf diese Sicherheitsgrenze nicht umgehen.

## Phase 2

Phase 2 arbeitet ausschließlich auf vollständig freigegebenen Ordnern in `TEMP_DONE` und ist als wiederaufnehmbare Transaktion ausgeführt. Sie darf ARWs erst bereinigen, wenn das zugehörige Archiv geprüft, aktiviert und im Batch-Zustand dokumentiert ist.

1. Aktive JPGs im Hauptordner bestimmen und die dazugehörigen ARWs ableiten.
2. Zu archivierende und nach aktiver-JPG-Regel entbehrliche ARWs als Plan mit Dateiliste und Fingerprint erfassen.
3. Das Archiv `SAVE/<Ordner>_SORTARW.zip` zunächst als temporäre Datei schreiben.
4. Archivinhalt, Lesbarkeit und erwartete Dateiliste prüfen; bei Erfolg das Archiv atomar aktivieren.
5. Finalen Archivpfad, Hash und Prüfergebnis in der Batch-Zustandsdatei speichern.
6. Erst danach ARWs gemäß Plan einzeln oder als vollständig geprüften Ordner bereinigen und jeden Abschluss idempotent protokollieren.
7. Prozessmarker, Run-Summary und Status `completed` erst schreiben, wenn Archivierung, Bereinigung und alle Integritätsprüfungen erfolgreich sind.

Bei Abbruch vor der atomaren Archivaktivierung darf kein ARW entfernt werden. Bei Abbruch danach darf der nächste Lauf das geprüfte Archiv wiederverwenden, den Zustand mit noch vorhandenen ARWs abgleichen und nur die offenen Schritte fortsetzen. Bei ZIP-Kollisionen sind eindeutige Folgezielnamen wie `...EXTRA2.zip` zu verwenden; fremde oder unsichere ZIP-Dateien dürfen nie überschrieben oder still entfernt werden.


## Bildbewertung

Die Bildbewertung ist lokal und ressourcenschonend. Sie darf auf kleine Vorschauen herunterskalieren und muss keine großen Deep-Learning-Modelle laden.

### Technische Komponenten

Der Basisscore soll mindestens folgende fachliche Merkmale unterstützen:

- **Schärfe:** z. B. Kantenvarianz auf einer verkleinerten Graustufenvorschau.
- **Ästhetik:** einfache, erklärbare Kombination aus Kontrast, Sättigung, Bildbalance und optionaler Kompositionsnäherung.
- **Belichtung:** Strafe für stark geclipptes Schwarz/Weiß und unausgewogene mittlere Helligkeit.
- **Auflösung/Detail:** moderates Signal, das kleine oder sehr stark komprimierte Bilder nicht unangemessen bevorzugt.
- **Augen-Signal:** optional; nur verwenden, wenn ein leichtgewichtiges lokales Face-Backend verfügbar ist.
- **Referenzähnlichkeit:** optional; kleine visuelle Referenzprofile können das persönliche Scoring ergänzen.

Alle Teilwerte liegen normiert zwischen 0 und 1. Nicht verfügbare Komponenten sind `None`, nicht künstlich `0`.

### Gewichtung und Entscheidung

Die finale Bewertung kombiniert verfügbare Komponenten mit konfigurierbaren Gewichten. Fehlt eine optionale Komponente, werden die verbleibenden aktiven Gewichte auf 100 Prozent neu normiert.

Beispiel:

```yaml
culling:
  final_component_weights:
    base_score: 0.55
    eye_score: 0.10
    personal_score: 0.20
    family_score: 0.15
  keep_threshold: 0.65
  reject_threshold: 0.35
  auto_keep_min_rating: 2
```

Die Entscheidung lautet:

- `final_score >= keep_threshold`: `keep`
- `final_score <= reject_threshold`: `reject`
- sonst: `review`

Die Serienlogik darf nur moderat korrigieren. Sie darf ein technisch schwaches Bild nicht ohne nachvollziehbaren Grund zu `keep` machen.

## Serienlogik

Ähnliche Aufnahmen eines Batches sollen anhand kleiner Bild-Embeddings oder anderer lokaler Ähnlichkeitsmerkmale gruppiert werden können.

Pro Bild müssen mindestens nachvollziehbar sein:

- Serien-ID,
- Seriengröße,
- Rang innerhalb der Serie,
- Kennzeichnung als Serienbestes,
- Abstand zum Serienbesten.

Das beste Bild einer Serie soll normalerweise `keep` bleiben. Nahe Alternativen können `review`, deutlich schwächere Alternativen `reject` werden. Die Funktion muss abschaltbar bleiben, damit schwache NAS-Systeme oder Sonderfälle nicht blockiert werden.

## Persönlicher Geschmack

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

Richtwerte: `min_active: 50`, `target_active: 75`, `max_active: 100`, `max_not_used: 200`, höchstens zehn neue Vorschläge pro Lauf, höchstens 100 offene Vorschläge und keine neuen Vorschläge bei vollem `not_used/`. Eine spätere optional freigegebene Bereinigung darf nur automatisch erzeugte Kopien nach Aufbewahrungsfrist löschen.

Ein Bild darf nach `new_refs/` kopiert werden, wenn es `keep` ist, die höchste konfigurierbare Sternklasse (standardmäßig fünf Sterne) erreicht, technisch ausreichend gut ist, kein Duplikat darstellt und Stil, Komposition, Motiv, Licht oder Farbstimmung gegenüber der aktiven Auswahl messbar erweitert. Der Nutzer bestätigt ein Sample nur durch manuelles Kopieren nach `reference/`. Nicht angenommene oder verdrängte automatisch erzeugte Kopien können nach `not_used/` verschoben werden; sie trainieren das Modell nicht.


## Bekannte Gesichtserkennung

Die Gesichtserkennung verarbeitet ausschließlich bekannte, manuell gepflegte Personen. Sie liefert ein moderates positives Signal für die Bildbewertung und erzeugt aus klaren Treffern prüfbare Vorschläge zur Verbesserung der Referenzbasis. Unbekannte Gesichter werden nicht gespeichert, nicht geclustert und keiner Person zugeordnet.

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

Ein Crop darf nur für eine bekannte Person erzeugt werden, wenn genau ein Personenmatch eine hohe Konfidenz erreicht, der Abstand zum zweitbesten Match eine Sicherheitsmarge erfüllt, das Gesicht Mindestwerte für Größe, Schärfe und Belichtung erfüllt, das Quellbild `keep` oder Manual Keep ist und kein exaktes oder visuell nahes Duplikat zu `reference/` oder `new_faces/` besteht. Die Backend-unabhängige Konfiguration definiert mindestens Match-Metrik mit Richtung, `min_match_similarity`, `min_best_second_margin`, `require_single_known_match` und `min_face_size_px`; Standardwerte werden als konservative Startwerte dokumentiert und müssen getestet werden. Enthält ein Bild mehrere bekannte Personen, darf je Person höchstens ein Crop entstehen, sofern ihr eigener Treffer alle Grenzen erfüllt. Zusätzliche unbekannte Gesichter werden weder gespeichert noch als Kandidat dokumentiert.

Der Crop wird aus dem JPG mit konfigurierbarem Rand erzeugt und in `new_faces/` abgelegt. Ein lesbarer, kollisionssicherer Dateiname folgt diesem Muster: `YYYY-MM-DD__source-basename__face-01__hash8.jpg`. Die vollständige technische Herkunft steht zentral in `candidates.json`, nicht in vielen Seitendateien. Pro Kandidat werden relativer Quellpfad, voller Quell-Hash, Bounding Box, Crop-Rand, Match- und zweitbester Matchwert, Qualitätswert, Neuheitswert, Gesamtwert, Zeitstempel und Status gespeichert.

`candidate_value` kombiniert standardmäßig Gesichtsqualität (40 Prozent), Diversitätsgewinn gegenüber aktiven Referenzen und offenen Vorschlägen (35 Prozent), Erkennungssicherheit (15 Prozent) und Bildkontext wie Keep/Serienrang (10 Prozent). Nur Kandidaten oberhalb einer konfigurierten Mindestschwelle werden kopiert. Standardlimits: maximal zehn neue Vorschläge je Person und Lauf sowie maximal 100 offene Vorschläge je Person.

Ist `new_faces/` voll, gilt standardmäßig: keine neuen Crops, sichtbarer Status und keine automatische Löschung. Optional kann ein neuer Crop einen schwächeren, automatisch erzeugten Crop nach `not_used/` verdrängen, wenn sein Gesamtwert höher ist; der alte Eintrag erhält in `candidates.json` den Status `superseded`. Alle Vorschläge werden vor einer Modellaktivierung vom Menschen geprüft. Der Nutzer kopiert geeignete Crops manuell nach `reference/`; beim nächsten Start aktualisiert das System Manifest und Modell.

### Score und Metadaten

Ein eindeutiger Treffer darf einen begrenzten `family_score` liefern, ein Bild bei aktivierter Schutzregel von `reject` auf höchstens `review` anheben und Personentags für Metadaten bereitstellen. Er darf technische Mängel nicht vollständig überstimmen und keine neue Identität automatisch aktivieren.


## Metadaten

Culling-Ergebnisse und bekannte Gesichtstreffer sollen optional mit Exiftool in JPG-Metadaten geschrieben werden. Der Workflow bleibt lauffähig, wenn Exiftool fehlt; dann wird ein klarer Status protokolliert.

### Zu schreibende Informationen

- Sternrating aus `final_score` nach konfigurierbaren Bändern.
- Namespaced Keywords, z. B. `workflow:aicull`, `decision:keep`, `series:best`.
- Score-Bänder, nicht zwingend rohe Dezimalwerte.
- Bei bekannten Personen: `person:Kind1`, `family:match`.
- Optional `manualkeep:true` für WhatsApp-/Manual-Keep-Treffer.

Rohscores bleiben primär in `SAVE/culling_scores.csv` und der JSON-Run-Summary. Das verhindert unnötige Metadatenüberladung.

Exiftool muss ausschließlich über argumentbasierte Aufrufe mit `shell=False` gestartet werden.

## WhatsApp Manual Keep

Über WhatsApp vorab ausgewählte Bilder liegen oft in kleinerer Auflösung vor. Sie sind trotzdem eine explizite menschliche Vorauswahl und sollen den passenden Originalbildern im aktuellen Batch zugeordnet werden.

### Ordner und Ablauf

```text
MANUALKEEP/
  inbox/   # neue WhatsApp-/manuell ausgewählte JPGs
  used/    # erfolgreich zugeordnete Dateien
```

Während Phase 1:

1. Alle passenden Bilddateien aus `MANUALKEEP/inbox` werden gelesen.
2. Für jede Datei wird mit derselben leichten visuellen Ähnlichkeitslogik wie bei der Serienerkennung ein Kandidat im aktuellen Batch gesucht.
3. Es wird ausschließlich im aktuell verarbeiteten Batch zugeordnet, wenn die konfigurierte Ähnlichkeitsschwelle erreicht ist und der beste Treffer ausreichend Abstand zum zweitbesten Treffer hat. Die verbindliche Standardmetrik ist `cosine_similarity` im Bereich 0 bis 1; höhere Werte bedeuten größere Ähnlichkeit. Ein Treffer verlangt `similarity >= 0.95` und `best_similarity - second_best_similarity >= 0.03`. Eine andere Metrik ist nur zulässig, wenn ihre Vergleichsrichtung, ihr Wertebereich, eine äquivalente Standardgrenze und die Sicherheitsmarge vollständig konfiguriert und dokumentiert sind.
4. Der zugeordnete Original-JPG-Kandidat erhält zwingend `keep` und den Grund `manual_keep_match`.
5. Der Kandidat durchläuft weiterhin normales Scoring, Serienanalyse und Metadatenschreiben.
6. Nach erfolgreicher eindeutiger Zuordnung wird die kleinere WhatsApp-Datei nach `MANUALKEEP/used` verschoben.
7. Nicht lesbare, mehrdeutige oder nicht zuordenbare Dateien bleiben in `inbox`; sie werden geloggt und in der Run-Summary gezählt.

Ein konfigurierter Dateinamenmarker wie `whatsappmanualkeep` darf zusätzlich unterstützt werden, ersetzt aber nicht die sichere visuelle Zuordnung über `inbox` und `used`.



## Datenverträge und Schema-Versionen

Steuerdateien sind verbindliche Datenverträge zwischen Workflow-Schritten. Dazu gehören `selection.json`, `candidates.json`, `runtime/state/<batch-id>.json` und die JSON-Run-Summary. Jede dieser Dateien enthält mindestens `schema_version`, `created_at`, `updated_at`, `producer_version` und eine stabile Kennung ihres Geltungsbereichs (Personen-Slug, `samples`, Batch-ID oder Run-ID).

Vor jeder Nutzung wird eine Steuerdatei gegen ihre bekannte Schema-Version und Pflichtfelder validiert. Eine unbekannte zukünftige, ungültige oder unlesbare Datei wird niemals still überschrieben: Sie wird mit Grund, Zeitstempel und Hash nach `runtime/quarantine/` kopiert, in Log und Run-Summary als blockierend ausgewiesen und erfordert eine sichere Neuerstellung oder menschliche Prüfung.

Jeder Schreibvorgang folgt derselben Reihenfolge: Inhalt erzeugen, gegen das Schema validieren, in eine temporäre Datei schreiben, temporäre Datei erneut einlesen und validieren, dann auf demselben Dateisystem atomar ersetzen. Die vorherige gültige Version bleibt bis zum erfolgreichen Ersetzen erhalten.

`selection.json` enthält zusätzlich Pool-Fingerprint, Modellkennung, Algorithmusversion und zu jeder verwalteten Datei mindestens relativen Pfad, Herkunft, Status, Auswahlwert und Auswahlgrund. `candidates.json` enthält pro Vorschlag mindestens Quellpfad, Quell-Hash, Status, Qualitäts-, Neuheits- und Konfidenzwerte, Dedupe-Bezug und Zeitstempel. Die Batch-Zustandsdatei enthält die im Wiederaufnahmeabschnitt beschriebenen Fortschritts- und Integritätsdaten. Die Run-Summary enthält Run-ID, Batch-ID, wirksamen Konfigurationsfingerprint, angeforderten und tatsächlich verwendeten Automatikmodus, Ergebnisstatus sowie priorisierte `user_actions_required`. Zusätzlich enthält jeder manuell freigegebene Batch ein unveränderliches `review_decision_record.json` nach dem in „Kalibrierung und lernende Gewichtung“ definierten Schema. Dieses Batch-Artefakt ist die fachliche Quelle für menschliche Endentscheidungen; ein globaler Trainingsindex ist daraus lediglich ableitbar und darf jederzeit neu aufgebaut werden.

Eine Datei ist nur dann automatisch verwaltbar, wenn ihr Manifest `origin: generated` und einen vollständigen Quell-Hash enthält. Fehlen Herkunft oder Hash, wird sie konservativ als `origin: manual` beziehungsweise `manual_protected` behandelt; automatische Verschiebung oder Löschung ist dann verboten.


## Task Scheduler, Docker und Wiederaufnahme

Der Betrieb über Synology Task Scheduler und Docker ist voll unterstützt. Der Scheduler startet den Container mit persistentem NAS-Mount und einem eindeutig dokumentierten Befehl; der Container beendet sich nach einem Lauf kontrolliert. Alle Zustände liegen auf dem NAS, nicht im beschreibbaren Container-Dateisystem.

Pro Batch existiert genau eine zentrale, atomar geschriebene Zustandsdatei unter `runtime/state/<batch-id>.json`. Eine zentrale Datei für alle Batches wird nicht verwendet, weil unabhängige Batch-Zustände dadurch unnötig gekoppelt und schwerer wiederherstellbar wären. Die Batch-ID lautet `<source-folder-name>__<fingerprint8>`, beispielsweise `2026-07-24__a1b2c3d4`; sie bleibt bei Wechsel von `temp_sd` zu `temp_images` und `temp_done` unverändert und verhindert Kollisionen mehrerer Importe desselben Tages.

Sie enthält mindestens Batch-ID, ursprünglichen Ordnernamen, relativen aktuellen Batch-Pfad, vollständigen Quellfingerprint, Phase, Status (`pending`, `running`, `paused`, `completed`, `failed`), Start- und Aktualisierungszeit, Konfigurations-Fingerprint, abgeschlossene Schritte, aktuellen Schritt, Fortschrittszeiger für lange Bildverarbeitung, Zähler, Fehler und Pausen-/Abbruchgrund. Sie wird über temporäre Datei und atomisches `os.replace` aktualisiert. Ungültige Zustandsdateien werden quarantänisiert und verhindern eine unkontrollierte Wiederaufnahme.

Bei jedem Start prüft der Workflow Lock und Zustände zuerst. Er setzt den ältesten pausierten oder unterbrochenen Batch vor neuen `temp_sd`-Batches fort. Bereits bestätigte atomare Schritte werden nicht wiederholt; unvollständige Schritte werden anhand temporärer Artefakte, Marker und Integritätsprüfungen sicher fortgesetzt oder neu ausgeführt. Nur vollständig erfolgreiche Phase 1 darf nach `temp_images` beziehungsweise im expliziten Automatikmodus nach `temp_done` übergehen. Alle Dateioperationen sind idempotent: Crop-Erzeugung, Metadaten, Archivierung und Verschiebung prüfen vor Wiederholung Zielartefakt, Herkunft, Hash, Größe und Marker. Bei Quelle und Ziel zugleich oder bei fehlenden erwarteten Artefakten wird nicht geraten, sondern geprüft und bei Widerspruch quarantänisiert. Ein `completed`-Status ist erst zulässig, wenn alle erwarteten Artefakte und Integritätsprüfungen erfolgreich sind.

```yaml
workflow:
  # Anzahl vollständiger neuer oder fortzusetzender Batches je Phase und Lauf.
  # 1 ist der sichere Standard; 0 verarbeitet alle gültigen Batches.
  batch_limit: 1
  # Reihenfolge der Batch-Auswahl; nur oldest_first ist zulässig.
  batch_sort: oldest_first
  # Maximale Laufzeit in Stunden; vor einem neuen teuren Teilschritt prüfen.
  max_run_hours: 10
  # Setzt pausierte Batches vor neuen Eingängen fort.
  resume_incomplete_batches: true
```

Nach Ablauf des Zeitbudgets wird kein neuer teurer Schritt gestartet. Der laufende sichere Teilschritt wird abgeschlossen, der Status `paused` mit Grund `time_budget_exceeded` atomar gespeichert und der Container kontrolliert beendet. Bei `SIGTERM` gilt dieselbe Regel. Ein harter Abbruch darf keine stillen Löschungen oder einen erfolgreichen Phasenmarker erzeugen. Der nächste Scheduler-Lauf setzt an der dokumentierten Stelle fort.



## Kalibrierung und lernende Gewichtung

Die transparenten, konfigurierten Komponentengewichte bleiben die verbindliche Ausgangslogik. Ein lernendes Modell ersetzt weder die Berechnung von Schärfe, Ästhetik, Belichtung, persönlichem Score, Familien-Score, Serienrang und Duplikatnähe noch die Hard-Safety-Regeln. Es lernt ausschließlich aus bestätigten menschlichen Endentscheidungen, ob und in welchem begrenzten Umfang diese bereits vorhandenen Merkmale für diesen Nutzer anders kombiniert werden sollten.

### Datenablage: Batch-Record und globaler Index

Für jeden nach manueller Sichtung nach `TEMP_DONE` verschobenen Batch erzeugt Phase 2 vor jeder ARW-Archivierung oder -Bereinigung ein atomar geschriebenes, validiertes und danach unveränderliches Batch-Record. Empfohlener Pfad ist `runtime/calibration/batches/<batch-id>/review_decision_record.json`; alternativ kann es als eindeutig benannte Steuerdatei im Batch verbleiben, solange es nicht mit den zu archivierenden Bilddaten vermischt wird. Es enthält nur relative Pfade, stabile Bild-Hashes, Merkmale, Vorhersage, menschliche Endentscheidung, Modell- und Konfigurationsfingerprint sowie Zeitstempel – niemals private Bilddateien.

Ein einzelnes Record pro Batch ist die primäre Wahrheit: Es bleibt beim fachlichen Kontext, ist leicht zu prüfen, lässt sich bei Unterbrechung idempotent fortsetzen und kann aus Backup oder Archiv gezielt wiederhergestellt werden. Eine einzige globale, fortlaufend beschreibbare Trainingsdatei wäre einfacher abzufragen, ist aber bei Teilkorruption, parallelen Läufen, Modellwechseln und einer späteren Korrektur schwerer nachvollziehbar. Deshalb ist sie nicht die Wahrheit.

Aus den validen Batch-Records erzeugt oder aktualisiert der Workflow optional `runtime/calibration/decision_index.jsonl` sowie eine aggregierte `calibration_summary.json`. Diese globalen Dateien sind leistungsoptimierte, reproduzierbare Indizes und Statistiken, keine irreversiblen Originaldaten: Sie müssen bei fehlendem, beschädigtem oder veraltetem Zustand vollständig aus allen Batch-Records neu gebaut werden können. Sie enthalten ebenfalls keine Bilddateien und gehören wegen ihrer privaten Entscheidungs- und Hashdaten nicht in Git; Git enthält nur Schema, Beispiel ohne echte Daten und Konfiguration.

### Record-Inhalt und manueller Übergabepunkt

Phase 1 speichert im Batch-Status und in `SAVE/culling_scores.csv` je Bild die Merkmale, die regelbasierte Vorhersage, Teilwerte, finale Punktzahl, Modellversion und Konfigurationsfingerprint. Der Ordner kann anschließend beliebig lange in `TEMP_IMAGES` liegen. Der manuelle Umzug nach `TEMP_DONE` bleibt der einzige Freigabeschritt und signalisiert, dass der aktuelle JPG-/Metadatenzustand die menschliche Endentscheidung darstellt.

Beim ersten Phase-2-Lauf für einen manuell übergebenen Batch liest das System die eingefrorene Phase-1-Prognose und den aktuellen finalen Zustand aus. Es schreibt zuerst den validierten `review_decision_record.json`, aktualisiert danach atomar den ableitbaren Index und die Kalibrierungsstatistik und beginnt erst dann mit dem ARW-Archiv und der aktiven-JPG-Regel. Fehlt eine Phase-1-Grundlage, passen Fingerprints nicht zusammen oder ist der finale Zustand nicht eindeutig lesbar, wird der Batch mit `review_state_invalid` blockiert; Phase 2 darf keine ARWs verändern.

Jeder Bildeintrag enthält mindestens `image_id` als vollständigen Hash, relativen Pfad zum Phase-1-Zeitpunkt, `predicted_decision`, `final_decision`, `correction_type`, normierte Feature-Werte, `final_score`, Modellversion, Konfigurationsfingerprint und `reviewed_at`. Zulässige Korrekturtypen sind `confirmed`, `promoted`, `demoted` und `manual_keep`. Ein automatischer Übergang nach `TEMP_DONE` erhält `handoff_source: automatic`; er erzeugt keinen menschlichen Trainingsdatensatz und darf keine eigene Vorhersage als Label speichern.

### Kennzahlen und Empfehlung

Nach jedem Lauf berechnet und berichtet der Workflow für den aktiven Konfigurations- und Modellfingerprint eine Modellkonfidenz pro Bild sowie historische Kalibrierungskennzahlen. Modellkonfidenz beschreibt nur die Sicherheit einer einzelnen Vorhersage. Die Automatikempfehlung stützt sich dagegen auf manuell bestätigte historische Daten im gleitenden Auswertungsfenster.

Die terminale Übereinstimmung ist der Anteil bestätigter direkter `keep`- und `reject`-Entscheidungen an allen direkten `keep`-/`reject`-Vorhersagen. `review` wird separat ausgewiesen; seine spätere manuelle Auflösung ist kein Sicherheitsfehler, sondern der vorgesehene Unsicherheitsweg. Zusätzlich sind Gesamtübereinstimmung, `reject_to_keep_rate`, `reject_to_review_rate`, `keep_to_reject_rate`, Review-Rate und Trend gegenüber dem vorherigen Fenster auszugeben. `reject -> keep` ist kritisch, weil ein gewünschtes Bild sonst als nicht aktiv gelten und eine spätere ARW-Bereinigung falsch beeinflussen könnte.

Das System gibt eine Empfehlung ab, schaltet aber niemals selbst einen Automatikmodus ein. Die Statuswerte sind `collecting`, `learning`, `promising`, `eligible_conservative`, `eligible_automatic_phase2` und `not_eligible`; jeder Status enthält eine konkrete Begründung und nächste Aktion. Änderungen an Gewichten, Schwellen, Feature-Logik, Referenzbasis oder Modellversion erzeugen einen neuen Kalibrierungsbereich; Daten verschiedener Fingerprints werden nicht still gemischt.

### Lernmodell und Transparenz

Nach einer ausreichenden Zahl bestätigter Entscheidungen kann ein schlankes CPU-taugliches Kandidatenmodell trainiert werden, beispielsweise eine regularisierte logistische Regression oder ein begrenztes Gradient-Boosting-Modell. Es verwendet nur die gespeicherten Merkmale und Labels; ein großes Bildmodell wird auf der NAS nicht neu trainiert. Die vorhandenen 0–5-Sterne-Bewertungen können zusätzlich als persönliche, geordnete Präferenzdaten für `personal_score` dienen, werden aber nicht mit den Keep/Review/Reject-Labels verwechselt.

In der ersten Lernstufe darf das Kandidatenmodell nur globale, begrenzte Gewichtsänderungen vorschlagen. Die YAML-Basisgewichte bleiben sichtbar, unverändert und referenzierbar. Der Report zeigt Basisgewichte, vorgeschlagene Gewichte, Testmetrik, kritische Fehler und Feature-Beiträge; die Gewichte dürfen nur innerhalb konfigurierter Min-/Max-Werte liegen. Hard-Safety-Regeln bleiben unveränderlich: Manual Keep erzwingt `keep`, technische Mindestschutzregeln bleiben aktiv und ein Gesichtstreffer darf keine Sicherheitsgrenze überstimmen.

Neue Modelle werden ausschließlich als `candidate` im Schattenmodus trainiert. Das aktive Regelmodell trifft weiterhin die sichtbare Entscheidung; beide Varianten werden auf zeitlich oder batchweise getrennten, nicht zum Training verwendeten bestätigten Records verglichen. Ein Kandidat darf nur nach bewusster Nutzerfreigabe aktiv werden, wenn er die terminale Übereinstimmung mindestens erreicht oder verbessert und bei `reject_to_keep_rate` nicht schlechter ist. Aktive, Kandidaten- und historische Modelle werden mit Trainingsfenster, Datenfingerprint, Metriken und Konfiguration versioniert; ein Rollback auf das letzte aktive Modell muss ohne Neubewertung möglich sein.

### Konfigurationsvorschlag

```yaml
calibration:
  enabled: true
  records_root: runtime/calibration/batches
  derived_index: runtime/calibration/decision_index.jsonl
  minimum_reviewed_batches: 3
  minimum_reviewed_images: 300
  evaluation_window:
    reviewed_batches: 10
    reviewed_images: 1000
  min_terminal_decision_agreement: 0.90
  max_reject_to_keep_rate: 0.00
  max_reject_to_review_rate: 0.01
  max_review_rate_warning: 0.35
  require_same_config_fingerprint: true
  learned_model:
    enabled: false
    mode: shadow
    min_weight: 0.05
    max_weight: 0.60
    base_score_min_weight: 0.20
    family_score_max_weight: 0.25
    activation_requires_user_approval: true
```

Die 90-Prozent-Grenze ist eine Mindesthürde für direkte terminale Entscheidungen, keine Freigabe allein. Für `eligible_automatic_phase2` müssen mindestens drei repräsentative manuell geprüfte Batches und 300 Bilder im kompatiblen Fenster vorliegen, die terminale Übereinstimmung mindestens 90 Prozent betragen, `reject_to_keep_rate` bei 0 Prozent liegen und keine blockierende technische Störung vorhanden sein. Die Empfehlung `eligible_conservative` kann zuvor ausgegeben werden, wenn die Datenlage gut ist, aber die umfassendere Stabilitätsbeobachtung noch fehlt.

### Modi und Rückfall

`automatic_phase2_conservative` ist die empfohlene Zwischenstufe. Eindeutige Keep-Bilder bleiben aktiv; Review-Bilder bleiben ebenfalls aktiv und werden nicht als Ausschluss behandelt; Reject-Bilder werden als nicht aktiv markiert und sicher archiviert beziehungsweise nach der bestehenden `_Rejected/`-Semantik geführt, ohne dass eine irreversible neue Löschregel aus dem Kalibrierungsfeature entsteht. In `automatic_phase2` darf Phase 1 nach erfolgreicher Bewertung direkt nach `TEMP_DONE` übergeben. Solche automatischen Batches werden technisch abgeschlossen, liefern jedoch keine neuen Trainingslabels.

Sinkt eine relevante Kennzahl im aktiven Fenster unter die konfigurierten Grenzen, tritt ein kritischer Fehler auf oder ändert sich der Fingerprint, meldet der Workflow `not_eligible` und empfiehlt `assisted_review`. Ein bereits konfigurierter Automatikmodus wird nicht still geändert; der Lauf blockiert die riskante automatische Übergabe und verlangt eine bewusste Konfigurationsentscheidung des Nutzers.

## Konsolidierte Bestandskompatibilität und technische Defaults

Dieser Abschnitt harmonisiert die übernommene Bestandsbeschreibung mit den v6-Erweiterungen. Bei abweichenden früheren Beispielen in diesem Dokument gilt dieser Abschnitt vorrangig. Er ist kein optionaler Entwurf, sondern der verbindliche Kompatibilitäts- und Benennungsvertrag.

### Ordner, Namen und Reihenfolge

Der produktive Ablauf lautet unverändert `TEMP_SD -> TEMP_IMAGES -> TEMP_DONE`. `TEMP_IMAGES` ist ein Review-Bereich ohne Ablaufzeit; ein Batch darf dort Tage oder Wochen verbleiben. Nur der bewusste manuelle Umzug nach `TEMP_DONE` ist das Freigabesignal für menschlich geprüfte Batches. Die Unterordner je Batch heißen verbindlich `ARW/`, `SAVE/`, `_Review/` und `_Rejected/`. Nur JPGs im Batch-Hauptordner sind aktiv; ein manuell aus `_Review/` oder `_Rejected/` zurückgeholtes JPG ist dadurch ohne weitere Metadatenaktion aktiv und sein passendes ARW bleibt geschützt.

Phase 1 führt zwingend in dieser Reihenfolge aus: (1) Stabilitäts-, Namens-, Lock- und Symlink-Prüfung; (2) Datumsnormalisierung; (3) Verschieben der ARWs nach `ARW/`; (4) validiertes Original-JPG-Archiv; (5) Feature-Ermittlung, Score, Manual Keep und begrenzte Serienkorrektur; (6) eingebettete Metadaten, CSV und Phase-1-Manifest; (7) Ablage der JPGs in Hauptordner, `_Review/` oder `_Rejected/`; (8) atomare Übergabe nach `TEMP_IMAGES`.

Phase 2 validiert für einen manuell freigegebenen Batch zuerst die Endentscheidungen und schreibt Kalibrierungsrecord und abgeleitete Statistik. Danach erstellt sie aus den entbehrlichen ARWs ein geprüftes Archiv, aktiviert es atomar und protokolliert dessen Hash. Erst dann löscht sie die ARWs, die nach aktiver-JPG-Regel nicht erhalten bleiben. Nach einer erfolgreichen, vollständig dokumentierten Bereinigung wird `ARW/` entfernt. Die Endbehandlung ist damit verbindlich: **Löschen nach validiertem Archiv**, ohne stillen Quarantänepfad.

### Legacy-Datum und ZIP-Namen

```yaml
workflow:
  date_reconstruction:
    mode: legacy_bash # legacy_bash | full_year
    decade_prefix: "202"
    year_digit_index: 3
```

`legacy_bash` rekonstruiert das Jahr aus dem historischen Kameraordnerformat mit `decade_prefix` und `year_digit_index`; `full_year` akzeptiert ausschließlich echte Namen im Format `YYYYMMDD`. Ungültige, mehrdeutige oder nicht kalendergültige Namen werden blockiert. Die konkreten Artefaktnamen sind `SAVE/<batch>_ALL_JPG.zip` und `SAVE/<batch>_SORT_ARW.zip`. Bestehende Zielnamen werden niemals überschrieben: Der erste freie Kollisionsname lautet `<stem>_EXTRA_<n>.zip`, beginnend mit 1. Klassifikation, Kollisionsgrund, Quelle und endgültiges Ziel erscheinen in Log, Run-Summary und `zip_conflicts`.

### Scoring, Sterne und Serien

`base_score`, `eye_score`, `personal_score` und `family_score` sind die einzigen finalen Standardkomponenten. Alle liegen in [0,1] oder sind `null`; verfügbare Gewichte werden proportional auf 1,0 renormiert. `eye_score` ist ausdrücklich ein separater Baustein und darf nicht zugleich Bestandteil von `base_score` sein.

```yaml
culling:
  auto_keep_min_rating: 2
  keep_threshold: 0.65
  reject_threshold: 0.35
  final_component_weights:
    base_score: 0.55
    eye_score: 0.10
    personal_score: 0.20
    family_score: 0.15
  base_weights:
    sharpness: 0.35
    aesthetic: 0.35
    exposure: 0.20
    reference_score: 0.10
  star_rating_bands:
    - {min: 0.00, max: 0.19, rating: 0}
    - {min: 0.20, max: 0.39, rating: 1}
    - {min: 0.40, max: 0.59, rating: 2}
    - {min: 0.60, max: 0.74, rating: 3}
    - {min: 0.75, max: 0.89, rating: 4}
    - {min: 0.90, max: 1.00, rating: 5}
```

`auto_keep_min_rating: 2` ist eine konservative Phase-1-Anzeige- und Vorauswahlgrenze, nicht die finale Keep-Regel und kein Phase-2-Filter. Der Score erzeugt zunächst `score_decision`; die Serienlogik darf das Serienbestbild höchstens um eine Klasse verbessern und andere Serienbilder nur nach dokumentierter Distanz zu `review` oder `reject` abwerten. `final_decision` ist danach die operative Phase-1-Entscheidung; die menschliche Phase-2-Endentscheidung folgt ausschließlich dem Ordnerprotokoll des technischen Implementierungsvertrags.

### CSV und eingebettete Metadaten

Der verbindliche Dateiname lautet `SAVE/culling_scores.csv` (Unterstrich, nicht `cullingscores.csv`). Er enthält mindestens `image_id`, `relative_path`, `base_score`, `eye_score`, `personal_score`, `family_score`, `final_score`, `star_rating`, `score_decision`, `final_decision`, `decision_reason`, `series_id`, `series_size`, `series_rank`, `series_best`, `series_margin_to_best`, `model_version` und `config_fingerprint`. Bestehende Leselogik darf den historischen Namen `cullingscores.csv` als Importalias akzeptieren, schreibt aber ausschließlich den neuen Namen.

Der Normalweg ist eingebettetes Schreiben in JPG per `exiftool`, nicht XMP-Sidecars. Vor dem Schreiben wird die Quelldatei geprüft; nach dem Schreiben liest der Workflow die gesetzten Tags zurück. Fehlgeschlagene Validierung blockiert den Metadatenabschluss und wird in Log und Summary gemeldet, ohne die Bilddatei als erfolgreich zu markieren. Sidecars sind nur ein explizit aktivierter Recovery-Fallback und dürfen nicht unbemerkt entstehen.

Neu geschriebene Keywords verwenden ausschließlich: `workflow:ai_cull`, `workflow:model:<model-id>`, `decision:predicted:<keep|review|reject>`, `decision:final:<keep|review|reject>`, `series:id:<series-id>`, `series:role:<best|member>`, `family:match:<true|false>`, `person:<personen-slug>`, `score_band:final:<0..5>` und `whatsapp:manual_keep`. Alte Großschreibungs-Tags werden nur lesend als Migrationsalias unterstützt.

### Persönliche und Familienmodelle

Ein gemeinsamer Sample-Ordner darf Referenz- und persönlichen Score speisen. Änderungen an Bildhash, Konfiguration oder Modellversion lösen über einen Quellen-Fingerprint den Rebuild des persistierten Referenzprofils aus. `cache_enabled`, `cache_dir` und `force_cache_rebuild` sind Pflichtfelder; der Status `cache_used` oder `cache_rebuilt` wird in Log, Summary und Scheduler-Kurzmeldung ausgegeben.

Die verbindliche erste Familienimplementierung ist ein lokales Python-Backend `opencv_yunet_sface`: `opencv-contrib-python-headless`, YuNet für Detektion, SFace für Embeddings, persistenter Embedding-Cache und Cosine Similarity. Modellpfade, SHA-256 der ONNX-Dateien, Backendversion und Matchmetrik gehören in Konfiguration und Cache-Fingerprint. `match_threshold` bleibt vor dem ersten NAS-Referenztest zwingend konfigurierbar und nicht fest vorgegeben; ein früherer Toleranzwert von 0,55 ist wegen möglicher abweichender Metrik nur Importmigrationswert. Ein eindeutiger bekannter Match darf bei aktiviertem Schutz `reject` höchstens in `review` überführen. Unbekannte Gesichter werden weder als bekannte Person noch als Trainingsreferenz aktiviert.

```yaml
family_recognition:
  enabled: false
  backend: opencv_yunet_sface
  detector_model: models/faces/face_detection_yunet.onnx
  recognizer_model: models/faces/face_recognition_sface.onnx
  similarity_metric: cosine_similarity
  match_threshold: null # Vor NAS-Referenztest setzen
  protect_detected_family: true
  cache_dir: models/family_faces
```

### Bash, Scheduler und Persistenz

Das Bash-Skript bleibt ausschließlich Notfall-Rückfallebene und wird nicht erweitert, migriert oder als Recovery-Werkzeug für teilweise verarbeitete Python-Batches verwendet. Es gehört nicht zur aktiven Projektausführung, darf Python-Artefakte nicht interpretieren und wird nur nach bewusster manueller Entscheidung außerhalb eines Python-Teilzustands verwendet.

Der DSM Task Scheduler startet den Python-/Docker-Workflow. `stdout` enthält Startblock, Warnungen/Blocker und Abschlussblock mit Startzeit, Version, Pfaden, gefundenen, verarbeiteten, übersprungenen und fehlerhaften Batches, Move-/Merge-Zählern, Logpfad und Kalibrierungsstatus. Die vollständige JSON-Historie liegt persistent unter `_workflow_data/run_summaries/`; Konfiguration, Zustände, Kalibrierung, Modelle und Logs liegen ebenfalls auf dem NAS-Mount. `config-debug-local.yaml` ist nur eine versionskontrollierte lokale Beispielkonfiguration ohne Produktionspfade oder Geheimnisse.

## Technischer Implementierungsvertrag: Kalibrierung

Dieser Abschnitt präzisiert „Kalibrierung und lernende Gewichtung“ als deterministische Implementierungsvorgabe. Bei Widerspruch haben die Sicherheits- und Datenvertragsregeln dieser Spezifikation Vorrang. Die Implementierung darf keine privaten Bilddateien, Vorschaubilder oder absoluten NAS-Pfade in Kalibrierungsartefakte schreiben.

### Begriffe, IDs und Zustandsautomat

`batch_id` ist unveränderlich und entspricht der bestehenden Form `<source-folder-name>__<fingerprint8>`. `image_id` ist der vollständige SHA-256-Hash der JPG-Datei zum Ende von Phase 1. Der relative, normalisierte POSIX-Pfad ist nur ein zusätzliches Diagnosefeld; Pfade außerhalb des Batch-Wurzelordners sind ungültig. Jede Entscheidung ist an `config_fingerprint` und `model_version` der Phase 1 gebunden.

Der Batch-Zustand folgt zwingend diesem Ablauf: `phase1_completed` in `TEMP_IMAGES` -> manueller Move nach `TEMP_DONE` -> `review_comparison_pending` -> `review_record_committed` -> `calibration_index_committed` -> `phase2_archiving` -> `phase2_completed`. Bei einem automatisch übergebenen Batch lautet der Übergang `phase1_completed` -> `automatic_handoff` -> `phase2_archiving` -> `phase2_completed`; die Zwischenzustände für Review-Record und Kalibrierungsindex entfallen. Jeder Übergang wird atomar in `runtime/state/<batch-id>.json` persistiert und ist nur vorwärts zulässig.

### Verbindliches Endentscheidungsprotokoll

Phase 2 ermittelt `final_decision` je Phase-1-Bild in dieser Reihenfolge. Sie verwendet dabei nur die im Batch vorgefundenen JPGs, deren Sidecars/Metadaten und die konfigurierten Ordnernamen; eine Nachberechnung von Scores oder Modellvorhersagen ist verboten.

1. Ein valides, eindeutig zugeordnetes Manual-Keep-Signal erzwingt `keep`.
2. Ein Bild im konfigurierten `_Rejected/`-Unterordner ergibt `reject`.
3. Ein Bild im konfigurierten `_Review/`-Unterordner ergibt `review`.
4. Ein Bild im Batch-Hauptordner ergibt immer `keep`, unabhängig von Sternrating, Score oder vorheriger Vorhersage.
5. Fehlt das Bild, ist der Hash nicht eindeutig, widersprechen sich Ordnerzustand und Manual Keep oder liegen mehrere wirksame Bildkopien vor, ist der Batch ungültig.

Die Reihenfolge ist absichtlich: Manual Keep überstimmt jede andere Entscheidung; `_Rejected/` und `_Review/` sind sichtbare manuelle Entscheidungen; der Hauptordner ist die abschließende menschliche Keep-Entscheidung. `auto_keep_min_rating` gilt ausschließlich für die automatische Phase-1-Vorauswahl und wird in Phase 2 niemals zur Aberkennung eines manuell im Hauptordner liegenden Bildes verwendet. Ein ungültiger Fall setzt den gesamten Batch auf `review_state_invalid`, erzeugt keinen Review-Record und blockiert jede Phase-2-ARW-Aktion. Das System meldet Bild-ID, relative Pfade und Konfliktgrund, aber nie Bildinhalte in stdout.

### JSON-Verträge

Alle JSON-Artefakte verwenden UTF-8, ISO-8601-Zeitstempel in UTC mit `Z`, `schema_version` als positive Ganzzahl und atomisches Schreiben gemäß Datenvertragskapitel. Zusätzliche Felder sind nur erlaubt, wenn sie keine Bedeutung bestehender Felder verändern. Ein unbekanntes `schema_version` oder unbekannter Enum-Wert ist blockierend.

```json
{
  "schema_version": 1,
  "record_id": "batch-id__review-v1",
  "batch_id": "2026-07-24__a1b2c3d4",
  "handoff_source": "manual_review",
  "phase1_completed_at": "2026-07-24T19:00:00Z",
  "reviewed_at": "2026-07-25T10:15:00Z",
  "config_fingerprint": "sha256:<64-hex>",
  "model_version": "rule-v1",
  "images": [{
    "image_id": "sha256:<64-hex>",
    "phase1_relative_path": "DSC00001.JPG",
    "predicted_decision": "review",
    "predicted_probabilities": {"keep": 0.41, "review": 0.47, "reject": 0.12},
    "final_decision": "keep",
    "correction_type": "promoted",
    "final_score": 0.58,
    "features": {"base_score": 0.61, "personal_score": 0.74, "family_score": null, "series_rank": 1, "duplicate_distance": 0.31},
    "final_decision_source": "main_folder_rating",
    "final_relative_path": "DSC00001.JPG"
  }],
  "counts": {"keep": 1, "review": 0, "reject": 0},
  "integrity": {"phase1_manifest_hash": "sha256:<64-hex>", "record_hash": "sha256:<64-hex>"}
}
```

`predicted_decision` und `final_decision` sind ausschließlich `keep`, `review` oder `reject`. `handoff_source` ist ausschließlich `manual_review` oder `automatic`. `correction_type` wird deterministisch abgeleitet: gleiche Entscheidung `confirmed`; `review -> keep` oder `reject -> keep` `promoted`; `keep -> review`, `keep -> reject` oder `reject -> review` `demoted`; Manual-Keep-Vorrang `manual_keep`. Alle numerischen Scores liegen in [0,1], mit Ausnahme von ganzzahligem `series_rank`; nicht verfügbare Features sind `null`.

`calibration_summary.json` enthält mindestens Schema-Version, Erstellungszeit, aktiven Fingerprint, Record-Anzahl, Bildanzahl, Auswertungsfenster, alle Kennzahlen, Status, Empfehlung, Gründe, nächste Aktion und Hash der verwendeten Record-IDs. `decision_index.jsonl` enthält pro Zeile genau einen normalisierten Bilddatensatz plus `record_id`; ein Eintrag ist erst gültig, wenn sein referenzierter Batch-Record validiert ist.

### Transaktion, Wiederaufnahme und Korrektur

Für einen manuellen Batch ist die Reihenfolge zwingend: Phase-1-Manifest validieren -> alle Endentscheidungen vollständig ermitteln -> Record bauen und validieren -> Record atomar schreiben -> Batch-Zustand `review_record_committed` schreiben -> Index und Summary aus validen Records neu berechnen oder atomar aktualisieren -> Zustand `calibration_index_committed` schreiben -> erst danach Phase 2 ausführen. Ein Absturz vor Record-Commit darf keine ARW-Änderung bewirken. Ein Absturz nach Record-Commit darf denselben Record nicht überschreiben; der nächste Lauf validiert ihn per Hash und setzt bei der nächsten offenen Transaktionsstufe fort.

Ein vorhandener, valider Record mit gleichem `phase1_manifest_hash`, `config_fingerprint` und gleicher Endentscheidung ist idempotent wiederzuverwenden. Weichen diese Werte ab, blockiert der Batch mit `review_record_conflict`; eine stillschweigende Neuberechnung oder Überschreibung ist verboten. Der globale Index und die Summary gelten als Cache: Fehlen sie, sind sie defekt oder stimmen ihre Record-Hashes nicht, werden sie vollständig aus den unveränderlichen Batch-Records neu erzeugt.

Nach erfolgreichem `phase2_completed` ist eine Änderung des Batch nicht Teil des normalen Flows. Korrigiert der Nutzer ausnahmsweise einen abgeschlossenen Batch, muss ein expliziter, privilegierter `reopen-review <batch-id>`-Vorgang den Batch sperren, alte und neue Entscheidung mit Begründung in einem Append-only-Korrekturprotokoll referenzieren, Index/Summary neu bauen und Phase 2 erneut vor Ausführung einer sicheren Fachprüfung unterziehen. Dieser Befehl ist standardmäßig deaktiviert; er darf niemals alte Archive oder gelöschte ARWs still wiederherstellen.

### Kennzahlen und Fensterregeln

Das kompatible Fenster enthält ausschließlich valide manuelle Batch-Records mit exakt demselben `config_fingerprint` und `model_version` wie der aktuelle Auswertungsbereich. Es wird zuerst nach absteigendem `reviewed_at` bis `reviewed_batches` Batches gebildet und anschließend auf die neuesten `reviewed_images` Bildeinträge begrenzt. Durch ein Bildlimit abgeschnittene ältere Batches zählen nicht als vollständige Batches für Mindestanforderungen. Bei weniger Daten umfasst das Fenster alle kompatiblen Records.

Für Bildmengen gilt: `N_all` = alle Einträge, `N_terminal` = Vorhersage `keep` oder `reject`, `N_terminal_correct` = direkte Vorhersage gleich Endentscheidung, `N_rk` = Vorhersage `reject` und Endentscheidung `keep`, `N_rr` = Vorhersage `reject` und Endentscheidung `review`, `N_kr` = Vorhersage `keep` und Endentscheidung `reject`, `N_review_predicted` = Vorhersage `review`. Es gelten:

\[
terminal\_agreement = N_{terminal\_correct} / N_{terminal}
\]

\[
reject\_to\_keep\_rate = N_{rk} / N_{terminal}
\]

\[
reject\_to\_review\_rate = N_{rr} / N_{terminal}
\]

\[
keep\_to\_reject\_rate = N_{kr} / N_{terminal}
\]

\[
review\_rate = N_{review\_predicted} / N_{all}
\]

Die Gesamtübereinstimmung ist die Anzahl aller Einträge mit gleicher Vorhersage und Endentscheidung geteilt durch `N_all`. Ist ein Nenner 0, lautet die jeweilige Rate `null`, nicht 0; eine `null`-Rate erfüllt niemals eine Freigabeschwelle. Der Trend ist `terminal_agreement` des aktuellen Fensters minus des unmittelbar vorherigen, disjunkten Fensters gleicher maximaler Größe; fehlt dieses, lautet Trend `null`.

### Status- und Empfehlungslogik

`collecting` gilt bei weniger als `minimum_reviewed_batches` vollständigen Batches oder weniger als `minimum_reviewed_images` Bildern. `learning` gilt, sobald Mindestmengen vorliegen, aber kein Kandidat oder kein ausreichendes vorheriges Trendfenster vorhanden ist. `promising` gilt bei terminaler Übereinstimmung mindestens der Zielschwelle und bei nicht überschrittenen kritischen Fehlerraten, sofern die Stabilitätsregel für die gewünschte Automatikstufe noch nicht erfüllt ist. `eligible_conservative` gilt bei erfüllten Mindestmengen, terminaler Übereinstimmung mindestens 0,90, `reject_to_keep_rate` exakt 0,0 und keiner blockierenden technischen Störung. `eligible_automatic_phase2` gilt zusätzlich erst bei mindestens 10 vollständigen kompatiblen Batch-Records im Fenster, nicht negativem Trend oder fehlendem Trend bei identischen stabilen Metriken und erfüllten Grenzen für `reject_to_review_rate`.

`not_eligible` gilt bei jeder überschrittenen kritischen Grenze, bei negativem Trend von mehr als 0,03 Punkten, bei Fingerprint-Mischung, ungültigem Record oder blockierender technischer Störung. Die Summary nennt alle zutreffenden Gründe in Prioritätsreihenfolge und genau eine nächste Hauptaktion. Status und Empfehlung sind informativ: Sie verändern `automation.mode` nie selbst. Bei aktiv konfiguriertem `automatic_phase2` und Status `not_eligible` blockiert der Lauf den automatischen Übergabeschritt mit `automation_safety_hold`; bereits in `TEMP_DONE` liegende manuell freigegebene Batches dürfen nach den normalen Sicherheitsprüfungen abgeschlossen werden.

### Lernmodellvertrag

Training ist nur zulässig bei mindestens 500 kompatiblen manuell bestätigten Bildern, mindestens 50 terminalen Beispielen je vorhandener Zielklasse und ohne blockierende Datenqualität. Die erste Implementierung verwendet eine regularisierte multinomiale logistische Regression über die normierten Features; fehlende Werte erhalten je Feature einen fehlend-Indikator und eine im Training bestimmte, persistierte Imputation. Das Verfahren muss deterministisch mit festem Seed laufen und alle Preprocessing-Parameter im Modellartefakt speichern.

Der Split erfolgt batchweise, nicht bildweise: Die neuesten 20 Prozent vollständiger kompatibler Batches, mindestens ein Batch, bilden die Holdout-Prüfmenge; ältere Batches sind Training. Bei weniger als fünf Batches wird nicht trainiert. Damit dürfen Bilder derselben Serie nicht zugleich Training und Prüfung sein. Das Modellartefakt enthält `model_id`, Algorithmus, Seed, Trainings-/Holdout-Record-IDs, Feature-Liste, Imputation, Skalierung, gelernte Koeffizienten, Gewichtungsgrenzen, Kennzahlen, Zeitstempel und Datenfingerprint.

Ein Kandidat liegt unter `models/culling/candidate/<model-id>/`; das aktive Modell unter `models/culling/active/`; unveränderliche frühere Modelle unter `models/culling/history/`. Im Schattenmodus berechnet der Kandidat nur zusätzliche Vorhersage und Feature-Beiträge. Er wird nur zur Aktivierung vorgeschlagen, wenn die Holdout-terminale-Übereinstimmung mindestens die des aktiven Regelmodells erreicht und seine `reject_to_keep_rate` nicht größer ist. Aktivierung erfolgt ausschließlich durch einen expliziten Nutzerbefehl oder eine gleichwertige bestätigte Konfigurationsänderung, erzeugt einen Audit-Eintrag und behält das vorherige Modell für Rollback. Ein Rollback ändert nur den aktiven Modellzeiger; Phase-1-Records bleiben unverändert.

### Verbindliche Testfälle

- Ein Batch bleibt 30 Tage in `TEMP_IMAGES`; sein manueller Move nach `TEMP_DONE` erzeugt denselben validen Record wie ein sofortiger Move.
- Jede der fünf Endentscheidungsprioritäten wird einzeln getestet, einschließlich widersprüchlicher Signale und fehlendem Bild; ungültige Fälle verändern keine ARW-Datei.
- Unterbrechungen vor Record-Commit, nach Record-Commit, nach Index-Commit und während Phase 2 führen bei Wiederaufnahme zu keinem doppelten Record und keiner doppelten ARW-Aktion.
- Löschen oder Beschädigen von Index/Summary erzeugt bei Rebuild identische Kennzahlen aus den Batch-Records; ein defekter Index verändert keinen Record.
- Fenstergrenzen, Nenner 0, Fingerprint-Trennung, Trend und jeder Empfehlungsstatus sind mit festen Datenmengen getestet.
- Automatischer Handoff speichert keinen menschlichen Label-Record; `automation_safety_hold` verhindert den automatischen Handoff bei `not_eligible`.
- Schattenmodell verändert weder sichtbaren Score noch Entscheidung; der batchweise Split trennt Serien-Batches; Aktivierung und Rollback sind auditierbar.

## Kapazität und Automatikstufen

Die Automatik wird stufenweise freigegeben. Ziel ist, wiederholbare technische Arbeit möglichst weit zu automatisieren, ohne Entscheidungen zu automatisieren, die Bildverluste verursachen oder die Qualität von Gesichts- und Geschmacksmodellen dauerhaft verschlechtern könnten. Jede Stufe baut auf den Prüfungen und Protokollen der vorherigen Stufe auf; sie ist konfigurierbar, dokumentiert und muss vor der produktiven Freigabe auf NAS-Testdaten abgenommen werden.

Die Grundregel lautet: Das System darf Bilder analysieren, bewerten, sortieren, Kandidaten erzeugen, doppelte Vorschläge vermeiden, Kapazitäten verwalten und sichere Folgearbeiten ausführen. Ein Mensch bleibt zunächst für die Freigabe von Phase 2 sowie für jede Aufnahme neuer Face- oder Geschmackssamples in `reference/` verantwortlich. Damit ist der tägliche manuelle Aufwand klein und auf Entscheidungen mit langfristiger Wirkung konzentriert.

### Kapazitätsampel

Für `new_faces/`, `new_refs/` und `not_used/` wird je Person beziehungsweise Sample-Pool eine Kapazitätsampel geführt. Sie ist Teil von `selection.json` oder `candidates.json`, Log und Run-Summary und enthält mindestens `active_count`, `pending_count`, `inactive_count`, `limit`, `capacity_status` und `new_candidates_skipped`.

| Status | Belegung | Verhalten | Nutzeraktion |
|---|---|---|---|
| `normal` | Unter 80 Prozent | Vorschläge normal erzeugen und priorisieren | Keine |
| `warning` | 80 bis unter 100 Prozent | Vorschläge weiter erzeugen, Warnung protokollieren | Bei Gelegenheit Vorschläge prüfen |
| `full` | Vorschlagslimit erreicht | Keine neuen Vorschläge für den betroffenen Pool | Vorschläge prüfen, bestätigen oder nach `not_used/` verschieben |
| `blocked` | `not_used/` erreicht sein Limit | Keine Verdrängung und keine neuen Vorschläge | `not_used/` prüfen und bewusst aufräumen oder Limit ändern |

Die Standardregel bleibt nicht-destruktiv: Volle Pools blockieren neue Vorschläge, löschen aber nichts. Eine spätere optionale Bereinigung darf ausschließlich automatisch erzeugte Kopien nach konfigurierter Aufbewahrungsfrist entfernen, muss jede Löschung vorher auditierbar ankündigen und bleibt standardmäßig deaktiviert. Manuell eingebrachte oder als `manual_protected` markierte Dateien dürfen nie automatisch gelöscht werden.

### Stufenübersicht

| Stufe | Betriebsmodus | Automatisch | Manuell | Freigabestatus |
|---|---|---|---|---|
| 1 | `assisted_review` | Phase 1, Scoring, Metadaten, Kandidaten, Reporting | Übergabe nach Phase 2, Bestätigung neuer Referenzen | Standard, `stable` |
| 2 | `automatic_phase2` | Zusätzlich die Übergabe und Ausführung von Phase 2 nach definierten Regeln | Bestätigung neuer Referenzen | Erst nach dokumentierter NAS-Abnahme, `advanced` |
| 3 | `automatic_candidates` | Zusätzlich Priorisierung, Begrenzung und Verschiebung verwalteter Kandidaten | Bestätigung neuer Referenzen | Erst nach dokumentierter NAS-Abnahme, `advanced` |
| 4 | automatische Referenzaktivierung | Optional auch Übernahme besonders sicherer Kandidaten in `reference/` | Kontrolle und Audits | Nur vorbereitet, `experimental`, standardmäßig verboten |

Die Stufen 2 und 3 können gemeinsam oder getrennt freigegeben werden. Ein höherer Modus schaltet keine weiteren Rechte stillschweigend frei: Insbesondere bedeutet eine automatische Phase 2 **nicht**, dass das System Lernreferenzen selbst aktivieren darf.

### Stufe 1: Assisted Review

`assisted_review` ist der verbindliche Startmodus. Der Workflow verarbeitet den ältesten zulässigen Batch aus `TEMP_SD` in Phase 1, bewertet die JPGs, erstellt die vorgesehenen Arbeitsartefakte, erzeugt gegebenenfalls begrenzte Kandidaten in `new_faces/` oder `new_refs/` und übergibt den Batch nach `TEMP_IMAGES`.

Der Nutzer prüft dort nur die Ergebnisse, die eine menschliche Entscheidung benötigen: insbesondere Review-Bilder, auffällige Serien, Fehlklassifikationen oder ein ungewöhnliches Ergebnis in der Run-Summary. Danach verschiebt er den geprüften Ordner nach `TEMP_DONE`. Erst dadurch wird Phase 2 berechtigt, die aktive-JPG-Regel anzuwenden, ARWs zu archivieren und nicht mehr benötigte ARWs im erlaubten Bereich zu bereinigen.

Neue Gesichts- oder Geschmackskandidaten werden parallel sichtbar gesammelt, aber nicht zu einer täglichen Pflichtprüfung. Der Nutzer kann sie bei Bedarf gesammelt sichten und nur geeignete Bilder nach `reference/` kopieren. Das System erkennt diese bewusste Änderung beim nächsten Lauf, aktualisiert Manifest und Modell und dokumentiert den Rebuild.

### Stufe 2: Automatic Phase 2

In `automatic_phase2` darf das System nach vollständig erfolgreicher Phase 1 den Batch selbst nach `TEMP_DONE` übergeben und Phase 2 ausführen. Dies reduziert die tägliche manuelle Arbeit erheblich, weil die Ordnerübergabe entfällt. Voraussetzung ist, dass Culling-Regeln, RAW-Zuordnung, ZIP-Archivierung, Wiederaufnahme und Fehlerbehandlung über einen dokumentierten Zeitraum auf realen NAS-Daten überprüft wurden.

Die Freigabe darf nur erfolgen, wenn kein kritischer Zustand vorliegt: kein pausierter oder fehlgeschlagener Modell-Rebuild, keine beschädigte Zustandsdatei, keine unaufgelöste Dateikollision, kein unvollständiger Eingangsordner und kein nicht behandelter kritischer Fehler im Batch. Tritt einer dieser Fälle auf, bleibt der Batch in einem sicheren Arbeitszustand und benötigt wieder die Behandlung nach den Regeln von `assisted_review`.

Die automatische Phase 2 ändert keine Regeln für Lernreferenzen. `new_faces/` und `new_refs/` bleiben Vorschlagsordner; weder ein hoher Score noch eine hohe Gesichtskonfidenz erlaubt eine automatische Übernahme nach `reference/`.

### Stufe 3: Automatic Candidates

In `automatic_candidates` übernimmt das System zusätzlich die wiederkehrende Verwaltung von Kandidaten. Es darf hochwertige bekannte Face-Crops nach `new_faces/` und hochwertige Geschmacksvorschläge nach `new_refs/` kopieren, sie anhand von Qualität, Dedupe, Erkennungssicherheit und Diversitätsgewinn priorisieren und Kapazitätsgrenzen durchsetzen.

Es darf automatisch erzeugte, verwaltete Dateien zwischen `reference/` und `not_used/` verschieben, wenn die dokumentierte Auswahl einen besseren aktiven Satz ergibt. Jede Aktion muss im Manifest mit Herkunft, altem und neuem Status, Auswahlwert, Begründung und Zeitstempel sichtbar sein. Dateien mit `origin: manual` oder Status `manual_protected` sind von dieser Automatik ausgeschlossen.

Diese Stufe spart vor allem Aufräumarbeit: Der Nutzer sieht in `new_faces/` und `new_refs/` vorrangig Kandidaten mit hohem Mehrwert statt einer unkontrolliert wachsenden Menge ähnlicher Dateien. Sie darf jedoch niemals eine Datei aus einem Vorschlagsordner selbst nach `reference/` aktivieren. Die manuelle Kopierhandlung bleibt die klare und einfache Zustimmung für jedes neue Trainingsbeispiel.

### Stufe 4: Referenzaktivierung

Die automatische Referenz- oder Sample-Aktivierung ist nur als späterer, technisch vorbereiteter Erweiterungspunkt vorgesehen. Sie bleibt standardmäßig deaktiviert und ist nicht Bestandteil der ersten produktiven Betriebsfreigabe. Ihr Zweck wäre ausschließlich, in einem späteren, ausdrücklich abgenommenen Betrieb sehr eindeutige Kandidaten ohne tägliche manuelle Sichtung zu übernehmen.

Vor einer solchen Freigabe müssen mindestens eine lange fehlerfreie Beobachtungsphase, dokumentierte Fehlermessungen, ein Dry-Run ohne Dateioperationen, ein nachvollziehbarer Audit-Export, ein schneller Rollback sowie konservative Konfidenz-, Qualitäts- und Diversitätsschwellen nachgewiesen sein. Auch dann dürfen nur automatisch erzeugte Kandidaten aktiviert werden; manuelle Referenzen bleiben geschützt. Die konkrete Freigabelogik wird erst als eigene, separate Anforderung festgelegt, nicht implizit durch einen Automatikmodus.

### Freigabe und Rückfall

```yaml
automation:
  # Stabilitätsstatus: stable. Manuelle Phase-2-Freigabe bleibt aktiv.
  mode: assisted_review
  # Advanced: Nur nach dokumentierter NAS-Abnahme aktivieren.
  automatic_phase2_enabled: false
  # Advanced: Automatisiert nur Kandidatenverwaltung, nie ihre Aktivierung.
  automatic_candidates_enabled: false
  # Experimental: Für die erste produktive Version verboten.
  automatic_reference_activation: false
  automatic_sample_activation: false
  # Bei kritischem Fehler sicher auf assisted_review zurückfallen.
  rollback_on_error: true
```

Ein kritischer Fehler ist mindestens ein fehlgeschlagener oder pausierter verpflichtender Modell-Rebuild, eine ungültige Zustands-, Auswahl- oder Kandidatendatei, ein nicht auflösbarer Konflikt bei Dateioperationen, eine nicht bestandene Integritätsprüfung oder ein Sicherheitsfehler. Bei aktivierter Rückfallregel stoppt der Workflow den betroffenen Batch kontrolliert, schreibt Status und Begründung in Log und Run-Summary und behandelt nachfolgende Batches wieder nach `assisted_review`. Ein Rückfall darf keine Dateioperation rückgängig machen, die bereits atomar und erfolgreich abgeschlossen wurde; er verhindert nur weitere automatische Übergaben.

Die Run-Summary weist mindestens den angeforderten und tatsächlich wirksamen Automatikmodus, jede automatische Entscheidung, eine Rückfallursache sowie offene Nutzeraktionen aus. Das Handbuch beschreibt dazu einen kurzen Entscheidungsbaum: prüfen, fortsetzen, manuell freigeben oder einen Fehler beheben. So bleibt die spätere Bedienung einfach, obwohl die technische Absicherung umfassend ist.


## Performance für kleine NAS-Systeme

Die Implementierung ist auf kleine NAS-Systeme zu optimieren.

- Bildanalyse nur für JPG/JPEG; ARW wird nicht dekodiert.
- Verarbeitung nach Möglichkeit batchweise und begrenzt durch `batch_limit`.
- Kleine Vorschauen verwenden, z. B. 256 bis 512 Pixel längste Kante für technische Metriken und 32 bis 64 Pixel für Ähnlichkeitsvektoren.
- Referenzprofile, Geschmacksmodell und Face-Referenzmerkmale persistent cachen.
- Cache nur bei Änderung der Eingabebestände neu erzeugen.
- Keine parallele Vollauslastung: konfigurierbare niedrige Worker-Zahl, Standard `1`.
- Speicher begrenzen; Bilder sofort schließen und keine vollständigen Batches im RAM halten.
- Gesichtserkennung nur starten, wenn aktiviert und Referenzen verfügbar sind.
- Metadaten nur für veränderte/entscheidungsrelevante JPGs schreiben.
- Feature-Timeouts und Fehler pro Bild isolieren; ein defektes Bild darf nicht den Batch abbrechen.

## Stabilität und Sicherheit

- Ein globaler Lock verhindert parallele produktive Läufe.
- Alle produktiven Pfade liegen unter dem erlaubten Basisverzeichnis; Path Traversal und Symlink-Ausbrüche sind abzulehnen.
- Es gibt einen Dry-Run-Modus ohne Umbenennen, Verschieben, Archivieren, Löschen, Metadatenschreiben oder Cache-Änderung.
- Unvollständige oder fehlerhafte Batches werden übersprungen oder nach `TEMP_ERROR` quarantänisiert.
- ZIP-Dateien werden vor Nutzung auf Defekte, Traversal, Größenlimits und Kompressionsverhältnis geprüft.
- Dateioperationen dürfen keine stillen Überschreibungen ausführen.
- Optionale, deaktivierte Module melden kontrolliert `disabled`; eine aktivierte Funktion mit fehlender Abhängigkeit oder fehlerhaftem Pflicht-Rebuild führt zu einem dokumentierten, sicheren Batch-Stopp statt zu stiller Deaktivierung. Der davon unabhängige Kernworkflow darf nicht abstürzen.

## Reporting und Artefakte

Pro Lauf sind erforderlich:

- kurze Scheduler-Ausgabe auf stdout,
- strukturierte JSON-Run-Summary,
- `SAVE/culling_scores.csv` je verarbeitetem Batch,
- Logeinträge zu Cache-Nutzung, Manual Keep, Metadatenschreiben, Fehlern und ZIP-Kollisionen.
- Kalibrierungsstatus, Auswertungsfenster, Treffer- und kritische Fehlerraten sowie Automatikempfehlung.

Mindestens zu erfassen sind Anzahl gefundener, verarbeiteter, übersprungener und fehlerhafter Batches sowie Keep/Review/Reject-Zahlen, Manual-Keep-Ergebnisse, Modell-/Cache-Status und Metadatenstatus. Zusätzlich enthält die Summary eine priorisierte Liste `user_actions_required`. Jeder Eintrag enthält `severity` (`info`, `warning` oder `blocking`), `scope` (Batch, Person oder Sample-Pool), eine kurze menschenlesbare Handlung und optional einen Anker in `docs/HANDBUCH.md`. Beispiele sind Review-Ordner freigeben, `new_faces/` prüfen, Kapazität bereinigen, Cache-Rebuild fortsetzen oder eine quarantänisierte Zustandsdatei untersuchen. Scheduler-stdout zeigt nur `warning` und `blocking`; die vollständige Liste bleibt in der JSON-Summary. Die Summary enthält zusätzlich einen kompakten Block `automation_readiness` mit Status, geprüften Batches/Bildern, terminaler Übereinstimmung, `reject_to_keep_rate`, Review-Rate, Trend, kompatiblem Modell-/Konfigurationsfingerprint, Empfehlung und nächster Aktion.


## Konfiguration und Dokumentation

Konfiguration und Dokumentation sind verbindliche Produktbestandteile. Eine Implementierung gilt nicht als fertig, wenn neue oder geänderte Funktionen nur im Code existieren, aber weder konfigurierbar noch für Betrieb, Wartung und Tests nachvollziehbar beschrieben sind.

### Konfigurationsdateien

Die produktive Konfiguration liegt in einer versionierten Beispiel-/Vorlagendatei, etwa `config/config.example.yaml`; lokale produktive Werte liegen getrennt, etwa in `config/config.yaml`, und dürfen keine Zugangsdaten oder personenbezogenen Pfade in Git veröffentlichen. Eine lokale Debug-Konfiguration darf bereitgestellt werden, muss aber als Beispiel gekennzeichnet und ebenfalls secrets-frei sein.

Jede Konfigurationsvariable muss unmittelbar durch einen YAML-Kommentar dokumentiert werden. Der Kommentar erklärt mindestens Zweck, erwarteten Datentyp bzw. zulässige Werte, Einheit oder Wertebereich falls relevant, Standardverhalten und sicherheits- oder performancebezogene Auswirkung. Zusätzlich kennzeichnet der Kommentar den Stabilitätsstatus `stable`, `advanced` oder `experimental`; Standardkonfigurationen dürfen nur `stable`-Werte aktivieren.

Vor **jedem Konfigurationsabschnitt** steht zusätzlich ein mehrzeiliger Kommentarblock, der die fachliche Funktion des Bereichs, Abhängigkeiten, typische Betriebswirkung und sichere Empfehlungen erläutert. Kommentare müssen aktuell bleiben: Jede Änderung an einer Variablen erfordert im selben Commit die passende Aktualisierung der Dokumentation und Validierung.

Beispiel:

```yaml
# =============================================================================
# CULLING: Bewertet JPGs, trifft Keep/Review/Reject-Entscheidungen und steuert
# die Übergabe nach Phase 1. "assistedreview" ist der sichere Standard: Ein
# Nutzer prüft TEMP_IMAGES und verschiebt freigegebene Ordner nach TEMP_DONE.
# "automatic" nur nach erfolgreichem Test auf echten NAS-Daten aktivieren.
# =============================================================================
culling:
  # Aktiviert die Bildbewertung. Typ: boolean; false lässt den Dateigrundfluss
  # unverändert, erzeugt aber keine KI-Entscheidung oder Culling-Metadaten.
  enabled: true

  # Übergabemodus nach Phase 1. Zulässig: assistedreview | automatic.
  # Standard: assistedreview; automatic kann Phase 2 im gleichen Lauf auslösen.
  decision_mode: assistedreview

  # Finaler Score ab diesem Wert ist keep. Typ: float, Bereich 0.0 bis 1.0.
  # Höhere Werte sind konservativer und erzeugen mehr Review-Ergebnisse.
  keep_threshold: 0.65
```

Die Konfigurationsvalidierung muss unbekannte Schlüssel, unzulässige Werte, widersprüchliche Grenzen und Pfade außerhalb des erlaubten Basisverzeichnisses verständlich ablehnen. Sie prüft insbesondere Automatikstufe gegen Übergabemodus, aktive Limits gegen Zielwerte, Bereinigungsrechte gegen Dateiherkünfte, Zeitbudget gegen Wiederaufnahme und verpflichtende Funktionen gegen verfügbare Abhängigkeiten. Ein `--print-effective-config`- oder gleichwertiger Dry-Run-Ausgabemodus soll die wirksamen Werte ohne Secrets anzeigen.

### Erforderliche Dokumente

Das Repository muss mindestens folgende aktuelle, in Markdown gepflegte Dokumente enthalten:

| Datei | Mindestinhalt |
|---|---|
| `README.md` | Kurzüberblick, Funktionsumfang, Voraussetzungen, Schnellstart, sicherer Standardablauf und Verweise auf das Handbuch |
| `docs/HANDBUCH.md` | Bedienhandbuch: Ordnerfluss, Phase 1/2, manuelle Freigabe, Automatic-Modus, Bildbewertung, Manual Keep, bekannte Gesichter, `new_faces/`, `selection.json`, Metadaten, Fehlerbehandlung und Wiederherstellung |
| `docs/CONFIGURATION.md` | Vollständige Referenz aller Konfigurationsabschnitte und Variablen, Standardwerte, gültige Werte, Auswirkungen sowie sichere Empfehlungen |
| `docs/INSTALLATION.md` | Installation auf Synology/NAS, Python- und Docker-Variante, Berechtigungen, Verzeichnisanlage, Konfigurationskopie, Exiftool sowie Erstlauf im Dry Run |
| `docs/BETRIEB.md` | Scheduler/Task Scheduler, Locks, Logs, Run-Summaries, Backup, Update, Rollback und Nutzung der Bash-Rückfallebene |
| `docs/TESTING.md` | Testvoraussetzungen, Unit-/Integrationstests, Lint/Format, Testdatenregeln, Dry Run, manuelle NAS-Abnahme und erwartete Ergebnisse |
| `docs/ARCHITEKTUR.md` | Modulverantwortlichkeiten, Datenflüsse, optionale Abhängigkeiten, Cache-Invalidierung und Sicherheitsgrenzen |
| `SECURITY.md` | Berechtigungsmodell, Umgang mit privaten Fotos und Secrets, Vulnerability-Reporting sowie bekannte Sicherheitsgrenzen |
| `CHANGELOG.md` | Versionierte, verständliche Änderungen, Migrationen, behobene Fehler und potenziell inkompatible Anpassungen |

Kleine Projekte dürfen Dokumente bündeln, wenn die Inhalte eindeutig über Überschriften auffindbar sind. `README.md`, ein ausführliches Handbuch, Konfigurationsreferenz, Installations-/Betriebsanleitung, Testanleitung, `SECURITY.md` und `CHANGELOG.md` bleiben jedoch Pflicht.

### Handbuch und Inbetriebnahme

Das Handbuch muss einen neuen Nutzer ohne Codekenntnis vom leeren NAS-Verzeichnis bis zum ersten sicheren Lauf führen. Es enthält einen klaren Entscheidungsbaum für `paused`, `failed`, `not_used_limit_exceeded`, `face_model_rebuild_failed` und nicht zuordenbare Manual-Keep-Dateien. Es beschreibt insbesondere den Unterschied zwischen Python-Workflow und Bash-Rückfallebene, die Bedeutung aller Arbeitsordner, die aktive-JPG-Regel, die Prüfung in `TEMP_IMAGES`, die Freigabe nach `TEMP_DONE` und das Verhalten von Phase 2.

Die Installation beschreibt beide unterstützten Wege: lokale Python-Ausführung in einer isolierten virtuellen Umgebung sowie Docker-Ausführung mit bind-gemounteten Daten- und Konfigurationspfaden. Sie muss Mindestversionen, Abhängigkeiten, Beispielbefehle, Least-Privilege-Berechtigungen, keine Secrets in Git und eine Konfiguration für kleine NAS-Systeme enthalten.

Die Betriebsdokumentation muss mit konkreten, kopierbaren Befehlen erklären, wie ein Dry Run, ein Phase-1-Lauf, ein Phase-2-Lauf, ein vollständiger Lauf, ein Cache-Rebuild und der Bash-Fallback ausgeführt werden. Sie muss klar markieren, welche Befehle Dateien verändern können.

### Test- und GitHub-Standard

Die Testanleitung muss mindestens die vorgesehenen Befehle für Syntaxprüfung, Unit-/Integrationstests und Lint nennen, beispielsweise `python -m compileall`, `pytest`, `python -m unittest discover` und den gewählten Linter. Testdaten dürfen keine privaten Originalbilder enthalten; sie müssen anonymisiert, synthetisch oder ausdrücklich freigegeben sein.

Für GitHub sind eine `.gitignore` für Caches, lokale Konfigurationen, Modelle, Logs, Run-Summaries und Bilddaten sowie eine CI-Pipeline erforderlich. Die CI führt mindestens Konfigurationsvalidierung, Syntaxprüfung, Tests und Lint aus. Docker-bezogene Dokumentation muss außerdem Build, lokale Ausführung, Volume-Mounts, nicht-root-Ausführung soweit praktikabel und das Aktualisieren von Abhängigkeiten beschreiben.

Neue Funktionen werden erst abgenommen, wenn Code, kommentierte Konfiguration, Handbuch, technische Dokumentation, Changelog und automatisierte Tests gemeinsam aktualisiert sind.



## Bedienung im Alltag

Im Normalbetrieb legt der Nutzer einen vollständigen Kameraordner in `TEMP_SD` ab und startet den geplanten Scheduler-Lauf. Im sicheren Standard prüft er anschließend nur die kurze Run-Summary und verschiebt einen geprüften Ordner von `TEMP_IMAGES` nach `TEMP_DONE`; die aufwendige technische Verarbeitung erledigt der Workflow. Bei aktivierter automatischer Phase 2 entfällt auch diese Ordnerübergabe, sofern keine Warnung oder Sicherheitsblockade vorliegt.

Gesichts- und Geschmacksvorschläge werden nicht bei jedem Lauf einzeln bearbeitet. Der Nutzer prüft sie gesammelt, wenn die Summary dies empfiehlt oder die Kapazitätsampel `warning` meldet, und kopiert nur geeignete Dateien nach `reference/`. Dadurch ist die menschliche Handlung eindeutig, reversibel und auf die wenigen Lernentscheidungen beschränkt, die das System langfristig beeinflussen.

Bei `paused` wartet der nächste Lauf oder der Nutzer startet ihn erneut; bei `failed` oder `face_model_rebuild_failed` bleibt der Batch unverändert im sicheren Arbeitszustand und die Summary nennt den nächsten Schritt. Bei `full` oder `blocked` entstehen keine neuen Vorschläge, bestehende Daten bleiben erhalten und der Nutzer kann gezielt bestätigen, manuell nach `not_used/` verschieben oder die Grenzen bewusst anpassen.


## Prüfung der bestehenden Codebasis

Eine implementierende KI soll zunächst feststellen:

1. Welche Teile von Phase 1 und Phase 2 tatsächlich produktiv aufgerufen werden.
2. Ob der Python-Ordnerfluss zum Bash-Referenzablauf passt.
3. Ob die aktive JPG-Regel in Phase 2 durchgesetzt wird.
4. Ob Bildscore, persönlicher Score und Familien-Score echte Werte liefern oder nur Platzhalter sind.
5. Ob Manual Keep vollständig läuft: Inbox lesen, sicher matchen, Ziel auf `keep`, Quelle nach `used`.
6. Ob Exiftool-Ausgabe tatsächlich an den Culling-/Face-Ergebnissen hängt.
7. Ob Caches sicher, klein und invalidierbar sind.
8. Ob ausgeschlossene Funktionen wie Unknown-Clustering nicht versehentlich eingebaut oder aktiviert werden.
9. Ob alle Konfigurationsvariablen und Konfigurationsabschnitte kommentiert sowie README, Handbuch, Installations-, Betriebs-, Sicherheits- und Testdokumentation aktualisiert sind.

Eine Funktion gilt erst als umgesetzt, wenn sie im Workflow aufgerufen wird, konfigurierbar ist und einen automatisierten Test besitzt.

## Mindesttests

- Konfiguration: Wertebereiche, Standardwerte, ungültige Modi.
- Datenverträge: Schema-Versionen, Pflichtfelder, atomarer Schreibvorgang, Quarantäne ungültiger Steuerdateien und konservative Herkunftsbehandlung.
- CLI: `run`, `phase1`, `phase2`, Cache-Rebuilds.
- Phase 1: stabile und instabile Eingänge, Datumslogik, ARW-Auslagerung, JPG-ZIP, Übergabe nach `TEMP_IMAGES`.
- Phase 2: aktive JPG-Regel, ARW-Zuordnung, sichere ZIP-Kollisionen, temporäres Archiv, atomare Aktivierung, Wiederaufnahme vor und nach Archivaktivierung sowie Prozessmarker.
- Automatik: nur bei explizitem Modus Übergabe nach `TEMP_DONE` und anschließende Phase 2.
- Kalibrierung: manueller Umzug nach `TEMP_DONE` nach beliebiger Liegezeit in `TEMP_IMAGES`, atomarer Batch-Record vor Phase-2-ARW-Aktion, Abbruch/Wiederaufnahme, fehlender oder nicht passender Phase-1-Status blockiert Phase 2, automatische Übergabe erzeugt kein Label.
- Kalibrierungsindex: Rebuild des globalen Index und der Summary ausschließlich aus Batch-Records; defekter Index darf keine Batch-Records verändern.
- Lernmodell: Schattenmodus verändert sichtbare Entscheidung nicht, zeitlich getrennte Prüfung, begrenzte Gewichte, keine Aktivierung ohne Nutzerfreigabe, Rollback und Fingerprint-Trennung.
- Automatikempfehlung: 90-Prozent-Schwelle, kritische Reject-Fehler, Mindest-Batches/-Bilder, Trend und Rückfallstatus.
- Scoring: Normierung bei fehlenden Komponenten, Grenzwerte, keine Doppelgewichtung.
- Serie: deterministische Gruppierung und begrenzte Korrektur.
- Personal: Cache-Invaliderung sowie Annahme nur bei Qualität, Dedupe und Diversitätsgewinn.
- Familie: Cache-Invaliderung, bekannter Treffer, begrenzter Score-Boost, kein Absturz ohne Backend.
- Face-Crops: nur eindeutige bekannte Person, Qualitätsgrenzen, Dedupe und Ablage in `new_faces/`; keine Speicherung unbekannter Gesichter.
- Manuelle Freigabe: Nur ein manuell in den Personenordner kopierter Crop wird beim nächsten Rebuild berücksichtigt.
- Auswahlmanifest: deterministische Auswahl aus dem verwalteten Pool; nur `active`-Einträge speisen das Modell; `manual_protected` wird nie automatisch verschoben oder gelöscht; automatisch erzeugte Dateien wechseln ausschließlich atomar, auditierbar und idempotent zwischen `reference/` und `not_used/`.
- Manual Keep: eindeutiger kleiner WhatsApp-Treffer erzwingt `keep` und wandert nach `used`; unklare Treffer bleiben in `inbox`.
- Manual-Keep-Metrik: Cosine-Ähnlichkeit, 0.95-Schwelle, 0.03-Marge und ausschließliche Suche im aktuellen Batch.
- Metadaten: Mock- oder Integrationsprüfung der Exiftool-Argumente und der geschriebenen Keywords/Ratings.
- Sicherheit: Dry Run, Lock, Pfadausbruch, ZIP-Traversal, keine stillen Überschreibungen.
- Dokumentation: Jeder YAML-Abschnitt und jede Variable hat den vorgeschriebenen Kommentar; Beispiele sind syntaktisch valide und die dokumentierten Befehle werden mindestens in CI oder einem Smoke-Test ausgeführt.
- Wiederaufnahme: pausierter Batch, SIGTERM, Zeitlimit, atomare Zustandsdatei, beschädigte Zustandsdatei und Fortsetzen ohne doppelte Dateioperationen.
- Auswahlpools: `reference/`, `new_faces`/`new_refs`, `not_used`, Limits, Copy-Verify-Delete, Manifest-Aktualisierung und Ausschluss nicht aktiver Dateien aus den Modellen.
- Batch-Identität: zwei gleichnamige Tagesordner mit unterschiedlichen Inhaltsfingerprints und getrennten Zustandsdateien.
- Modell-Rebuild: Unterbrechung vor atomarer Aktivierung, Zeitbudget, Wiederaufnahme und Blockierung des Batches.
- Referenzschutz: Reaktivierung verwalteter Alternativen aus `not_used/`, aber keine automatische Verschiebung von `manual_protected`-Dateien.
- Kapazität und Automatik: Warn-/Full-/Blocked-Status, nicht-destruktive Limits und Rückfall nach kritischem Fehler auf `assisted_review`.
- Nutzbarkeit: Run-Summary erzeugt für alle blockierenden oder manuellen Zustände eine verständliche, umsetzbare `user_actions_required`-Meldung.

## Abnahmekriterien

Die Umsetzung ist akzeptabel, wenn:

1. Bash-Rückfallebene und fachliche Phase-1-/Phase-2-Logik erhalten bleiben.
2. Der sichere Standard `TEMP_SD -> TEMP_IMAGES -> TEMP_DONE -> Phase 2` funktioniert.
3. Automatische Phase-1-zu-Phase-2-Nutzung nur explizit konfigurierbar ist.
4. Technisches Bildscoring, persönlicher Score und bekannter Familien-Score nachvollziehbar kombiniert werden.
5. Persönliche Samples und bekannte Gesichtsreferenzen ausschließlich bei messbarem Mehrwert automatisch erweitert werden.
6. Neue Crops nur für bekannte Personen in deren `new_faces/` entstehen, der Nutzer sie manuell bestätigt und kein unbekanntes Gesicht gespeichert oder geclustert wird.
7. Pro bekannter Person ein menschenlesbares `selection.json` 30 bis 50 aktive, vielfältige bestätigte Referenzen festlegt, ohne Bilddateien zu verschieben oder zu löschen.
8. Culling- und Gesichtsergebnisse optional in JPG-Metadaten geschrieben werden.
9. WhatsApp-/Manual-Keep-Dateien sicher gematcht, als `keep` behandelt und danach nach `used` verschoben werden.
10. Der Betrieb auf kleiner NAS-Hardware ohne große Modelle, GPU oder übermäßigen Speicherverbrauch möglich ist.
11. Jede Konfigurationsvariable und jeder Konfigurationsabschnitt verständlich kommentiert ist und die Pflichtdokumente aktuell, konsistent und testbar sind.
12. NAS-Mount, Docker-Task-Scheduler-Betrieb, pro-Batch-Zustandsdatei, Zeitbudget und kontrollierte Wiederaufnahme ohne Datenverlust funktionieren.
13. Die ordnerbasierte Blaupause für Faces und Geschmackssamples konsistent umgesetzt wird: aktive Referenzen, menschlich prüfbare Vorschläge, begrenzte Alternativen und autoritative Manifeste.
14. Batch-IDs kollisionssicher, Dateioperationen idempotent und Rebuilds unterbrechbar sowie atomar aktivierbar sind.
15. Kapazitätsampel, geschützte manuelle Referenzen und stufenweise, rückfallfähige Automatik umgesetzt und getestet sind.
16. Run-Summaries offene Nutzeraktionen klar, knapp und ohne technische Detailkenntnisse benennen.
17. Steuerdateien versioniert, validiert, atomar geschrieben und bei Ungültigkeit sicher quarantänisiert werden.
18. Phase 2 bei jeder Unterbrechungsstelle ohne ARW-Verlust wiederaufnehmbar ist.
19. Manual Keep die dokumentierte Cosine-Ähnlichkeitsmetrik, Schwelle und Marge ausschließlich im aktuellen Batch anwendet.
20. Alle Kernfunktionen durch Unit- und Integrationstests nachgewiesen sind.


## Ergänzende Abnahmekriterien für Kalibrierung

21. Ein manuell geprüfter Ordner darf beliebig lange in `TEMP_IMAGES` liegen und wird ausschließlich durch seinen manuellen Umzug nach `TEMP_DONE` als geprüft behandelt.
22. Vor jeder Phase-2-ARW-Aktion wird für einen manuell übergebenen Batch ein valider, idempotenter und unveränderlicher `review_decision_record.json` gespeichert; ohne ihn ist der Batch blockiert.
23. Batch-Records sind die rekonstruierbare fachliche Quelle; globaler Index und Kalibrierungsreport lassen sich vollständig daraus neu erzeugen und enthalten keine privaten Bilddateien.
24. Jede Run-Summary enthält Trefferquote, kritische Fehlerraten, Review-Rate, Trend, Kalibrierungsstatus, konkrete Automatikempfehlung und nächste Aktion.
25. `automatic_phase2` wird nie selbst aktiviert; die Empfehlung erfordert die konfigurierten Mindestdaten, mindestens 90 Prozent terminale Übereinstimmung und 0 Prozent `reject -> keep` im kompatiblen Fenster.
26. Das Lernmodell trainiert nur auf menschlich bestätigten Entscheidungen, läuft zunächst im Schattenmodus, verändert keine sichtbare Entscheidung und darf nur nach bewusster Freigabe aktiv werden.
27. Transparente YAML-Basisgewichte, Manual Keep und alle Hard-Safety-Regeln bleiben bei lernender Gewichtung sichtbar und wirksam.


# Anhang v7.1 – Finaler Implementierungs- und Abnahmevertrag

## Normativer Status und Leseregel

Dieser Anhang ist zusammen mit den vorstehenden Abschnitten die **finale Spezifikation v7.1**. Er konkretisiert nur dort, wo v7 bisher einen Ermessensspielraum ließ. Bei einem Widerspruch gilt diese Reihenfolge: (1) Daten- und Löschsicherheit, (2) dieser Anhang, (3) der vorstehende v7-Haupttext, (4) explizite Migrationsregeln, (5) ältere Projektbeschreibungen und Bash-Referenzen. Historische Beispiele, alte Schlüssel und alte Tag-Namen sind niemals führend.

Der produktive Mindestumfang ist: zweiphasiger JPG-/ARW-Workflow, Assisted Review, Culling, eingebettete Metadaten, sichere Archive, Batch-Zustand, Reporting und Kalibrierung. Die ältere Face-Learning-Erweiterung mit Unknown-Clustern, Kandidatenrouting, Referenzselektion und Indexverwaltung ist ein separat konfiguriertes Erweiterungsmodul. Sie darf den Mindestworkflow nicht blockieren und darf niemals selbst Identitäten bestätigen oder Referenzen aktivieren.

## Kanonische Begriffe

| Begriff | Verbindliche Bedeutung |
|---|---|
| Batch | Ein bearbeitbarer Kameraordner mit stabiler `batch_id` und eindeutiger Manifest-ID. |
| Aktives JPG | JPG im Hauptordner des Batches; nur dieses schützt ein passendes ARW. |
| Score-Entscheidung | Regelbasierte Klasse vor manueller Sichtung (`keep`, `review`, `reject`). |
| Finale Entscheidung | Menschliche Endentscheidung aus dem Phase-2-Ordnerzustand. |
| Entbehrliches ARW | ARW ohne exakt zugeordnetes aktives JPG nach erfolgreicher Phase-2-Validierung. |
| Archivaktivierung | Atomarer Wechsel einer vollständig geschriebenen und validierten temporären ZIP zur finalen ZIP. |
| Wiederaufnahme | Sicheres Fortsetzen anhand von Zustand und Manifest; kein erneutes Raten oder Überschreiben. |

Alle Enum-Werte, Dateinamen, JSON-Feldnamen und Konfigurationsschlüssel dieser Spezifikation verwenden `snake_case`. Sichtbare Ordnernamen und die ausdrücklich festgelegten Keyword-Präfixe bleiben Ausnahmen.

## Referenzkonfiguration

Die Implementierung muss diese YAML-Struktur vollständig validieren. Nicht bekannte Schlüssel sind ein Konfigurationsfehler, außer sie liegen unter einem explizit als erweiterbar dokumentierten `extensions`-Block. Relative Pfade werden gegen `paths.base_dir` aufgelöst und dürfen dieses Verzeichnis nach Normalisierung nie verlassen.

```yaml
specification:
  version: "7.1"

paths:
  base_dir: "/volume1/photo-workflow"
  temp_sd: "TEMP_SD"
  temp_images: "TEMP_IMAGES"
  temp_done: "TEMP_DONE"
  temp_error: "TEMP_ERROR"
  workflow_data: "_workflow_data"

workflow:
  phase_execution: "phase1_then_phase2" # phase1_only | phase2_only
  batch_limit: 0                          # 0 = alle vollständigen Batches
  batch_sort: "oldest_first"
  skip_incomplete_batches: true
  date_reconstruction:
    mode: "legacy_bash"                  # legacy_bash | full_year
    decade_prefix: "202"
    year_digit_index: 3

culling:
  decision_mode: "assisted_review"
  auto_keep_min_rating: 2
  keep_threshold: 0.65
  reject_threshold: 0.35
  final_component_weights:
    base_score: 0.55
    eye_score: 0.10
    personal_score: 0.20
    family_score: 0.15
  base_weights:
    sharpness: 0.35
    aesthetic: 0.35
    exposure: 0.20
    reference_score: 0.10
  star_rating_bands:
    - {min: 0.00, max: 0.19, rating: 0}
    - {min: 0.20, max: 0.39, rating: 1}
    - {min: 0.40, max: 0.59, rating: 2}
    - {min: 0.60, max: 0.74, rating: 3}
    - {min: 0.75, max: 0.89, rating: 4}
    - {min: 0.90, max: 1.00, rating: 5}

phase2:
  delete_unneeded_arws_after_verified_archive: true
  allow_automatic_handoff: false

metadata:
  write_mode: "embedded_exiftool"
  verify_after_write: true
  create_exiftool_backups: false
  sidecar_recovery_enabled: false

family_recognition:
  enabled: false
  backend: "opencv_yunet_sface"
  detector_model: "models/faces/face_detection_yunet.onnx"
  recognizer_model: "models/faces/face_recognition_sface.onnx"
  similarity_metric: "cosine_similarity"
  match_threshold: null
  protect_detected_family: true
  cache_dir: "models/family_faces"

automation:
  enabled: false
  phase2_auto_handoff: false
  activation_requires:
    explicit_user_approval: true
    readiness_status: "eligible_automatic_phase2"
    config_fingerprint_match: true
    model_fingerprint_match: true
    completed_nas_e2e_acceptance: true
```

`decision_mode: automatic` ist bis zu einer späteren, explizit versionierten Erweiterung ungültig. Die vorhandene historische Automatikfunktion wird damit bewusst nicht Teil des v7.1-Produktivumfangs. `allow_automatic_handoff` und `phase2_auto_handoff` müssen in v7.1 `false` sein; jede Abweichung ist ein Validierungsfehler, nicht nur eine Warnung.

Validierungsregeln: `batch_limit` ist eine Ganzzahl größer oder gleich 0; `0 <= reject_threshold < keep_threshold <= 1`; alle Gewichte sind nicht negativ und ihre Summe ist bei voller Komponentenverfügbarkeit exakt 1,0; Sternbänder sind lückenlos, nicht überlappend und decken [0,1] ab; `auto_keep_min_rating` liegt in [0,5]. Ein gesetzter Face-`match_threshold` liegt in der für das Backend dokumentierten Skala. `null` bedeutet unkalibriert und verbietet Family-Scoring sowie Personentags.

## CLI- und Modulvertrag

Der einzige produktiv unterstützte Einstiegspunkt lautet:

```bash
python -m app.photoworkflow --config /config/config.yaml run
```

Erlaubte Befehle sind `run`, `phase1`, `phase2`, `rebuild_family_cache`, `validate_config`, `recover_batch` und `rebuild_calibration_index`. `run` folgt `workflow.phase_execution`; ein expliziter Phasenbefehl überschreibt diese Einstellung. `recover_batch` akzeptiert genau eine `batch_id`, führt keine neue Culling-Bewertung aus und darf niemals ohne vorhandenes Batch-Manifest ARWs löschen.

| Modul | Exklusive Verantwortung |
|---|---|
| `app.cli` | Argumente, Konfiguration laden, Exit-Codes und Befehlsdispatch |
| `app.configuration` | YAML-Schema, Alias-Migration, Validierung, Pfadauflösung, Konfigurationsfingerprint |
| `app.phases` | Auswahl und Orchestrierung von Phase 1 und Phase 2 |
| `app.inventory` | Stabile Eingänge, Fingerprints, Datei- und Paarinventar |
| `app.culling` | Basis-/Finalscore, Sterne, Score- und Serienentscheidung |
| `app.metadata` | Exiftool-Aufruf, Keyword-Merge und Rückleseprüfung |
| `app.archives` | ZIP-Sicherheitsprüfung, Erstellung, Hash, Validierung und Aktivierung |
| `app.batch_state` | Zustandsmaschine, Manifeste, Resume-Entscheidungen |
| `app.calibration` | Review-Records, rebuildbare Indizes und Readiness-Berechnung |
| `app.family_recognition` | YuNet/SFace, Embedding-Cache, Diagnose und Schutzsignal |
| `app.reporting` | stdout, Logs, JSON-Run-Summaries |
| `app.locks` | Lauf- und Batch-Locks, Eigentümer und Stale-Lock-Prüfung |

Fachlogik darf nicht in `app.cli` dupliziert werden. Jedes Modul stellt eine kleine, testbare Schnittstelle bereit; Dateisystemmutationen erfolgen ausschließlich über die Module `archives`, `metadata`, `batch_state` und die kontrollierten Phase-Operationen.

## Datei- und Zuordnungsvertrag

Ein Batch hat diesen sichtbaren Aufbau:

```text
<batch>/
  <aktive JPGs im Hauptordner>
  ARW/
  _Review/
  _Rejected/
  SAVE/
    <batch>_ALL_JPG.zip
    <batch>_SORT_ARW.zip
    culling_scores.csv
```

Nur `.jpg` und `.jpeg` sowie `.arw` sind im MVP unterstützte Arbeitsformate; Erweiterungen werden ASCII-case-insensitiv verglichen. Die Paarbildung verwendet den vollständigen Dateinamen ohne letzte Erweiterung (Basename), keine Teilstrings und keine Ähnlichkeitssuche. Genau ein oder mehrere aktive JPGs mit identischem Basename schützen das zugehörige einzelne ARW. Mehrere ARWs mit gleichem Basename, nicht normalisierbare Unicode-Namen, nicht eindeutige Inventare oder eine nicht dokumentierte Umbenennung blockieren Phase 2 mit `FAILED_VALIDATION`. Bei einer Blockade wird kein ARW gelöscht.

Eine bewusst unterstützte Umbenennung benötigt vor Phase 2 einen im Phase-1-Manifest hinterlegten `arw_binding` mit altem Basename, neuem Pfad, Hash des JPG und ursprünglichem ARW-Fingerprint. Ohne diesen Beleg schützt ein umbenanntes JPG kein ARW. Symlinks, Hardlink-Sonderfälle und Pfade außerhalb von `base_dir` werden abgewiesen.

## Phase- und Zustandsmaschine

Zulässige technische Zustände sind ausschließlich:

```text
DISCOVERED -> VALIDATED -> PHASE1_RUNNING -> REVIEW_READY
REVIEW_READY -> HUMAN_APPROVED -> PHASE2_VALIDATING
PHASE2_VALIDATING -> ARW_ARCHIVE_STAGED -> ARW_ARCHIVE_VERIFIED
ARW_ARCHIVE_VERIFIED -> ARW_DELETE_RUNNING -> COMPLETED
```

Fehlerzustände sind `BLOCKED_INCOMPLETE`, `FAILED_VALIDATION`, `FAILED_METADATA`, `FAILED_ARCHIVE`, `FAILED_DELETE`, `RECOVERY_REQUIRED` und `QUARANTINED`. Ein Fehlerstatus enthält `error_code`, `message`, `at`, `run_id`, `retryable` und einen Verweis auf Log und Manifest.

Phase 1 führt in fester Reihenfolge aus: Eingang sperren und auf Stabilität prüfen; Batch-ID/Datenname validieren; ARWs verschieben; Original-JPG-Archiv erzeugen und validieren; Inventar, Scores, Sternrating und Serienkorrektur ermitteln; Metadaten schreiben und rücklesen; `culling_scores.csv` sowie Phase-1-Manifest schreiben; Dateien einsortieren; Batch atomar nach `TEMP_IMAGES` übergeben und `REVIEW_READY` schreiben.

Der manuelle Move nach `TEMP_DONE` ist der alleinige Übergang von `REVIEW_READY` zu `HUMAN_APPROVED`. Phase 2 darf einen Batch nur bearbeiten, wenn Manifest, Konfigurationsfingerprint, Dateifingerprints und Ordnerprotokoll plausibel sind. Der Hauptordner bedeutet immer `keep`, `_Review/` bedeutet `review`, `_Rejected/` bedeutet `reject`; ein gültiges Manual-Keep-Signal hat Vorrang. `auto_keep_min_rating` wird in Phase 2 nicht verwendet.

Jeder Zustand wird mittels Write-to-temp, `fsync`, atomarem Rename und anschließendem Directory-`fsync` persistiert, soweit das Dateisystem dies unterstützt. Ein Prozess schreibt vor jeder Mutation seinen `run_id`-Lock; konkurrierende Läufe dürfen denselben Batch nicht bearbeiten. Ein abgelaufener Lock wird nur nach dokumentierter Besitzer-, PID-/Host- und Zeitprüfung als stale markiert, nie blind gelöscht.

## Archiv-, Lösch- und Wiederaufnahmevertrag

Für entbehrliche ARWs erstellt Phase 2 zunächst einen unveränderlichen Archivplan. Das temporäre Archiv enthält für jede Datei relativen Pfad, Größe und SHA-256. Nach dem Schreiben werden ZIP-Lesbarkeit, sichere Memberpfade, erwartete Dateiliste, Größe und SHA-256 aller Einträge geprüft. Erst dann erfolgt die atomare Aktivierung zur finalen ZIP und die Persistierung von `archive_manifest.json`.

Wenn `SAVE/<batch>_SORT_ARW.zip` existiert und sein Archivmanifest mit geplantem Inhalt, Entry-Hashes und Konfigurationsfingerprint exakt übereinstimmt, wird das vorhandene Archiv wiederverwendet. Existiert es, ist aber nicht identisch oder nicht vertrauenswürdig, wird die erste freie Datei `SAVE/<batch>_SORT_ARW_EXTRA_<n>.zip` verwendet. Eine `_EXTRA_`-Datei ist somit ausschließlich ein Kollisionsschutz. Sie erzeugt zwingend `ZIP_TARGET_COLLISION` in Log, Run-Summary und `zip_conflicts`.

ARWs dürfen erst nach `ARW_ARCHIVE_VERIFIED` gelöscht werden. Jede Löschung wird unmittelbar mit ARW-Fingerprint, Archivpfad, Archivhash und Zeitstempel in `batch_state.json` ergänzt. Bei Absturz nach Archivvalidierung, aber vor oder während der Löschung, löscht `recover_batch` nur noch existierende, exakt im verifizierten Archivmanifest enthaltene ARWs. Jede Abweichung führt zu `RECOVERY_REQUIRED`; es wird keine heuristische Bereinigung versucht. Nach vollständiger dokumentierter Löschung wird ein leeres `ARW/` entfernt und `COMPLETED` geschrieben.

## Persistente Datenverträge

Alle JSON-Artefakte haben mindestens `schema_version`, `batch_id`, `created_at`, `run_id` und `config_fingerprint`. Zeiten sind UTC im RFC-3339-Format. Hashes sind SHA-256 in hexadezimaler Kleinschreibung. `null` bedeutet unbekannt/nicht verfügbar; 0 ist ein gemessener numerischer Wert.

```text
_workflow_data/
  batches/<batch_id>/phase1_manifest.json
  batches/<batch_id>/batch_state.json
  batches/<batch_id>/review_decision_record.json
  batches/<batch_id>/archive_manifest.json
  locks/<batch_id>.lock
  run_summaries/<run_id>.json
  calibration/decision_index.jsonl
  calibration/calibration_summary.json
```

`SAVE/culling_scores.csv` ist UTF-8, RFC-4180-konform, hat eine Header-Zeile und mindestens: `image_id`, `relative_path`, `base_score`, `eye_score`, `personal_score`, `family_score`, `final_score`, `star_rating`, `score_decision`, `final_decision`, `decision_reason`, `series_id`, `series_size`, `series_rank`, `series_best`, `series_margin_to_best`, `model_version`, `config_fingerprint`. Alte Namen dürfen nur lesend migriert werden; geschrieben wird ausschließlich dieser Name.

Minimalform des `archive_manifest.json`:

```json
{
  "schema_version": "1.0",
  "batch_id": "2026-07-24",
  "archive_kind": "sort_arw",
  "archive_path": "SAVE/2026-07-24_SORT_ARW.zip",
  "archive_sha256": "<sha256>",
  "archive_verified_at": "2026-07-24T12:00:00Z",
  "entries": [{"relative_path":"ARW/DSC00001.ARW","sha256":"<sha256>","size_bytes":12345678,"deletion_eligible":true}],
  "config_fingerprint": "<sha256>"
}
```

`review_decision_record.json` enthält pro Phase-1-Bild mindestens Phase-1-Prognose, finale menschliche Entscheidung, relative Endposition, Bildhash, Teilmerkmale, Modell-/Konfigurationsfingerprints und Zeitstempel. Es wird vor jeder ARW-Mutation geschrieben. `decision_index.jsonl` und `calibration_summary.json` sind ausschließlich rebuildbare Ableitungen aus diesen Batch-Records und werden nicht in Git eingecheckt.

## Scoring, Serien und Family Recognition

Alle Score-Komponenten liegen in [0,1] oder sind `null`; aktive Finalgewichte werden proportional auf 1,0 renormiert. `base_score` besteht nur aus Schärfe, Ästhetik, Belichtung und Referenzscore. `eye_score` ist ein separater optionaler Finalbaustein und darf nicht als Base-Untergewicht erscheinen. `score_decision` folgt den beiden Schwellen; Sternrating folgt ausschließlich den Score-Bändern. `final_decision` nach Phase 1 dokumentiert die Serienkorrektur, während die menschliche Phase-2-Entscheidung das verbindliche Endergebnis ist.

Die Serienerkennung arbeitet ausschließlich innerhalb eines Batches, muss deterministisch sein und liefert `series_id`, `series_size`, `series_rank`, `series_best` und `series_margin_to_best`. Das Serienbestbild darf die Score-Klasse höchstens um eine Stufe verbessern. Andere Serienbilder dürfen nur aufgrund einer konfigurierten, geloggten Distanz zum Bestbild abgewertet werden. Fehlt die Serienanalyse, bleibt die Score-Entscheidung unverändert und der Grund wird protokolliert.

Family Recognition nutzt im ersten Backend `opencv-contrib-python-headless`, YuNet und SFace mit Cosine Similarity. Bei `enabled: false`, fehlendem Modell, fehlendem `match_threshold`, Mehrdeutigkeit oder Backendfehler liefert sie keinen Family-Score und keine Personentags; der Workflow läuft mit Warnung weiter. Erst ein eindeutig kalibrierter Match darf, bei aktiviertem Schutz, `reject` maximal zu `review` anheben. Eine automatische Identitätsbestätigung, Referenzaufnahme oder Unknown-to-Known-Überführung ist verboten.

## Eingebettete Metadaten

Der Normalweg schreibt direkt in JPG per `exiftool`; XMP-Sidecars entstehen nur bei einem später explizit aktivierten Recovery-Modus. Exiftool wird ohne Backup-Dateien aufgerufen. Vor dem Schreiben wird die Quelldatei inventarisiert, danach werden die verwalteten Felder zurückgelesen. Bei jeder Abweichung entsteht `FAILED_METADATA`; der Batch darf nicht zu Phase 2 fortschreiten.

| Information | Zielfeld | Update-Regel |
|---|---|---|
| Sternrating | `XMP:Rating` | Wert 0 bis 5 ersetzen |
| Workflow-/Entscheidungs-/Serien-/Familientags | `XMP-dc:Subject` | Nur workflow-eigene Präfixe ersetzen; fremde Keywords erhalten |
| Exakte Scores und Teilwerte | Kein Bildfeld | Nur CSV, Manifeste und JSON |

Die ausschließlich neu geschriebenen Keywords lauten `workflow:ai_cull`, `workflow:model:<model_id>`, `decision:predicted:<keep|review|reject>`, `decision:final:<keep|review|reject>`, `series:id:<series_id>`, `series:role:<best|member>`, `family:match:<true|false>`, `person:<person_slug>`, `score_band:final:<0..5>` und `whatsapp:manual_keep`.

## Reporting, Fehler und Exit-Codes

Jeder Lauf erzeugt eine JSON-Run-Summary und eine kurze Scheduler-Ausgabe. `automation_readiness` enthält mindestens `status`, `compatible_reviewed_batches`, `compatible_reviewed_images`, `terminal_agreement`, `reject_to_keep_rate`, `reject_to_review_rate`, `review_rate`, `trend`, `recommendation`, `reasons` und `next_action`. Sie darf nur empfehlen; sie verändert keine Konfiguration.

Exit-Code 0 bedeutet vollständig erfolgreich ohne Blocker. Exit-Code 2 bedeutet validierungsbedingt nicht ausgeführte Batches; 3 bedeutet recoverable Fehler ohne ARW-Löschung; 4 bedeutet mindestens ein Batch in `RECOVERY_REQUIRED` oder `FAILED_DELETE`; 5 bedeutet Konfigurationsfehler; 6 bedeutet interne, unerwartete Ausnahme. Ein Einzelbatchfehler darf andere unabhängige Batches nicht gefährden, muss aber in der Gesamtsummary erscheinen.

## Abnahme- und Testmatrix

| ID | Prüfszenario | Verbindliches Sollresultat |
|---|---|---|
| ACC-01 | Stabiler vollständiger Eingang in `TEMP_SD` | Phase 1 erzeugt Manifest, Archiv, CSV und übergibt nach `TEMP_IMAGES` |
| ACC-02 | Noch wachsender oder gesperrter Eingang | Keine Mutation; Zustand `BLOCKED_INCOMPLETE` |
| ACC-03 | Ungültiger Legacy- oder Volljahresname | `FAILED_VALIDATION`; keine Datei wird gelöscht |
| ACC-04 | JPG aus `_Rejected/` zurück in Hauptordner | Phase 2 bewertet es final als `keep`; passendes ARW bleibt |
| ACC-05 | Metadaten-Rücklesetest fehlerhaft | `FAILED_METADATA`; keine Übergabe zu Phase 2 |
| ACC-06 | Archiv kann nicht vollständig validiert werden | `FAILED_ARCHIVE`; keine ARW-Löschung |
| ACC-07 | Identisches bestehendes `SORT_ARW.zip` | Wiederverwendung, kein `_EXTRA_`-Archiv |
| ACC-08 | Abweichendes bestehendes `SORT_ARW.zip` | Erstes freies `_EXTRA_<n>`; `ZIP_TARGET_COLLISION` und `zip_conflicts` |
| ACC-09 | Crash nach Archivvalidierung, vor ARW-Löschung | Recovery löscht nur manifestierte noch vorhandene ARWs |
| ACC-10 | Mehrdeutige JPG-/ARW-Paarbildung | `FAILED_VALIDATION`; keine ARW-Löschung |
| ACC-11 | Family Backend deaktiviert/unkalibriert | Kein Family-Score und keine Personentags |
| ACC-12 | Readiness erfüllt alle Schwellen | Nur Empfehlung, keine automatische Aktivierung |
| ACC-13 | Pfadflucht, Symlink oder unsicheres ZIP | Blockade oder Quarantäne innerhalb von `TEMP_ERROR` |
| ACC-14 | NAS-Pilot mit Kopien realer Batches | Manuell dokumentierter Nachweis für Mounts, UID/GID, Scheduler, Last, Restore und Recovery |

Die Implementierung gilt erst als abgenommen, wenn alle automatisierten Fälle reproduzierbar bestehen und ACC-14 auf der realen Synology NAS dokumentiert wurde. Ein bestandener Unit- oder Container-Test ersetzt den NAS-Pilot nicht.

## Deployment-Gates

Docker und DSM Task Scheduler dürfen nur mit persistierend gemountetem `base_dir`, dediziertem Least-Privilege-Benutzer, schreibbaren Unterordnern für `_workflow_data` und nachvollziehbarer UID/GID betrieben werden. Modelle, Referenzbilder, Caches, Logs, Run-Summaries und Archive liegen außerhalb des Container-Images auf dem NAS. Geheimnisse und produktive Pfade gehören nicht in Git oder Debug-Konfigurationen.

Vor Freigabe sind mindestens zu prüfen: Konfigurationsvalidierung, Paket-CLI-Hilfe, Unit- und Integrationstests, Pfad-/ZIP-Sicherheitstests, Container-Dependency-Scan, Restore eines validierten ARW-Archivs, paralleler Scheduler-Start, Strom-/Prozessabbruch während jeder Phase-2-Transaktionsstufe sowie Ressourcenverhalten auf der Ziel-NAS.
