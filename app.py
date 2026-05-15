import streamlit as st
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf2image import convert_from_path
from homr.main import process_image, ProcessingConfig
from homr.music_xml_generator import XmlGeneratorArguments
import subprocess

st.title("Sheet Music Transcriber")
st.write("Upload a PDF of sheet music and get back a MusicXML file you can edit in MuseScore.")

uploaded_file = st.file_uploader("Upload your sheet music PDF", type="pdf")

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded PDF to temp location
        pdf_path = os.path.join(tmp_dir, uploaded_file.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        pdf_name = os.path.splitext(uploaded_file.name)[0]
        pages_folder = os.path.join(tmp_dir, "pages")
        os.makedirs(pages_folder, exist_ok=True)

        with st.spinner("Converting PDF to images..."):
            pages = convert_from_path(pdf_path, dpi=300)
            for index, page in enumerate(pages):
                page.save(os.path.join(pages_folder, f"page_{index + 1}.png"), "PNG")

        config = ProcessingConfig(
            enable_debug=False,
            enable_cache=False,
            write_staff_positions=False,
            read_staff_positions=False,
            selected_staff=-1,
            use_gpu_inference=False
        )

        with st.spinner("Reading sheet music (this takes a moment)..."):
            for filename in sorted(os.listdir(pages_folder)):
                if filename.endswith(".png"):
                    filepath = os.path.join(pages_folder, filename)
                    process_image(filepath, config, XmlGeneratorArguments())

        with st.spinner("Merging pages..."):
            xml_files = sorted([
                os.path.join(pages_folder, f)
                for f in os.listdir(pages_folder)
                if f.endswith(".musicxml")
            ])
            output_xml = os.path.join(tmp_dir, f"{pdf_name}.musicxml")
            homr_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            subprocess.run(["poetry", "run", "relieur"] + xml_files + ["-o", output_xml], cwd=homr_folder)

        # Offer download
        if os.path.exists(output_xml):
            with open(output_xml, "rb") as f:
                st.download_button(
                    label="Download MusicXML",
                    data=f,
                    file_name=f"{pdf_name}.musicxml",
                    mime="application/xml"
                )
            st.success("Done! Click the button above to download your file.")
        else:
            st.error("Something went wrong — no output file was created.")