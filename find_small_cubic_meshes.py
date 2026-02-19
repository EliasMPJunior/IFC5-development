import json
import os
import glob
import math

def calculate_bbox(points):
    if not points:
        return None
    
    # Points can be a flat list [x1, y1, z1, x2, y2, z2...] or list of lists [[x1,y1,z1], ...]
    # Based on previous file reads, it seems to be a list of lists or flattened. 
    # Let's handle flattened for now as seen in render.ts (flat())
    
    xs = []
    ys = []
    zs = []
    
    # If it's a list of lists
    if len(points) > 0 and isinstance(points[0], list):
        for p in points:
            if len(p) >= 3:
                xs.append(p[0])
                ys.append(p[1])
                zs.append(p[2])
    else:
        # Flattened
        for i in range(0, len(points), 3):
            if i+2 < len(points):
                xs.append(points[i])
                ys.append(points[i+1])
                zs.append(points[i+2])
                
    if not xs:
        return None
        
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    
    return {
        'dx': max_x - min_x,
        'dy': max_y - min_y,
        'dz': max_z - min_z,
        'dims': (max_x - min_x, max_y - min_y, max_z - min_z)
    }

def search_files(root_dir):
    print(f"Searching in {root_dir}...")
    
    matches = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.ifcx'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'data' not in data:
                    continue
                    
                # Index objects to resolve potential inheritance/references if needed, 
                # but for now let's just scan for mesh points directly in attributes
                
                for item in data['data']:
                    if 'attributes' in item:
                        attrs = item['attributes']
                        path = item.get('path', 'unknown')
                        
                        points = None
                        if 'usd::usdgeom::mesh::points' in attrs:
                            points = attrs['usd::usdgeom::mesh::points']
                        elif 'usd::usdgeom::mesh' in attrs and isinstance(attrs['usd::usdgeom::mesh'], dict):
                            mesh_data = attrs['usd::usdgeom::mesh']
                            if 'points' in mesh_data:
                                points = mesh_data['points']
                        
                        if points:
                            bbox = calculate_bbox(points)
                            if bbox:
                                dx, dy, dz = bbox['dims']
                                
                                # Store all results for sorting later
                                volume = dx * dy * dz
                                matches.append({
                                    'file': file,
                                    'path': path,
                                    'dims': (dx, dy, dz),
                                    'volume': volume,
                                    'full_path': file_path
                                })
                                    
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Sort by volume (smallest first, but ignore zero volume)
    matches = [m for m in matches if m['volume'] > 0]
    
    # Filter for "cubic-like" candidates around 5cm
    candidates = []
    for m in matches:
        dx, dy, dz = m['dims']
        dims = [dx, dy, dz]
        max_d = max(dims)
        min_d = min(dims)
        
        # Check size: roughly 2cm to 10cm
        if 0.02 <= max_d <= 0.10 and 0.02 <= min_d:
             # Check aspect ratio: roughly cubic (longest side not more than 2.5x shortest)
             if max_d / min_d <= 2.5:
                 candidates.append(m)
    
    candidates.sort(key=lambda x: x['volume'])
    
    return candidates

if __name__ == "__main__":
    results = search_files("/Users/eliasmpjunior/buildingsmart/IFC5-development/examples")
    
    print(f"\nFound {len(results)} cubic candidates (~5cm):\n")
    for r in results:
        dx, dy, dz = r['dims']
        print(f"File: {r['file']}")
        print(f"  Object: {r['path']}")
        print(f"  Dims: {dx:.6f} x {dy:.6f} x {dz:.6f}")
        print(f"  Volume: {r['volume']:.6f}")
        print("-" * 40)
