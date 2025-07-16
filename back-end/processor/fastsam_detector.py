# processor/fastsam_detector.py
import cv2
import numpy as np
from ultralytics import YOLO, FastSAM
import torch
import os
import time


class FastSamDetector:
    def __init__(self, model_path):
        """
        初始化FastSAM检测器
        Args:
            model_path: 模型权重文件路径
        """

        self.DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.segmentation_model = FastSAM(model_path)

    def order_points(self, pts):
        '''Rearrange coordinates to order: 
        top-left, top-right, bottom-right, bottom-left'''
        rect = np.zeros((4, 2), dtype='float32')
        pts = np.array(pts)
        s = pts.sum(axis=1)
        # Top-left point will have the smallest sum.
        rect[0] = pts[np.argmin(s)]
        # Bottom-right point will have the largest sum.
        rect[2] = pts[np.argmax(s)]
        
        diff = np.diff(pts, axis=1)
        # Top-right point will have the smallest difference.
        rect[1] = pts[np.argmin(diff)]
        # Bottom-left will have the largest difference.
        rect[3] = pts[np.argmax(diff)]
        # Return the ordered coordinates.
        return rect.astype('int').tolist()

    def preprocess_image(self, image_bgr):
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Run FastSAM inference
        results = self.segmentation_model(image_rgb, device=self.DEVICE, retina_masks=True, imgsz=1024, conf=0.5, iou=0.7)

        # Check if results contain masks
        if not results or not hasattr(results[0], 'masks') or results[0].masks is None:
            raise ValueError("FastSAM returned no valid masks")

        # Select the largest mask by area
        masks = results[0].masks.data.cpu().numpy()  # Shape: (num_masks, height, width)
        areas = [np.sum(mask) for mask in masks]
        largest_mask_idx = np.argmax(areas)
        segmentation_mask = masks[largest_mask_idx]  # Binary mask (height, width)

        # Convert mask to binary (0 or 1)
        binary_mask = np.where(segmentation_mask > 0, 1, 0).astype(np.uint8)
        black_background = np.zeros_like(image_bgr)

        # Apply the binary mask to remove background
        new_image = np.where(binary_mask[..., np.newaxis] == 1, image_bgr, black_background)
        
        # Make a copy of the masked image
        orig_img = new_image.copy()

        # Sharpen the image
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        for _ in range(3):
            new_image = cv2.filter2D(new_image, -1, kernel)

        # Morphological closing
        kernel = np.ones((5, 5), np.uint8)
        new_image = cv2.morphologyEx(new_image, cv2.MORPH_CLOSE, kernel, iterations=3)

        # Gaussian blur
        new_image = cv2.GaussianBlur(new_image, (11, 11), 0)

        # Edge detection
        canny = cv2.Canny(new_image, 100, 200)
        canny = cv2.dilate(canny, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

        # Find contours
        contours, _ = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        if not contours:
            raise ValueError("No contours found for perspective transform")
        
        # Select the largest contour
        page = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        # Find quadrilateral contour
        corners = None
        for c in page:
            epsilon = 0.02 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            if len(approx) == 4:
                corners = approx
                break
        
        if corners is None:
            raise ValueError("No quadrilateral contour found")

        # Sort and order corners
        corners = np.concatenate(corners).tolist()
        corners = self.order_points(corners)
        (tl, tr, br, bl) = corners

        # Calculate dimensions for perspective transform
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        # Define destination corners
        destination_corners = [
            [0, 0],
            [maxWidth, 0],
            [maxWidth, maxHeight],
            [0, maxHeight]
        ]

        # Apply perspective transform
        homography = cv2.getPerspectiveTransform(np.float32(corners), np.float32(destination_corners))
        final = cv2.warpPerspective(orig_img, np.float32(homography), (maxWidth, maxHeight), flags=cv2.INTER_LINEAR)
        # save results
        return final

    def create_tiles(self, image, overlap=0.1):
        """Divide an image into overlapping tiles and save them for debugging."""
        height, width = image.shape[:2]
        tile_size = max(640, min(height, width) // 2)
        stride = int(tile_size * (1 - overlap))  # Calculate stride based on overlap
        tiles = []
        coordinates = []

        # Generate and save tiles
        tile_idx = 0
        for y in range(0, height, stride):
            for x in range(0, width, stride):
                # Ensure tile doesn't exceed image boundaries
                y_end = min(y + tile_size, height)
                x_end = min(x + tile_size, width)
                if (y_end - y) >= tile_size * 0.5 and (x_end - x) >= tile_size * 0.5:
                    tile = image[y:y_end, x:x_end]
                    # Pad tile to tile_size if smaller (e.g., at edges)
                    if tile.shape[0] < tile_size or tile.shape[1] < tile_size:
                        padded_tile = np.zeros((tile_size, tile_size, 3), dtype=np.uint8)
                        padded_tile[:tile.shape[0], :tile.shape[1]] = tile
                        tile = padded_tile
                    tiles.append(tile)
                    coordinates.append((x, y, x_end - x, y_end - y))  # Store (x, y, w, h)
                    tile_idx += 1
        
        return tiles, coordinates
    
    def merge_detections(self, detections, coordinates, image_shape, iou_threshold=0.3, conf_threshold=0.3):
        """Merge YOLO detections from tiles using NMS."""
        all_boxes = []
        all_scores = []
        all_classes = []

        # Process detections from each tile
        for tile_dets, (x_offset, y_offset, tile_w, tile_h) in zip(detections, coordinates):
            if tile_dets is None:
                continue
            for det in tile_dets.boxes:
                # Extract bounding box, confidence, and class
                x1, y1, x2, y2 = det.xyxy[0].cpu().numpy()
                score = det.conf[0].item()
                cls = int(det.cls[0].cpu().numpy())
                
                # Map coordinates back to original image
                x1 = x1 + x_offset
                y1 = y1 + y_offset
                x2 = x2 + x_offset
                y2 = y2 + y_offset
                
                # Clip to image boundaries
                x1 = max(0, min(x1, image_shape[1]))
                x2 = max(0, min(x2, image_shape[1]))
                y1 = max(0, min(y1, image_shape[0]))
                y2 = max(0, min(y2, image_shape[0]))
                
                if score >= conf_threshold:
                    all_boxes.append([x1, y1, x2, y2])
                    all_scores.append(score)
                    all_classes.append(cls)

        # Apply NMS to merged detections
        if all_boxes and all_scores:
            try:
                boxes = torch.tensor(all_boxes, dtype=torch.float32)
                scores = torch.tensor(all_scores, dtype=torch.float32)  # Ensure scalar values
                classes = torch.tensor(all_classes, dtype=torch.int64)
                indices = torch.ops.torchvision.nms(boxes, scores, iou_threshold)
                return boxes[indices].numpy(), scores[indices].numpy(), classes[indices].numpy()
            except Exception as e:
                print(f"Error during NMS: {e}")
                return np.array([]), np.array([]), np.array([])
        else:
            print("No valid detections to merge")
            return np.array([]), np.array([]), np.array([])

    def detect(self, image, conf_threshold=0.25, overlap=0.3):
        """
        执行目标检测
        Args:
            image: 输入图像（OpenCV格式）
            conf_threshold: 置信度阈值
        Returns:
            detections: 检测结果列表
        """
        # Run FastSAM model
        results = self.segmentation_model(image, device=self.DEVICE, retina_masks=True, imgsz=1024, conf=conf_threshold)

        original_area = image.shape[0] * image.shape[1]  # Original image area
        detections = []

        for result in results:
            if result.masks is not None and len(result.masks) > 0:
                # Iterate through all masks
                for idx, (mask_data, conf) in enumerate(zip(result.masks.data, result.boxes.conf)):
                    # Convert mask to numpy array
                    mask = mask_data.cpu().numpy()  # Shape: (H, W), binary mask

                    # Resize mask to match image dimensions (if necessary)
                    mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

                    # Find the bounding box of the masked area
                    coords = np.where(mask > 0)
                    if coords[0].size > 0:  # Ensure mask is not empty
                        y_min, y_max = coords[0].min(), coords[0].max()
                        x_min, x_max = coords[1].min(), coords[1].max()

                        # Calculate bounding box dimensions
                        box_height = y_max - y_min + 1
                        box_width = x_max - x_min + 1
                        cropped_area = box_height * box_width

                        # Check if cropped area is significantly smaller than original (e.g., < 80% of original area)
                        area_threshold = 0.8
                        if cropped_area < original_area * area_threshold:
                            detections.append({
                                'class': '',
                                'confidence': float(conf.cpu().numpy()),
                                'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
                                'size': {
                                    'width': int(x_max - x_min),
                                    'height': int(y_max - y_min)
                                }
                            })
        return detections

    def visualize(self, image, detections):
        """
        可视化检测结果
        Args:
            image: 输入图像
            detections: 检测结果列表
        Returns:
            annotated_image: 标注后的图像
        """
        annotated_image = image.copy()

        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            label = f"Segment {confidence:.2f}"

            # Draw bounding box (green color in BGR, thickness=2)
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Add confidence score above the bounding box
            cv2.putText(
                annotated_image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,  # Font scale
                (0, 255, 0),  # Green color in BGR
                1,  # Thickness
                cv2.LINE_AA
            )

        return annotated_image

    def process_image(self, image, conf_threshold=0.25):
        """
        处理图像：执行检测并可视化
        Args:
            image: 输入图像（OpenCV格式）
            conf_threshold: 置信度阈值
        Returns:
            detections: 检测结果列表
            annotated_image: 标注后的图像
        """
        image = self.preprocess_image(image)  # Remove background using SAM
        detections = self.detect(image, conf_threshold)
        annotated_image = self.visualize(image, detections)

        return detections, annotated_image
    

if __name__ == "__main__":
    # Example usage
    model_path = "FastSAM-x.pt"
    detector = FastSamDetector(model_path)

    # Load an example image
    image_path = "example_image.jpg"
    image = cv2.imread(image_path)

    # Process the image
    detections, annotated_image = detector.process_image(image)

    # Save or display the annotated image
    cv2.imwrite("annotated_image.jpg", annotated_image)
    
