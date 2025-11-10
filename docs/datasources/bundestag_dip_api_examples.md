# Bundestag DIP API - Terminal Examples

This document provides ready-to-use terminal commands for exploring the comprehensive DIP (Documentation and Information System) Bundestag API.

## Prerequisites

These examples use:
- `curl`: HTTP client
- `jq`: JSON processor (install with `brew install jq` on macOS)

## API Key

All examples use the public test API key (valid until May 2026):
`OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw`

## Quick Start Examples

### 1. Get Recent Proceedings (Vorgänge)

List proceedings from the 20th Wahlperiode:

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

### 2. Get Plenary Protocols

List recent parliamentary session transcripts:

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

### 3. Get Printed Materials (Drucksachen)

List official documents from current period:

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

### 4. Get Full Text of Protocol

Retrieve complete stenographic transcript:

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/5701?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

### 5. Search for Specific Person

Find information about a parliament member:

```bash
curl -s "https://search.dip.bundestag.de/api/v1/person?f.id=40&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

## Resource-Specific Examples

### Vorgänge (Proceedings)

#### List All Proceedings with Count

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '{total: .numFound, count: (.documents | length), first_id: .documents[0].id}'
```

#### Get Specific Proceeding by ID

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang/320244?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Filter by Date Range

Get proceedings from specific time period:

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&f.datum.start=2025-01-01&f.datum.end=2025-03-31&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Extract Proceeding Summaries

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | {id, titel, vorgangstyp, datum, sachgebiet}]' | head -100
```

#### Find Legislation (Gesetzgebung)

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.vorgangstyp == "Gesetzgebung") | {id, titel, datum}]' | head -50
```

### Drucksachen (Printed Materials)

#### List All Document Types

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[].drucksachetyp] | unique'
```

#### Get Bills (Gesetzentwürfe)

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&f.drucksachetyp=Gesetzentwurf&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Get Government Responses (Antworten)

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&f.drucksachetyp=Antwort&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Get Specific Document by Number

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.dokumentnummer=20/15151&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Extract PDF URLs

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.documents[] | {number: .dokumentnummer, pdf: .fundstelle.pdf_url}' | head -20
```

#### Get Documents by Ministry (Ressort)

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.ressort[]?.titel == "Auswärtiges Amt") | {nummer: .dokumentnummer, titel}]' | head -50
```

### Plenarprotokolle (Plenary Protocols)

#### List Recent Sessions

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.documents[0:10] | [.[] | {session: .dokumentnummer, date: .datum, topics: .vorgangsbezug_anzahl}]'
```

#### Get Bundestag vs Bundesrat Protocols

Bundestag only:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.herausgeber == "BT") | {session: .dokumentnummer, date: .datum}]' | head -50
```

Bundesrat only:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.herausgeber == "BR") | {session: .dokumentnummer, date: .datum}]' | head -50
```

#### Get Protocol with Related Proceedings

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll/5701?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '{session: .dokumentnummer, date: .datum, topics: [.vorgangsbezug[] | {id, titel, typ: .vorgangstyp}]}'
```

#### Extract Protocol Download Links

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.documents[] | select(.herausgeber == "BT") | {session: .dokumentnummer, pdf: .fundstelle.pdf_url, xml: .fundstelle.xml_url}' | head -40
```

### Plenarprotokoll-Text (Full Transcript)

#### Get Complete Transcript

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/5701?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Extract Just the Text

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/5701?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.text' | head -100
```

#### Save Full Transcript to File

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/5701?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.text' > protokoll_20_214.txt
```

#### Get Transcript Metadata

```bash
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/5701?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq 'del(.text) | .'
```

### Personen (Persons)

#### Search for Person by ID

```bash
curl -s "https://search.dip.bundestag.de/api/v1/person?f.id=40&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### List All Persons (First Page)

```bash
curl -s "https://search.dip.bundestag.de/api/v1/person?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.documents[0:20] | [.[] | {id, name: "\(.vorname) \(.nachname)", fraktion, funktion}]'
```

#### Extract Person Roles

```bash
curl -s "https://search.dip.bundestag.de/api/v1/person?f.id=40&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.documents[0].person_roles'
```

#### Find MPs from Specific Party

```bash
curl -s "https://search.dip.bundestag.de/api/v1/person?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.fraktion[]? == "BÜNDNIS 90/DIE GRÜNEN") | {name: "\(.vorname) \(.nachname)", wahlperiode}]' | head -50
```

### Vorgangspositionen (Proceeding Positions)

#### List Positions for Electoral Period

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgangsposition?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

#### Get Specific Position

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgangsposition/[ID]?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

### Aktivitäten (Activities)

#### List Recent Activities

```bash
curl -s "https://search.dip.bundestag.de/api/v1/aktivitaet?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

## Pagination Examples

### Basic Pagination Pattern

```bash
# Get first page
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '{cursor, numFound, count: (.documents | length)}'
```

### Extract and Use Cursor

```bash
# Save cursor to variable
CURSOR=$(curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.cursor')

echo "Cursor: $CURSOR"

# Use cursor for next page
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&cursor=$CURSOR&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '{cursor, count: (.documents | length)}'
```

### Paginate Through All Results (Shell Script)

```bash
#!/bin/bash

APIKEY="OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
WAHLPERIODE=20
ENDPOINT="vorgang"
CURSOR=""
PAGE=1

echo "Fetching all ${ENDPOINT} for Wahlperiode ${WAHLPERIODE}..."

while true; do
  echo "Fetching page $PAGE..."

  if [ -z "$CURSOR" ]; then
    URL="https://search.dip.bundestag.de/api/v1/${ENDPOINT}?f.wahlperiode=${WAHLPERIODE}&apikey=${APIKEY}"
  else
    URL="https://search.dip.bundestag.de/api/v1/${ENDPOINT}?f.wahlperiode=${WAHLPERIODE}&cursor=${CURSOR}&apikey=${APIKEY}"
  fi

  RESPONSE=$(curl -s "$URL")
  NEW_CURSOR=$(echo "$RESPONSE" | jq -r '.cursor // empty')
  COUNT=$(echo "$RESPONSE" | jq '.documents | length')

  echo "Got $COUNT documents"
  echo "$RESPONSE" > "${ENDPOINT}_page_${PAGE}.json"

  # Check if cursor is empty or unchanged
  if [ -z "$NEW_CURSOR" ] || [ "$CURSOR" = "$NEW_CURSOR" ]; then
    echo "Reached end of results"
    break
  fi

  CURSOR="$NEW_CURSOR"
  PAGE=$((PAGE + 1))

  # Be respectful to the API
  sleep 1
done

echo "Downloaded $PAGE pages total"
```

## Filtering Examples

### By Date Range

Recent proceedings:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&f.datum.start=2025-03-01&f.datum.end=2025-03-31&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.numFound'
```

### By Update Date (Incremental Sync)

Get documents updated since specific date:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.aktualisiert.start=2025-03-15&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '{total: .numFound, recent: [.documents[0:5] | .[] | {id, titel, aktualisiert}]}'
```

### By Document Number

Specific document:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.dokumentnummer=20/15096&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

### By Proceeding Reference

Find documents related to specific proceeding:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.vorgang=320244&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.'
```

## Analysis Examples

### Count Documents by Type

```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[].drucksachetyp] | group_by(.) | map({type: .[0], count: length}) | sort_by(.count) | reverse'
```

### Extract Subject Areas (Sachgebiete)

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[].sachgebiet[]?] | unique | sort' | head -50
```

### Find Government Initiatives

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.initiative[]? == "Bundesregierung") | {id, titel, datum}]' | head -50
```

### Track Proceeding Status

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[].beratungsstand] | group_by(.) | map({status: .[0], count: length})'
```

### Find Proceedings with Keywords

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '[.documents[] | select(.deskriptor[]?.name | test("Klima|Energie")) | {id, titel, keywords: [.deskriptor[].name]}]' | head -100
```

## Data Export Examples

### Export to CSV

Extract proceedings to CSV:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.documents[] | [.id, .datum, .vorgangstyp, .titel] | @csv' > vorgaenge.csv
```

Export documents with PDF links:
```bash
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq -r '.documents[] | [.dokumentnummer, .datum, .drucksachetyp, .fundstelle.pdf_url] | @csv' > drucksachen.csv
```

### Save Complete JSON

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang/320244?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.' > vorgang_320244.json
```

### Create Document Inventory

```bash
#!/bin/bash

APIKEY="OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"

echo "Resource,Total Count" > dip_inventory.csv

for resource in vorgang vorgangsposition drucksache plenarprotokoll person aktivitaet; do
  count=$(curl -s "https://search.dip.bundestag.de/api/v1/${resource}?f.wahlperiode=20&apikey=${APIKEY}" | jq -r '.numFound // "N/A"')
  echo "${resource},${count}" >> dip_inventory.csv
  echo "${resource}: ${count}"
  sleep 1
done

cat dip_inventory.csv
```

## Relationship Traversal Examples

### Get Proceeding and All Related Documents

```bash
# Get proceeding
VORGANG_ID=320244
curl -s "https://search.dip.bundestag.de/api/v1/vorgang/${VORGANG_ID}?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" > vorgang.json

# Find related drucksachen
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.vorgang=${VORGANG_ID}&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" > related_drucksachen.json

# Display summary
echo "Proceeding:"
jq '.titel' vorgang.json
echo -e "\nRelated Documents:"
jq '.documents[] | {nummer: .dokumentnummer, typ: .drucksachetyp, datum}' related_drucksachen.json
```

### Find All Protocols Discussing a Topic

```bash
# Get protocols mentioning specific proceeding
curl -s "https://search.dip.bundestag.de/api/v1/plenarprotokoll?f.vorgang=320785&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '.documents[] | {session: .dokumentnummer, date: .datum, pdf: .fundstelle.pdf_url}'
```

## Advanced Examples

### Monitor Recent Changes

Check for updates in last 24 hours:
```bash
YESTERDAY=$(date -u -v-1d +"%Y-%m-%dT%H:%M:%S")

curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.aktualisiert.start=${YESTERDAY}&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq '{total: .numFound, changes: [.documents[] | {id, titel, aktualisiert}]}'
```

### Download All PDFs for a Proceeding

```bash
#!/bin/bash

VORGANG_ID=320244
APIKEY="OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"

mkdir -p pdfs_${VORGANG_ID}

# Get related documents
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.vorgang=${VORGANG_ID}&apikey=${APIKEY}" | \
  jq -r '.documents[] | .fundstelle.pdf_url' | \
  while read url; do
    filename=$(basename "$url")
    echo "Downloading $filename..."
    curl -s "$url" -o "pdfs_${VORGANG_ID}/${filename}"
    sleep 1
  done

echo "PDFs saved to pdfs_${VORGANG_ID}/"
```

### Build Proceeding Timeline

```bash
VORGANG_ID=320244
APIKEY="OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"

echo "=== Proceeding Timeline ==="
echo ""

# Get proceeding info
curl -s "https://search.dip.bundestag.de/api/v1/vorgang/${VORGANG_ID}?apikey=${APIKEY}" | \
  jq -r '"\(.datum): \(.titel)\nType: \(.vorgangstyp)\nStatus: \(.beratungsstand)\n"'

echo "=== Related Documents ==="
curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.vorgang=${VORGANG_ID}&apikey=${APIKEY}" | \
  jq -r '.documents | sort_by(.datum) | .[] | "\(.datum): \(.drucksachetyp) \(.dokumentnummer)"'
```

### Compare Two Electoral Periods

```bash
APIKEY="OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"

echo "Wahlperiode,Total Vorgänge,Total Drucksachen"

for wp in 19 20; do
  vorgaenge=$(curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=${wp}&apikey=${APIKEY}" | jq -r '.numFound')
  drucksachen=$(curl -s "https://search.dip.bundestag.de/api/v1/drucksache?f.wahlperiode=${wp}&apikey=${APIKEY}" | jq -r '.numFound')
  echo "${wp},${vorgaenge},${drucksachen}"
  sleep 1
done
```

## Troubleshooting Examples

### Test API Connectivity

```bash
curl -I "https://search.dip.bundestag.de/api/v1/"
```

### Validate API Key

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=invalid_key" | jq '.'
# Should return 401 error
```

### Check Response Time

```bash
time curl -s "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" > /dev/null
```

### Verify JSON Structure

```bash
curl -s "https://search.dip.bundestag.de/api/v1/vorgang/320244?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" | jq empty && echo "Valid JSON" || echo "Invalid JSON"
```

### Debug with Verbose Output

```bash
curl -v "https://search.dip.bundestag.de/api/v1/vorgang?f.wahlperiode=20&apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw" 2>&1 | head -50
```

## Performance Tips

1. **Use Specific Filters:** Reduce result sets with filters
   ```bash
   # Better: filtered query
   curl -s "...?f.wahlperiode=20&f.datum.start=2025-03-01"

   # Avoid: unfiltered query
   curl -s "...?apikey=..."
   ```

2. **Fetch Metadata First, Full Text Later:**
   ```bash
   # Step 1: Get list
   curl -s ".../plenarprotokoll?..." | jq '.documents[].id' > ids.txt

   # Step 2: Fetch full text for relevant IDs only
   cat ids.txt | while read id; do
     curl -s ".../plenarprotokoll-text/${id}?..."
   done
   ```

3. **Cache Results Locally:**
   ```bash
   # Check if cached
   if [ ! -f "cache_vorgang_20.json" ]; then
     curl -s "..." > cache_vorgang_20.json
   fi
   cat cache_vorgang_20.json | jq '.'
   ```

4. **Implement Rate Limiting:**
   ```bash
   for id in $(seq 1 100); do
     curl -s ".../${id}?..."
     sleep 0.5  # 2 requests/second
   done
   ```

## Quick Reference

| Task | Command Template |
|------|------------------|
| List proceedings | `curl -s ".../vorgang?f.wahlperiode=20&apikey=..."` |
| Get by ID | `curl -s ".../vorgang/{id}?apikey=..."` |
| Filter by date | `...?f.datum.start=YYYY-MM-DD&f.datum.end=YYYY-MM-DD` |
| Get updates | `...?f.aktualisiert.start=YYYY-MM-DD` |
| Paginate | `...?cursor={cursor}` |
| Get full text | `curl -s ".../plenarprotokoll-text/{id}?apikey=..."` |
| Export to CSV | `jq -r '[...] \| @csv'` |
| Count results | `jq '.numFound'` |
| Extract field | `jq '.documents[].titel'` |

## Next Steps

After exploring with these examples:

1. Review the full API documentation: [bundestag_dip_api.md](bundestag_dip_api.md)
2. Plan your data extraction strategy
3. Identify which resources are most valuable for your use case
4. Design your document schema and metadata fields
5. Implement pagination for bulk extraction
6. Consider incremental updates using `f.aktualisiert.start`
