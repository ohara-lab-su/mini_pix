from pathlib import Path

import numpy as np
from PIL import Image


files = [
    Path("example_1.png"),
    Path("example_2.png"),
    Path("example_3.png"),
    Path("example_4.png"),
    Path("example_5.png"),
]

images = []

print("=== 各画像 ===")

for path in files:
    image = np.array(Image.open(path))

    if image.ndim == 3:
        image = image[:, :, 0]

    images.append(image)

    positions = np.argwhere(image != 0)

    print()
    print(path.name)
    print("  dtype   :", image.dtype)
    print("  min     :", image.min())
    print("  max     :", image.max())
    print("  sum     :", image.sum())
    print("  nonzero :", len(positions))


print()
print("=== 画像間の非ゼロ画素の重複 ===")

for i in range(5):
    mask_i = images[i] != 0

    for j in range(i + 1, 5):
        mask_j = images[j] != 0

        intersection = np.count_nonzero(mask_i & mask_j)
        union = np.count_nonzero(mask_i | mask_j)

        if union == 0:
            jaccard = 0.0
        else:
            jaccard = intersection / union

        print(
            f"{files[i].name} vs {files[j].name}: "
            f"共通={intersection}, "
            f"Jaccard={jaccard:.6f}"
        )


print()
print("=== 同じ座標が何回出現したか ===")

hit_count = np.zeros(images[0].shape, dtype=np.uint8)

for image in images:
    hit_count += image != 0

for count in range(5, 1, -1):
    positions = np.argwhere(hit_count == count)

    print()
    print(f"{count} / 5 回出現: {len(positions)} pixels")

    for y, x in positions:
        values = []

        for image in images:
            values.append(int(image[y, x]))

        print(
            f"  x={x:3d}, y={y:3d}, "
            f"values={values}"
        )


print()
print("=== 出現回数の集計 ===")

for count in range(1, 6):
    n = np.count_nonzero(hit_count == count)
    print(f"{count}回だけ/以上ではなく、正確に{count}回出現: {n} pixels")