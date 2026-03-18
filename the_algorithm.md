# Vokabeltrainer Algorithmus

## Übersicht

Der Vokabeltrainer verwendet einen **prioritätsbasierten Lernalgorithmus** mit vier Pools. Das System lernt automatisch deine schwierigsten Vokabeln und zeigt sie häufiger, während bekannte Vokabeln seltener auftauchen.

## Kernkonzepte

### Endlos-Modus
- Es gibt keine Session-Begrenzung
- Das System wählt kontinuierlich die nächste Vokabel basierend auf Prioritäten
- du lernst so lange du willst

### Lernregeln

| Regel | Beschreibung |
|-------|--------------|
| **3x richtig** | Streak erhöht sich, bei Streak ≥ 3 = "Gelernt" |
| **1x falsch auf Gelernt/Gemeistert** | Sofort zurück in "Currently Learning" |
| **Keine Wiederholung** | Eine Vokabel wird nicht direkt hintereinander gezeigt |

## Die Pools

### Pool 1: Currently Learning (🎯)
**Wahrscheinlichkeit: 60%**

Enthält:
- 6 Vokabeln mit der niedrigsten Confidence
- Vokabeln die von "Gelernt" oder "Gemeistert" zurückgesetzt wurden (negative_streak > 0)
- Vokabeln mit aktiver Streak (1-2), aber noch nicht gelernt

**Warum 60%?** Die meisten Vokabeln die du übst sollten die sein, die du wirklich lernen musst.

### Pool 2: Rest
**Wahrscheinlichkeit: 30%**

Enthält:
- Alle Vokabeln die nicht in Currently Learning, Gelernt oder Gemeistert sind
- Inklusive Vokabeln die du noch nie gesehen hast
- Sortiert nach Confidence (schlechteste zuerst)

**Warum 30%?** Mischung aus anderen Vokabeln für Abwechslung, aber nicht zu häufig.

### Pool 3: Gelernt (✓)
**Wahrscheinlichkeit: 8%**

Vokabeln mit Streak ≥ 3.
- Diese Vokabeln sind stabil gelernt
- Werden gelegentlich gezeigt um sie im Gedächtnis zu behalten
- Bei 1x falsch → sofort zurück in Currently Learning

### Pool 4: Gemeistert (⭐)
**Wahrscheinlichkeit: 2%**

Vokabeln mit Streak ≥ 5.
- Sehr selten gezeigt, nur um sie nicht komplett zu vergessen
- Bei 1x falsch → sofort zurück in Currently Learning

## Der Algorithmus (Schritt für Schritt)

```
1. Kategorisiere alle Vokabeln in Pools:

   Currently Learning:
   - negative_streak > 0 (von oben zurückgesetzt)
   - streak > 0 AND streak < 3 (in Lernphase)
   - Wenn < 6: Fülle mit schlechtesten aus Rest auf

   Rest:
   - Alle Vokabeln nicht in anderen Pools
   - Inkl. nie gesehene Vokabeln

   Gelernt: streak >= 3

   Gemeistert: streak >= 5


2. Würfele eine Zahl zwischen 0 und 1

3. Wähle basierend auf Wahrscheinlichkeit:
   - 0.00 - 0.60 → Currently Learning (60%)
   - 0.60 - 0.90 → Rest (30%)
   - 0.90 - 0.98 → Gelernt (8%)
   - 0.98 - 1.00 → Gemeistert (2%)

4. Zeige die gewählte Vokabel

5. Nach Antwort:
   - Richtig: streak++, wenn streak >= 3 → ist jetzt "Gelernt"
   - Falsch: streak = 0, negative_streak++, 
             Wenn vorher Gelernt/Gemeistert → sofort zurück in Currently Learning

6. Zurück zu Schritt 2
```

## Datenmodell

### UserWordStats Fields

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `streak` | int | Anzahl korrekter Antworten in Folge |
| `is_learned` | bool | true wenn Streak ≥ 3 erreicht |
| `negative_streak` | int | Anzahl falscher Antworten seit letztem Erfolg |
| `times_reviewed` | int | Wie oft geübt |
| `times_shown` | int | Wie oft gezeigt |
| `last_reviewed` | datetime | Letzte Übung |
| `next_review` | datetime | Für Spaced Repetition (geplant) |

## API Endpoints

### `POST /api/get_next_word`
Gibt die nächste Vokabel basierend auf dem Algorithmus zurück.

**Request:**
```json
{
  "lessons": [1, 2, 3],
  "last_word_id": 42
}
```

**Response:**
```json
{
  "id": 42,
  "latin": "amare",
  "german": "lieben",
  "streak": 2,
  "tier": "learning",
  "confidence": 0.75,
  "is_learned": false,
  "learning_pool_size": 6,
  "rest_pool_size": 85,
  "mastered_count": 10,
  "learned_count": 25
}
```

### `POST /api/submit_result`
Sendet das Ergebnis einer Antwort.

**Request:**
```json
{
  "word_id": 42,
  "correct": true
}
```

**Response:**
```json
{
  "status": "success",
  "confidence": 0.875,
  "streak": 3,
  "is_learned": true,
  "just_learned": true,
  "demoted": false,
  "tier_change": "learned",
  "lesson_progress": {
    "learned": 26,
    "total": 100,
    "percent": 26
  }
}
```

### `POST /api/get_learning_status`
Gibt den aktuellen Lernfortschritt zurück.

**Response:**
```json
{
  "total": 100,
  "rest": 50,
  "learning": 6,
  "learned": 35,
  "mastered": 9,
  "learning_words": [...],
  "overall_progress": 44
}
```

## UI Anzeigen

| Anzeige | Beschreibung |
|---------|--------------|
| 🔥🔥 | Streak-Indikator (Anzahl = Streak) |
| 🎯 Lernend | Currently Learning Pool |
| 💤 Rest | Rest Pool |
| ✓ Gelernt | Streak ≥ 3 |
| ⭐ Gemeistert | Streak ≥ 5 |

## Pool-Farben im UI

| Pool | Farbe |
|------|-------|
| Currently Learning | 🔴 Rot |
| Rest | ⚪ Grau |
| Gelernt | 🟢 Grün |
| Gemeistert | 🟣 Lila |

## Tastenkürzel

| Taste | Aktion |
|-------|--------|
| Leertaste | Übersetzung anzeigen |
| ↑ (Pfeil hoch) | Richtig |
| ↓ (Pfeil runter) | Falsch |
| S | Session-Statistik anzeigen |
| H | Hilfe ein-/ausblenden |

## Geplante Features

- [ ] Spaced Repetition Integration (next_review nutzen)
- [ ] Tägliche Review-Erinnerungen
- [ ] Fortschritts-Charts
- [ ] Export/import von Lernstatistiken
- [ ] Multi-User Vergleich (optional)
