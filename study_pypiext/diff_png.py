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

for path in files:
    image = np.array(Image.open(path))

    if image.ndim == 3:
        image = image[:, :, 0]

    images.append(image)


# 5回すべてで光っている画素
# → 常時点灯している固定画素として今回の比較から除外
always_on = np.ones(images[0].shape, dtype=bool)

for image in images:
    always_on &= image != 0


print("=== 固定画素 ===")
print("5回すべてで点灯:", np.count_nonzero(always_on))

for y, x in np.argwhere(always_on):
    print(f"  x={x:3d}, y={y:3d}")


print()
print("=== X線イベント候補 ===")

event_masks = []

for i, image in enumerate(images):
    # 光っている画素から固定画素を除外
    event_mask = (image != 0) & ~always_on
    event_masks.append(event_mask)

    positions = np.argwhere(event_mask)

    print()
    print(files[i].name)
    print("  event pixels:", len(positions))

    for y, x in positions:
        print(
            f"  x={x:3d}, y={y:3d}, "
            f"value={image[y, x]}"
        )


print()
print("=== 測定ごとのX線イベント位置の比較 ===")

for i in range(5):
    for j in range(i + 1, 5):
        common = np.count_nonzero(
            event_masks[i] & event_masks[j]
        )

        print(
            f"{files[i].name} vs {files[j].name}: "
            f"共通イベント画素={common}"
        )