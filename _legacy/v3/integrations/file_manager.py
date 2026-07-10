"""
File Management System - Create, Read, Edit, Delete files
With safety checks and validation
"""
import os
from pathlib import Path
from typing import Optional, List, Dict
import json
import config

class FileManager:
    """Manages file operations with safety checks"""
    
    def __init__(self):
        self.allowed_extensions = [
            '.txt', '.md', '.json', '.yaml', '.yml', '.csv',
            '.py', '.js', '.html', '.css', '.xml', '.log',
            '.cfg', '.conf', '.ini', '.env'
        ]
        self.forbidden_dirs = [
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin'
        ]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def is_safe_path(self, filepath: str) -> bool:
        """Check if path is safe to operate on"""
        try:
            path = Path(filepath).resolve()
            
            # Check forbidden directories
            for forbidden in self.forbidden_dirs:
                if str(path).startswith(forbidden):
                    return False
            
            # Check if in system directories
            if 'system32' in str(path).lower():
                return False
            
            return True
            
        except Exception:
            return False
    
    def is_allowed_extension(self, filepath: str) -> bool:
        """Check if file extension is allowed"""
        ext = Path(filepath).suffix.lower()
        return ext in self.allowed_extensions or ext == ''
    
    def create_file(self, filepath: str, content: str = "", overwrite: bool = False) -> Dict:
        """
        Create a new file
        
        Args:
            filepath: Path to file
            content: Initial content
            overwrite: Allow overwriting existing file
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Validate path
            if not self.is_safe_path(filepath):
                return {
                    'success': False,
                    'error': 'Path not allowed for safety reasons',
                    'filepath': filepath
                }
            
            path = Path(filepath)
            
            # Check extension
            if not self.is_allowed_extension(filepath):
                return {
                    'success': False,
                    'error': f'File extension not allowed. Allowed: {", ".join(self.allowed_extensions)}',
                    'filepath': filepath
                }
            
            # Check if exists
            if path.exists() and not overwrite:
                return {
                    'success': False,
                    'error': 'File already exists. Use overwrite=True to replace',
                    'filepath': filepath
                }
            
            # Create directory if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            path.write_text(content, encoding='utf-8')
            
            return {
                'success': True,
                'message': f'File created: {filepath}',
                'filepath': str(path.absolute()),
                'size': len(content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create file: {str(e)}',
                'filepath': filepath
            }
    
    def read_file(self, filepath: str, max_lines: Optional[int] = None) -> Dict:
        """
        Read a file
        
        Args:
            filepath: Path to file
            max_lines: Maximum lines to read (None for all)
            
        Returns:
            Result dictionary with content
        """
        try:
            # Validate path
            if not self.is_safe_path(filepath):
                return {
                    'success': False,
                    'error': 'Path not allowed for safety reasons'
                }
            
            path = Path(filepath)
            
            if not path.exists():
                return {
                    'success': False,
                    'error': 'File does not exist'
                }
            
            # Check size
            if path.stat().st_size > self.max_file_size:
                return {
                    'success': False,
                    'error': f'File too large (max {self.max_file_size / 1024 / 1024}MB)'
                }
            
            # Read content
            content = path.read_text(encoding='utf-8')
            
            # Limit lines if requested
            if max_lines:
                lines = content.split('\n')
                if len(lines) > max_lines:
                    content = '\n'.join(lines[:max_lines])
                    content += f"\n... ({len(lines) - max_lines} more lines)"
            
            return {
                'success': True,
                'content': content,
                'filepath': str(path.absolute()),
                'size': path.stat().st_size,
                'lines': len(content.split('\n'))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to read file: {str(e)}'
            }
    
    def edit_file(self, filepath: str, old_text: str, new_text: str) -> Dict:
        """
        Edit file by replacing text
        
        Args:
            filepath: Path to file
            old_text: Text to find
            new_text: Text to replace with
            
        Returns:
            Result dictionary
        """
        try:
            # Read file first
            read_result = self.read_file(filepath)
            if not read_result['success']:
                return read_result
            
            content = read_result['content']
            
            # Check if old_text exists
            if old_text not in content:
                return {
                    'success': False,
                    'error': 'Text to replace not found in file'
                }
            
            # Replace
            new_content = content.replace(old_text, new_text)
            
            # Write back
            path = Path(filepath)
            path.write_text(new_content, encoding='utf-8')
            
            return {
                'success': True,
                'message': f'File edited: {filepath}',
                'replacements': content.count(old_text),
                'filepath': str(path.absolute())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to edit file: {str(e)}'
            }
    
    def append_to_file(self, filepath: str, content: str) -> Dict:
        """
        Append content to file
        
        Args:
            filepath: Path to file
            content: Content to append
            
        Returns:
            Result dictionary
        """
        try:
            if not self.is_safe_path(filepath):
                return {
                    'success': False,
                    'error': 'Path not allowed for safety reasons'
                }
            
            path = Path(filepath)
            
            # Create if doesn't exist
            if not path.exists():
                return self.create_file(filepath, content)
            
            # Append
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'Content appended to {filepath}',
                'filepath': str(path.absolute())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to append to file: {str(e)}'
            }
    
    def delete_file(self, filepath: str, confirm: bool = False) -> Dict:
        """
        Delete a file
        
        Args:
            filepath: Path to file
            confirm: Must be True to actually delete
            
        Returns:
            Result dictionary
        """
        if not confirm:
            return {
                'success': False,
                'error': 'Delete requires confirmation (confirm=True)'
            }
        
        try:
            if not self.is_safe_path(filepath):
                return {
                    'success': False,
                    'error': 'Path not allowed for safety reasons'
                }
            
            path = Path(filepath)
            
            if not path.exists():
                return {
                    'success': False,
                    'error': 'File does not exist'
                }
            
            # Delete
            path.unlink()
            
            return {
                'success': True,
                'message': f'File deleted: {filepath}',
                'filepath': str(path.absolute())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delete file: {str(e)}'
            }
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict:
        """
        List files in directory
        
        Args:
            directory: Directory to list
            pattern: File pattern (e.g., "*.txt")
            
        Returns:
            Result dictionary with file list
        """
        try:
            if not self.is_safe_path(directory):
                return {
                    'success': False,
                    'error': 'Path not allowed for safety reasons'
                }
            
            path = Path(directory)
            
            if not path.exists() or not path.is_dir():
                return {
                    'success': False,
                    'error': 'Directory does not exist'
                }
            
            # List files
            files = []
            for item in path.glob(pattern):
                files.append({
                    'name': item.name,
                    'path': str(item.absolute()),
                    'size': item.stat().st_size if item.is_file() else 0,
                    'type': 'file' if item.is_file() else 'directory'
                })
            
            return {
                'success': True,
                'directory': str(path.absolute()),
                'files': files,
                'count': len(files)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list files: {str(e)}'
            }
    
    def get_file_info(self, filepath: str) -> Dict:
        """Get detailed file information"""
        try:
            if not self.is_safe_path(filepath):
                return {
                    'success': False,
                    'error': 'Path not allowed for safety reasons'
                }
            
            path = Path(filepath)
            
            if not path.exists():
                return {
                    'success': False,
                    'error': 'File does not exist'
                }
            
            stat = path.stat()
            
            return {
                'success': True,
                'name': path.name,
                'path': str(path.absolute()),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'extension': path.suffix,
                'is_file': path.is_file(),
                'is_directory': path.is_dir()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get file info: {str(e)}'
            }
