import logging

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)


def _rgb_to_lab(rgb_u8: np.ndarray) -> np.ndarray:
    lab = (
        cv2.cvtColor(rgb_u8.reshape(-1, 1, 3), cv2.COLOR_RGB2Lab)
        .reshape(-1, 3)
        .astype(np.float32)
    )
    return lab


def _lab_to_rgb(lab_f32: np.ndarray) -> np.ndarray:
    lab_u8 = np.clip(lab_f32, 0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(lab_u8.reshape(-1, 1, 3), cv2.COLOR_Lab2RGB).reshape(-1, 3)
    return rgb


def _lab_to_lch(lab: np.ndarray) -> np.ndarray:
    l = lab[:, 0]
    a = lab[:, 1] - 128.0  # OpenCV a,b is offset by 128
    b = lab[:, 2] - 128.0
    c = np.sqrt(a * a + b * b)
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
    if lch1[0, 0] > lch2[0, 0]:
        luma_max, luma_min = lch1[0, 0], lch2[0, 0]
    else:
        luma_max, luma_min = lch2[0, 0], lch1[0, 0]
    ratio = (luma_max / 255 + 0.05) / (luma_min / 255 + 0.05)
    return ratio


def _lch_from_contrast(desired_ratio, lch1) -> np.ndarray:
    # Returns an LCH color with a brighter luma than lch1 to match desired contrast ratio
    luma_low = lch1[0, 0]
    luma_high = (desired_ratio * (luma_low / 255 + 0.05) - 0.05) * 255
    lch2 = lch1.copy()
    lch2[0, 0] = luma_high
    return lch2


def _neutral_chroma_threshold(luma, min_threshold=3.5, max_threshold=14) -> float:
    # Returns dynamic threshold to consider a color to be "neutral". Brighter colors = higher chroma threshold.
    return min_threshold + (max_threshold - min_threshold) * (luma / 255) ** 0.5


def _sample_pixels(img, max_samples=12500, random_state=69):
    n = img.shape[0]
    if n <= max_samples:
        return img
    rs = np.random.RandomState(random_state)
    idx = rs.choice(n, size=max_samples, replace=False)
    return img[idx]


def _read_image(source: str | Image.Image) -> np.ndarray:
    if isinstance(source, str):
        try:
            source = Image.open(source)
        except FileNotFoundError:
            logger.warning(f'Banner image not found')
            return np.array([[0, 0, 0]], dtype=np.uint8)

    # Crop code to target (from canvas.py)
    target_width, target_height = 1440, 260
    banner_width, banner_height = source.size

    ratio = max(target_width / banner_width, target_height / banner_height)
    new_width = int(banner_width * ratio)
    new_height = int(banner_height * ratio)
    source = source.resize((new_width, new_height), Image.Resampling.LANCZOS)

    width_diff = (new_width - target_width) // 2
    height_diff = (new_height - target_height) // 2
    source = source.crop(
        (
            width_diff,
            height_diff,
            width_diff + target_width,
            height_diff + target_height,
        )
    )

    # Alpha mask, only consider pixels without high transparency
    pil_img = source.convert('RGBA')
    rgba = np.array(pil_img)

    alpha_threshold = 150
    rgba = rgba.reshape(-1, 4)
    rgba = rgba[rgba[:, 3] >= alpha_threshold]
    rgb = rgba[:, :3]

    if rgb.size == 0:
        logger.warning(f'Banner image is empty: {source}')
        rgb = np.array([[0, 0, 0]], dtype=np.uint8)

    return rgb.astype(np.uint8)


def _choose_k_dynamic(sample_lab: np.ndarray, k_min=3, k_max=9) -> int:
    def evaluate_k(k_test: int):
        km = MiniBatchKMeans(n_clusters=k_test, random_state=42, n_init='auto')
        labels = km.fit_predict(sample_lab)
        try:
            sil = silhouette_score(sample_lab, labels, metric='euclidean')
        except Exception as e:  # Divide by 0, overflow, etc
            logger.debug(f'Failed to compute silhouette_score: {e}')
            sil = -1.0

        counts = np.bincount(labels, minlength=k_test).astype(np.float32)
        weights = counts / counts.sum()
        small_fraction = float((weights < 0.01).mean())
        cluster_variance = float(weights.max() - weights.min())
        score = sil - 0.20 * small_fraction - 0.10 * cluster_variance
        logger.debug(f'k={k_test}: score {score}')
        return k_test, score, small_fraction

    results = []
    for k in range(k_min, k_max + 1):
        results.append(evaluate_k(k))

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
        logger.debug(
            f'Weighted average chroma = {weighted_avg_chroma}, image is monochrome'
        )
        initial_chroma = 10

    # Weight clusters based on saturation so neutral clusters do not influence text color as much
    neutral_mult = np.clip(chroma / 20.0, 0.15, 1.0)
    weights = img_weights * neutral_mult

    best = 0
    best_color = np.array(
        [[initial_luma, initial_chroma, candidates_h[0]]], dtype=np.float32
    )

    # Select most palate-matching analogous hue
    for h in candidates_h:
        lch_test = np.array([[initial_luma, initial_chroma, h]], dtype=np.float32)

        text_h = lch_test[0, 2]
        centers_h = img_centers_lch[:, 2]
        angular_diff = np.abs(((text_h - centers_h + 180) % 360) - 180)

        score = np.sum((1 - angular_diff / 180) * weights)
        logger.debug(f'Text candidates h = {h} similarity score = {score}')
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
        logger.debug(f'{ratio} < {target_contrast_ratio}, using white')
        return np.array([[255, 255, 255]], dtype=np.float32)

    return _lab_to_rgb(_lch_to_lab(best_color))


async def get_image_colors(source: Image.Image) -> tuple[tuple, tuple, tuple, tuple]:
    rgb = _read_image(source)
    rgb = _sample_pixels(rgb, max_samples=15000)
    lab = _rgb_to_lab(rgb)
    lab_subset = _sample_pixels(lab, max_samples=5000)

    k = _choose_k_dynamic(lab_subset)

    source_name = source if isinstance(source, str) else 'image'
    logger.debug(f'{source_name} chose k={k} clusters')
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(lab)

    centers_lab = kmeans.cluster_centers_.astype(np.float32)
    labels = kmeans.labels_
    counts = np.bincount(labels, minlength=k).astype(np.float32)

    order = np.argsort(counts)[::-1]
    centers_lab = centers_lab[order]
    counts = counts[order]
    weights = counts / counts.sum()

    lch_centers = _lab_to_lch(centers_lab)
    skin_mask = _is_skin_lab(centers_lab)

    neutral_dominant_threshold = 0.45
    skin_dominant_threshold = 0.33

    target_primary_l = 35  # Primary luma
    box_primary_contrast = 1.25
    box_label_contrast = 2.5
    bad_luma_threshold = 0.42
    bad_luma_delta = 100
    yellow_range = (78, 102)

    chroma = lch_centers[:, 1]
    luma = lch_centers[:, 0]
    neutral_mask = chroma < _neutral_chroma_threshold(luma)

    # Select primary
    primary_idx = None
    for i in range(k):
        if bool(neutral_mask[i]):
            continue
        is_skin = bool(skin_mask[i])
        is_yellow = yellow_range[0] < lch_centers[i][2] < yellow_range[1]
        if (not is_skin) or (is_skin and weights[i] >= skin_dominant_threshold):
            if lch_centers[i][0] - target_primary_l > bad_luma_delta and (
                bad_luma_threshold > weights[i] or is_yellow
            ):
                continue
            primary_idx = i
            break
    # Remove luma check
    if primary_idx is None:
        logger.debug(f'{source_name} Failed luma check')
        for i in range(k):
            if bool(neutral_mask[i]):
                continue
            is_skin = bool(skin_mask[i])
            if (not is_skin) or (is_skin and weights[i] >= skin_dominant_threshold):
                primary_idx = i
                break
    # Remove skin check
    if primary_idx is None:
        logger.debug(f'{source_name} Failed skin check')
        for i in range(k):
            if bool(neutral_mask[i]):
                continue
            primary_idx = i
            break
    # Remove strict neutral check
    if primary_idx is None:
        logger.debug(f'{source_name} Failed strict neutral check')
        for i in range(k):
            if bool(neutral_mask[i]) and weights[i] >= neutral_dominant_threshold:
                primary_idx = i
                break
    # Remove all checks (backup)
    if primary_idx is None:
        logger.debug(f'{source_name} Failed all checks')
        primary_idx = int(np.argmax(weights))

    primary_lch = lch_centers[[primary_idx]]

    # Luminance and chroma adjustment
    chroma_cap = float(max(np.percentile(chroma, 85), 12.0))

    def adjust_l_and_cap_c(
        lch: np.ndarray, target_l: float, alpha_l: float, c_cap: float
    ) -> np.ndarray:
        out = lch.copy()
        out[:, 0] = np.clip((1 - alpha_l) * out[:, 0] + alpha_l * target_l, 0, 255)
        out[:, 1] = np.minimum(out[:, 1], c_cap)
        return out

    # Alpha [0, 1] - Lower values will adjust primary luma less, keeping closer to original value in image
    alpha = 0.9 if primary_lch[:, 0] > target_primary_l else 0.5

    primary_lch = adjust_l_and_cap_c(
        primary_lch, target_primary_l, alpha_l=alpha, c_cap=chroma_cap
    )
    primary_rgb = _lab_to_rgb(_lch_to_lab(primary_lch))[0]

    box_lch = _lch_from_contrast(desired_ratio=box_primary_contrast, lch1=primary_lch)
    box_rgb = _lab_to_rgb(_lch_to_lab(box_lch))[0]

    label_lch = _lch_from_contrast(desired_ratio=box_label_contrast, lch1=box_lch)
    label_rgb = _lab_to_rgb(_lch_to_lab(label_lch))[0]

    text_rgb = _get_text_color(
        box_color_lch=box_lch, img_centers_lch=lch_centers, img_weights=weights
    )[0]
    return (
        tuple(int(x) for x in primary_rgb),
        tuple(int(x) for x in box_rgb),
        tuple(int(x) for x in text_rgb),
        tuple(int(x) for x in label_rgb),
    )


def apply_color_overlay(base_path, color_rgb) -> Image.Image:
    base = Image.open(base_path).convert('RGBA')
    overlay = Image.new('RGBA', base.size, color_rgb + (255,))
    overlay.putalpha(base.split()[3])
    return overlay


class ColorUtils:
    """Color conversion and manipulation utilities"""

    @staticmethod
    def hex_to_rgb(hex_color):
        r = int(hex_color[1:3], 16) / 255
        g = int(hex_color[3:5], 16) / 255
        b = int(hex_color[5:7], 16) / 255
        return r, g, b, 1.0

    @staticmethod
    def hex_to_rgb_int(hex_color):
        hex_color = hex_color.lstrip('#')
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    @staticmethod
    def to_rgb_tuple(color):
        if isinstance(color, tuple):
            return color
        return ColorUtils.hex_to_rgb_int(color)

    @staticmethod
    def rgb_to_hex(rgb_tuple):
        """Convert RGB tuple to hex color"""
        if isinstance(rgb_tuple, str):
            return rgb_tuple
        r, g, b = rgb_tuple[:3]
        return f'#{r:02x}{g:02x}{b:02x}'

    @staticmethod
    def normalize_color(color):
        """Normalize color to consistent format"""
        if isinstance(color, str):
            return ColorUtils.hex_to_rgb(color)
        if isinstance(color, tuple) and len(color) >= 3:
            if all(0 <= c <= 1 for c in color[:3]):
                return color
            r, g, b = color[:3]
            return r / 255.0, g / 255.0, b / 255.0, 1.0
        return color
