import face_recognition
import numpy as np
from pathlib import Path
from typing import Optional
import os
import cv2

class FaceRecognition:
    """
    FaceRecognition class provides methods for saving and verifying face encodings.
    
    Methods:
        save_face_encoding(image_data: bytes, username: str) -> tuple[bool, str, bytes]:
            Processes the provided image data to detect a face and save its encoding.
            Returns a tuple indicating success, a message, and the encoding bytes.
        
        verify_face(image_data: bytes, saved_encoding_bytes: bytes) -> bool:
            Verifies if the provided image data matches the saved face encoding.
            Returns True if a match is found, otherwise returns False.
    """

    async def save_face_encoding(self, image_data: bytes, username: str) -> tuple[bool, str, bytes]:
        try:
            # Convert image bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                return False, "No face detected in the image", None
                
            if len(face_locations) > 1:
                return False, "Multiple faces detected. Please ensure only one face is in the frame", None
            
            # Get face encoding
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            
            # Convert encoding to bytes for database storage
            encoding_bytes = face_encoding.tobytes()
            
            return True, "Face registered successfully", encoding_bytes
            
        except Exception as e:
            return False, f"Error processing face: {str(e)}", None

    async def verify_face(self, image_data: bytes, saved_encoding_bytes: bytes) -> bool:
        try:
            # Convert image bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face encoding from image
            face_locations = face_recognition.face_locations(rgb_image)
            if not face_locations:
                return False
                
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            
            # Convert saved encoding bytes back to numpy array
            saved_encoding = np.frombuffer(saved_encoding_bytes, dtype=np.float64)
            saved_encoding = saved_encoding.reshape((128,))
            
            # Compare faces
            matches = face_recognition.compare_faces([saved_encoding], face_encoding, tolerance=0.6)
            return matches[0]
            
        except Exception as e:
            print(f"Error during face verification: {e}")
            return False