import os
import shutil

import yaml

# Base paths
SRC_DIR = "src"
DOCS_DIR = "docs/src"
MKDOCS_FILE = "mkdocs.yml"


SECTION_TEMPLATE = """## {section_name}

::: {full_import_path}
"""

DATASOURCE_MD_TEMPLATE = """# {module_name} Datasource

This module contains functionality related to the `{module_name}` datasource.

{sections}
"""

REGULAR_MD_TEMPLATE = """# {module_name}

This module contains functionality related to the {module_description}.

{sections}
"""


def get_module_description(module_name: str, parent_module: str) -> str:
    """Generate contextualized module description."""
    if not parent_module or parent_module == "src":
        return f"the `{module_name}` script"

    # Clean up parent module path
    context = parent_module.replace("src.", "")
    return f"the `{module_name}` module for `{context}`"


def clean_docs_directory(docs_dir: str):
    """Remove the existing documentation directory and recreate it."""
    if os.path.exists(docs_dir):
        print(f"Removing existing documentation directory: {docs_dir}")
        shutil.rmtree(docs_dir)
    os.makedirs(docs_dir, exist_ok=True)
    print(f"Created fresh documentation directory: {docs_dir}")


def generate_markdown_template(base_dir, docs_dir, parent_module):
    """
    Aggregate documentation for all files in a datasource folder.
    """
    module_name = os.path.basename(base_dir)
    module_doc_path = os.path.join(docs_dir, f"{module_name}.md")

    # Check if this is under embedding/datasources
    is_datasource = "embedding/datasources" in base_dir

    sections = []
    builders_section = None

    for entry in sorted(os.listdir(base_dir)):
        entry_path = os.path.join(base_dir, entry)
        if entry.endswith(".py") and not entry.startswith("__"):
            file_name = os.path.splitext(entry)[0]
            full_import_path = f"{parent_module}.{module_name}.{file_name}"
            section = SECTION_TEMPLATE.format(
                section_name=file_name.capitalize(),
                full_import_path=full_import_path,
            )
            if file_name == "builders":
                builders_section = section
            else:
                sections.append(section)

    if builders_section:
        sections.append(builders_section)

    os.makedirs(docs_dir, exist_ok=True)
    with open(module_doc_path, "w") as md_file:
        template = (
            DATASOURCE_MD_TEMPLATE if is_datasource else REGULAR_MD_TEMPLATE
        )
        md_file.write(
            template.format(
                module_name=module_name.capitalize(),
                sections="\n".join(sections),
            )
        )
    print(f"Generated: {module_doc_path}")

    return {module_name.capitalize(): os.path.relpath(module_doc_path, "docs")}


def generate_markdown_files(base_dir, docs_dir, parent_module="src"):
    """
    Generate Markdown documentation for the entire project structure.

    :param base_dir: Source directory to scan.
    :param docs_dir: Destination directory for the documentation.
    :param parent_module: Parent module name to construct import paths.
    """
    nav_entries = []

    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)

        # Special handling for `embedding/datasources`
        if os.path.basename(base_dir) == "datasources" and os.path.isdir(
            entry_path
        ):
            nav_entries.append(
                generate_markdown_template(entry_path, docs_dir, parent_module)
            )
        elif os.path.isdir(entry_path) and not entry.startswith("__"):
            # Process subdirectories recursively
            module_name = f"{parent_module}.{entry}" if parent_module else entry
            module_docs_dir = os.path.join(docs_dir, entry)
            nav_entries.append(
                {
                    entry.capitalize(): generate_markdown_files(
                        entry_path, module_docs_dir, module_name
                    )
                }
            )
        elif entry.endswith(".py") and not entry.startswith("__"):
            # Process individual Python files
            file_name = os.path.splitext(entry)[0]
            full_import_path = (
                f"{parent_module}.{file_name}" if parent_module else file_name
            )
            md_file_path = os.path.join(docs_dir, f"{file_name}.md")
            sections = SECTION_TEMPLATE.format(
                section_name=file_name.capitalize(),
                full_import_path=full_import_path,
            )
            module_description = get_module_description(
                file_name, parent_module
            )
            md_content = REGULAR_MD_TEMPLATE.format(
                module_name=file_name.capitalize(),
                module_description=module_description,
                sections=sections,
            )
            os.makedirs(docs_dir, exist_ok=True)
            with open(md_file_path, "w") as md_file:
                md_file.write(md_content)
            nav_entries.append(
                {file_name.capitalize(): os.path.relpath(md_file_path, "docs")}
            )
            print(f"Generated: {md_file_path}")

    return nav_entries


def update_mkdocs_yml(nav_structure):
    """
    Update mkdocs.yml with the generated navigation structure.

    Enforces the following order:
    1. Home (index.md)
    2. Quickstart:
        - Quickstart Setup (quickstart/quickstart_setup.md)
        - Developer Setup (quickstart/developer_setup.md)
    3. How to:
        - How To Add New LLM (how_to/how_to_add_new_llm.md)
    4. Code Docs:
        - Chat (src/chat.md)
        - Embed (src/embed.md)
        - Evaluate (src/evaluate.md)
        - Augmentation (folder)
        - Embedding -> Datasources (aggregated Markdown files for datasources)
        - Evaluation (folder)

    :param nav_structure: Nested navigation structure for the documentation.
    """
    # Manually organize the structure
    ordered_nav = [
        {"Home": "index.md"},
        {
            "Quickstart": [
                {"Quickstart Setup": "quickstart/quickstart_setup.md"},
                {"Local Developement Setup": "quickstart/developer_setup.md"},
            ]
        },
        {
            "How to": [
                {"Configure RAG System": "how_to/how_to_configure.md"},
                {"Add a New LLM": "how_to/how_to_add_new_llm.md"},
                {
                    "Add a New Embedding Model": "how_to/how_to_add_new_embedding_model.md"
                },
                {
                    "Add a New Vector Store": "how_to/how_to_add_new_vector_store.md"
                },
                {"Add a New Datasource": "how_to/how_to_add_new_datasource.md"},
            ]
        },
        {
            "Evaluation": [
                {"In progress": "evaluation/in_progress.md"},
            ]
        },
        {
            "Monitoring": [
                {"In progress": "monitoring/in_progress.md"},
            ]
        },
        {
            "Code Docs": [
                {"Chat": "src/chat.md"},
                {"Embed": "src/embed.md"},
                {"Evaluate": "src/evaluate.md"},
            ]
        },
    ]

    section_order = ["augmentation", "common", "embedding", "evaluation"]

    # Process each section in order
    for section in section_order:
        for entry in nav_structure:
            if section.capitalize() in entry:
                # Special case for embedding/datasources
                if section == "embedding" and "Datasources" in entry.get(
                    "Embedding", {}
                ):
                    embedding_entry = entry["Embedding"]
                    datasources_entry = {
                        "Datasources": embedding_entry.pop("Datasources")
                    }
                    ordered_nav[-1]["Code Docs"].append(
                        {
                            "Embedding": [datasources_entry]
                            + list(embedding_entry.items())
                        }
                    )
                # Regular section handling
                else:
                    ordered_nav[-1]["Code Docs"].append(entry)

    # Base configuration for MkDocs
    config = {
        "site_name": "RAG Systems",
        "repo_url": "https://github.com/feld-m/rag_blueprint/",
        "edit_uri": "edit/main/docs/",
        "theme": "readthedocs",
        "plugins": ["mkdocstrings", "search"],
        "watch": ["."],
        "nav": ordered_nav,
    }

    # Write the configuration to mkdocs.yml
    with open(MKDOCS_FILE, "w") as file:
        yaml.dump(config, file, default_flow_style=False)

    print(f"Updated: {MKDOCS_FILE}")


if __name__ == "__main__":
    # Clean the docs/src directory
    clean_docs_directory(DOCS_DIR)

    # Generate documentation for the entire project
    nav_structure = generate_markdown_files(SRC_DIR, DOCS_DIR)

    # Update mkdocs.yml
    update_mkdocs_yml(nav_structure)
