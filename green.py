import os

try:
    import cv2
    import numpy as np
except:
    os.system("autorun.cmd")

def findGreen(base_img, prevCx=0, prevCy=0) -> tuple[int, int, any]:
    # Set brightness to max
    hsv_img = cv2.cvtColor(base_img, cv2.COLOR_BGR2HSV)
    hsv_img[:,:,2] = 255
    hsv_img[:,:,1] = 255
    saturated_img = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)

    # Remove non-green pixels
    mask = cv2.inRange(saturated_img, np.array([0, 127, 0]), np.array([127, 255, 127]))
    saturated_img[mask != 255] = np.array([0, 0, 0])

    # Remove details
    STRENGHT = 20
    fixed_img = cv2.GaussianBlur(saturated_img, (STRENGHT*2+1,STRENGHT*2+1), 0)
    gray_img = cv2.cvtColor(fixed_img, cv2.COLOR_BGR2GRAY)
    _, fixed_img = cv2.threshold(gray_img, 1, 255, cv2.THRESH_BINARY)

    # Find contours
    _, thresh = cv2.threshold(fixed_img, 127, 255, 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if (len(contours) == 0):
        return (0, 0, base_img)

    # Find largest contour
    main_contour = None
    max_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            main_contour = contour

    # Find center of mass
    M = cv2.moments(main_contour)
    Cx = int(M['m10']/M['m00'])
    Cy = int(M['m01']/M['m00'])

    # Make sure our center of mass is inside of a green zone
    done = False
    for search_radius in range(min(len(fixed_img), len(fixed_img[0]))):
        for x in range(Cx-search_radius, Cx+search_radius):
            for y in range(Cy-search_radius, Cy+search_radius):
                if (fixed_img[y, x] > 127):
                    Cx, Cy = x, y
                    done = True
                if done: break
            if done: break
        if done: break

    
    # Remove aberations
    if (abs(Cx-prevCx) > len(base_img) * (10/100) or abs(Cy-prevCy) > len(base_img[0])) and prevCx != 0 and prevCy != 0:
        return (0, 0, base_img)
    if cv2.contourArea(main_contour) < (len(base_img)*len(base_img[0])) * (1/100):
        return (0, 0, base_img)

    # Apply contours
    cv2.drawContours(base_img, [main_contour], 0, (255, 0, 0), 5)

    # Apply center of mass
    cv2.circle(base_img, (Cx,Cy), 25, (0, 0, 255), -1)

    return (Cx, Cy, base_img)
    

def main():
    cap = cv2.VideoCapture(0)
    
    Cx, Cy = 0, 0
    while True:
        _, frame = cap.read()
        Cx, Cy, img = findGreen(frame, Cx, Cy)
        
        # Define the text, font, and position
        text = 'Press ESC to exit'
        font = cv2.FONT_HERSHEY_SIMPLEX
        position = (0, 20)
        font_scale = .7
        font_color = (255, 0, 0)  # BGR format
        thickness = 1

        # Add text to the image
        cv2.putText(img, text, position, font, font_scale, font_color, thickness)
        
        cv2.imshow("Green image", img)
        if cv2.waitKey(1) == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()