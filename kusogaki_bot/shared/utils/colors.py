import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from joblib import Parallel, delayed
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def _rgb_to_lab(rgb_u8: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(rgb_u8.reshape(-1, 1, 3), cv2.COLOR_RGB2Lab).reshape(-1, 3).astype(np.float32)
    return lab

def _lab_to_rgb(lab_f32: np.ndarray) -> np.ndarray:
    lab_u8 = np.clip(lab_f32, 0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(lab_u8.reshape(-1, 1, 3), cv2.COLOR_Lab2RGB).reshape(-1, 3)
    return rgb

def _lab_to_lch(lab: np.ndarray) -> np.ndarray:
    l = lab[:, 0]
    a = lab[:, 1] - 128.0  # OpenCV a,b is offset by 128
    b = lab[:, 2] - 128.0
    c = np.sqrt(a*a + b*b)
    h = np.degrees(np.arctan2(b, a)) % 360.0
    return np.stack([l, c, h], axis=1).astype(np.float32)

def _lch_to_lab(lch: np.ndarray) -> np.ndarray:
    l, c, h = lch[:, 0], lch[:, 1], np.radians(lch[:, 2])
    a = c * np.cos(h)
    b = c * np.sin(h)
    lab = np.stack([l, a + 128.0, b + 128.0], axis=1).astype(np.float32)
    return lab


def _is_skin_lab(lab: np.ndarray) -> np.ndarray:
    # Flag Lab colors likely to be skin to avoid using as background
    rgb = _lab_to_rgb(lab)
    ycrcb = cv2.cvtColor(rgb.reshape(-1, 1, 3), cv2.COLOR_RGB2YCrCb).reshape(-1, 3)
    cr, cb = ycrcb[:, 1], ycrcb[:, 2]
    return (cr >= 135) & (cr <= 180) & (cb >= 85) & (cb <= 135)

def _lch_contrast_ratio(lch1, lch2) -> float:
    if lch1[:, 0] > lch2[0, 0]:
        luma_max, luma_min = lch1[0, 0], lch2[0, 0]
    else:
        luma_max, luma_min = lch2[0, 0], lch1[0, 0]
    ratio = (luma_max/255 + 0.05) / (luma_min/255 + 0.05)
    return ratio

def _lch_from_contrast(desired_ratio, lch1) -> np.ndarray:
    # Returns an LCH color with a brighter luma than lch1 to match desired contrast ratio
    luma_low = lch1[0, 0]
    luma_high = (desired_ratio * (luma_low/255 + 0.05) - 0.05)*255
    lch2 = lch1.copy()
    lch2[0, 0] = luma_high
    return lch2


def _read_image(source: str | Image.Image) -> np.ndarray:
    if isinstance(source, str):
        img = cv2.imread(source, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"Image not found: {source}")
    else:
        pil_img = source.convert("RGBA")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)

    h, w = img.shape[:2]
    if max(h, w) > 500:
        scale = 500.0 / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        rgb = img.reshape(-1, 3)
    elif img.shape[2] == 4:
        rgba = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        rgba = rgba.reshape(-1, 4)
        rgba = rgba[rgba[:, 3] > 250]
        rgb = rgba[:, :3]
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).reshape(-1, 3)

    return rgb.astype(np.uint8)


def _choose_k_dynamic(img_rgb_uint8: np.ndarray, k_min=3, k_max=10) -> int:
    def sample_pixels(max_samples=9500, random_state=69):
        n = img_rgb_uint8.shape[0]
        if n <= max_samples:
            return img_rgb_uint8
        rs = np.random.RandomState(random_state)
        idx = rs.choice(n, size=max_samples, replace=False)
        return img_rgb_uint8[idx]

    sample_rgb = sample_pixels()
    sample_lab = _rgb_to_lab(sample_rgb)

    def evaluate_k(k: int):
        km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = km.fit_predict(sample_lab)
        try:
            sil = silhouette_score(sample_lab, labels, metric='euclidean')
        except Exception as e:  # Divide by 0, overflow, etc
            logger.debug(f"Failed to compute silhouette_score: {e}")
            sil = -1.0

        counts = np.bincount(labels, minlength=k).astype(np.float32)
        weights = counts / counts.sum()
        small_fraction = float((weights < 0.01).mean())
        cluster_variance = float(weights.max() - weights.min())
        score = sil - 0.20 * small_fraction - 0.10 * cluster_variance
        logger.debug(f"k={k}: score {score}")
        return k, score, small_fraction

    results = Parallel(n_jobs=-1, prefer="threads")(delayed(evaluate_k)(k) for k in range(k_min, k_max + 1))
    best_score = max(r[1] for r in results)
    tol = 0.02
    near = [r for r in results if (best_score - r[1]) <= tol]
    best_k = sorted(near, key=lambda r: (r[2], r[0]))[0][0]
    return best_k


def _get_text_color(box_color_lch, img_centers_lch, img_weights) -> np.ndarray:
    # img_centers_lch, img_weights = K-means LCH centers and weights
    initial_luma = 220
    initial_chroma = 28
    target_contrast_ratio = 3.0
    box_hue = float(box_color_lch[0, 2])

    candidates_h = [(box_hue + 30.0) % 360.0, (box_hue - 30.0) % 360.0]

    # Chroma clamping for monochrome images
    chroma = img_centers_lch[:, 1].astype(np.float32)
    weighted_avg_chroma = np.sum(chroma * img_weights)
    if weighted_avg_chroma < 0.1:
        logger.debug(f"Weighted average chroma = {weighted_avg_chroma}, image is monochrome")
        initial_chroma = 10

    # Weight clusters based on saturation so neutral clusters do not influence text color as much
    neutral_mult = np.clip(chroma / 20.0, 0.15, 1.0)
    weights = img_weights * neutral_mult

    best = 0
    best_color = np.array([[initial_luma, initial_chroma, candidates_h[0]]], dtype=np.float32)

    # Select most pallatte-matching analagous hue
    for h in candidates_h:
        lch_test = np.array([[initial_luma, initial_chroma, h]], dtype=np.float32)

        text_h = lch_test[0, 2]
        centers_h = img_centers_lch[:, 2]
        angular_diff = np.abs(((text_h - centers_h + 180) % 360) - 180)

        score = np.sum((1 - angular_diff/180) * weights)
        logger.debug(f"Text candidates h = {h} similarity score = {score}")
        if score > best:
            best = score
            best_color = lch_test

    ratio = _lch_contrast_ratio(best_color, box_color_lch)

    # Check ratio, raise luma as needed to get contrast correct
    if ratio < target_contrast_ratio:
        lo = initial_luma
        hi = 255.0
        for _ in range(10):
            test_l = (lo + hi) / 2.0
            best_color[:, 0] = test_l
            ratio_test = _lch_contrast_ratio(best_color, box_color_lch)
            if ratio_test >= target_contrast_ratio:
                ratio = ratio_test
                break
            lo = test_l

    if ratio < target_contrast_ratio:
        logger.debug(f"{ratio} < {target_contrast_ratio}, using white")
        return np.array([[255, 255, 255]], dtype=np.float32)

    return _lab_to_rgb(_lch_to_lab(best_color))


def get_image_colors(source: Image.Image) -> tuple[tuple, tuple, tuple, tuple]:
    logger.info(f"Extracting colors from image")
    rgb = _read_image(source)
    lab = _rgb_to_lab(rgb)

    k = _choose_k_dynamic(rgb)
    # k = 6
    source_name = source if isinstance(source, str) else "image"
    logger.debug(f"{source_name} chose k={k} clusters")
    kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, n_init="auto").fit(lab)

    centers_lab = kmeans.cluster_centers_.astype(np.float32)
    labels = kmeans.labels_
    counts = np.bincount(labels, minlength=k).astype(np.float32)

    order = np.argsort(counts)[::-1]
    centers_lab = centers_lab[order]
    counts = counts[order]
    weights = counts / counts.sum()

    lch_centers = _lab_to_lch(centers_lab)
    skin_mask   = _is_skin_lab(centers_lab)

    neutral_chroma_threshold   = 8.0
    neutral_dominant_threshold = 0.45
    skin_dominant_threshold = 0.25

    target_primary_l = 35  # Primary luma
    box_primary_contrast = 1.25
    box_label_contrast = 2.5
    bad_luma_threshold = 0.45
    bad_luma_delta = 100

    chroma = lch_centers[:, 1]
    neutral_mask = chroma < neutral_chroma_threshold

    # Select primary
    primary_idx = None
    for i in range(k):
        if bool(neutral_mask[i]):
            continue
        is_skin = bool(skin_mask[i])
        if (not is_skin) or (is_skin and weights[i] >= skin_dominant_threshold):
            if lch_centers[i][0] - target_primary_l > bad_luma_delta and bad_luma_threshold > weights[i]:
                continue
            primary_idx = i
            break
    # Remove skin check
    if primary_idx is None:
        logger.debug(f"{source_name} Failed skin check")
        for i in range(k):
            if bool(neutral_mask[i]):
                continue
            if lch_centers[i][0] - target_primary_l > bad_luma_delta and bad_luma_threshold > weights[i]:
                continue
            primary_idx = i
            break
    # Remove luma check
    if primary_idx is None:
        logger.debug(f"{source_name} Failed luma check")
        for i in range(k):
            if bool(neutral_mask[i]):
                continue
            primary_idx = i
            break
    # Remove strict neutral check
    if primary_idx is None:
        logger.debug(f"{source_name} Failed strict neutral check")
        for i in range(k):
            if bool(neutral_mask[i]) and weights[i] >= neutral_dominant_threshold:
                primary_idx = i
                break
    # Remove all checks (backup)
    if primary_idx is None:
        logger.debug(f"{source_name} Failed all checks")
        primary_idx = int(np.argmax(weights))

    primary_lch = lch_centers[[primary_idx]]

    # Luminance and chroma adjustment
    chroma_cap = float(max(np.percentile(chroma, 85), 12.0))

    def adjust_l_and_cap_c(lch: np.ndarray, target_l: float, alpha_l: float, c_cap: float) -> np.ndarray:
        out = lch.copy()
        out[:, 0] = np.clip((1 - alpha_l) * out[:, 0] + alpha_l * target_l, 0, 255)
        out[:, 1] = np.minimum(out[:, 1], c_cap)
        return out

    # Alpha [0, 1] - Lower values will adjust primary luma less, keeping closer to original value in image
    alpha = 0.9 if primary_lch[:, 0] > target_primary_l else 0.5
    
    primary_lch = adjust_l_and_cap_c(primary_lch, target_primary_l, alpha_l=alpha, c_cap=chroma_cap)
    primary_rgb = _lab_to_rgb(_lch_to_lab(primary_lch))[0]

    box_lch = _lch_from_contrast(desired_ratio=box_primary_contrast, lch1=primary_lch)
    box_rgb = _lab_to_rgb(_lch_to_lab(box_lch))[0]

    label_lch = _lch_from_contrast(desired_ratio=box_label_contrast, lch1=box_lch)
    label_rgb = _lab_to_rgb(_lch_to_lab(label_lch))[0]

    text_rgb = _get_text_color(box_color_lch=box_lch, img_centers_lch=lch_centers, img_weights=weights)[0]
    logger.info(f"{source_name} Primary: {primary_rgb}, Box: {box_rgb}, Text: {text_rgb}, Label: {label_rgb}")
    return (
        tuple(int(x) for x in primary_rgb),
        tuple(int(x) for x in box_rgb),
        tuple(int(x) for x in text_rgb),
        tuple(int(x) for x in label_rgb)
        )


def apply_color_overlay(base_path, color_rgb) -> Image.Image:
    base = Image.open(base_path).convert("RGBA")
    overlay = Image.new("RGBA", base.size, color_rgb + (255,))
    overlay.putalpha(base.split()[3])
    return overlay


"""
def create_wrapped_image(banner_path, pfp_path, output_path):
    primary_color, box_color, text_color, label_color = get_image_colors(banner_path)

    img = Image.new("RGBA", (1440, 1080), (0, 0, 0))

    banner = Image.open(banner_path).convert("RGBA")
    target_width, target_height = 1440, 260
    banner_width, banner_height = banner.size

    ratio = max(target_width / banner_width, target_height / banner_height)
    new_width = int(banner_width * ratio)
    new_height = int(banner_height * ratio)
    banner = banner.resize((new_width, new_height), Image.Resampling.LANCZOS)

    width_diff = (new_width - target_width) // 2
    height_diff = (new_height - target_height) // 2
    banner = banner.crop(
        (
            width_diff,
            height_diff,
            width_diff + target_width,
            height_diff + target_height,
        )
    )

    img.paste(banner, (0, 0), banner)

    gradient_colored = apply_color_overlay("Images/gradient.png", primary_color)
    temp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    temp.paste(gradient_colored, (0, 29))
    img = Image.alpha_composite(img, temp)

    background_colored = apply_color_overlay("Images/background.png", primary_color)
    temp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    mask = Image.new("RGBA", background_colored.size, (0, 0, 0, 200))
    temp.paste(background_colored, (0, 247), mask)
    # temp.paste(background_colored, (0, 247))
    img = Image.alpha_composite(img, temp)

    template_colored = apply_color_overlay("Images/template3.png", box_color)
    temp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    temp.paste(template_colored, (92, 308))
    img = Image.alpha_composite(img, temp)

    pfp = Image.open(pfp_path).convert("RGBA")
    pfp = pfp.resize((145, 145), Image.Resampling.LANCZOS)
    img.paste(pfp, (92, 92), pfp)

    label_img = apply_color_overlay("Images/template4.png", label_color)
    img.paste(label_img, (92, 308), label_img)

    img.save(output_path, "PNG")


def main():
    test_pairs = [
        ("Test Images/banner.jpg", "Test Images/pfp.png"),
        ("Test Images/Banner2.png", "Test Images/pfp2.png"),
        ("Test Images/banner3.jpg", "Test Images/pfp3.png"),
        ("Test Images/banner4.jpg", "Test Images/pfp4.png"),
        ("Test Images/banner5.jpg", "Test Images/pfp5.png"),
        ("Test Images/banner6.jpg", "Test Images/pfp6.png"),
        ("Test Images/banner7.jpg", "Test Images/pfp7.jpg"),
        ("Test Images/banner8.jpg", "Test Images/pfp8.png"),
        ("Test Images/banner9.jpg", "Test Images/pfp9.png"),
        ("Test Images/banner10.jpg", "Test Images/pfp10.png"),
        ("Test Images/banner11.jpg", "Test Images/pfp11.png"),
        ("Test Images/banner12.jpg", "Test Images/pfp12.jpg"),
        ("Test Images/banner13.jpg", "Test Images/pfp13.png"),
        ("Test Images/banner14.jpg", "Test Images/pfp14.jpg"),
        ("Test Images/banner15.jpg", "Test Images/pfp15.png"),
        ("Test Images/banner16.jpg", "Test Images/pfp16.png"),
        ("Test Images/banner17.jpg", "Test Images/pfp17.png"),
        ("Test Images/banner18.png", "Test Images/pfp18.png"),
        ("Test Images/banner19.jpg", "Test Images/pfp19.png"),
        ("Test Images/banner20.jpg", "Test Images/pfp20.png"),
        ("Test Images/banner21.jpg", "Test Images/pfp21.png"),
        ("Test Images/banner22.jpg", "Test Images/pfp22.png"),
        ("Test Images/banner23.jpg", "Test Images/pfp23.png"),
        ("Test Images/banner24.jpg", "Test Images/pfp24.png"),
        ("Test Images/banner25.jpg", "Test Images/pfp25.png"),
        ("Test Images/banner27.jpg", "Test Images/pfp26.png"),
        ("Test Images/banner28.jpg", "Test Images/pfp27.jpg"),
        ("Test Images/banner29.jpg", "Test Images/pfp28.png"),
        ("Test Images/banner30.jpg", "Test Images/pfp29.jpg"),
        ("Test Images/banner31.jpg", "Test Images/pfp30.png"),
        ("Test Images/banner32.jpg", "Test Images/pfp31.jpg"),
        ("Test Images/banner33.jpg", "Test Images/pfp32.png"),
        ("Test Images/banner34.jpg", "Test Images/pfp33.png"),
        ("Test Images/banner35.jpg", "Test Images/pfp34.png"),
        ("Test Images/banner36.jpg", "Test Images/pfp35.png"),
        ("Test Images/banner37.jpg", "Test Images/pfp36.png"),
        ("Test Images/banner38.jpeg", "Test Images/pfp37.png"),
        ("Test Images/banner39.jpg", "Test Images/pfp38.png"),
        ("Test Images/banner40.jpg", "Test Images/pfp39.png"),
        ("Test Images/banner41.jpeg", "Test Images/pfp40.png"),
        ("Test Images/banner42.jpg", "Test Images/pfp41.png"),
        ("Test Images/banner43.jpg", "Test Images/pfp42.png"),
    ]

    for i, (banner_path, pfp_path) in enumerate(test_pairs, 1):
        output_path = f"Profile Test Images/profile{i}.png"
        create_wrapped_image(banner_path, pfp_path, output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
"""
