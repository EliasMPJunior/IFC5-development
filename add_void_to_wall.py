import json
import uuid

INPUT_FILE = "examples/Hello Wall/hello-wall-elias.ifcx"
OUTPUT_FILE = "examples/Hello Wall/hello-wall-with-hole.ifcx"

# Wall Dimensions
WALL_LENGTH = 10.0
WALL_HEIGHT = 3.0
WALL_THICKNESS = 0.1 # Y direction

# Holes Definitions (x_start, x_end, z_bottom, z_top)
# We use the analyzed coordinates
HOLES = [
    {"x1": 1.7676749, "x2": 2.667675, "z1": 1.0, "z2": 2.2}, # Window 1
    {"x1": 4.9466066, "x2": 5.8466067, "z1": 1.0, "z2": 2.2}, # Window 2
    {"x1": 8.0,       "x2": 8.9,       "z1": 1.0, "z2": 2.2}  # Window 3 (New)
]

def generate_wall_mesh():
    points = []
    indices = []
    
    # Helper to add a quad (4 points) and return indices
    # p1, p2, p3, p4 in CCW order
    def add_quad(p1, p2, p3, p4):
        start_idx = len(points)
        points.append(p1)
        points.append(p2)
        points.append(p3)
        points.append(p4)
        # Face indices: 4 points
        indices.extend([start_idx, start_idx+1, start_idx+2, start_idx, start_idx+2, start_idx+3]) # Triangulated for safety

    # Helper to add a quad using existing point indices (not used here for simplicity, we duplicate vertices for flat shading look/simple logic)
    
    # We define the wall as a series of rectangular blocks for Front and Back faces
    # Segments in X:
    # 1. 0 -> h1_x1
    # 2. h1_x1 -> h1_x2 (Hole 1)
    # 3. h1_x2 -> h2_x1
    # 4. h2_x1 -> h2_x2 (Hole 2)
    # 5. h2_x2 -> h3_x1
    # 6. h3_x1 -> h3_x2 (Hole 3)
    # 7. h3_x2 -> 10
    
    x_cuts = [0.0]
    for h in HOLES:
        x_cuts.append(h["x1"])
        x_cuts.append(h["x2"])
    x_cuts.append(WALL_LENGTH)
    
    # Iterate through segments
    for i in range(len(x_cuts) - 1):
        x_start = x_cuts[i]
        x_end = x_cuts[i+1]
        
        # Check if this segment is a hole
        current_hole = None
        for h in HOLES:
            # Approx check float equality
            if abs(h["x1"] - x_start) < 0.01 and abs(h["x2"] - x_end) < 0.01:
                current_hole = h
                break
        
        if current_hole:
            # It's a hole column: Draw Top Lintel and Bottom Sill
            # Bottom Sill: Z=0 to z1
            # Front Face
            add_quad(
                [x_start, 0, 0], [x_end, 0, 0], 
                [x_end, 0, current_hole["z1"]], [x_start, 0, current_hole["z1"]]
            )
            # Back Face (Order reversed for normal)
            add_quad(
                [x_start, WALL_THICKNESS, current_hole["z1"]], [x_end, WALL_THICKNESS, current_hole["z1"]],
                [x_end, WALL_THICKNESS, 0], [x_start, WALL_THICKNESS, 0]
            )
            
            # Top Lintel: Z=z2 to HEIGHT
            # Front Face
            add_quad(
                [x_start, 0, current_hole["z2"]], [x_end, 0, current_hole["z2"]],
                [x_end, 0, WALL_HEIGHT], [x_start, 0, WALL_HEIGHT]
            )
            # Back Face
            add_quad(
                [x_start, WALL_THICKNESS, WALL_HEIGHT], [x_end, WALL_THICKNESS, WALL_HEIGHT],
                [x_end, WALL_THICKNESS, current_hole["z2"]], [x_start, WALL_THICKNESS, current_hole["z2"]]
            )
            
            # INNER FACES OF THE HOLE
            # Bottom of Hole (Top of Sill)
            add_quad(
                [x_start, 0, current_hole["z1"]], [x_end, 0, current_hole["z1"]],
                [x_end, WALL_THICKNESS, current_hole["z1"]], [x_start, WALL_THICKNESS, current_hole["z1"]]
            )
            # Top of Hole (Bottom of Lintel)
            add_quad(
                [x_start, WALL_THICKNESS, current_hole["z2"]], [x_end, WALL_THICKNESS, current_hole["z2"]],
                [x_end, 0, current_hole["z2"]], [x_start, 0, current_hole["z2"]]
            )
            # Left Side of Hole
            add_quad(
                [x_start, WALL_THICKNESS, current_hole["z1"]], [x_start, WALL_THICKNESS, current_hole["z2"]],
                [x_start, 0, current_hole["z2"]], [x_start, 0, current_hole["z1"]]
            )
            # Right Side of Hole
            add_quad(
                [x_end, 0, current_hole["z1"]], [x_end, 0, current_hole["z2"]],
                [x_end, WALL_THICKNESS, current_hole["z2"]], [x_end, WALL_THICKNESS, current_hole["z1"]]
            )

        else:
            # It's a solid column: Draw full height
            # Front Face
            add_quad(
                [x_start, 0, 0], [x_end, 0, 0],
                [x_end, 0, WALL_HEIGHT], [x_start, 0, WALL_HEIGHT]
            )
            # Back Face
            add_quad(
                [x_start, WALL_THICKNESS, WALL_HEIGHT], [x_end, WALL_THICKNESS, WALL_HEIGHT],
                [x_end, WALL_THICKNESS, 0], [x_start, WALL_THICKNESS, 0]
            )

    # OUTER BOUNDARY FACES
    # Bottom Face (Z=0)
    add_quad(
        [0, WALL_THICKNESS, 0], [WALL_LENGTH, WALL_THICKNESS, 0],
        [WALL_LENGTH, 0, 0], [0, 0, 0]
    )
    # Top Face (Z=HEIGHT)
    add_quad(
        [0, 0, WALL_HEIGHT], [WALL_LENGTH, 0, WALL_HEIGHT],
        [WALL_LENGTH, WALL_THICKNESS, WALL_HEIGHT], [0, WALL_THICKNESS, WALL_HEIGHT]
    )
    # Left Face (X=0)
    add_quad(
        [0, WALL_THICKNESS, 0], [0, WALL_THICKNESS, WALL_HEIGHT],
        [0, 0, WALL_HEIGHT], [0, 0, 0]
    )
    # Right Face (X=LENGTH)
    add_quad(
        [WALL_LENGTH, 0, 0], [WALL_LENGTH, 0, WALL_HEIGHT],
        [WALL_LENGTH, WALL_THICKNESS, WALL_HEIGHT], [WALL_LENGTH, WALL_THICKNESS, 0]
    )

    return points, indices

def main():
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
        return

    # 1. Generate new mesh data
    new_points, new_indices = generate_wall_mesh()
    print(f"Generated mesh with {len(new_points)} vertices and {len(new_indices)} indices.")

    # 2. Find the Wall Body object to update
    wall_id = "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b"
    body_id = None
    
    # Find wall to get body ID
    for item in data['data']:
        if item.get('path') == wall_id:
            if 'children' in item:
                body_id = item['children'].get('Body')
            break
            
    if not body_id:
        print("Could not find Wall Body ID.")
        return
        
    print(f"Updating Wall Body ID: {body_id}")
    
    # 3. Update the Body object
    updated = False
    for item in data['data']:
        if item.get('path') == body_id:
            if 'attributes' in item and 'usd::usdgeom::mesh' in item['attributes']:
                item['attributes']['usd::usdgeom::mesh']['points'] = new_points
                item['attributes']['usd::usdgeom::mesh']['faceVertexIndices'] = new_indices
                updated = True
                print("Mesh data updated successfully.")
            break
            
    if not updated:
        print("Could not find or update the Mesh attribute in the Body object.")
        return

    # 4. Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
