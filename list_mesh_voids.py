import json
from collections import defaultdict

INPUT_FILE = "examples/Hello Wall/hello-wall-elias.ifcx"

def analyze_mesh_voids():
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
        return

    # 1. Encontrar a Parede e sua geometria
    wall_id = None
    # Procurar objeto com class IfcWall
    for item in data['data']:
        if 'attributes' in item and 'bsi::ifc::class' in item['attributes']:
            if item['attributes']['bsi::ifc::class']['code'] == 'IfcWall':
                wall_id = item['path']
                break
    
    if not wall_id:
        print("Parede não encontrada.")
        return

    # Encontrar o Body da parede
    body_id = None
    wall_obj = next((i for i in data['data'] if i.get('path') == wall_id), None)
    if wall_obj and 'children' in wall_obj:
        body_id = wall_obj['children'].get('Body')

    if not body_id:
        print("Geometria (Body) da parede não encontrada.")
        return

    # Encontrar a malha do Body
    body_obj = next((i for i in data['data'] if i.get('path') == body_id), None)
    points = []
    if body_obj and 'attributes' in body_obj:
        mesh = body_obj['attributes'].get('usd::usdgeom::mesh')
        if mesh:
            points = mesh.get('points', [])

    if not points:
        print("Nenhum ponto encontrado na malha.")
        return

    print(f"Analisando {len(points)} vértices da parede...")

    # 2. Filtrar pontos internos (que formam os buracos)
    # Assumindo parede alinhada aos eixos (como visto anteriormente)
    xs = [p[0] for p in points]
    zs = [p[2] for p in points]
    
    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)
    
    # Tolerância para float
    tol = 0.01
    
    internal_points = []
    for p in points:
        x, y, z = p
        # Ponto é interno se não estiver nas bordas externas do bounding box da parede
        is_on_edge = (
            abs(x - min_x) < tol or abs(x - max_x) < tol or
            abs(z - min_z) < tol or abs(z - max_z) < tol
        )
        
        if not is_on_edge:
            internal_points.append(p)

    if not internal_points:
        print("Nenhum buraco detectado na malha (sem vértices internos).")
        return

    # 3. Agrupar pontos por proximidade em X para identificar janelas distintas
    # Ordenar por X
    internal_points.sort(key=lambda p: p[0])
    
    clusters = []
    current_cluster = [internal_points[0]]
    
    for i in range(1, len(internal_points)):
        p = internal_points[i]
        prev = current_cluster[-1]
        
        # Se a distância X for grande (> 50cm), é outro buraco
        if abs(p[0] - prev[0]) > 0.5:
            clusters.append(current_cluster)
            current_cluster = []
        
        current_cluster.append(p)
    
    if current_cluster:
        clusters.append(current_cluster)

    # 4. Analisar cada cluster
    print(f"\n{'Void ID':<10} | {'X Start':<8} | {'X End':<8} | {'Y (Base)':<8} | {'Width':<8} | {'Height':<8}")
    print("-" * 75)
    
    for i, cluster in enumerate(clusters):
        c_xs = [p[0] for p in cluster]
        c_zs = [p[2] for p in cluster]
        
        x_start = min(c_xs)
        x_end = max(c_xs)
        z_base = min(c_zs)
        z_top = max(c_zs)
        
        width = x_end - x_start
        height = z_top - z_base
        
        print(f"{i+1:<10} | {x_start:<8.2f} | {x_end:<8.2f} | {z_base:<8.2f} | {width:<8.2f} | {height:<8.2f}")

if __name__ == "__main__":
    analyze_mesh_voids()
