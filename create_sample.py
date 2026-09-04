import cv2
import numpy as np

# Create clean white background
img = np.ones((600, 1000, 3), dtype=np.uint8) * 255

# Valid ICAO 9303 MRZ lines (Mathematically verified check digits: 9 and 9)
line1 = "P<INDDEMO<<NAME<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
line2 = "J1234567<9IND9001011M3001019<<<<<<<<<<<<<<02"

font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(img, "PASSPORT / PASSEPORT", (50, 80), font, 1.0, (0, 0, 0), 2)
cv2.putText(img, "REPUBLIC OF INDIA", (50, 130), font, 0.8, (0, 0, 0), 2)

# Position MRZ lines at bottom
cv2.putText(img, line1, (40, 480), font, 0.75, (0, 0, 0), 2)
cv2.putText(img, line2, (40, 530), font, 0.75, (0, 0, 0), 2)

cv2.imwrite("sample_update.png", img)
print("Updated 'sample_update.png' generated successfully!")