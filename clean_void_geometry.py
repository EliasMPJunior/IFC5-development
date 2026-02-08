import json

INPUT_FILE = "examples/Hello Wall/hello-wall-with-hole.ifcx"
OUTPUT_FILE = "examples/Hello Wall/hello-wall-final.ifcx"

VOID_ID = "8fada721-cff8-590b-8d0b-9300b5fe8e18"

def clean_void_mesh():
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
        return

    found = False
    for item in data['data']:
        if item.get('path') == VOID_ID:
            if 'attributes' in item and 'usd::usdgeom::mesh' in item['attributes']:
                print(f"Removendo malha do objeto Void: {VOID_ID}")
                del item['attributes']['usd::usdgeom::mesh']
                found = True
            break
            
    if not found:
        print("Void não encontrado ou já sem malha.")
        # Pode ser que esteja dividido em múltiplos blocos, vamos varrer tudo
        count = 0
        for item in data['data']:
             if item.get('path') == VOID_ID:
                if 'attributes' in item and 'usd::usdgeom::mesh' in item['attributes']:
                    del item['attributes']['usd::usdgeom::mesh']
                    count += 1
        if count > 0:
            print(f"Removida malha de {count} ocorrência(s) do Void.")
        else:
            print("Nenhuma malha encontrada para remover.")

    # Salvar
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Arquivo limpo salvo em: {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_void_mesh()
