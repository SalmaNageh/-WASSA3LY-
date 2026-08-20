import streamlit as st
from pathlib import Path
import tempfile
import json
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from fast_alpr import ALPR
import subprocess
import base64
from backend.integration import (
    process_member2_entry,
    process_member2_exit,
    get_current_status,
    get_history,
    get_revenue
)

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="WASSA3LY | وسّعلي Parking",
    page_icon=str(BASE_DIR / "assets" / "logo.jfif"),
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
logo_path = BASE_DIR / "assets" / "logo.jfif"

if logo_path.exists():
    logo = Image.open(logo_path)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image(logo, width=500)

# ============================================================
# MAIN LOGO
# ============================================================

logo_path = BASE_DIR / "assets" / "logo.jfif"

if logo_path.exists():
    logo = Image.open(logo_path)

    col1, col2, col3 = st.columns([2, 2, 2])

# ============================================================
# THEME — "NIGHT GARAGE CONTROL ROOM"
# Dark asphalt surface + the red/green indicator-light language
# real smart-parking sensors use above every bay, plus a torn
# ticket-stub receipt for the one moment that deserves a prop.
# ============================================================

def inject_theme():

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

        :root{
            --bg-void:#14161B;
            --bg-surface:#1D2027;
            --bg-raised:#262A33;
            --line:#31353F;
            --line-soft:#2A2E37;
            --text-primary:#F3EFE6;
            --text-muted:#9AA0AC;
            --text-faint:#666B78;
            --accent-green:#34D399;
            --accent-green-dim:rgba(52,211,153,.14);
            --accent-red:#F0555C;
            --accent-red-dim:rgba(240,85,92,.14);
            --accent-amber:#F5A524;
            --accent-amber-dim:rgba(245,165,36,.14);
            --accent-blue:#5AA9FF;
            --accent-blue-dim:rgba(90,169,255,.14);
            --radius-md:14px;
            --radius-lg:20px;
            --font-display:'Cairo', sans-serif;
            --font-body:'Inter', sans-serif;
            --font-mono:'JetBrains Mono', monospace;
        }

        html, body, [class*="css"]{
            font-family: var(--font-body);
        }

        [data-testid="stAppViewContainer"], .main{
            background: var(--bg-void);
        }

        [data-testid="stHeader"]{
            background: transparent;
        }

        .block-container{
            padding-top: 1.6rem;
            max-width: 1200px;
        }

        h1, h2, h3{
            font-family: var(--font-display) !important;
            color: var(--text-primary) !important;
            letter-spacing: .01em;
        }

        h2{
            border-bottom: 1px dashed var(--line);
            padding-bottom: .5rem;
        }

        h3{
            color: var(--text-primary) !important;
            font-size: 1.05rem !important;
        }

        p, span, label, li{
            color: var(--text-muted);
        }

        hr, [data-testid="stDivider"]{
            border-color: var(--line) !important;
        }

        /* ---------------- SIDEBAR ---------------- */

        [data-testid="stSidebar"]{
            background: var(--bg-surface);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] h1{
            font-size: 1.05rem !important;
            text-transform: uppercase;
            letter-spacing: .12em;
            color: var(--text-faint) !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"]{
            gap: .35rem;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 10px;
            padding: .55rem .7rem;
            transition: all .15s ease;
            width: 100%;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{
            display: none;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:hover{
            background: var(--bg-raised);
            border-color: var(--line);
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
            background: var(--accent-blue-dim);
            border-color: var(--accent-blue);
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label p{
            font-weight: 600;
            color: var(--text-primary);
        }

        /* ---------------- CARDS / CONTAINERS ---------------- */

        [data-testid="stVerticalBlockBorderWrapper"]{
            background: var(--bg-surface);
            border: 1px solid var(--line) !important;
            border-radius: var(--radius-lg) !important;
        }

        /* ---------------- BUTTONS ---------------- */

        .stButton > button, .stDownloadButton > button{
            background: var(--bg-raised);
            color: var(--text-primary);
            border: 1px solid var(--line);
            border-radius: 10px;
            font-weight: 600;
            padding: .55rem 1rem;
            transition: all .15s ease;
        }

        .stButton > button:hover, .stDownloadButton > button:hover{
            transform: translateY(-1px);
            border-color: var(--accent-blue);
            box-shadow: 0 6px 18px rgba(90,169,255,.15);
            color: var(--text-primary);
        }

        .stButton > button[kind="primary"]{
            background: linear-gradient(135deg, var(--accent-green), #1FA97C);
            border: none;
            color: #0B120F;
        }

        .stButton > button[kind="primary"]:hover{
            box-shadow: 0 6px 18px rgba(52,211,153,.3);
        }

        /* ---------------- FILE UPLOADER ---------------- */

        [data-testid="stFileUploaderDropzone"]{
            background: var(--bg-void);
            border: 1px dashed var(--line);
            border-radius: var(--radius-md);
        }

        [data-testid="stFileUploaderDropzone"]:hover{
            border-color: var(--accent-blue);
        }

        /* ---------------- PROGRESS (occupancy gauge look) ---------------- */

        [data-testid="stProgress"] > div > div{
            background: var(--bg-raised);
            border-radius: 99px;
        }

        [data-testid="stProgress"] > div > div > div{
            background-image: linear-gradient(90deg, var(--accent-green), var(--accent-amber) 65%, var(--accent-red));
            border-radius: 99px;
        }

        /* ---------------- METRIC (fallback) ---------------- */

        [data-testid="stMetric"]{
            background: var(--bg-surface);
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            padding: .8rem 1rem;
        }

        [data-testid="stMetricValue"]{
            font-family: var(--font-mono) !important;
            color: var(--text-primary) !important;
        }

        /* ---------------- ALERTS ---------------- */

        .stAlert, [data-testid="stAlertContainer"]{
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--line) !important;
        }

        /* ---------------- DATAFRAME ---------------- */

        [data-testid="stDataFrame"]{
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            overflow: hidden;
        }

        /* ================= CUSTOM COMPONENTS ================= */

        .hero{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: .8rem;
            padding-bottom: 1.1rem;
            margin-bottom: 1.6rem;
            border-bottom: 2px dashed var(--line);
        }

        .hero-left{
            display: flex;
            align-items: center;
            gap: .9rem;
        }

        .hero-logo{
            font-size: 2.1rem;
        }

        .hero-title{
            font-family: var(--font-display);
            font-weight: 800;
            font-size: 1.6rem;
            color: var(--text-primary);
            line-height: 1.1;
        }

        .hero-title span{
            color: var(--accent-amber);
            font-size: 1rem;
            letter-spacing: .1em;
            margin-left: .4rem;
        }

        .hero-sub{
            font-size: .85rem;
            color: var(--text-muted);
            margin-top: .15rem;
        }

        .hero-right{
            font-family: var(--font-mono);
            font-size: .78rem;
            letter-spacing: .1em;
            color: var(--accent-green);
            border: 1px solid var(--accent-green-dim);
            background: var(--accent-green-dim);
            padding: .35rem .8rem;
            border-radius: 99px;
            white-space: nowrap;
        }

        .live-dot{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent-green);
            display: inline-block;
            margin-right: 6px;
            animation: pulse 1.6s infinite;
        }

        @keyframes pulse{
            0%{ box-shadow: 0 0 0 0 rgba(52,211,153,.55); }
            70%{ box-shadow: 0 0 0 7px rgba(52,211,153,0); }
            100%{ box-shadow: 0 0 0 0 rgba(52,211,153,0); }
        }

        .section-head{
            display: flex;
            align-items: center;
            gap: .6rem;
            margin: .1rem 0 1rem 0;
        }

        .section-head-icon{
            font-size: 1.3rem;
        }

        .section-head-title{
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.15rem;
            color: var(--text-primary);
        }

        .section-sub{
            font-size: .8rem;
            color: var(--text-faint);
        }

        .stat-tile{
            background: var(--bg-surface);
            border: 1px solid var(--line);
            border-top: 3px solid var(--tile-accent, var(--accent-blue));
            border-radius: var(--radius-md);
            padding: 1rem 1.1rem;
            position: relative;
            overflow: hidden;
        }

        .stat-tile::after{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 100% 0%, var(--tile-accent, var(--accent-blue)) 0%, transparent 55%);
            opacity: .1;
            pointer-events: none;
        }

        .stat-tile-icon{
            font-size: 1.2rem;
            opacity: .85;
            margin-bottom: .3rem;
        }

        .stat-tile-value{
            font-family: var(--font-mono);
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }

        .stat-tile-label{
            font-family: var(--font-body);
            font-size: .74rem;
            letter-spacing: .07em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-top: .4rem;
        }

        .plate-chip{
            display: inline-block;
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: .12em;
            background: var(--bg-void);
            border: 1px solid var(--line-soft);
            color: var(--accent-green);
            padding: .4rem .9rem;
            border-radius: 8px;
        }

        .ticket-stub{
            font-family: var(--font-mono);
            background: var(--bg-surface);
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            padding: 1.3rem 1.5rem 1.1rem;
            color: var(--text-primary);
            max-width: 460px;
        }

        .ticket-head{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: .72rem;
            letter-spacing: .12em;
            text-transform: uppercase;
            color: var(--text-faint);
        }

        .ticket-head-tag{
            border: 1px solid var(--line-soft);
            border-radius: 99px;
            padding: .15rem .6rem;
        }

        .ticket-plate{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: .15em;
            background: var(--bg-void);
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            padding: .55rem 1rem;
            text-align: center;
            margin: .9rem 0 1rem 0;
            color: var(--accent-green);
        }

        .ticket-row{
            display: flex;
            justify-content: space-between;
            font-size: .85rem;
            padding: .25rem 0;
            color: var(--text-muted);
        }

        .ticket-row span:last-child{
            color: var(--text-primary);
        }

        .ticket-perforation{
            border-top: 2px dashed var(--line);
            margin: 1rem -1.5rem;
            position: relative;
        }

        .ticket-perforation::before, .ticket-perforation::after{
            content: "";
            position: absolute;
            top: -9px;
            width: 18px;
            height: 18px;
            background: var(--bg-void);
            border: 1px solid var(--line);
            border-radius: 50%;
        }

        .ticket-perforation::before{ left: -9px; }
        .ticket-perforation::after{ right: -9px; }

        .ticket-fee-row{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: .3rem;
        }

        .ticket-fee-row > span:first-child{
            font-size: .78rem;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: var(--text-faint);
        }

        .ticket-fee{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--accent-amber);
        }

        .ticket-vip{
            display: inline-block;
            background: var(--accent-amber-dim);
            color: var(--accent-amber);
            border: 1px solid var(--accent-amber-dim);
            border-radius: 99px;
            padding: .05rem .5rem;
            font-size: .68rem;
            margin-right: .4rem;
            letter-spacing: .05em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_header():

    st.markdown(
        """
        <div class="hero">
            <div class="hero-left">
                <div class="hero-logo"></div>
                <div>
                    <div class="hero-title"> WASSA3LY | وسّعلي  <span>SMART PARKING</span></div>
                    <div class="hero-sub">AI-powered monitoring · plate recognition · وصّلك لأقرب مكان فاضي</div>
                </div>
            </div>
            <div class="hero-right"><span class="live-dot"></span>SYSTEM LIVE</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_section_header(icon, title, subtitle=None):

    subtitle_html = (
        f'<div class="section-sub">{subtitle}</div>'
        if subtitle else ""
    )

    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-head-icon">{icon}</div>
            <div>
                <div class="section-head-title">{title}</div>
                {subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_stat_tile(icon, label, value, accent="blue"):

    accent_map = {
        "green": "var(--accent-green)",
        "red": "var(--accent-red)",
        "amber": "var(--accent-amber)",
        "blue": "var(--accent-blue)",
    }

    color = accent_map.get(accent, accent_map["blue"])

    st.markdown(
        f"""
        <div class="stat-tile" style="--tile-accent:{color};">
            <div class="stat-tile-icon">{icon}</div>
            <div class="stat-tile-value">{value}</div>
            <div class="stat-tile-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_ticket_stub(result):

    vip_badge = (
        '<span class="ticket-vip">⭐ VIP</span>'
        if result.get("vip") else ""
    )

    st.markdown(
        f"""
        <div class="ticket-stub">
            <div class="ticket-head">
                <span>WASSA3LY PARKING</span>
                <span class="ticket-head-tag">RECEIPT</span>
            </div>
            <div class="ticket-plate">{result['plate_number']}</div>
            <div class="ticket-row"><span>Vehicle ID</span><span>{result['vehicle_id']}</span></div>
            <div class="ticket-row"><span>Space</span><span>{result['parking_space']}</span></div>
            <div class="ticket-row"><span>Entry</span><span>{result['entry_time']}</span></div>
            <div class="ticket-row"><span>Exit</span><span>{result['exit_time']}</span></div>
            <div class="ticket-row"><span>Duration</span><span>{result['duration_minutes']} min</span></div>
            <div class="ticket-perforation"></div>
            <div class="ticket-fee-row">
                <span>{vip_badge}TOTAL FEE</span>
                <span class="ticket-fee">{result['fee']} EGP</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# LOAD PARKING MODEL
# ============================================================

@st.cache_resource
def load_parking_model():

    if not PARKING_MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Parking model not found: {PARKING_MODEL_PATH}"
        )

    return YOLO(
        str(PARKING_MODEL_PATH)
    )


# ============================================================
# LOAD FAST-ALPR
# ============================================================

@st.cache_resource
def load_alpr():

    return ALPR(
        detector_model="yolo-v9-t-384-license-plate-end2end",
        ocr_model="cct-xs-v2-global-model",
    )


# ============================================================
# LOAD PARKING SPOTS
# ============================================================

@st.cache_data
def load_parking_spots():

    if not PARKING_SPOTS_PATH.exists():
        return []

    with open(
        PARKING_SPOTS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# PARKING SPACE HELPERS
# ============================================================

def point_inside_polygon(
    point,
    polygon
):

    polygon = np.array(
        polygon,
        dtype=np.int32
    )

    return cv2.pointPolygonTest(
        polygon,
        point,
        False
    ) >= 0


def get_space_center(
    polygon
):

    points = np.array(
        polygon,
        dtype=np.int32
    )

    x = int(
        np.mean(points[:, 0])
    )

    y = int(
        np.mean(points[:, 1])
    )

    return x, y


# ============================================================
# DETECT PARKING STATUS
# ============================================================

def detect_parking_status(
    results
):

    occupied = 0
    available = 0

    for result in results:

        if result.boxes is None:
            continue

        for cls in result.boxes.cls.cpu().numpy():

            class_id = int(cls)

            class_name = (
                result.names[class_id]
                .lower()
                .strip()
            )

            if class_name == "car":

                occupied += 1

            elif class_name == "free":

                available += 1

    return occupied, available


# ============================================================
# PROCESS PARKING IMAGE
# ============================================================

def process_parking_image(
    image
):

    model = load_parking_model()

    results = model.predict(
        source=image,
        conf=0.40,
        verbose=False
    )

    result_image = results[0].plot()

    occupied, available = (
        detect_parking_status(
            results
        )
    )

    total_spaces = (
        occupied +
        available
    )

    occupancy_rate = (

        occupied /
        total_spaces *
        100

        if total_spaces > 0

        else 0
    )

    return (
        result_image,
        total_spaces,
        occupied,
        available,
        occupancy_rate
    )


# ============================================================
# PROCESS PARKING VIDEO
# ============================================================
def process_parking_video(
    uploaded_file,
    progress_bar=None,
    status_text=None
):
    """
    Process uploaded parking video frame-by-frame using YOLO.
    No FFmpeg required.
    """

    model = load_parking_model()

    input_suffix = (
        Path(uploaded_file.name).suffix.lower()
        or ".mp4"
    )

    # --------------------------------------------------------
    # Temporary directory
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(temp_dir)

        input_path = temp_dir / f"input{input_suffix}"
        output_path = temp_dir / "wassa3ly_detection.mp4"

        # Save uploaded video
        input_path.write_bytes(
            uploaded_file.getbuffer()
        )

        # --------------------------------------------------------
        # Open input video
        # --------------------------------------------------------

        cap = cv2.VideoCapture(
            str(input_path)
        )

        if not cap.isOpened():
            raise RuntimeError(
                "Could not open the uploaded video."
            )

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        if fps <= 0 or np.isnan(fps):
            fps = 25.0

        total_frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        if width <= 0 or height <= 0:
            cap.release()

            raise RuntimeError(
                "Could not read video dimensions."
            )

        # --------------------------------------------------------
        # Video Writer
        # --------------------------------------------------------

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (width, height)
        )

        if not writer.isOpened():
            cap.release()

            raise RuntimeError(
                "Could not create output video."
            )

        # --------------------------------------------------------
        # Variables
        # --------------------------------------------------------

        last_occupied = 0
        last_available = 0

        frame_number = 0

        # --------------------------------------------------------
        # Process frame by frame
        # --------------------------------------------------------

        try:

            while True:

                success, frame = cap.read()

                if not success:
                    break

                # ================================================
                # YOLO DETECTION
                # ================================================

                results = model.predict(
                    source=frame,
                    conf=0.40,
                    verbose=False
                )

                result = results[0]

                # ================================================
                # DRAW DETECTIONS
                # ================================================

                annotated_frame = result.plot()

                # Make sure frame dimensions are correct
                if (
                    annotated_frame.shape[1] != width
                    or annotated_frame.shape[0] != height
                ):

                    annotated_frame = cv2.resize(
                        annotated_frame,
                        (width, height)
                    )

                # ================================================
                # PARKING STATUS
                # ================================================

                occupied, available = (
                    detect_parking_status(
                        results
                    )
                )

                last_occupied = occupied
                last_available = available

                # ================================================
                # WRITE FRAME
                # ================================================

                writer.write(
                    annotated_frame
                )

                frame_number += 1

                # ================================================
                # PROGRESS
                # ================================================

                if total_frames > 0:

                    progress = min(
                        frame_number / total_frames,
                        1.0
                    )

                    if progress_bar is not None:

                        progress_bar.progress(
                            progress
                        )

                    if status_text is not None:

                        status_text.text(
                            f"Processing frame "
                            f"{frame_number} / "
                            f"{total_frames}"
                        )

                else:

                    if status_text is not None:

                        status_text.text(
                            f"Processing frame "
                            f"{frame_number}"
                        )

        finally:

            cap.release()
            writer.release()

        # --------------------------------------------------------
        # Check output
        # --------------------------------------------------------

        if not output_path.exists():

            raise RuntimeError(
                "Detection video was not created."
            )

        if output_path.stat().st_size == 0:

            raise RuntimeError(
                "Detection video is empty."
            )

        # --------------------------------------------------------
        # Read video into memory BEFORE temp folder is deleted
        # --------------------------------------------------------

        with open(
            output_path,
            "rb"
        ) as video_file:

            video_bytes = video_file.read()

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    total_spaces = (
        last_occupied +
        last_available
    )

    occupancy_rate = (
        last_occupied / total_spaces * 100
        if total_spaces > 0
        else 0
    )

    return (
        video_bytes,
        total_spaces,
        last_occupied,
        last_available,
        occupancy_rate
    )
# ============================================================
# FAST-ALPR
# ============================================================

def detect_plate(
    image
):

    alpr = load_alpr()

    frame = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR
    )

    drawn = alpr.draw_predictions(
        frame
    )

    annotated_frame = (
        drawn.image
    )

    results = drawn.results

    plates = []

    for result in results:

        plate_number = None
        bbox = None

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        ocr_result = getattr(
            result,
            "ocr",
            None
        )

        if ocr_result is not None:

            if isinstance(
                ocr_result,
                str
            ):

                plate_number = (
                    ocr_result
                )

            else:

                plate_number = getattr(
                    ocr_result,
                    "text",
                    None
                )

        # ----------------------------------------------------
        # DETECTION
        # ----------------------------------------------------

        detection = getattr(
            result,
            "detection",
            None
        )

        if detection is not None:

            bbox = getattr(
                detection,
                "bounding_box",
                None
            )

        plates.append(
            {
                "number": plate_number,
                "bbox": bbox,
                "raw_result": result
            }
        )

    return (
        annotated_frame,
        plates
    )


# ============================================================
# GET PLATE NUMBER
# ============================================================

def get_plate_number(
    plates
):

    for plate in plates:

        number = plate.get(
            "number"
        )

        if number:

            number = str(
                number
            ).strip()

            if number:

                return number

    return None


# ============================================================
# THEME + HEADER
# ============================================================

inject_theme()
render_header()

# ============================================================
# SIDEBAR
# ============================================================
# ============================================================
# SIDEBAR
# ============================================================

if logo_path.exists():
    logo = Image.open(logo_path)

    col1, col2, col3 = st.sidebar.columns([1, 2, 1])

    with col2:
        st.image(logo, width=100)

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose Section",
    [
        "🅿️ Parking Monitor",
        "🚗 Vehicle Management",
        "📊 Dashboard",
        "📜 Parking History"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()

# System Status
st.sidebar.markdown("### ⚡ System Status")

status = get_current_status()

st.sidebar.success("🟢 System Online")

st.sidebar.metric(
    "Available Spaces",
    status["available"]
)

st.sidebar.metric(
    "Occupancy Rate",
    f'{status["occupancy_rate"]}%'
)
# ============================================================
# PARKING MONITOR
# ============================================================

if page == "🅿️ Parking Monitor":

    render_section_header(
        "🅿️",
        "Parking Area Monitoring",
        "Run the bay-detection model on a still image or a full walkthrough video."
    )

    image_col, video_col = st.columns(
        2,
        gap="large"
    )

    # ========================================================
    # IMAGE DETECTION
    # ========================================================

    with image_col, st.container(border=True):

        st.subheader(
            "🖼️ Image Detection"
        )

        uploaded_image = st.file_uploader(
            "Upload parking image",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            key="parking_image"
        )

        if uploaded_image:

            image = Image.open(
                uploaded_image
            ).convert("RGB")

            st.image(
                image,
                caption="Original Image",
                use_container_width=True
            )

            if st.button(
                "🔍 Run YOLO Detection",
                use_container_width=True,
                key="run_image_detection",
                type="primary"
            ):

                with st.spinner(
                    "Running YOLO..."
                ):

                    (
                        result_image,
                        total,
                        occupied,
                        available,
                        rate
                    ) = process_parking_image(
                        np.array(image)
                    )

                st.image(
                    result_image,
                    channels="BGR",
                    caption="YOLO Detection",
                    use_container_width=True
                )

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    render_stat_tile("🅿️", "Total", total, "blue")

                with c2:
                    render_stat_tile("🚗", "Occupied", occupied, "red")

                with c3:
                    render_stat_tile("✅", "Available", available, "green")

                with c4:
                    render_stat_tile("📈", "Occupancy", f"{rate:.1f}%", "amber")

    # ========================================================
    # VIDEO DETECTION
    # ========================================================

    with video_col, st.container(border=True):

        st.subheader(
            "🎥 Video Detection"
        )

        uploaded_video = st.file_uploader(
            "Upload parking video",
            type=[
                "mp4",
                "avi",
                "mov"
            ],
            key="parking_video"
        )

        if uploaded_video:

            st.video(
                uploaded_video
            )

            if st.button(
                "▶️ Run YOLO Detection",
                use_container_width=True,
                key="run_video_detection",
                type="primary"
            ):

                progress_bar = st.progress(
                    0
                )

                status_text = st.empty()

                try:

                    with st.spinner(
                        "Running YOLO on video..."
                    ):

                        (
                            video_bytes,
                            total,
                            occupied,
                            available,
                            rate
                        ) = process_parking_video(
                            uploaded_video,
                            progress_bar,
                            status_text
                        )

                    progress_bar.progress(
                        1.0
                    )

                    status_text.success(
                        "Video processing completed!"
                    )

                    st.subheader(
                        "🎥 YOLO Detection Result"
                    )

                    # ------------------------------------------------
                    # READ FINAL VIDEO
                    # ------------------------------------------------

                   
                    # ------------------------------------------------
                    # PLAY VIDEO
                    # ------------------------------------------------

                    st.video(
                        video_bytes,
                        
                    )

                    st.divider()

                    # ------------------------------------------------
                    # STATISTICS
                    # ------------------------------------------------

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:
                        render_stat_tile("🅿️", "Total", total, "blue")

                    with c2:
                        render_stat_tile("🚗", "Occupied", occupied, "red")

                    with c3:
                        render_stat_tile("✅", "Available", available, "green")

                    with c4:
                        render_stat_tile("📈", "Occupancy", f"{rate:.1f}%", "amber")

                    # ------------------------------------------------
                    # DOWNLOAD
                    # ------------------------------------------------

                    st.download_button(
                        "⬇️ Download Detection Video",
                        data=video_bytes,
                        file_name=(
                            "wassa3ly_parking_detection.mp4"
                        ),
                        mime="video/mp4",
                        use_container_width=True
                    )

                except Exception as e:

                    progress_bar.empty()
                    status_text.empty()

                    st.error(
                        f"Video processing failed: {e}"
                    )


# ============================================================
# VEHICLE MANAGEMENT
# ============================================================

elif page == "🚗 Vehicle Management":

    render_section_header(
        "🚗",
        "Vehicle Management",
        "Scan a plate on entry and exit to open and close a parking session."
    )

    entry_col, exit_col = st.columns(
        2,
        gap="large"
    )

    # ========================================================
    # VEHICLE ENTRY
    # ========================================================

    with entry_col, st.container(border=True):

        st.subheader(
            "🚗 Vehicle Entry"
        )

        st.write(
            "Upload a vehicle image "
            "containing the license plate."
        )

        uploaded_entry_image = st.file_uploader(
            "Upload entry vehicle image",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            key="entry_image"
        )


        if uploaded_entry_image:

            image = Image.open(
                uploaded_entry_image
            ).convert("RGB")

            st.image(
                image,
                caption="Vehicle Image",
                use_container_width=True
            )

            if st.button(
                "🔍 Detect License Plate",
                use_container_width=True,
                key="detect_entry_plate"
            ):

                with st.spinner(
                    "Running Fast-ALPR..."
                ):

                    (
                        result_image,
                        plates
                    ) = detect_plate(
                        np.array(image)
                    )

                st.image(
                    result_image,
                    channels="BGR",
                    caption="ALPR Result",
                    use_container_width=True
                )

                if plates:

                    plate_number = (
                        get_plate_number(
                            plates
                        )
                    )

                    if plate_number:

                        st.markdown(
                            f'<div class="plate-chip">{plate_number}</div>',
                            unsafe_allow_html=True
                        )

                        st.session_state[
                            "entry_plate_number"
                        ] = plate_number

                    else:

                        st.warning(
                            "License plate detected, "
                            "but OCR could not read the text."
                        )

                else:

                    st.error(
                        "No license plate detected."
                    )

            # ------------------------------------------------
            # CONFIRM ENTRY
            # ------------------------------------------------

            if (
                "entry_plate_number"
                in st.session_state
            ):

                plate_number = (
                    st.session_state[
                        "entry_plate_number"
                    ]
                )

                st.markdown("Detected plate, ready to check in:")

                st.markdown(
                    f'<div class="plate-chip">{plate_number}</div>',
                    unsafe_allow_html=True
                )

                st.write("")

                if st.button(
                    "🚗 Confirm Vehicle Entry",
                    use_container_width=True,
                    key="confirm_entry",
                    type="primary"
                ):

                    result = result = process_member2_entry(
                    plate_number=plate_number
                    )

                    if result.get(
                        "success"
                    ):

                        st.success(
                            "Vehicle entered successfully!"
                        )

                        st.json(
                            result
                        )

                        del st.session_state[
                            "entry_plate_number"
                        ]

                    else:

                        st.error(
                            result.get(
                                "message",
                                "Entry failed."
                            )
                        )

    # ========================================================
    # VEHICLE EXIT
    # ========================================================

    with exit_col, st.container(border=True):

        st.subheader(
            "🚪 Vehicle Exit"
        )

        st.write(
            "Upload an image of the vehicle "
            "to detect its plate."
        )

        uploaded_exit_image = st.file_uploader(
            "Upload exit vehicle image",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            key="exit_image"
        )

        if uploaded_exit_image:

            image = Image.open(
                uploaded_exit_image
            ).convert("RGB")

            st.image(
                image,
                caption="Vehicle Image",
                use_container_width=True
            )

            if st.button(
                "🔍 Detect License Plate",
                use_container_width=True,
                key="detect_exit_plate"
            ):

                with st.spinner(
                    "Running Fast-ALPR..."
                ):

                    (
                        result_image,
                        plates
                    ) = detect_plate(
                        np.array(image)
                    )

                st.image(
                    result_image,
                    channels="BGR",
                    caption="ALPR Result",
                    use_container_width=True
                )

                if plates:

                    plate_number = (
                        get_plate_number(
                            plates
                        )
                    )

                    if plate_number:

                        st.markdown(
                            f'<div class="plate-chip">{plate_number}</div>',
                            unsafe_allow_html=True
                        )

                        st.session_state[
                            "exit_plate_number"
                        ] = plate_number

                    else:

                        st.warning(
                            "License plate detected, "
                            "but OCR could not read the text."
                        )

                else:

                    st.error(
                        "No license plate detected."
                    )

            # ------------------------------------------------
            # CONFIRM EXIT
            # ------------------------------------------------

            if (
                "exit_plate_number"
                in st.session_state
            ):

                plate_number = (
                    st.session_state[
                        "exit_plate_number"
                    ]
                )

                st.markdown("Detected plate, ready to check out:")

                st.markdown(
                    f'<div class="plate-chip">{plate_number}</div>',
                    unsafe_allow_html=True
                )

                st.write("")

                if st.button(
                    "🚪 Confirm Vehicle Exit",
                    use_container_width=True,
                    key="confirm_exit",
                    type="primary"
                ):

                    result = (
                        process_member2_exit(
                            plate_number
                        )
                    )

                    if result.get(
                        "success"
                    ):

                        st.success(
                            "Vehicle exited successfully!"
                        )

                        render_ticket_stub(result)

                        del st.session_state[
                            "exit_plate_number"
                        ]

                    else:

                        st.error(
                            result.get(
                                "message",
                                "Exit failed."
                            )
                        )


# ============================================================
# DASHBOARD
# ============================================================

elif page == "📊 Dashboard":

    render_section_header(
        "📊",
        "Parking Dashboard",
        "Live read of the lot, right now."
    )

    status = get_current_status()

    revenue = get_revenue()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_stat_tile("🅿️", "Total Spaces", status["total"], "blue")

    with c2:
        render_stat_tile("🚗", "Occupied", status["occupied"], "red")

    with c3:
        render_stat_tile("✅", "Available", status["available"], "green")

    with c4:
        render_stat_tile("📈", "Occupancy Rate", f'{status["occupancy_rate"]}%', "amber")

    st.write("")

    with st.container(border=True):

        rc1, rc2 = st.columns([1, 2])

        with rc1:
            render_stat_tile("💰", "Total Revenue", f"{revenue:.2f} EGP", "amber")

        with rc2:

            st.markdown("**Parking Occupancy**")

            if status["total"] > 0:

                st.progress(
                    min(
                        status["occupancy_rate"] / 100,
                        1.0
                    )
                )

                st.caption(
                    f'{status["occupied"]} of {status["total"]} spaces occupied '
                    f'· {status["available"]} free right now'
                )

            else:

                st.caption("No spaces configured yet.")


# ============================================================
# PARKING HISTORY
# ============================================================

elif page == "📜 Parking History":

    render_section_header(
        "📜",
        "Parking History",
        "Every session that has passed through the gate."
    )

    history = get_history()

    with st.container(border=True):

        if history:

            st.dataframe(
                history,
                use_container_width=True
            )

        else:

            st.info(
                "No parking history available."
            )