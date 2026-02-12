import boto3
import json
from PIL import Image
import io
import base64
from typing import Dict, Optional
from flask import current_app

class OCRClient:
    def __init__(self):
        self.aws_access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = current_app.config.get('AWS_REGION', 'us-east-1')
        
        if self.aws_access_key and self.aws_secret_key:
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
        else:
            self.textract_client = None
        
        self.last_confidence_score = 0.0
    
    def extract_text_from_image(self, image_path: str) -> str:
        if not self.textract_client:
            raise Exception("AWS Textract not configured")
        
        try:
            # Read and process image
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Optimize image for OCR
            optimized_image = self._optimize_image_for_ocr(image_bytes)
            
            # Call AWS Textract
            response = self.textract_client.detect_document_text(
                Document={'Bytes': optimized_image}
            )
            
            # Extract text and calculate confidence
            extracted_text, confidence = self._parse_textract_response(response)
            self.last_confidence_score = confidence
            
            return extracted_text
            
        except Exception as e:
            current_app.logger.error(f"OCR extraction error: {str(e)}")
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _optimize_image_for_ocr(self, image_bytes: bytes) -> bytes:
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if too large (max 2048px)
            max_size = 2048
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            return output.getvalue()
            
        except Exception as e:
            current_app.logger.warning(f"Image optimization failed: {str(e)}")
            return image_bytes  # Return original if optimization fails
    
    def _parse_textract_response(self, response: Dict) -> tuple:
        extracted_text = ""
        total_confidence = 0.0
        block_count = 0
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text = block.get('Text', '')
                confidence = block.get('Confidence', 0.0)
                
                extracted_text += text + " "
                total_confidence += confidence
                block_count += 1
        
        # Calculate average confidence
        avg_confidence = total_confidence / max(block_count, 1) / 100.0
        
        return extracted_text.strip(), avg_confidence
    
    def get_confidence_score(self) -> float:
        return self.last_confidence_score
    
    def extract_handwriting(self, image_path: str) -> Dict:
        # Specialized method for handwritten text
        if not self.textract_client:
            return {"error": "AWS Textract not configured"}
        
        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Optimize specifically for handwriting
            optimized_image = self._optimize_for_handwriting(image_bytes)
            
            response = self.textract_client.detect_document_text(
                Document={'Bytes': optimized_image}
            )
            
            # Parse with handwriting-specific logic
            result = self._parse_handwriting_response(response)
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Handwriting extraction error: {str(e)}")
            return {"error": f"Failed to extract handwriting: {str(e)}"}
    
    def _optimize_for_handwriting(self, image_bytes: bytes) -> bytes:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Adjust for handwriting (higher contrast, sharper)
            from PIL import ImageEnhance, ImageFilter
            
            # Sharpen for better character definition
            image = image.filter(ImageFilter.SHARPEN)
            
            # Increase contrast more aggressively for handwriting
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Adjust brightness
            brightness_enhancer = ImageEnhance.Brightness(image)
            image = brightness_enhancer.enhance(1.2)
            
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            return output.getvalue()
            
        except Exception as e:
            current_app.logger.warning(f"Handwriting optimization failed: {str(e)}")
            return image_bytes
    
    def _parse_handwriting_response(self, response: Dict) -> Dict:
        lines = []
        words = []
        total_confidence = 0.0
        item_count = 0
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                line_text = block.get('Text', '')
                line_confidence = block.get('Confidence', 0.0)
                
                lines.append({
                    'text': line_text,
                    'confidence': line_confidence / 100.0,
                    'bounding_box': block.get('Geometry', {}).get('BoundingBox', {})
                })
                
                total_confidence += line_confidence
                item_count += 1
                
            elif block['BlockType'] == 'WORD':
                word_text = block.get('Text', '')
                word_confidence = block.get('Confidence', 0.0)
                
                words.append({
                    'text': word_text,
                    'confidence': word_confidence / 100.0
                })
        
        # Combine all text
        full_text = ' '.join([line['text'] for line in lines])
        avg_confidence = total_confidence / max(item_count, 1) / 100.0
        
        self.last_confidence_score = avg_confidence
        
        return {
            'full_text': full_text,
            'lines': lines,
            'words': words,
            'confidence': avg_confidence,
            'word_count': len(words),
            'line_count': len(lines)
        }
    
    def validate_image(self, image_path: str) -> Dict:
        # Validate image before OCR processing
        try:
            with Image.open(image_path) as img:
                return {
                    'valid': True,
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'file_size': len(open(image_path, 'rb').read())
                }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def preprocess_student_work(self, image_path: str) -> Dict:
        # Specialized preprocessing for student handwriting/worksheets
        validation = self.validate_image(image_path)
        if not validation['valid']:
            return validation
        
        try:
            # Extract text with high confidence filtering
            handwriting_result = self.extract_handwriting(image_path)
            
            if 'error' in handwriting_result:
                return handwriting_result
            
            # Filter out low-confidence words (likely OCR errors)
            filtered_words = [
                word for word in handwriting_result['words'] 
                if word['confidence'] > 0.5
            ]
            
            # Reconstruct text from high-confidence words
            filtered_text = ' '.join([word['text'] for word in filtered_words])
            
            return {
                'original_text': handwriting_result['full_text'],
                'filtered_text': filtered_text,
                'confidence': handwriting_result['confidence'],
                'word_count': len(filtered_words),
                'processing_notes': self._generate_processing_notes(handwriting_result)
            }
            
        except Exception as e:
            return {'error': f'Preprocessing failed: {str(e)}'}
    
    def _generate_processing_notes(self, ocr_result: Dict) -> list:
        notes = []
        
        confidence = ocr_result.get('confidence', 0)
        word_count = len(ocr_result.get('words', []))
        
        if confidence < 0.6:
            notes.append("Low confidence - image quality may be poor")
        if word_count < 5:
            notes.append("Very short text detected")
        if confidence > 0.9:
            notes.append("High quality text extraction")
        
        return notes