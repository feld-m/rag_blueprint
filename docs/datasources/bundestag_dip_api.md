# Bundestag DIP API Documentation

## Overview

The **DIP (Dokumentations- und Informationssystem für Parlamentsmaterialien)** API is the official German Bundestag API providing comprehensive access to parliamentary materials, activities, and information. This is the most complete and authoritative source for Bundestag data.

**Official Name:** Documentation and Information System for Parliamentary Materials
**Provider:** Deutscher Bundestag (German Federal Parliament)
**API Version:** 1.2
**OpenAPI Specification:** https://dip.bundestag.api.bund.dev/openapi.yaml

## Why Use This API?

The DIP API is **the most comprehensive Bundestag data source** available, providing:

- **Full Parliamentary Proceedings (Vorgänge):** Complete legislative processes from start to finish
- **Printed Materials (Drucksachen):** Bills, motions, government responses, reports
- **Full-Text Content:** Complete text of plenary protocols and printed materials
- **Person Data:** MPs, ministers, and other parliamentary actors
- **Activity Tracking:** All parliamentary activities and positions
- **Structured Metadata:** Rich relational data connecting all resources

This is **significantly more comprehensive** than specialized APIs like:
- Bundestag Lobby Register (only lobbying data)
- Bundestag Mine (only speech data)

## API Specifications

### Base Information

- **Base URL:** `https://search.dip.bundestag.de/api/v1`
- **Data Formats:** JSON (primary), XML (alternative)
- **OpenAPI Docs:** https://dip.bundestag.api.bund.dev/
- **Terms of Service:** https://dip.bundestag.de/über-dip/nutzungsbedingungen
- **Support Contact:** parlamentsdokumentation@bundestag.de

### Authentication

**Required:** API key for all requests

**Public Test Key (valid until May 2026):**
`OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw`

**Request Permanent Key:**
Email: parlamentsdokumentation@bundestag.de

**Implementation Methods:**

1. **HTTP Header (recommended):**
   ```
   Authorization: ApiKey OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw
   ```

2. **Query Parameter:**
   ```
   ?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw
   ```

### Rate Limiting

No explicit rate limiting documented. Best practices:
- Implement reasonable request delays
- Use cursor-based pagination efficiently
- Cache results appropriately
- Be respectful of API resources

## Available Resources and Endpoints

The API provides 8 main resource types with 16 endpoints:

### 1. Vorgänge (Proceedings/Processes)

Legislative and parliamentary processes from initiation to completion.

**Endpoints:**
- `GET /vorgang` - List all proceedings (with filters)
- `GET /vorgang/{id}` - Get specific proceeding by ID

**Use Cases:**
- Track legislation through the parliamentary process
- Monitor bills, motions, and resolutions
- Analyze legislative activity by topic or party

**Example Data:**
- Legislative type (Gesetzgebung, Antrag, etc.)
- Status (in debate, completed, rejected)
- Subject areas (Sachgebiet)
- Initiators (Bundesregierung, parties, Bundesrat)
- Associated documents and protocols

### 2. Vorgangspositionen (Proceeding Positions)

Individual positions/steps within a larger proceeding.

**Endpoints:**
- `GET /vorgangsposition` - List all positions (with filters)
- `GET /vorgangsposition/{id}` - Get specific position by ID

**Use Cases:**
- Track individual steps in legislative process
- Monitor committee activities
- Analyze procedural timeline

### 3. Drucksachen (Printed Materials)

Official printed documents (bills, motions, reports, responses).

**Endpoints:**
- `GET /drucksache` - List all printed materials (with filters)
- `GET /drucksache/{id}` - Get specific material by ID

**Document Types (Drucksachetyp):**
- Gesetzentwurf (Bill)
- Antrag (Motion)
- Kleine Anfrage (Minor Inquiry)
- Große Anfrage (Major Inquiry)
- Antwort (Response)
- Beschlussempfehlung und Bericht (Recommendation and Report)
- Unterrichtung (Information/Notification)
- And many more...

**Use Cases:**
- Access official government documents
- Retrieve bills and legislative proposals
- Get responses to parliamentary inquiries

### 4. Drucksache-Text (Printed Material Full Text)

Full-text content of printed materials.

**Endpoints:**
- `GET /drucksache-text` - List materials with full text (with filters)
- `GET /drucksache-text/{id}` - Get specific material with full text

**Use Cases:**
- Full-text search in parliamentary documents
- Extract complete document content for RAG
- Analyze actual legislative language

### 5. Plenarprotokolle (Plenary Protocols)

Official transcripts of parliamentary sessions.

**Endpoints:**
- `GET /plenarprotokoll` - List all protocols (with filters)
- `GET /plenarprotokoll/{id}` - Get specific protocol by ID

**Publishers (Herausgeber):**
- BT (Bundestag)
- BR (Bundesrat)

**Use Cases:**
- Access official session transcripts
- Track debates on specific topics
- Analyze parliamentary discourse

**Key Fields:**
- Session number (dokumentnummer)
- Date of session
- PDF URL and XML URL (for Bundestag)
- Associated proceedings (vorgangsbezug)
- PDF and XML hashes for integrity

### 6. Plenarprotokoll-Text (Plenary Protocol Full Text)

Complete stenographic records with full text.

**Endpoints:**
- `GET /plenarprotokoll-text` - List protocols with full text (with filters)
- `GET /plenarprotokoll-text/{id}` - Get protocol with complete text

**Content Includes:**
- Stenographic transcript
- Speaker identification
- Procedural notes
- Interruptions and remarks
- Voting results

**Use Cases:**
- Full-text search in parliamentary debates
- Speech analysis and attribution
- RAG applications with complete debate context

### 7. Aktivitäten (Activities)

Parliamentary activities and actions.

**Endpoints:**
- `GET /aktivitaet` - List all activities (with filters)
- `GET /aktivitaet/{id}` - Get specific activity by ID

**Use Cases:**
- Track specific parliamentary actions
- Monitor committee activities
- Analyze procedural steps

### 8. Personen (Persons)

Members of Parliament, ministers, and other parliamentary actors.

**Endpoints:**
- `GET /person` - List all persons (with filters)
- `GET /person/{id}` - Get specific person by ID

**Data Includes:**
- Name and function (MdB - Member of Bundestag, etc.)
- Party/Fraction (Fraktion)
- Electoral periods served (Wahlperiode)
- Historical role information

**Use Cases:**
- Link documents to specific MPs
- Track individual parliamentary activity
- Analyze party membership and roles

## Query Parameters and Filtering

All list endpoints support filtering parameters (prefixed with `f.`):

### Common Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `f.id` | string | Filter by ID | `f.id=320244` |
| `f.wahlperiode` | integer | Electoral period number | `f.wahlperiode=20` |
| `f.datum.start` | date | Start date (YYYY-MM-DD) | `f.datum.start=2024-01-01` |
| `f.datum.end` | date | End date (YYYY-MM-DD) | `f.datum.end=2024-12-31` |
| `f.aktualisiert.start` | datetime | Updated after | `f.aktualisiert.start=2025-03-01` |
| `f.aktualisiert.end` | datetime | Updated before | `f.aktualisiert.end=2025-03-31` |
| `f.drucksache` | string | Document number | `f.drucksache=20/15096` |
| `f.plenarprotokoll` | string | Protocol number | `f.plenarprotokoll=20/214` |
| `f.dokumentnummer` | string | Document number | `f.dokumentnummer=20/214` |
| `f.dokumentart` | string | Document type | `f.dokumentart=Plenarprotokoll` |
| `f.drucksachetyp` | string | Print type | `f.drucksachetyp=Gesetzentwurf` |
| `f.zuordnung` | string | Assignment/classification | varies |
| `cursor` | string | Pagination cursor | (see Pagination) |
| `format` | string | Response format | `json` or `xml` |

### Resource-Specific Filters

**Vorgang:**
- `f.gesta` - GESTA procedure number

**Vorgangsposition:**
- `f.aktivitaet` - Activity ID
- `f.vorgang` - Proceeding ID

**Drucksache:**
- No additional specific filters beyond common ones

**Person:**
- No common filters apply (use ID-based lookup)

## Pagination

The API uses **cursor-based pagination** for efficient traversal of large result sets.

### How It Works

1. **Initial Request:** Make request without cursor parameter
2. **Response:** API returns results + `cursor` field
3. **Next Page:** Include returned cursor in next request
4. **End Detection:** When no more results, cursor may be empty or unchanged

### Important Notes

- **No page size control:** API determines result count per page
- **Cursor format:** Opaque Base64-encoded string
- **Stateful:** Cursor maintains query state
- **Expiration:** Cursors may expire; unclear documentation on timeout

### Pagination Pattern

```
GET /vorgang?f.wahlperiode=20&apikey={key}
→ Returns {numFound: 37666, cursor: "ABC123...", documents: [...]}

GET /vorgang?f.wahlperiode=20&cursor=ABC123...&apikey={key}
→ Returns next batch with new cursor

... repeat until all results fetched
```

## Response Structure

### List Response Format

All list endpoints return the same structure:

```json
{
  "numFound": 37666,
  "cursor": "AoQIQ4zX03n+rouj/w...",
  "documents": [
    { /* document object */ },
    { /* document object */ },
    ...
  ]
}
```

**Fields:**
- `numFound`: Total number of matching documents (may be null for some queries)
- `cursor`: Pagination token for next page
- `documents`: Array of document objects

### Detail Response Format

Single-item endpoints return the document object directly:

```json
{
  "id": "5701",
  "typ": "Dokument",
  "dokumentart": "Plenarprotokoll",
  "dokumentnummer": "20/214",
  /* ... other fields ... */
}
```

## Data Models

### Common Fields

Most resources share these fields:

- `id`: Unique identifier (string or integer)
- `typ`: Type (e.g., "Vorgang", "Dokument", "Person")
- `wahlperiode`: Electoral period number(s)
- `datum`: Date (YYYY-MM-DD)
- `aktualisiert`: Last update timestamp (ISO 8601)
- `titel`: Title or name

### Vorgang (Proceeding) Schema

```json
{
  "id": "320244",
  "typ": "Vorgang",
  "vorgangstyp": "Selbständiger Antrag von Ländern auf Entschließung",
  "titel": "Title of the proceeding",
  "abstract": "Summary description",
  "datum": "2025-09-26",
  "wahlperiode": 20,
  "initiative": ["Brandenburg"],  // Who initiated
  "beratungsstand": "In der Beratung...",  // Status
  "sachgebiet": ["Öffentliche Finanzen, Steuern und Abgaben"],  // Subject areas
  "deskriptor": [  // Keywords/descriptors
    {
      "name": "Steuerbefreiung",
      "typ": "Sachbegriffe",
      "fundstelle": true
    }
  ],
  "aktualisiert": "2025-10-15T11:06:54+02:00"
}
```

**Key Fields:**
- `vorgangstyp`: Type of proceeding (legislation, motion, report, etc.)
- `beratungsstand`: Current status in parliamentary process
- `initiative`: Initiating body (government, party, Bundesrat)
- `sachgebiet`: Policy areas
- `deskriptor`: Controlled vocabulary keywords
- `mitteilung`: Additional notes/messages

### Drucksache (Printed Material) Schema

```json
{
  "id": "279131",
  "typ": "Dokument",
  "dokumentart": "Drucksache",
  "drucksachetyp": "Antwort",
  "dokumentnummer": "20/15151",
  "wahlperiode": 20,
  "herausgeber": "BT",
  "titel": "Document title",
  "datum": "2025-03-26",
  "pdf_hash": "8321f919a809d05581eccb4ba5bdb8b3",
  "vorgangsbezug_anzahl": 1,
  "vorgangsbezug": [
    {
      "id": "320358",
      "titel": "Related proceeding title",
      "vorgangstyp": "Kleine Anfrage"
    }
  ],
  "urheber": [
    {
      "einbringer": false,
      "bezeichnung": "BRg",
      "titel": "Bundesregierung"
    }
  ],
  "ressort": [
    {
      "federfuehrend": true,
      "titel": "Auswärtiges Amt"
    }
  ],
  "fundstelle": {
    "pdf_url": "https://dserver.bundestag.de/btd/20/151/2015151.pdf",
    "id": "279131",
    "dokumentnummer": "20/15151",
    "datum": "2025-03-26",
    "verteildatum": "2025-04-01"
  },
  "autoren_anzahl": 0,
  "aktualisiert": "2025-04-01T08:01:10+02:00"
}
```

**Key Fields:**
- `drucksachetyp`: Type (Bill, Motion, Inquiry, Response, Report, etc.)
- `herausgeber`: Publisher (BT=Bundestag, BR=Bundesrat)
- `urheber`: Authors/originators
- `ressort`: Responsible ministry/department
- `fundstelle`: Document location with PDF URL
- `vorgangsbezug`: Related proceedings
- `pdf_hash`: PDF file hash for integrity checking

### Plenarprotokoll (Plenary Protocol) Schema

```json
{
  "id": "5701",
  "typ": "Dokument",
  "dokumentart": "Plenarprotokoll",
  "dokumentnummer": "20/214",
  "wahlperiode": 20,
  "herausgeber": "BT",
  "titel": "Protokoll der 214. Sitzung des 20. Deutschen Bundestages",
  "datum": "2025-03-18",
  "pdf_hash": "adbabad803cbf3ca32661d5336d8281e",
  "xml_hash": "6e1e62918ae23f99e075c58803b1b183",
  "vorgangsbezug_anzahl": 12,
  "vorgangsbezug": [
    {
      "id": "320785",
      "titel": "Related proceeding",
      "vorgangstyp": "Gesetzgebung"
    }
  ],
  "fundstelle": {
    "id": "5701",
    "dokumentnummer": "20/214",
    "datum": "2025-03-18",
    "verteildatum": "2025-03-19",
    "pdf_url": "https://dserver.bundestag.de/btp/20/20214.pdf",
    "xml_url": "https://dserver.bundestag.de/btp/20/20214.xml",
    "dokumentart": "Plenarprotokoll",
    "herausgeber": "BT"
  },
  "aktualisiert": "2025-04-29T10:20:33+02:00"
}
```

**Key Fields:**
- `xml_url`: Structured XML version (Bundestag only)
- `pdf_url`: PDF version
- `xml_hash`, `pdf_hash`: File integrity hashes
- `vorgangsbezug`: Proceedings discussed in session
- `verteildatum`: Distribution date

**With Full Text (`/plenarprotokoll-text/{id}`):**
- Adds `text` field with complete stenographic transcript
- Includes speaker names, speeches, votes, procedures
- Plain text format with section markers

### Person Schema

```json
{
  "id": "40",
  "typ": "Person",
  "nachname": "Ströbele",
  "vorname": "Hans-Christian",
  "funktion": ["MdB"],
  "fraktion": ["BÜNDNIS 90/DIE GRÜNEN"],
  "wahlperiode": [10, 14, 15, 16, 17, 18],
  "titel": "Hans-Christian Ströbele, MdB, BÜNDNIS 90/DIE GRÜNEN",
  "datum": "2017-10-23",
  "basisdatum": "1985-04-15",
  "person_roles": [
    {
      "funktion": "MdB",
      "fraktion": "Die Grünen",
      "nachname": "Ströbele",
      "vorname": "Hans-Christian",
      "wahlperiode_nummer": [10]
    }
  ],
  "aktualisiert": "2022-07-26T19:57:10+02:00"
}
```

**Key Fields:**
- `funktion`: Role (MdB = Member of Bundestag, Minister, etc.)
- `fraktion`: Party/parliamentary group
- `wahlperiode`: Electoral periods served (array)
- `person_roles`: Historical role breakdown
- `basisdatum`: Base date (first appearance)

### Vorgangsposition Schema

Similar to Vorgang but represents a single step/position within a larger proceeding. Contains references to parent proceeding.

### Aktivität Schema

Represents specific parliamentary activities. Structure varies by activity type.

## Document Numbering System

Understanding document numbers is crucial for working with the API:

### Drucksache Numbers

Format: `{wahlperiode}/{number}`

Examples:
- `20/15151` - Wahlperiode 20, Document 15151
- `19/12345` - Wahlperiode 19, Document 12345

### Plenarprotokoll Numbers

**Bundestag:** `{wahlperiode}/{session}`
- Example: `20/214` - 214th session of 20th Bundestag

**Bundesrat:** `{session}`
- Example: `1052` - 1052nd session of Bundesrat

### Wahlperiode (Electoral Period)

The Bundestag operates in electoral periods (typically 4 years):
- **20th Wahlperiode:** 2021-2025 (current as of 2025)
- **19th Wahlperiode:** 2017-2021
- **18th Wahlperiode:** 2013-2017

Each period resets document numbering.

## Data Relationships

The API provides rich relational data:

```
Vorgang (Proceeding)
  ├─> Vorgangsposition (Positions)
  ├─> Drucksache (Printed Materials)
  ├─> Plenarprotokoll (Protocols)
  └─> Aktivität (Activities)

Drucksache
  ├─> Vorgang (Parent Proceeding)
  └─> PDF/Text Content

Plenarprotokoll
  ├─> Multiple Vorgänge (Discussed Proceedings)
  ├─> XML/PDF Files
  └─> Full Text Transcript

Person
  └─> Associated Documents (via authorship, speeches)
```

**Use `vorgangsbezug` to traverse relationships:**
- Documents link to their parent proceedings
- Protocols link to all discussed proceedings
- Positions link to parent proceedings and documents

## Use Cases for RAG/LLM Applications

The DIP API is ideal for building comprehensive parliamentary knowledge systems:

### 1. Legislative Tracking and Analysis
- Track bills from introduction to passage
- Analyze legislative timelines and bottlenecks
- Monitor specific policy areas

### 2. Full-Text Parliamentary Search
- Search across all speeches, documents, inquiries
- Semantic search on debate transcripts
- Answer questions about parliamentary positions

### 3. MP Activity and Behavior Analysis
- Track individual MP activities and votes
- Analyze party positions on issues
- Study parliamentary discourse patterns

### 4. Government Accountability
- Access all government responses to inquiries
- Track ministry activities and communications
- Monitor implementation of legislation

### 5. Historical Research
- Access complete parliamentary records
- Track policy evolution across electoral periods
- Analyze long-term political trends

### 6. Multi-Document Question Answering
- Connect debates to bills to votes to outcomes
- Provide comprehensive answers with full context
- Trace arguments across multiple sessions

## Metadata Recommendations for RAG

### Core Identification
- `document_id`: Unique identifier
- `document_type`: Vorgang, Drucksache, Plenarprotokoll, etc.
- `document_number`: Official number (e.g., 20/214)
- `wahlperiode`: Electoral period

### Content Context
- `title`: Document title
- `abstract`: Summary (if available)
- `sachgebiet`: Subject areas (for filtering)
- `deskriptor`: Keywords (for semantic grouping)

### Temporal Context
- `date`: Official date
- `updated`: Last modification date
- `distribution_date`: When distributed (verteildatum)

### Relational Context
- `related_proceeding_ids`: Linked proceedings
- `proceeding_type`: Type of legislative process
- `status`: Current state in process

### Authority Context
- `publisher`: BT or BR
- `authors`: Who created/submitted
- `responsible_ministry`: Ministry (Ressort)
- `initiator`: Who initiated (party, government, etc.)

### Document Location
- `pdf_url`: Link to PDF
- `xml_url`: Link to XML (if available)
- `pdf_hash`: For integrity checking

### For Speeches (from Plenarprotokoll-Text)
- `speaker`: Person who spoke
- `party`: Speaker's party
- `session_date`: When spoken
- `topic`: Related proceeding/agenda item

## Data Quality Considerations

### Completeness
- **Full text available:** Yes, for most documents via `-text` endpoints
- **Historical coverage:** Complete for recent Wahlperioden (18+), partial for earlier
- **Update frequency:** Real-time to daily updates
- **Missing data:** Some older documents may lack full text or XML

### Accuracy
- **Official source:** Direct from Bundestag; authoritative
- **Verification:** PDF/XML hashes provided for integrity
- **Corrections:** Updates reflected in `aktualisiert` timestamp

### Consistency
- **Structured format:** Well-defined schemas
- **Controlled vocabulary:** `deskriptor` uses standardized terms
- **ID stability:** IDs appear stable across requests

### Language
- **Primary language:** German
- **Translation:** Not provided; consider external translation for non-German users
- **Field names:** Mix of German (data) and some English (structure)

## Best Practices for Data Extraction

### 1. Incremental Updates
Use `f.aktualisiert.start` to fetch only recent changes:
```
GET /vorgang?f.aktualisiert.start=2025-03-01&apikey={key}
```

### 2. Filter by Electoral Period
Limit scope with `f.wahlperiode` for focused extraction:
```
GET /drucksache?f.wahlperiode=20&apikey={key}
```

### 3. Leverage Relationships
Use `vorgangsbezug` IDs to fetch related documents efficiently.

### 4. Full Text Strategy
- Start with metadata endpoints (faster)
- Fetch full text only for relevant documents
- Cache full text locally to avoid re-fetching

### 5. Pagination Pattern
```python
cursor = ""
while True:
    response = fetch_data(cursor)
    process_documents(response['documents'])
    new_cursor = response.get('cursor')
    if not new_cursor or new_cursor == cursor:
        break
    cursor = new_cursor
```

### 6. Error Handling
- Handle missing fields gracefully (not all documents have all fields)
- Retry on network errors
- Respect API rate limits (implement backoff)

### 7. Data Storage
- Store `pdf_hash`/`xml_hash` to detect changes
- Track `aktualisiert` for incremental updates
- Maintain relationships (vorgangsbezug IDs)

## Comparison: DIP vs. Other Bundestag APIs

| Feature | DIP API | Lobby Register | Bundestag Mine |
|---------|---------|----------------|----------------|
| **Scope** | Complete parliamentary data | Lobbying only | Speeches only |
| **Documents** | All types | Lobby entries | None |
| **Full Text** | Yes | N/A | Speech text |
| **Proceedings** | Complete | No | No |
| **Persons** | All MPs/Ministers | Lobbyists | Speakers |
| **Historical** | Full archives | From 2022 | Limited |
| **Relationships** | Rich | Minimal | Minimal |
| **Best For** | Comprehensive RAG | Transparency research | Speech analysis |

**Recommendation:** Use DIP as primary source; supplement with specialized APIs if needed.

## Technical Specifications

### HTTP Methods
- `GET` only (read-only API)

### Response Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found (invalid ID)

### Headers
```
Accept: application/json
Authorization: ApiKey {your-key}
```

### Content-Type
- Request: Not applicable (GET only)
- Response: `application/json` or `application/xml`

### Character Encoding
- UTF-8

### Date/Time Format
- Dates: `YYYY-MM-DD`
- Timestamps: ISO 8601 (`YYYY-MM-DDTHH:mm:ss+02:00`)

## Limitations and Considerations

### API Limitations
- **No full-text search:** API filters on metadata only; implement search in your application
- **No batch endpoints:** Must fetch documents individually or paginate lists
- **Cursor expiration:** Unclear; may need to restart pagination if cursor becomes invalid
- **No rate limit documentation:** Implement conservative rate limiting

### Data Limitations
- **German language:** All content in German; translation needed for multilingual applications
- **Historical gaps:** Very old documents may have limited metadata or missing full text
- **No sentiment/analysis:** Raw data only; NLP/analysis must be done client-side
- **Large full-text responses:** Protocol transcripts can be very long (100KB+)

### Practical Considerations
- **Storage requirements:** Full corpus is large (GB to TB range)
- **Processing time:** Complete extraction takes hours/days
- **Update frequency:** Check `aktualisiert` regularly for changes
- **PDF processing:** For documents without text endpoints, may need OCR

## Example Extraction Strategy

For building a comprehensive RAG system:

### Phase 1: Core Data (Metadata)
1. Extract all `vorgang` for recent Wahlperiode
2. Extract associated `drucksache` metadata
3. Extract `plenarprotokoll` metadata
4. Extract `person` data
5. Build relationship graph

### Phase 2: Full Text
1. Fetch `drucksache-text` for all documents
2. Fetch `plenarprotokoll-text` for all protocols
3. Parse and chunk text appropriately
4. Extract embedded metadata (speakers, votes, etc.)

### Phase 3: Incremental Updates
1. Query with `f.aktualisiert.start` daily
2. Update changed documents
3. Add new documents
4. Refresh relationships

### Phase 4: Enhancement
1. Add embeddings for semantic search
2. Link to external resources (PDF URLs)
3. Implement cross-document search
4. Build knowledge graph

## Contact and Support

- **Email:** parlamentsdokumentation@bundestag.de
- **Purpose:** API keys, technical support, usage questions
- **Terms of Service:** https://dip.bundestag.de/über-dip/nutzungsbedingungen

## Related Resources

- **DIP Web Interface:** https://dip.bundestag.de
- **OpenAPI Spec:** https://dip.bundestag.api.bund.dev/openapi.yaml
- **Interactive Docs:** https://dip.bundestag.api.bund.dev/
- **GitHub:** https://github.com/bundesAPI/dip-bundestag-api
- **Bundestag Document Server:** https://dserver.bundestag.de

## Summary

The DIP API is the **most comprehensive and authoritative source** for German Bundestag data. It provides:

✅ **Complete Coverage:** All parliamentary documents, proceedings, and activities
✅ **Full Text:** Complete transcripts and document text
✅ **Rich Metadata:** Structured, relational data
✅ **Official Source:** Direct from Bundestag
✅ **Well-Documented:** OpenAPI specification available
✅ **Free Access:** Public API key available

**Ideal for:** Comprehensive RAG systems, legislative tracking, parliamentary research, policy analysis, government accountability tools.
