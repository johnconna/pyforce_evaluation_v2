import os
import shutil
import glob

def get_file_magic(file_path, num_bytes=8):
    """Read first few bytes of file as magic number"""
    try:
        with open(file_path, 'rb') as f:
            return f.read(num_bytes).hex().upper()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def create_directories():
    """Create three classification directories"""
    directories = ['zip_files', 'version_files', 'gzip_files', 'unknown_files']
    for dir_name in directories:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    return directories

def classify_and_rename_files():
    """Classify and rename files based on magic numbers"""
    # Define magic patterns
    magic_patterns = {
        '504B030414000000': 'zip_files',      # ZIP files
        '76657273696F6E20': 'version_files',  # Text files (starting with "version ")
        '1F8B08': 'gzip_files'                # GZIP files
    }
    
    # Create directories
    directories = create_directories()
    
    # Statistics
    stats = {dir_name: 0 for dir_name in directories}
    
    # Get all files
    all_files = glob.glob('*')
    files_to_process = [f for f in all_files if os.path.isfile(f)]
    
    print(f"Found {len(files_to_process)} files to process")
    
    for file_path in files_to_process:
        if file_path in directories:
            continue  # Skip our created directories
            
        magic = get_file_magic(file_path)
        if magic is None:
            continue
            
        # Determine file type and target directory
        target_dir = 'unknown_files'
        new_extension = '.unknown'
        
        # Check magic number matches
        for pattern, dir_name in magic_patterns.items():
            if magic.startswith(pattern):
                target_dir = dir_name
                if dir_name == 'zip_files':
                    new_extension = '.zip'
                elif dir_name == 'gzip_files':
                    new_extension = '.gz'
                elif dir_name == 'version_files':
                    new_extension = '.txt'
                break
        
        # Get filename and extension
        filename, old_extension = os.path.splitext(file_path)
        
        # Generate new filename
        new_filename = f"{filename}{new_extension}"
        target_path = os.path.join(target_dir, new_filename)
        
        # Handle filename conflicts
        counter = 1
        while os.path.exists(target_path):
            new_filename = f"{filename}_{counter}{new_extension}"
            target_path = os.path.join(target_dir, new_filename)
            counter += 1
        
        try:
            # Move and rename file
            shutil.move(file_path, target_path)
            stats[target_dir] += 1
            print(f"Moved: {file_path} -> {target_path}")
            
        except Exception as e:
            print(f"Failed to move file {file_path}: {e}")
    
    # Print statistics
    print("\nClassification completed! Statistics:")
    for dir_name, count in stats.items():
        print(f"{dir_name}: {count} files")

def analyze_file_types():
    """Analyze current file type distribution"""
    file_extensions = {}
    all_files = glob.glob('*')
    files = [f for f in all_files if os.path.isfile(f)]
    
    for file_path in files:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower() if ext else 'no_extension'
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    
    print("Current file type distribution:")
    for ext, count in sorted(file_extensions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ext}: {count} files")

if __name__ == "__main__":
    print("File Magic Number Classification Tool")
    print("=" * 50)
    
    # Analyze current file types first
    analyze_file_types()
    print("\n" + "=" * 50)
    
    # Confirm operation
    response = input("\nStart file classification? (y/N): ")
    if response.lower() in ['y', 'yes']:
        classify_and_rename_files()
    else:
        print("Operation cancelled")
