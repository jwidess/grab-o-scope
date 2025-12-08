import os


class NavigationManager:
    """Manages image navigation and capture directory scanning"""
    
    def __init__(self, capture_directory_func):
        """
        Initialize the navigation manager
        
        Args:
            capture_directory_func: Function that returns the captures directory path
        """
        self.get_capture_directory = capture_directory_func
        self.current_image = None
    
    def get_sorted_captures(self):
        """Get list of image files from captures directory sorted by modification time"""
        capture_dir = self.get_capture_directory()
        
        if not os.path.exists(capture_dir):
            return []
        
        image_files = []
        for filename in os.listdir(capture_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                filepath = os.path.join(capture_dir, filename)
                if os.path.isfile(filepath):
                    image_files.append(filepath)
        
        # Sort by modification time (oldest first)
        image_files.sort(key=lambda x: os.path.getmtime(x))
        return image_files
    
    def get_navigation_state(self, current_image=None):
        """
        Get the current navigation state
        
        Returns:
            dict with keys: prev_enabled, next_enabled, info_text, total_count
        """
        if current_image is not None:
            self.current_image = current_image
        
        sorted_captures = self.get_sorted_captures()
        total_count = len(sorted_captures)
        
        # No captures exist
        if not sorted_captures:
            return {
                'prev_enabled': False,
                'next_enabled': False,
                'info_text': '',
                'total_count': 0
            }
        
        # No image loaded but captures exist
        if not self.current_image or not os.path.exists(self.current_image):
            return {
                'prev_enabled': total_count > 0,
                'next_enabled': total_count > 0,
                'info_text': f"Total images: {total_count} | Use ← → arrow keys to navigate",
                'total_count': total_count
            }
        
        # Current image not in list (deleted/modified)
        if self.current_image not in sorted_captures:
            return {
                'prev_enabled': True,
                'next_enabled': True,
                'info_text': f"Total images: {total_count} | Use ← → arrow keys to navigate",
                'total_count': total_count
            }
        
        # Normal state - image is in the list
        current_index = sorted_captures.index(self.current_image)
        return {
            'prev_enabled': current_index > 0,
            'next_enabled': current_index < total_count - 1,
            'info_text': f"Image {current_index + 1} of {total_count} | Use ← → arrow keys to navigate",
            'total_count': total_count,
            'current_index': current_index
        }
    
    def get_previous_image(self):
        """Get the previous image path"""
        if not self.current_image:
            # Load most recent
            sorted_captures = self.get_sorted_captures()
            return sorted_captures[-1] if sorted_captures else None
        
        sorted_captures = self.get_sorted_captures()
        if not sorted_captures:
            return None
        
        # Handle deleted/modified current image
        if self.current_image not in sorted_captures:
            current_mtime = os.path.getmtime(self.current_image) if os.path.exists(self.current_image) else 0
            prev_image = None
            for img in sorted_captures:
                if os.path.getmtime(img) < current_mtime:
                    prev_image = img
                else:
                    break
            return prev_image
        
        # Normal case
        current_index = sorted_captures.index(self.current_image)
        if current_index > 0:
            return sorted_captures[current_index - 1]
        return None
    
    def get_next_image(self):
        """Get the next image path"""
        if not self.current_image:
            # Load oldest
            sorted_captures = self.get_sorted_captures()
            return sorted_captures[0] if sorted_captures else None
        
        sorted_captures = self.get_sorted_captures()
        if not sorted_captures:
            return None
        
        # Handle deleted/modified current image
        if self.current_image not in sorted_captures:
            current_mtime = os.path.getmtime(self.current_image) if os.path.exists(self.current_image) else float('inf')
            next_image = None
            for img in reversed(sorted_captures):
                if os.path.getmtime(img) > current_mtime:
                    next_image = img
                else:
                    break
            return next_image
        
        # Normal case
        current_index = sorted_captures.index(self.current_image)
        if current_index < len(sorted_captures) - 1:
            return sorted_captures[current_index + 1]
        return None
