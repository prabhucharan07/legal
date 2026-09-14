import streamlit as st
import cv2
import numpy as np
from step1_marker import process_step1
from step2_ocr import process_step2
from step3_classifier import classify_fields
from step4_pdp import calculate_pdp_and_fonts
from step5_rules import evaluate_rules
from step6_db_drift import init_db, log_inspection

st.set_page_config(page_title="Legal Metrology Checker", layout="wide")

st.title("⚖️ Automated Legal Metrology Packaging Checker")
st.write("Upload a packaging label image to verify compliance against regulatory standards.")

# Sidebar Configuration
st.sidebar.header("Packaging Parameters")
shape = st.sidebar.selectbox("Package Shape", ["rectangular", "cylindrical"])
height = st.sidebar.number_input("Height (cm)", value=15.0)
width = st.sidebar.number_input("Width / Circumference (cm)", value=10.0)
marker_size = st.sidebar.number_input("ArUco Marker Size (mm)", value=50.0)

# File Uploader
uploaded_file = st.file_uploader("Choose a packaging image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with open("temp_input.jpg", "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Run Compliance Audit"):
        with st.spinner("Processing image and validating rules..."):
            # Step 1
            warped_img, ratio = process_step1("temp_input.jpg", marker_real_size_mm=marker_size)
            
            if ratio is None:
                st.error("ArUco Marker not detected! Please ensure marker is visible.")
            else:
                # Steps 2–5
                ocr_data = process_step2("corrected_output.jpg")
                classified_data = classify_fields(ocr_data)
                pdp_data = calculate_pdp_and_fonts(classified_data, ratio=ratio, shape=shape, height_cm=height, width_or_circ_cm=width)
                report = evaluate_rules(pdp_data)
                
                # Step 6
                init_db()
                log_inspection(pdp_data, report)

                # Layout Display
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Processed Output Image")
                    st.image("corrected_output.jpg", use_container_width=True)

                with col2:
                    st.subheader("Compliance Audit Status")
                    all_passed = all(r["status"] == "PASS" for r in report)
                    
                    if all_passed:
                        st.success(" PASSED: Product is fully compliant.")
                    else:
                        st.error(" FAILED: Non-compliant label features detected.")

                    # Render Table
                    st.table(report)