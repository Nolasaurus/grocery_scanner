import cv2


def main():
    image_path = 'static/captures/capture_20250110_163128.jpg'
    image = cv2.imread(image_path)
    if image is not None:
        find_barcode(image)
    else:
        print('image failed to load')

def display_image(image):
        cv2.imshow('Image', image)  # Display the image in a window
        cv2.waitKey(0)  # Wait for a key press to close the window
        cv2.destroyAllWindows()  # Close the display window
    


def find_barcode(image_with_barcode):
    if image_with_barcode.any():  # Check if the image array contains any non-zero elements
        print('Image loaded successfully')
        
    else:
        print('Incorrect file type or invalid image')

    bw = cv2.cvtColor(image_with_barcode, cv2.COLOR_BGR2GRAY)
    # high_contrast = cv2.
    # display_image(image_with_barcode)
    display_image(bw)


    
    return None


if __name__ == "__main__":
    main()