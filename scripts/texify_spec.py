import os
import sys
from pathlib import Path

# Header and footer to be added to each file
HEADER = """\\begin{lstlisting}[style=SpectraStyle]
"""

FOOTER = """
\\end{lstlisting}
"""

def texify_spectra_files(folder_path):
    """
    Scans a folder for .spectra files, adds header and footer,
    and saves them as .tex files in a 'texified' subfolder.

    Args:
        folder_path: Path to the folder containing .spectra files
    """
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    # Create texified subfolder if it doesn't exist
    texified_folder = folder / "texified"
    texified_folder.mkdir(exist_ok=True)

    # Find all .spectra files
    spectra_files = list(folder.glob("*.spectra"))

    if not spectra_files:
        print(f"No .spectra files found in '{folder_path}'")
        return

    # Process each .spectra file
    for spectra_file in spectra_files:
        # Read the original file content
        with open(spectra_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add header and footer
        texified_content = HEADER + content + FOOTER

        # Create new filename with .tex extension
        tex_filename = spectra_file.stem + ".tex"
        tex_filepath = texified_folder / tex_filename

        # Write the texified content
        with open(tex_filepath, 'w', encoding='utf-8') as f:
            f.write(texified_content)

        print(f"Created: {tex_filepath}")

    print(f"\nProcessed {len(spectra_files)} file(s).")


if __name__ == "__main__":
    """
    if len(sys.argv) != 2:
        print("Usage: python texify_spec.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    """
    folder_path = "/Users/tg4018/Documents/PhD/SpecRepair/tests/test_files/out/maximal_solutions_from_ssh"
    texify_spectra_files(folder_path)
