import json
import uuid
import copy
import os

INPUT_FILE = "examples/Hello Wall/hello-wall-elias.ifcx"
OUTPUT_FILE = "examples/Hello Wall/hello-wall-parallel.ifcx"

def get_new_uuid():
    return str(uuid.uuid4())

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    # Encontrar a parede original
    wall_id = "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b"
    original_wall = None
    for item in data['data']:
        if item.get('path') == wall_id:
            original_wall = item
            break
    
    if not original_wall:
        print("Parede original não encontrada!")
        return

    print(f"Parede original encontrada: {wall_id}")

    items_to_add = []

    # 1. Clonar a Parede
    new_wall_id = get_new_uuid()
    new_wall = copy.deepcopy(original_wall)
    new_wall['path'] = new_wall_id
    
    # Adicionar transformação na parede nova (deslocamento 3m em Y)
    # Matriz 4x4 identidade com translação em Y = 3.0
    # A ordem no JSON parece ser linha por linha
    transform = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 3, 0, 1] 
    ]
    
    if 'attributes' not in new_wall:
        new_wall['attributes'] = {}
    
    # Se já tiver xformop, teríamos que compor, mas a original não tem.
    new_wall['attributes']['usd::xformop'] = {
        'transform': transform
    }
    
    # Atualizar nome interno
    if 'customdata' in new_wall['attributes']:
         val = new_wall['attributes']['customdata'].get('originalStepInstance', '')
         if 'Wall' in val:
             new_wall['attributes']['customdata']['originalStepInstance'] = val.replace("'Wall'", "'Wall_Parallel'")
         else:
             # Fallback se não achar a string exata
             new_wall['attributes']['customdata']['originalStepInstance'] = f"#{str(uuid.uuid4().int)[:5]}=IfcWall('{get_new_uuid()[:22]}',$,'Wall_Parallel',$,$,$,$,$,$)"

    items_to_add.append(new_wall)
    print(f"Nova parede criada: {new_wall_id}")

    # 2. Processar filhos da parede (Body, Axis, Windows, etc.)
    if 'children' in new_wall:
        new_children = {}
        for key, child_id in new_wall['children'].items():
            # Encontrar o objeto filho original
            child_obj = None
            for item in data['data']:
                if item.get('path') == child_id:
                    child_obj = item
                    break
            
            if child_obj:
                # Clonar filho
                new_child_id = get_new_uuid()
                new_child = copy.deepcopy(child_obj)
                new_child['path'] = new_child_id
                
                # Se for janela ou porta, atualizar ID interno para evitar conflito
                if 'Window' in key or 'Door' in key:
                     if 'attributes' in new_child and 'customdata' in new_child['attributes']:
                        orig_inst = new_child['attributes']['customdata'].get('originalStepInstance', '')
                        new_step_id = "#" + str(uuid.uuid4().int)[:5] 
                        if '=' in orig_inst:
                            parts = orig_inst.split('=', 1)
                            new_child['attributes']['customdata']['originalStepInstance'] = f"{new_step_id}={parts[1]}"
                
                # Importante: Se o filho tiver geometria (Body), a geometria também é um objeto?
                # No JSON atual:
                # "Body": "GUID"
                # E existe um objeto com "path": "GUID" que define a geometria.
                # Então ao clonar "child_obj", estamos clonando a definição da geometria se child_obj FOR a geometria.
                # MAS:
                # Wall -> children -> Body (ID1)
                # Objeto ID1 (Body) -> attributes -> usd::usdgeom::mesh -> ...
                # Sim, o objeto ID1 contém a malha. Então clonando ele, clonamos a malha.
                # E ao dar novo ID, desacoplamos da original.
                
                items_to_add.append(new_child)
                new_children[key] = new_child_id
            else:
                print(f"Aviso: Definição de filho {key} ({child_id}) não encontrada.")
                new_children[key] = child_id 
        
        new_wall['children'] = new_children

    # 3. Adicionar novos itens ao data
    data['data'].extend(items_to_add)

    # 4. Adicionar a nova parede ao Storey
    storey_id = "44af358b-3160-4063-8a89-a868335ff3b5"
    storey_found = False
    for item in data['data']:
        if item.get('path') == storey_id:
            if 'children' in item:
                item['children']['Wall_Parallel'] = new_wall_id
                storey_found = True
            break
    
    if not storey_found:
        print("Aviso: Storey não encontrado ou sem children. Tentando My_Space...")
        # Fallback para My_Space se necessário
        space_id = "e3035b71-bd9f-4cdc-86fd-b56e2f4605b6"
        for item in data['data']:
            if item.get('path') == space_id:
                if 'children' in item:
                    item['children']['Wall_Parallel'] = new_wall_id
                    print("Adicionado ao My_Space.")
                break

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Sucesso! Arquivo gerado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
