# ZoomOut

Errate das Gemälde. Du startest tief in ein berühmtes Bild gezoomt — jeder
Zoom-Schritt nach außen kostet Punkte, jeder Fehltipp auch. Wer ohne einen
einzigen Zoom richtig rät, nimmt die vollen 1000.

Ein Einzeldatei-Webspiel, mobile-first: `index.html` in einem beliebigen Browser
öffnen und spielen. Kein Build, kein Server, keine Abhängigkeiten.

> Privates Gestaltungs-Mockup, kein Produkt und keine Veröffentlichung eines
> Verlags. Die Oberfläche ist bewusst dem Dark Mode einer Nachrichten-App
> nachempfunden — als Fingerübung, wie sich ein Spiel in eine solche Umgebung
> einfügen würde.

## Wie es funktioniert

- 50 berühmte gemeinfreie Gemälde, Bilder direkt von Wikimedia Commons geladen.
- **Zoom** halten (oder aufziehen) und herauszoomen — flüssig und nur in eine
  Richtung: zurück geht es nicht. **Raten** öffnet das Eingabefeld
  (Vorschläge über Titel und Künstler), **Aufgeben** beendet die Runde.
- Von ×12 auf Vollbild sind es rund 9 Sekunden Halten.
- Auf das Bild tippen blendet die Bedienung aus, wenn du einfach nur schauen willst.

## Die Punkte

- **1000**, wenn du gar nicht erst zoomst.
- Sobald du zoomst, kostet das erst einmal pauschal **200** — der Preis dafür,
  den Mut-Bonus aufzugeben. Danach geht es von 800 auf 100 hinunter.
- **Preis pro Verdopplung:** Jede Halbierung der Zoomstufe kostet gleich viel
  (rund 195 Punkte). Das ist bewusst nicht linear: Was du erkennen kannst, hängt
  an der sichtbaren *Fläche*, und die wächst quadratisch. Linear nach Zoomstufe
  abgerechnet wäre die Hälfte des Guthabens zwischen ×12 und ×6 verbrannt — also
  dort, wo statt 0,7 % gerade einmal 2,8 % des Bildes zu sehen sind und noch
  nichts zu erkennen ist. So sind die frühen, blinden Schritte billig und die
  letzten, verräterischen teuer.
- **Reaktionsrabatt:** Beim Loslassen federt das Bild die letzten 0,3 Sekunden
  zurück. Die Zeit zwischen „ich erkenne es!" und „Finger hoch" soll nichts
  kosten. Jeder Druck bewirkt dabei mindestens so viel wie ein kurzer Tipp
  (−4 %), damit ein kurzer Druck nicht wirkungslos verpufft.
- **Fehltipp** kostet 15 % des aktuellen Standes — sticht immer gleich stark,
  ruiniert aber nie eine Runde.

## Sprache und Daten

Oberfläche, Titel, Epochen und Infotexte sind deutsch. Die englischen Titel
bleiben als unsichtbare Suchhilfe erhalten: Wer „The Scream" tippt, findet
„Der Schrei".

Die Infotexte stammen aus der deutschen Wikipedia. Vier Gemälde haben dort
keinen eigenen Artikel — sie kommen nur in Sammelartikeln vor — und tragen
deshalb eine von Hand eingetragene Übersetzung der englischen Zusammenfassung
(siehe `DESC_DE` in `generate.py`). Nichts davon wird zur Laufzeit übersetzt:
Das Spiel kommt ohne Dienste aus.

## Gestaltung

Die Farben sind aus einem Screenshot der Vorlage-App Pixel für Pixel gemessen,
nicht geschätzt: Grund `#111111`, Karten `#212121`, Linien `#2C2C2C`, Text
`#F5F6F6`, Signalrot `#E0352F`. Die Grautöne sind exakt neutral.

Die Hausschriften der Vorlage sind Kaufschriften und hier nicht verwendet —
stattdessen die nächste Näherung, die auf Mac und iPhone vorinstalliert ist:
Helvetica Neue für Headlines und Oberfläche, Charter für Fließtext. So bleibt
das Spiel eine eigenständige Datei, die nichts nachlädt.

Die Auflösung ist als Ergebnis gebaut, nicht als Artikel: Bild (immer
vollständig, egal welches Format), Titel, Datenzeile, Punktekasten, Infotext.

## Entwicklung

`generate.py` (Python 3, nur Standardbibliothek) frischt die Gemäldedaten auf
und schreibt sie in `index.html` zwischen die Marken `PAINTINGS:START/END`.
Die Liste `CURATED` bestimmt das Feld; jede Zeile nennt zwei Wikipedia-Artikel:
den englischen (liefert das Bild) und den deutschen (liefert den Text). Ein
erneuter Lauf erhält von Hand gesetzte `focal`- und `startScale`-Werte, gematcht
über den Anzeigetitel. Das Spiel selbst braucht kein Python.

Alle Gemälde sind gemeinfrei; die Beschreibungen stammen aus der Wikipedia
(CC BY-SA), die vier Übersetzungen sind Bearbeitungen davon.
