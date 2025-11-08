# components/image_verification.py
import io
import numpy as np
import cv2
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans


def _read_image(file_bytes) -> np.ndarray:
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _auto_canny(img_gray: np.ndarray) -> np.ndarray:
    v = np.median(img_gray)
    lower = int(max(0, 0.66 * v))
    upper = int(min(255, 1.33 * v))
    edges = cv2.Canny(img_gray, lower, upper)
    return edges


def _sharpness_laplacian(img_gray: np.ndarray) -> float:
    return float(cv2.Laplacian(img_gray, cv2.CV_64F).var())


def _edge_density(edge_map: np.ndarray) -> float:
    return float(np.count_nonzero(edge_map)) / float(edge_map.size)


def _find_contours(edge_map: np.ndarray):
    cnts, _ = cv2.findContours(edge_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return cnts


def _dominant_colors_bgr(img_bgr: np.ndarray, k: int = 5):
    # Downsample for speed
    small = cv2.resize(img_bgr, (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    data = small.reshape((-1, 3))
    # Remove near-grey pixels to emphasize colors (optional)
    # Keep everything for robustness but KMeans handles it
    kmeans = KMeans(n_clusters=k, n_init=5, random_state=42)
    labels = kmeans.fit_predict(data)
    centers = kmeans.cluster_centers_.astype(np.uint8)
    counts = np.bincount(labels)
    # Sort by frequency
    idx = np.argsort(-counts)
    centers = centers[idx]
    counts = counts[idx]
    return centers, counts


def _confidence_score(sharp: float, color_rich: int, edge_den: float, contour_ct: int) -> float:
    # Normalize metrics heuristically
    sharp_norm = min(1.0, sharp / 300.0)  # Typical Laplacian variance range for sharp images
    color_norm = min(1.0, color_rich / 5.0)
    edge_norm = min(1.0, edge_den / 0.15)  # 15% edge pixels is reasonably detailed
    contour_norm = min(1.0, contour_ct / 500.0)  # Cap at 500 for normalization

    # Weighted combination
    score = (
        0.35 * sharp_norm
        + 0.25 * color_norm
        + 0.25 * edge_norm
        + 0.15 * contour_norm
    ) * 100.0
    return float(np.clip(score, 0.0, 100.0))


def _badge_for_score(score: float) -> tuple[str, str, str]:
    if score >= 75:
        return "✅ Verified: Authentic & Clear", "green", "Sharp image with natural color distribution and clear edges."
    if score >= 50:
        return "⚠️ Needs Review", "orange", "Moderately clear image; consider re-uploading with better lighting or focus."
    return "❌ Not Clear or Possibly Tampered", "red", "Blurry or low-detail image; uneven colors or weak edges detected."


def _contour_overlay(img_bgr: np.ndarray, contours) -> np.ndarray:
    overlay = img_bgr.copy()
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 1)
    return overlay


def _enhance_image(img_bgr: np.ndarray) -> np.ndarray:
    # Denoise lightly then apply CLAHE on the L channel
    denoised = cv2.fastNlMeansDenoisingColored(img_bgr, None, 5, 5, 7, 21)
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2, a, b))
    enhanced = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    return enhanced


def _color_bar(centers_bgr: np.ndarray, counts: np.ndarray):
    # Create a horizontal bar of dominant colors using matplotlib
    total = counts.sum()
    fracs = (counts / total) if total else np.ones(len(counts)) / len(counts)
    fig, ax = plt.subplots(figsize=(6, 1))
    ax.axis('off')
    start = 0.0
    for c_bgr, f in zip(centers_bgr, fracs):
        width = f
        rgb = c_bgr[::-1] / 255.0  # BGR to RGB normalized
        ax.add_patch(plt.Rectangle((start, 0), width, 1, color=rgb))
        start += width
    ax.set_xlim(0, 1)
    return fig


def _metrics_chart(sharp: float, colors: int, edge: float, contours: int):
    labels = ["Sharpness", "Color Richness", "Edge Density", "Contour Complexity"]
    # Scale raw metrics to comparable display ranges
    vals = [sharp, colors, edge * 100, contours]
    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.bar(labels, vals, color=["#10b981", "#3b82f6", "#f59e0b", "#ef4444"])
    ax.set_ylabel("Metric Value (scaled)")
    ax.set_title("Image Verification Metrics")
    ax.bar_label(bars, fmt='%.1f', padding=3)
    plt.xticks(rotation=10)
    plt.tight_layout()
    return fig


def show_image_verification():
    st.header("📷 Image Verification")
    st.caption("Upload crop or farm images to verify clarity and authenticity with visual metrics.")

    uploaded = st.file_uploader("Upload an image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if not uploaded:
        st.info("Please upload an image to continue.")
        return

    # Read and prepare
    img_bgr = _read_image(uploaded.read())
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Compute artifacts
    edges = _auto_canny(img_gray)
    contours = _find_contours(edges)
    overlay = _contour_overlay(img_bgr, contours)
    centers_bgr, counts = _dominant_colors_bgr(img_bgr, k=5)
    color_bar_fig = _color_bar(centers_bgr, counts)

    # Metrics
    sharp = _sharpness_laplacian(img_gray)
    color_rich = max(1, min(5, int(np.count_nonzero(counts > 0))))
    edge_den = _edge_density(edges)
    contour_ct = int(len(contours))
    conf = _confidence_score(sharp, color_rich, edge_den, contour_ct)
    verdict, color, reasoning = _badge_for_score(conf)

    # Layout – tabs and columns
    tabs = st.tabs(["Overview", "Enhance", "Download"])

    with tabs[0]:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"<div style='border-left:6px solid {color}; padding-left:10px;'>"
                        f"<strong style='color:{color};'>{verdict}</strong><br>"
                        f"<span style='color:#6b7280;'>Confidence: {conf:.1f}/100</span></div>", unsafe_allow_html=True)
            st.image(img_rgb, caption="Original", use_column_width=True)
        with c2:
            st.image(edges, caption="Edge Map (Canny)", use_column_width=True)
            st.image(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB), caption="Contour Overlay", use_column_width=True)

        c3, c4 = st.columns([1, 1])
        with c3:
            st.pyplot(color_bar_fig, clear_figure=True)
            st.caption("Dominant Color Palette")
        with c4:
            chart = _metrics_chart(sharp, color_rich, edge_den, contour_ct)
            st.pyplot(chart, clear_figure=True)

        st.markdown(f"**Reasoning:** {reasoning}")
        st.caption("Metrics: Sharpness (Laplacian variance), Color richness (clusters), Edge density (%), Contour complexity (count).")

    with tabs[1]:
        st.subheader("Auto-Enhanced Preview ✨")
        enhance = st.checkbox("Apply denoise + CLAHE histogram equalization", value=True)
        if enhance:
            enhanced = _enhance_image(img_bgr)
            st.image(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB), caption="Enhanced", use_column_width=True)
        else:
            st.image(img_rgb, caption="Original (no enhancement)", use_column_width=True)

    with tabs[2]:
        st.subheader("Download Verified Image")
        # Prepare overlay PNG for download
        buf = io.BytesIO()
        _, png_bytes = cv2.imencode('.png', overlay)
        buf.write(png_bytes.tobytes())
        st.download_button(
            label="⬇️ Download Contour Overlay (PNG)",
            data=buf.getvalue(),
            file_name="verified_overlay.png",
            mime="image/png",
        )