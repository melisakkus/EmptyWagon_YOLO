import cv2

image_path = "data/reference/reference_image.png"
image = cv2.imread(image_path)
image = cv2.resize(image, (1200, 750))

def get_coordinates(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Selected point: X= {x}, Y={y}")
        cv2.circle(image, (x, y), 5, (0, 255, 0), -1) # Yeşil bir daire
        text = f" {x} , {y}"
        cv2.putText(image,text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
        cv2.imshow("Reference Image", image)

if image is None:
    print("Resim yüklenemedi. Dosya yolunu kontrol edin.")
else:
    cv2.imshow("Reference Image", image)

# Pencereye fare geri arama fonksiyonunu ata
cv2.setMouseCallback("Reference Image", get_coordinates)
cv2.waitKey(0)  # Bir tuşa basılana kadar bekle

output_path = "outputs/images/reference_image.png"
cv2.imwrite(output_path, image)
print(f"İşaretlenen resim '{output_path}' yoluna kaydedildi.")
cv2.destroyAllWindows()