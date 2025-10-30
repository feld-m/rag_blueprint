"""
bundesAPI "deutschland" Python Package - Comprehensive Examples

This file contains ready-to-use Python examples for the deutschland package,
especially focusing on Bundestag data access for RAG applications.

Installation:
    pip install deutschland[dip_bundestag]

Documentation:
    - Package: https://github.com/bundesAPI/deutschland
    - DIP API: docs/datasources/bundestag_dip_api.md
"""

# ==============================================================================
# EXAMPLE 1: Basic Setup and Configuration
# ==============================================================================


def example_basic_setup():
    """Configure and test basic DIP Bundestag API access."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    # Configure API
    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )

    # Set API key (public test key valid until May 2026)
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    # Create API client
    with dip_bundestag.ApiClient(configuration) as api_client:
        # Create API instance
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        # Test connection
        try:
            response = vorgang_api.get_vorgang_list(
                f_wahlperiode=21, format="json"
            )
            print(f"✓ Connection successful!")
            print(f"  Total proceedings: {response.num_found}")
            print(f"  First page results: {len(response.documents)}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False


# ==============================================================================
# EXAMPLE 2: Fetch Parliamentary Proceedings (Vorgänge)
# ==============================================================================


def example_fetch_proceedings():
    """Fetch and explore parliamentary proceedings."""
    from pprint import pprint

    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        # Get proceedings for Wahlperiode 20
        response = vorgang_api.get_vorgang_list(f_wahlperiode=21, format="json")

        print(f"Total proceedings in Wahlperiode 20: {response.num_found}\n")

        # Examine first proceeding
        if response.documents:
            vorgang = response.documents[0]
            print("Example Proceeding:")
            print(f"  ID: {vorgang.id}")
            print(f"  Title: {vorgang.titel}")
            print(f"  Type: {vorgang.vorgangstyp}")
            print(f"  Date: {vorgang.datum}")
            print(f"  Status: {vorgang.beratungsstand}")

            if hasattr(vorgang, "sachgebiet") and vorgang.sachgebiet:
                print(f"  Subject areas: {', '.join(vorgang.sachgebiet)}")

            if hasattr(vorgang, "initiative") and vorgang.initiative:
                print(f"  Initiated by: {', '.join(vorgang.initiative)}")

            if hasattr(vorgang, "abstract") and vorgang.abstract:
                print(f"  Abstract: {vorgang.abstract[:200]}...")

        return response.documents


# ==============================================================================
# EXAMPLE 3: Pagination - Fetch All Proceedings
# ==============================================================================


def example_fetch_all_with_pagination():
    """Demonstrate pagination to fetch all proceedings."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        all_vorgaenge = []
        cursor = None
        page = 1

        print("Fetching all proceedings with pagination...")

        while True:
            # Fetch page
            response = vorgang_api.get_vorgang_list(
                f_wahlperiode=21, cursor=cursor if cursor else "", format="json"
            )

            # Add to collection
            all_vorgaenge.extend(response.documents)

            print(
                f"  Page {page}: {len(response.documents)} documents "
                f"(total so far: {len(all_vorgaenge)})"
            )

            # Check for more pages
            new_cursor = getattr(response, "cursor", None)
            if not new_cursor or new_cursor == cursor:
                break

            cursor = new_cursor
            page += 1

            # Safety limit for example
            if page > 5:  # Remove this in production
                print("  (Stopping at 5 pages for example)")
                break

        print(f"\nFetched {len(all_vorgaenge)} total proceedings")
        return all_vorgaenge


# ==============================================================================
# EXAMPLE 4: Fetch Printed Materials (Drucksachen)
# ==============================================================================


def example_fetch_documents():
    """Fetch printed materials (bills, motions, reports)."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import drucksachen_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        drucksache_api = drucksachen_api.DrucksachenApi(api_client)

        # Get bills (Gesetzentwürfe) from Wahlperiode 20
        response = drucksache_api.get_drucksache_list(
            f_wahlperiode=21, f_drucksachetyp="Gesetzentwurf", format="json"
        )

        print(f"Total bills in Wahlperiode 21: {response.num_found}\n")

        # Examine first few bills
        for i, doc in enumerate(response.documents[:3]):
            print(f"Bill {i+1}:")
            print(f"  Number: {doc.dokumentnummer}")
            print(f"  Title: {doc.titel}")
            print(f"  Date: {doc.datum}")
            print(f"  Type: {doc.drucksachetyp}")

            if hasattr(doc, "fundstelle") and doc.fundstelle:
                print(f"  PDF: {doc.fundstelle.pdf_url}")

            if hasattr(doc, "vorgangsbezug") and doc.vorgangsbezug:
                print(f"  Related proceedings: {len(doc.vorgangsbezug)}")

            print()

        return response.documents


# ==============================================================================
# EXAMPLE 5: Get Full Text of Documents
# ==============================================================================


def example_fetch_fulltext_documents():
    """Fetch complete text content of printed materials."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import drucksachen_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        drucksache_api = drucksachen_api.DrucksachenApi(api_client)

        # First get list to find IDs
        response = drucksache_api.get_drucksache_list(
            f_wahlperiode=21, format="json"
        )

        if response.documents:
            # Get full text for first document
            doc_id = response.documents[0].id

            fulltext_doc = drucksache_api.get_drucksache_text(
                id=doc_id, format="json"
            )

            print(f"Document: {fulltext_doc.dokumentnummer}")
            print(f"Title: {fulltext_doc.titel}")

            if hasattr(fulltext_doc, "text") and fulltext_doc.text:
                print(f"Text length: {len(fulltext_doc.text)} characters")
                print(f"First 500 chars:\n{fulltext_doc.text[:500]}...\n")
            else:
                print("No full text available for this document")

            return fulltext_doc

        return None


# ==============================================================================
# EXAMPLE 6: Fetch Plenary Protocols
# ==============================================================================


def example_fetch_protocols():
    """Fetch plenary session protocols."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import plenarprotokolle_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        protokoll_api = plenarprotokolle_api.PlenarprotokolleApi(api_client)

        # Get Bundestag protocols from Wahlperiode 20
        response = protokoll_api.get_plenarprotokoll_list(
            f_wahlperiode=20, format="json"
        )

        print(f"Total protocols in Wahlperiode 21: {response.num_found}\n")

        # Show Bundestag protocols only
        bt_protocols = [p for p in response.documents if p.herausgeber == "BT"]

        for i, protocol in enumerate(bt_protocols[:5]):
            print(f"Session {i+1}:")
            print(f"  Number: {protocol.dokumentnummer}")
            print(f"  Date: {protocol.datum}")
            print(f"  Publisher: {protocol.herausgeber} (Bundestag)")

            if hasattr(protocol, "vorgangsbezug_anzahl"):
                print(f"  Topics discussed: {protocol.vorgangsbezug_anzahl}")

            if hasattr(protocol, "fundstelle") and protocol.fundstelle:
                print(f"  PDF: {protocol.fundstelle.pdf_url}")
                if (
                    hasattr(protocol.fundstelle, "xml_url")
                    and protocol.fundstelle.xml_url
                ):
                    print(f"  XML: {protocol.fundstelle.xml_url}")

            print()

        return bt_protocols


# ==============================================================================
# EXAMPLE 7: Get Full Transcript Text
# ==============================================================================


def example_fetch_protocol_transcript():
    """Fetch complete stenographic transcript of a plenary session."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import plenarprotokolle_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        protokoll_api = plenarprotokolle_api.PlenarprotokolleApi(api_client)

        # Get specific protocol with full text (session 214)
        transcript = protokoll_api.get_plenarprotokoll_text(
            id=5701, format="json"  # Example ID
        )

        print(f"Session: {transcript.dokumentnummer}")
        print(f"Date: {transcript.datum}")
        print(f"Publisher: {transcript.herausgeber}")

        if hasattr(transcript, "text") and transcript.text:
            print(f"\nTranscript length: {len(transcript.text)} characters")
            print(f"Word count: ~{len(transcript.text.split())} words")
            print(f"\nFirst 1000 characters:")
            print("-" * 80)
            print(transcript.text[:1000])
            print("-" * 80)

            # Show topics discussed
            if (
                hasattr(transcript, "vorgangsbezug")
                and transcript.vorgangsbezug
            ):
                print(f"\nTopics discussed in this session:")
                for i, topic in enumerate(transcript.vorgangsbezug[:5], 1):
                    print(f"  {i}. {topic.titel}")
                    print(f"     Type: {topic.vorgangstyp}")

        return transcript


# ==============================================================================
# EXAMPLE 8: Fetch Person Data (MPs, Ministers)
# ==============================================================================


def example_fetch_persons():
    """Fetch person data for MPs and ministers."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import personenstammdaten_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        person_api = personenstammdaten_api.PersonenstammdatenApi(api_client)

        # Get list of persons
        response = person_api.get_person_list(format="json")

        print(f"Total persons in database: {response.num_found}\n")

        # Show first few
        for i, person in enumerate(response.documents[:5]):
            name = f"{person.vorname} {person.nachname}"
            print(f"Person {i+1}: {name}")
            print(
                f"  Function: {', '.join(person.funktion) if hasattr(person, 'funktion') else 'N/A'}"
            )

            if hasattr(person, "fraktion") and person.fraktion:
                print(f"  Party: {', '.join(person.fraktion)}")

            if hasattr(person, "wahlperiode") and person.wahlperiode:
                print(f"  Electoral periods: {person.wahlperiode}")

            print()

        return response.documents


# ==============================================================================
# EXAMPLE 9: Filter by Date Range
# ==============================================================================


def example_filter_by_date():
    """Fetch proceedings from specific time period."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        # Get proceedings from Q1 2025
        response = vorgang_api.get_vorgang_list(
            f_wahlperiode=20,
            f_datum_start="2025-01-01",
            f_datum_end="2025-03-31",
            format="json",
        )

        print(f"Proceedings from Q1 2025: {response.num_found}\n")

        for i, vorgang in enumerate(response.documents[:5]):
            print(f"{i+1}. {vorgang.titel}")
            print(f"   Date: {vorgang.datum}")
            print(f"   Type: {vorgang.vorgangstyp}")
            print()

        return response.documents


# ==============================================================================
# EXAMPLE 10: Incremental Updates
# ==============================================================================


def example_incremental_updates():
    """Fetch only recently updated documents."""
    from datetime import datetime, timedelta

    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        # Get documents updated in last 7 days
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        response = vorgang_api.get_vorgang_list(
            f_aktualisiert_start=week_ago, format="json"
        )

        print(f"Proceedings updated since {week_ago}: {response.num_found}\n")

        for i, vorgang in enumerate(response.documents[:10]):
            print(f"{i+1}. {vorgang.titel[:60]}...")
            print(f"   Updated: {vorgang.aktualisiert}")
            print()

        return response.documents


# ==============================================================================
# EXAMPLE 11: Extract Data for RAG Application
# ==============================================================================


def example_extract_for_rag():
    """Extract and structure data suitable for RAG indexing."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import (
        drucksachen_api,
        plenarprotokolle_api,
        vorgnge_api,
    )

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    rag_documents = []

    with dip_bundestag.ApiClient(configuration) as api_client:

        # ============================================
        # Extract Proceedings
        # ============================================
        print("Extracting proceedings...")
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        vorgaenge = vorgang_api.get_vorgang_list(
            f_wahlperiode=21, format="json"
        )

        for vorgang in vorgaenge.documents[:10]:  # Limit for example
            doc = {
                "id": f"vorgang_{vorgang.id}",
                "type": "proceeding",
                "title": vorgang.titel,
                "text": (
                    vorgang.abstract if hasattr(vorgang, "abstract") else ""
                ),
                "metadata": {
                    "wahlperiode": vorgang.wahlperiode,
                    "date": (
                        str(vorgang.datum)
                        if hasattr(vorgang, "datum")
                        else None
                    ),
                    "vorgangstyp": vorgang.vorgangstyp,
                    "status": (
                        vorgang.beratungsstand
                        if hasattr(vorgang, "beratungsstand")
                        else None
                    ),
                    "sachgebiete": (
                        vorgang.sachgebiet
                        if hasattr(vorgang, "sachgebiet")
                        else []
                    ),
                    "updated": (
                        str(vorgang.aktualisiert)
                        if hasattr(vorgang, "aktualisiert")
                        else None
                    ),
                },
            }
            rag_documents.append(doc)

        print(f"  Extracted {len(rag_documents)} proceedings")

        # ============================================
        # Extract Documents with Full Text
        # ============================================
        print("Extracting documents with full text...")
        drucksache_api = drucksachen_api.DrucksachenApi(api_client)

        drucksachen = drucksache_api.get_drucksache_list(
            f_wahlperiode=21, format="json"
        )

        for drucksache in drucksachen.documents[:5]:  # Limit for example
            # Try to get full text
            try:
                fulltext = drucksache_api.get_drucksache_text(
                    id=drucksache.id, format="json"
                )

                if hasattr(fulltext, "text") and fulltext.text:
                    doc = {
                        "id": f"drucksache_{fulltext.id}",
                        "type": "printed_material",
                        "title": fulltext.titel,
                        "text": fulltext.text,
                        "metadata": {
                            "dokumentnummer": fulltext.dokumentnummer,
                            "drucksachetyp": (
                                fulltext.drucksachetyp
                                if hasattr(fulltext, "drucksachetyp")
                                else None
                            ),
                            "wahlperiode": fulltext.wahlperiode,
                            "date": (
                                str(fulltext.datum)
                                if hasattr(fulltext, "datum")
                                else None
                            ),
                            "pdf_url": (
                                fulltext.fundstelle.pdf_url
                                if hasattr(fulltext, "fundstelle")
                                else None
                            ),
                        },
                    }
                    rag_documents.append(doc)
            except Exception as e:
                print(f"    Skipping document {drucksache.id}: {e}")

        print(f"  Total RAG documents: {len(rag_documents)}")

        # ============================================
        # Show example RAG document
        # ============================================
        if rag_documents:
            print("\nExample RAG document:")
            import json

            example = rag_documents[0]
            print(
                json.dumps(
                    {
                        "id": example["id"],
                        "type": example["type"],
                        "title": example["title"][:80] + "...",
                        "text": (
                            example["text"][:200] + "..."
                            if example["text"]
                            else "No text"
                        ),
                        "metadata": example["metadata"],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )

    return rag_documents


# ==============================================================================
# EXAMPLE 12: Error Handling
# ==============================================================================


def example_error_handling():
    """Demonstrate proper error handling."""
    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        # Try to get non-existent proceeding
        try:
            vorgang = vorgang_api.get_vorgang(
                id=999999999, format="json"  # Non-existent ID
            )
            print("Found proceeding (unexpected!)")
        except dip_bundestag.ApiException as e:
            print(f"✓ Caught expected API exception:")
            print(f"  Status: {e.status}")
            print(f"  Reason: {e.reason}")
            if e.status == 404:
                print(f"  → Proceeding not found (expected)")

        # Try with invalid API key
        bad_config = dip_bundestag.Configuration(
            host="https://search.dip.bundestag.de/api/v1"
        )
        bad_config.api_key["ApiKeyQuery"] = "invalid_key_12345"

        try:
            with dip_bundestag.ApiClient(bad_config) as bad_client:
                bad_api = vorgnge_api.VorgngeApi(bad_client)
                response = bad_api.get_vorgang_list(
                    f_wahlperiode=20, format="json"
                )
        except dip_bundestag.ApiException as e:
            print(f"\n✓ Caught authentication error:")
            print(f"  Status: {e.status}")
            if e.status == 401:
                print(f"  → Unauthorized (invalid API key)")


# ==============================================================================
# EXAMPLE 13: Save to JSON/CSV for Further Processing
# ==============================================================================


def example_export_data():
    """Export data to JSON and CSV formats."""
    import csv
    import json

    from deutschland import dip_bundestag
    from deutschland.dip_bundestag.api import vorgnge_api

    configuration = dip_bundestag.Configuration(
        host="https://search.dip.bundestag.de/api/v1"
    )
    configuration.api_key["ApiKeyQuery"] = (
        "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
    )

    with dip_bundestag.ApiClient(configuration) as api_client:
        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        response = vorgang_api.get_vorgang_list(f_wahlperiode=21, format="json")

        # ============================================
        # Export to JSON
        # ============================================
        vorgaenge_list = []
        for v in response.documents[:10]:  # Limit for example
            vorgaenge_list.append(
                {
                    "id": v.id,
                    "titel": v.titel,
                    "typ": v.vorgangstyp,
                    "datum": str(v.datum) if hasattr(v, "datum") else None,
                    "wahlperiode": v.wahlperiode,
                    "sachgebiete": (
                        v.sachgebiet if hasattr(v, "sachgebiet") else []
                    ),
                }
            )

        with open("vorgaenge.json", "w", encoding="utf-8") as f:
            json.dump(vorgaenge_list, f, ensure_ascii=False, indent=2)
        print(f"✓ Exported {len(vorgaenge_list)} proceedings to vorgaenge.json")

        # ============================================
        # Export to CSV
        # ============================================
        with open("vorgaenge.csv", "w", encoding="utf-8", newline="") as f:
            if vorgaenge_list:
                writer = csv.DictWriter(
                    f, fieldnames=["id", "titel", "typ", "datum", "wahlperiode"]
                )
                writer.writeheader()
                for v in vorgaenge_list:
                    writer.writerow(
                        {
                            "id": v["id"],
                            "titel": v["titel"],
                            "typ": v["typ"],
                            "datum": v["datum"],
                            "wahlperiode": v["wahlperiode"],
                        }
                    )
        print(f"✓ Exported {len(vorgaenge_list)} proceedings to vorgaenge.csv")


# ==============================================================================
# MAIN FUNCTION - Run Examples
# ==============================================================================


def main():
    """Run all examples with menu selection."""
    examples = {
        "1": ("Basic Setup", example_basic_setup),
        "2": ("Fetch Proceedings", example_fetch_proceedings),
        "3": ("Pagination Demo", example_fetch_all_with_pagination),
        "4": ("Fetch Documents", example_fetch_documents),
        "5": ("Full Text Documents", example_fetch_fulltext_documents),
        "6": ("Fetch Protocols", example_fetch_protocols),
        "7": ("Protocol Transcript", example_fetch_protocol_transcript),
        "8": ("Fetch Persons", example_fetch_persons),
        "9": ("Filter by Date", example_filter_by_date),
        "10": ("Incremental Updates", example_incremental_updates),
        "11": ("Extract for RAG", example_extract_for_rag),
        "12": ("Error Handling", example_error_handling),
        "13": ("Export Data", example_export_data),
    }

    print("=" * 80)
    print("bundesAPI deutschland Package - Examples")
    print("=" * 80)
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print(f"  all. Run all examples")
    print(f"  q. Quit")
    print()

    choice = input("Select example (1-13, 'all', or 'q'): ").strip()

    if choice.lower() == "q":
        return

    if choice.lower() == "all":
        for key, (name, func) in examples.items():
            print("\n" + "=" * 80)
            print(f"Example {key}: {name}")
            print("=" * 80)
            try:
                func()
            except Exception as e:
                print(f"✗ Example failed: {e}")
            print()
            input("Press Enter to continue...")
    elif choice in examples:
        name, func = examples[choice]
        print("\n" + "=" * 80)
        print(f"Example {choice}: {name}")
        print("=" * 80)
        try:
            result = func()
            print(f"\n✓ Example completed successfully")
            return result
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback

            traceback.print_exc()
    else:
        print(f"Invalid choice: {choice}")


if __name__ == "__main__":
    main()
