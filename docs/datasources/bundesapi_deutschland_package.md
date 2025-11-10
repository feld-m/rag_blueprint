# bundesAPI "deutschland" Python Package Documentation

## Overview

The **deutschland** Python package provides unified, easy-to-use access to Germany's most important public datasets and APIs. Instead of dealing with multiple APIs individually, this package consolidates them into a single, consistent Python library with auto-generated clients for numerous German government and institutional data sources.

**Key Value Proposition:** One package, one installation, many APIs - all with consistent Python interfaces.

**Official Resources:**
- **GitHub:** https://github.com/bundesAPI/deutschland
- **PyPI:** https://pypi.org/project/deutschland/
- **Version:** 0.4.2 (released June 18, 2024)
- **License:** Apache-2.0
- **Maintainer:** Lilith Wittmann (bundesAPI)

## Why Use This Package?

### Advantages Over Direct API Access

✅ **Unified Interface:** Consistent Python API across all German government data sources
✅ **Type Safety:** Auto-generated Pydantic models for all data structures
✅ **No Manual HTTP:** Handle authentication, pagination, and errors automatically
✅ **IDE Support:** Full autocomplete and type hints in modern IDEs
✅ **Maintained:** Regular updates when APIs change
✅ **Tested:** Runs on Linux, macOS, and Windows (Python 3.9-3.12)
✅ **Well-Documented:** Generated documentation for all models and methods

### Comparison with Direct REST API Access

| Feature | deutschland Package | Direct REST API |
|---------|---------------------|-----------------|
| **Installation** | `pip install deutschland` | Manual HTTP library setup |
| **Authentication** | Configured once in code | Manual headers every request |
| **Data Models** | Pydantic models with validation | Manual dict parsing |
| **Type Hints** | Full IDE support | None |
| **Error Handling** | Structured exceptions | Manual HTTP error handling |
| **Pagination** | Often handled automatically | Manual cursor management |
| **Updates** | `pip install --upgrade` | Rewrite code when API changes |
| **Learning Curve** | Python-native, intuitive | Learn each API's quirks |

## Installation

### Basic Installation

```bash
pip install deutschland
```

This installs the core package with essential APIs (bundestag, bundesrat, autobahn, dwd, nina, and more).

### With Optional APIs

Many APIs are optional extras to keep the base package lightweight:

```bash
# Install with DIP Bundestag API
pip install deutschland[dip_bundestag]

# Install with Bundestag Lobby Register
pip install deutschland[bundestag_lobbyregister]

# Install with Bundestag Tagesordnung (agenda)
pip install deutschland[bundestag_tagesordnung]

# Install multiple extras
pip install deutschland[dip_bundestag,bundestag_lobbyregister,bundestag_tagesordnung]

# Install ALL extras (comprehensive installation)
pip install deutschland[all]
```

### With Poetry

```bash
# Basic installation
poetry add deutschland

# With specific extras
poetry add deutschland -E dip_bundestag
poetry add deutschland -E bundestag_lobbyregister

# With multiple extras
poetry add deutschland -E dip_bundestag -E bundestag_lobbyregister
```

## Supported Python Versions

**Python 3.9 - 3.12** (tested on Linux, macOS, Windows)

**Dependencies** (automatically installed):
- requests
- dateparser
- beautifulsoup4
- more-itertools
- numpy
- pandas
- pillow
- lxml
- onnxruntime
- And API-specific sub-packages

## Available APIs

### Core APIs (Included by Default)

These are installed automatically with the base package:

- **bundestag** - Basic Bundestag information API
- **bundesrat** - Federal Council information
- **autobahn** - German highway data, charging stations
- **dwd** - German Weather Service (Deutscher Wetterdienst)
- **interpol** - International police data
- **jobsuche** - Job search data
- **ladestationen** - Charging station locations
- **mudab** - Market transparency unit for electricity and gas
- **nina** - Disaster and emergency alerts
- **polizei_brandenburg** - Brandenburg police data
- **risikogebiete** - COVID-19 and other risk area classifications
- **smard** - Energy market data
- **strahlenschutz** - Radiation protection information
- **travelwarning** - Travel warnings and advisories
- **zoll** - Customs information

### Optional Bundestag APIs

Install with specific extras for comprehensive parliamentary data:

#### **dip_bundestag** ⭐ Most Comprehensive
- **Extra:** `deutschland[dip_bundestag]`
- **Package:** `de-dip-bundestag`
- **What it provides:** Complete DIP API access (proceedings, documents, protocols, full text)
- **Use case:** Building comprehensive RAG systems with all parliamentary data

#### **bundestag_lobbyregister**
- **Extra:** `deutschland[bundestag_lobbyregister]`
- **Package:** `de-bundestag-lobbyregister`
- **What it provides:** Lobby register data
- **Use case:** Transparency research, lobbying analysis

#### **bundestag_tagesordnung**
- **Extra:** `deutschland[bundestag_tagesordnung]`
- **Package:** `de-bundestag-tagesordnung`
- **What it provides:** Parliamentary agendas and schedules
- **Use case:** Tracking upcoming sessions and topics

### Other Optional APIs

Over 25 additional APIs available as extras:

- **destatis** - Federal Statistical Office
- **feiertage** - Public holidays
- **bundeshaushalt** - Federal budget data
- **dashboarddeutschland** - Government dashboard data
- **deutschlandatlas** - Germany atlas data
- **diga** - Digital health applications
- **entgeltatlas** - Wage atlas
- **hilfsmittel** - Medical aids registry
- **hochwasserzentralen** - Flood warning centers
- **klinikatlas** - Hospital atlas
- **marktstammdaten** - Master data register for energy market
- **pegel-online** - Water level data
- **pflanzenschutzmittelzulassung** - Plant protection product approvals
- **regionalatlas** - Regional atlas
- **studiensuche** - Study program search
- **weiterbildungssuche** - Further education search
- And more...

Complete list: See [pyproject.toml extras section](https://github.com/bundesAPI/deutschland/blob/main/pyproject.toml)

## Basic Usage Pattern

All auto-generated APIs follow the same pattern:

```python
from deutschland import <api_name>
from deutschland.<api_name>.api import <api_class>

# Configure authentication (if needed)
configuration = <api_name>.Configuration(
    host = "https://api.example.de",
    api_key = {'ApiKeyHeader': 'YOUR_KEY'}  # or ApiKeyQuery
)

# Create API client
with <api_name>.ApiClient(configuration) as api_client:
    api_instance = <api_class>(api_client)

    # Make requests
    response = api_instance.some_method(param1, param2)
    print(response)
```

## Bundestag Data Access

### 1. Basic Bundestag API (Included by Default)

Access basic Bundestag information without extra installation:

```python
from deutschland import bundestag
from deutschland.bundestag.api import default_api

configuration = bundestag.Configuration(
    host = "https://www.bundestag.de"
)

with bundestag.ApiClient(configuration) as api_client:
    api_instance = default_api.DefaultApi(api_client)

    # Get article details
    article_id = 849630
    response = api_instance.blueprint_servlet_content_articleidas_app_v2_newsarticle_xml_get(article_id)
    print(response)

    # Get plenary sessions overview
    response = api_instance.static_appdata_plenum_v2_conferences_xml_get()
    print(response)

    # Get current speaker
    response = api_instance.static_appdata_plenum_v2_speaker_xml_get()
    print(response)
```

**Available Endpoints:**
- News articles
- Plenary session overview
- Current speaker information
- Committee information
- MP biographies
- Video on demand

### 2. DIP Bundestag API (Most Comprehensive) ⭐

**Installation:**
```bash
pip install deutschland[dip_bundestag]
```

**Access complete parliamentary data:**

```python
from deutschland import dip_bundestag
from deutschland.dip_bundestag.api import (
    vorgnge_api,
    drucksachen_api,
    plenarprotokolle_api,
    personenstammdaten_api
)

# Configure with API key
configuration = dip_bundestag.Configuration(
    host = "https://search.dip.bundestag.de/api/v1"
)

# API key can be set as header or query param
configuration.api_key['ApiKeyQuery'] = 'OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw'

with dip_bundestag.ApiClient(configuration) as api_client:

    # ============================================
    # PROCEEDINGS (Vorgänge)
    # ============================================
    vorgang_api = vorgnge_api.VorgngeApi(api_client)

    # List all proceedings for Wahlperiode 20
    vorgaenge = vorgang_api.get_vorgang_list(
        f_wahlperiode=20,
        format='json'
    )
    print(f"Total proceedings: {vorgaenge.num_found}")

    # Get specific proceeding
    vorgang = vorgang_api.get_vorgang(id=320244, format='json')
    print(f"Title: {vorgang.titel}")
    print(f"Status: {vorgang.beratungsstand}")

    # ============================================
    # PRINTED MATERIALS (Drucksachen)
    # ============================================
    drucksache_api = drucksachen_api.DrucksachenApi(api_client)

    # List documents
    drucksachen = drucksache_api.get_drucksache_list(
        f_wahlperiode=20,
        f_drucksachetyp='Gesetzentwurf',  # Bills only
        format='json'
    )

    # Get document with full text
    drucksache_text = drucksache_api.get_drucksache_text(
        id=279131,
        format='json'
    )
    print(f"Full text: {drucksache_text.text[:500]}...")

    # ============================================
    # PLENARY PROTOCOLS (Plenarprotokolle)
    # ============================================
    protokoll_api = plenarprotokolle_api.PlenarprotokolleApi(api_client)

    # List protocols
    protokolle = protokoll_api.get_plenarprotokoll_list(
        f_wahlperiode=20,
        format='json'
    )

    # Get full transcript
    protokoll_text = protokoll_api.get_plenarprotokoll_text(
        id=5701,
        format='json'
    )
    print(f"Session: {protokoll_text.dokumentnummer}")
    print(f"Transcript length: {len(protokoll_text.text)} chars")

    # ============================================
    # PERSONS (MPs, Ministers)
    # ============================================
    person_api = personenstammdaten_api.PersonenstammdatenApi(api_client)

    # List persons
    personen = person_api.get_person_list(format='json')

    # Get specific person
    person = person_api.get_person(id=40, format='json')
    print(f"Name: {person.vorname} {person.nachname}")
    print(f"Party: {person.fraktion}")
    print(f"Served in periods: {person.wahlperiode}")
```

**Available API Classes:**
- `VorgngeApi` - Proceedings
- `DrucksachenApi` - Printed materials (with full text)
- `PlenarprotokolleApi` - Plenary protocols (with full text)
- `PersonenstammdatenApi` - Person data
- `VorgangspositionenApi` - Proceeding positions
- `AktivittenApi` - Activities

**All Data Models** (with type hints):
- `Vorgang` - Proceeding model
- `Drucksache`, `DrucksacheText` - Document models
- `Plenarprotokoll`, `PlenarprotokollText` - Protocol models
- `Person`, `PersonRole` - Person models
- `Vorgangsposition` - Position model
- `Aktivitaet` - Activity model
- And many more supporting models

### 3. Bundestag Lobby Register

**Installation:**
```bash
pip install deutschland[bundestag_lobbyregister]
```

**Usage:**
```python
from deutschland import bundestag_lobbyregister

# Similar pattern to DIP API
# See de-bundestag-lobbyregister documentation for specifics
```

### 4. Bundestag Tagesordnung (Agenda)

**Installation:**
```bash
pip install deutschland[bundestag_tagesordnung]
```

**Usage:**
```python
from deutschland import bundestag_tagesordnung

# Access parliamentary agenda and schedules
# See de-bundestag-tagesordnung documentation for specifics
```

## Built-in Helper Modules

### Geographic Data (Geo)

Fetch detailed location information including streets, buildings, addresses:

```python
from deutschland.geo import Geo

geo = Geo()

# Define bounding box (top-right and bottom-left coordinates)
top_right = [52.530116236589244, 13.426532801586827]
bottom_left = [52.50876180448243, 13.359631043007212]

data = geo.fetch(top_right, bottom_left)

print(data.keys())
# dict_keys(['Adresse', 'Barrierenlinie', 'Bauwerksflaeche', ...])

print(data["Adresse"][0])
# {'geometry': {'type': 'Point', 'coordinates': (13.422, 52.515)},
#  'properties': {'postleitzahl': '10179', 'ort': 'Berlin',
#                 'strasse': 'Holzmarktstraße', 'hausnummer': '55'}}
```

**Data provided by:** AdV SmartMapping (German state surveying offices)

### Company Data (Bundesanzeiger)

Get financial reports for German companies:

```python
from deutschland.bundesanzeiger import Bundesanzeiger

ba = Bundesanzeiger()

# Search for company
data = ba.get_reports("Deutsche Bahn AG")

print(data.keys())
# dict_keys(['Jahresabschluss zum Geschäftsjahr ...', ...])

# Returns fulltext financial reports extracted via ML
```

**Note:** Uses machine learning to extract structured data from fulltext documents.

### Consumer Protection (Lebensmittelwarnung)

Get product warnings from the federal food safety portal:

```python
from deutschland.lebensmittelwarnung import Lebensmittelwarnung

lw = Lebensmittelwarnung()

# Search by content type and region
data = lw.get("lebensmittel", "berlin")

print(data[0])
# {'id': 19601, 'title': 'Product Name',
#  'manufacturer': 'Lebensmittel', 'warning': 'Pyrrolizidinalkaloide',
#  'affectedStates': ['Baden-Württemberg', ...]}
```

### Autobahn Data

Access highway information and charging stations:

```python
from deutschland import autobahn
from deutschland.autobahn.api import default_api

api_instance = default_api.DefaultApi()

# List all Autobahns
autobahnen = api_instance.list_autobahnen()
print(autobahnen)

# Get charging station details
station_id = "RUxFQ1RSSUNfQ0hBUkdJTkdfU1RBVElPTl9fMTczMzM="
station = api_instance.get_charging_station(station_id)
print(station)
```

## Working with Pagination

Many APIs return paginated results with a cursor:

```python
from deutschland import dip_bundestag
from deutschland.dip_bundestag.api import vorgnge_api

configuration = dip_bundestag.Configuration(
    host = "https://search.dip.bundestag.de/api/v1"
)
configuration.api_key['ApiKeyQuery'] = 'YOUR_API_KEY'

with dip_bundestag.ApiClient(configuration) as api_client:
    vorgang_api = vorgnge_api.VorgngeApi(api_client)

    cursor = None
    all_vorgaenge = []

    while True:
        # Request with cursor
        response = vorgang_api.get_vorgang_list(
            f_wahlperiode=20,
            cursor=cursor if cursor else "",
            format='json'
        )

        all_vorgaenge.extend(response.documents)

        # Check if more pages
        new_cursor = getattr(response, 'cursor', None)
        if not new_cursor or new_cursor == cursor:
            break

        cursor = new_cursor

        print(f"Fetched {len(all_vorgaenge)} total proceedings...")

    print(f"Complete! Total: {len(all_vorgaenge)}")
```

## Error Handling

```python
from deutschland import dip_bundestag
from deutschland.dip_bundestag.api import vorgnge_api

configuration = dip_bundestag.Configuration(
    host = "https://search.dip.bundestag.de/api/v1"
)
configuration.api_key['ApiKeyQuery'] = 'YOUR_API_KEY'

with dip_bundestag.ApiClient(configuration) as api_client:
    vorgang_api = vorgnge_api.VorgngeApi(api_client)

    try:
        vorgang = vorgang_api.get_vorgang(id=999999999, format='json')
    except dip_bundestag.ApiException as e:
        print(f"API Error: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Body: {e.body}")
```

**Common exceptions:**
- `ApiException` - Base exception for API errors
- Status codes: 400 (Bad Request), 401 (Unauthorized), 404 (Not Found)

## Type Safety and IDE Support

All models are auto-generated with full type hints:

```python
from deutschland.dip_bundestag.model.vorgang import Vorgang
from deutschland.dip_bundestag.model.drucksache import Drucksache

# IDE will provide autocomplete for all fields
def process_vorgang(vorgang: Vorgang) -> None:
    print(vorgang.id)          # IDE knows this is an int/str
    print(vorgang.titel)       # IDE knows this is a string
    print(vorgang.wahlperiode) # IDE knows this is an int

    # Type checking at development time
    if vorgang.deskriptor:
        for descriptor in vorgang.deskriptor:
            print(descriptor.name)  # Full autocomplete!
```

## Advanced Configuration

### Custom Timeouts

```python
configuration = dip_bundestag.Configuration(
    host = "https://search.dip.bundestag.de/api/v1"
)

# Create client with custom timeout
import urllib3
http_client = urllib3.PoolManager(timeout=30.0)

with dip_bundestag.ApiClient(configuration) as api_client:
    api_client.rest_client.pool_manager = http_client
    # ... use api_client
```

### Proxy Support

```python
configuration = dip_bundestag.Configuration(
    host = "https://search.dip.bundestag.de/api/v1"
)

# Configure proxy
configuration.proxy = "http://proxy.example.com:8080"

with dip_bundestag.ApiClient(configuration) as api_client:
    # ... use api_client through proxy
```

### Debug Logging

```python
import logging

# Enable debug logging for all HTTP requests
logging.basicConfig(level=logging.DEBUG)

# Now all API calls will log detailed information
```

## Comparison: deutschland Package vs Direct DIP API

| Aspect | deutschland Package | Direct DIP API |
|--------|---------------------|----------------|
| **Installation** | `pip install deutschland[dip_bundestag]` | No installation needed |
| **Import** | `from deutschland import dip_bundestag` | `import requests` |
| **Auth Setup** | Configure once in Configuration object | Pass in every request |
| **Making Requests** | `api.get_vorgang_list(f_wahlperiode=20)` | `requests.get(url, params={...})` |
| **Response Parsing** | Auto-parsed to Pydantic models | Manual `response.json()` |
| **Type Hints** | Full type safety | None (dict) |
| **IDE Support** | Complete autocomplete | Minimal |
| **Error Handling** | Structured exceptions | Manual status code checking |
| **Pagination** | Helper methods available | Manual cursor management |
| **Documentation** | Generated docs + docstrings | Read API specs |
| **API Changes** | Update package | Rewrite code |
| **Learning Curve** | Pythonic, intuitive | Learn API quirks |

## Best Practices

### 1. Use Context Managers

Always use `with` statement for proper resource cleanup:

```python
with dip_bundestag.ApiClient(configuration) as api_client:
    # API operations
    pass
# Connections automatically closed
```

### 2. Configure Authentication Once

```python
# Don't repeat API key in every call
configuration.api_key['ApiKeyQuery'] = 'YOUR_KEY'

# Now all API instances use this configuration
with dip_bundestag.ApiClient(configuration) as api_client:
    vorgang_api = vorgnge_api.VorgngeApi(api_client)
    drucksache_api = drucksachen_api.DrucksachenApi(api_client)
    # Both use the same auth
```

### 3. Handle Large Responses

```python
# For endpoints with large responses, process in batches
cursor = None
while True:
    response = api.get_vorgang_list(f_wahlperiode=20, cursor=cursor)

    # Process batch
    for vorgang in response.documents:
        process_vorgang(vorgang)  # Process one at a time

    cursor = response.cursor
    if not cursor:
        break
```

### 4. Cache Results Locally

```python
import pickle
import os

CACHE_FILE = 'vorgaenge_cache.pkl'

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'rb') as f:
        vorgaenge = pickle.load(f)
else:
    vorgaenge = api.get_vorgang_list(f_wahlperiode=20)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(vorgaenge, f)
```

### 5. Use Specific Imports for Large APIs

If you encounter recursion errors:

```python
# Instead of:
from deutschland import dip_bundestag

# Use specific imports:
from deutschland.dip_bundestag.api.vorgnge_api import VorgngeApi
from deutschland.dip_bundestag.model.vorgang import Vorgang
```

Or increase recursion limit:

```python
import sys
sys.setrecursionlimit(1500)
from deutschland import dip_bundestag
```

## Use Cases for RAG Applications

### 1. Extract All Parliamentary Proceedings

```python
proceedings = []
cursor = None

while True:
    response = vorgang_api.get_vorgang_list(
        f_wahlperiode=20,
        cursor=cursor,
        format='json'
    )
    proceedings.extend(response.documents)

    if not response.cursor or response.cursor == cursor:
        break
    cursor = response.cursor

# Now embed and index proceedings
```

### 2. Get Full-Text Documents

```python
# Get document metadata
drucksachen = drucksache_api.get_drucksache_list(f_wahlperiode=20)

# Fetch full text for each
for doc_meta in drucksachen.documents:
    full_doc = drucksache_api.get_drucksache_text(
        id=doc_meta.id,
        format='json'
    )

    # Extract text and metadata for RAG
    text = full_doc.text
    metadata = {
        'id': full_doc.id,
        'nummer': full_doc.dokumentnummer,
        'typ': full_doc.drucksachetyp,
        'datum': full_doc.datum,
        'pdf_url': full_doc.fundstelle.pdf_url
    }

    # Add to vector database
    add_to_rag(text, metadata)
```

### 3. Incremental Updates

```python
from datetime import datetime, timedelta

# Get only recent updates
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

updated_vorgaenge = vorgang_api.get_vorgang_list(
    f_aktualisiert_start=yesterday,
    format='json'
)

# Update only changed documents in RAG
```

## Limitations and Considerations

### Package Limitations

- **Size:** Full installation with all extras is large (~100+ MB)
- **Recursion errors:** Some APIs may need `setrecursionlimit()` increase
- **Update lag:** Package updates may lag behind API changes
- **Python only:** Not available for other languages

### API-Specific Limitations

- **DIP API:** Same limitations as direct API access (rate limits, data completeness)
- **Authentication:** API keys still required for protected endpoints
- **No caching:** Package doesn't cache responses (implement yourself)

### When to Use Direct API Instead

Consider direct REST API when:
- Non-Python environment
- Extremely lightweight deployment needed
- Want maximum control over HTTP behavior
- API not yet supported by deutschland package

## Troubleshooting

### Installation Issues

```bash
# If installation fails, try upgrading pip
pip install --upgrade pip

# Or use specific Python version
python3.11 -m pip install deutschland[dip_bundestag]
```

### Import Errors

```python
# If imports fail with RecursionError:
import sys
sys.setrecursionlimit(1500)

# Then import
from deutschland import dip_bundestag
```

### API Key Issues

```python
# Check if API key is set correctly
print(configuration.api_key)

# Try both auth methods:
# Method 1: Header
configuration.api_key['ApiKeyHeader'] = 'YOUR_KEY'

# Method 2: Query param (more reliable for DIP)
configuration.api_key['ApiKeyQuery'] = 'YOUR_KEY'
```

### Timeout Issues

```python
# Increase timeout for slow endpoints
configuration.timeout = 60  # seconds
```

## Development and Contributing

### Repository Structure

```
deutschland/
├── src/deutschland/
│   ├── bundestag/           # Basic Bundestag API
│   ├── bundesanzeiger/      # Company financial data
│   ├── geo/                 # Geographic data
│   ├── lebensmittelwarnung/ # Food warnings
│   └── ...                  # Other modules
├── docs/                    # API documentation
│   ├── bundestag/
│   ├── dip_bundestag/      # Installed as extra
│   └── ...
└── tests/                   # Unit tests
```

### Running Tests

```bash
# Install with development dependencies
poetry install

# Run tests
poetry run pytest
```

### Contributing

Contributions welcome! See [GitHub repository](https://github.com/bundesAPI/deutschland) for:
- Issue tracker
- Contributing guidelines
- Development setup

## Related Resources

- **Main Repo:** https://github.com/bundesAPI/deutschland
- **PyPI:** https://pypi.org/project/deutschland/
- **DIP API Docs:** https://dip.bundestag.api.bund.dev/
- **bundesAPI Organization:** https://github.com/bundesAPI

## Summary

The **deutschland** Python package is the **easiest way for Python developers** to access German government APIs, including comprehensive Bundestag data through the DIP API.

### Quick Decision Guide

**Use deutschland package if:**
✅ You're developing in Python
✅ You want type safety and IDE support
✅ You prefer Pythonic interfaces over HTTP calls
✅ You're building production applications
✅ You want automatic pagination and error handling

**Use direct REST API if:**
✅ You're not using Python
✅ You need ultra-lightweight deployment
✅ You want maximum control over HTTP
✅ The API isn't supported by deutschland yet

### Installation Quick Reference

```bash
# Minimal installation
pip install deutschland

# With DIP Bundestag (most comprehensive parliamentary data)
pip install deutschland[dip_bundestag]

# With lobby register
pip install deutschland[bundestag_lobbyregister]

# With everything
pip install deutschland[all]
```

### Import Quick Reference

```python
# DIP Bundestag API (comprehensive)
from deutschland import dip_bundestag
from deutschland.dip_bundestag.api import vorgnge_api, drucksachen_api

# Basic Bundestag API
from deutschland import bundestag

# Geographic data
from deutschland.geo import Geo

# Company data
from deutschland.bundesanzeiger import Bundesanzeiger
```

**For RAG/LLM Applications:** Use `deutschland[dip_bundestag]` for easiest access to complete parliamentary data with type-safe, Pythonic interfaces.
