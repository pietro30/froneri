import time
from opcua import Client, ua
import pyodbc
import traceback

# Default parameters
DEFAULT_PARAMS = {
    "server": "192.168.0.183",
    "database": "RecipeDB",
    "username": "PC_SERVER_MIX1",
    "password": "PASSWORD01",
    "ip": "192.168.0.4",
}

# Initialize the variables with default values
server = DEFAULT_PARAMS["server"]
database = DEFAULT_PARAMS["database"]
username = DEFAULT_PARAMS["username"]
password = DEFAULT_PARAMS["password"]
ip = DEFAULT_PARAMS["ip"]

def log_error(message):
    with open("get_rcpready_log.txt", "a") as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {message}\n")

# Attempt to read the init file and extract the values
try:
    with open('init.txt', 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            if key == 'server':
                server = value.strip()
            elif key == 'database':
                database = value.strip()
            elif key == 'username':
                username = value.strip()
            elif key == 'password':
                password = value.strip()
            elif key == 'ip':
                ip = value.strip()
except FileNotFoundError:
    print("The 'init.txt' file was not found. Using default parameters.")
    message = traceback.print_exc()
    log_error(message)

# Database connection details
db_connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

#readyA = '"ns=3;s="REPORT"."Report_A_Ready"'
readyB = 'ns=3;s="REPORT"."Report_B_Ready"'
readyC = 'ns=3;s="REPORT"."Report_C_Ready"'
readyD = 'ns=3;s="REPORT"."Report_D_Ready"'

batchB = 'ns=3;s="REPORT"."Ricetta_B"."StampID"'
batchC = 'ns=3;s="REPORT"."Ricetta_C"."StampID"'
batchD = 'ns=3;s="REPORT"."Ricetta_D"."StampID"'

def print_variables_status(variables_dict):
    print("Current Variables Status:")
    for key, value in variables_dict.items():
        print(f"{key}: {value}")

def read_active_ingredients(client, recipe_letter):
    base_path = f'ns=3;s="REPORT"."Ricetta_{recipe_letter}"'
    active_ingredients_data = {}    
    
    # Define the ranges for different ingredient types
    ingredient_types = {
        "Polveri": range(1, 11),
        "Liquidi1": range(1, 6),
        "Liquidi2": range(1, 2),
        "AromiAPV": range(1, 11),
        "Semilavorati": range(1, 11),
        "Latte": [""],  # No range needed for single items
        "Acqua": [""],
        "Zucchero": [""]
    }

    # Iterate over the ingredient types and their ranges
    for ingredient_type, counts in ingredient_types.items():
        for count in counts:
            if ingredient_type in ["Latte", "Acqua", "Zucchero"]:  # Single items
                suffix = ""
            else:  # Ranged items
                suffix = f"[{count}]"
            
            # Construct the tag paths
            attivo_tag = f'{base_path}."{ingredient_type}"{suffix}."Attivo"'
            nome_prodotto_tag = f'{base_path}."{ingredient_type}"{suffix}."NomeProdotto"'
            q_effettiva_tag = f'{base_path}."{ingredient_type}"{suffix}."qEffettiva"'

            # Read the "Attivo" state
            attivo_value = client.get_node(attivo_tag).get_value()
            
            # If the ingredient is active, read the other tags
            if attivo_value:
                nome_prodotto_value = client.get_node(nome_prodotto_tag).get_value()
                q_effettiva_value = client.get_node(q_effettiva_tag).get_value()
                
                # Store the data in a dictionary
                active_ingredients_data[f"{ingredient_type}{suffix}"] = {
                    "NomeProdotto": nome_prodotto_value,
                    "qEffettiva": q_effettiva_value
                }

    return active_ingredients_data

def d_active_ingredients(client):
    tag_group = "D"
    nrwor = 'ns=3;s="REPORT"."Ricetta_D"."WorkOrder"'
    nrcpn = 'ns=3;s="REPORT"."Ricetta_D"."Codice"'
    nrcpd = 'ns=3;s="REPORT"."Ricetta_D"."Descrizione"'
    nqtyr = 'ns=3;s="REPORT"."Ricetta_D"."qTotaleMiscela"'
    nqh2o = 'ns=3;s="REPORT"."Ricetta_D"."Val_Eff_H2O"'
    nqglu = 'ns=3;s="REPORT"."Ricetta_D"."Val_Eff_Glu"'
    nqzuc = 'ns=3;s="REPORT"."Ricetta_D"."Val_Eff_Zu"'
    nqpur = 'ns=3;s="REPORT"."Ricetta_D"."Val_Eff_Purea"'
    nqmix = 'ns=3;s="REPORT"."Ricetta_D"."Val_Eff_Misc_Mix"'

    work_order = client.get_node(nrwor).get_value()
    codice = client.get_node(nrcpn).get_value()
    nome_prodotto = client.get_node(nrcpd).get_value()
    q_effettiva = client.get_node(nqtyr).get_value()
    acqua = client.get_node(nqh2o).get_value()
    gluc = client.get_node(nqglu).get_value()
    zucchero = client.get_node(nqzuc).get_value()
    purea = client.get_node(nqpur).get_value()
    mix = client.get_node(nqmix).get_value()

    conn = pyodbc.connect(db_connection_string)
    cursor = conn.cursor()
    
    # Select the TotalQty from the database
    cursor.execute("""
        SELECT TotalQty FROM RecipeDB.dbo.Reports
        WHERE RecipeID = ? AND BatchNumber = ? AND IngrDesc = ? AND PasteurizerID = ?
    """, (codice, work_order, nome_prodotto, tag_group))
    row = cursor.fetchone()
    
    # Check if we got a result
    if row:
        total_qty = row.TotalQty
        variance = ((q_effettiva - total_qty) / total_qty) * 100 if total_qty else 0
        
        try:
            # Update the EffectiveQty and Variance
            cursor.execute("""
                UPDATE RecipeDB.dbo.Reports
                SET EffectiveQty = ?, Variance = ?
                WHERE RecipeID = ? AND BatchNumber = ? AND IngrDesc = ? AND PasteurizerID = ? AND IngrTypeDesc = 'Acqua'
            """, (acqua, variance, codice, work_order, nome_prodotto, tag_group))
            conn.commit()
            cursor.execute("""
                UPDATE RecipeDB.dbo.Reports
                SET EffectiveQty = ?, Variance = ?
                WHERE RecipeID = ? AND BatchNumber = ? AND IngrDesc = ? AND PasteurizerID = ? AND IngrTypeDesc = 'Glucosio'
            """, (gluc, variance, codice, work_order, nome_prodotto, tag_group))
            conn.commit()
            cursor.execute("""
                UPDATE RecipeDB.dbo.Reports
                SET EffectiveQty = ?, Variance = ?
                WHERE RecipeID = ? AND BatchNumber = ? AND IngrDesc = ? AND PasteurizerID = ? AND IngrTypeDesc = 'Zucchero'
            """, (zucchero, variance, codice, work_order, nome_prodotto, tag_group))
            conn.commit()
            cursor.execute("""
                UPDATE RecipeDB.dbo.Reports
                SET EffectiveQty = ?, Variance = ?
                WHERE RecipeID = ? AND BatchNumber = ? AND IngrDesc = ? AND PasteurizerID = ? AND IngrTypeDesc = 'Purea'
            """, (purea, variance, codice, work_order, nome_prodotto, tag_group))
            conn.commit()
         
        except Exception as e:  
            message = traceback.print_exc()
            log_error(message)
        
        finally:
            cursor.close()
            conn.close() 

    return

def update_database(ingredient_data, batchopc, recipe_letter, client):
    base_path = f'ns=3;s="REPORT"."Ricetta_{recipe_letter}"'
    codice = client.get_node(f'{base_path}."Codice"').get_value()
    workorder = client.get_node(f'{base_path}."WorkOrder"').get_value()
    ricetta = client.get_node(f'{base_path}."Descrizione"').get_value()
    ingrediente = ingredient_data.get('NomeProdotto')
    q_effettiva = ingredient_data.get('qEffettiva')
    ingrcode = ingrediente.split('-')[0].strip()
    
    try:
        conn = pyodbc.connect(db_connection_string)
        cursor = conn.cursor()
        
        # Select the TotalQty from the database
        cursor.execute("""
            SELECT TotalQty FROM [RecipeDB].[dbo].[Reports]
            WHERE WorkOrderID = ? AND IngrDesc = ? AND RecipeID = ?
        """, (batchopc, ingrediente, codice))
        row = cursor.fetchone()
        
        # Check if we got a result
        if row:
            total_qty = row.TotalQty
            variance = ((q_effettiva - total_qty) / total_qty) * 100 if total_qty else 0
            
            # Update the EffectiveQty and Variance
            cursor.execute("""
                UPDATE [RecipeDB].[dbo].[Reports]
                SET EffectiveQty = ?, Variance = ?, TimeCompleted = GETDATE()
                WHERE WorkOrderID = ? AND IngrDesc = ? AND RecipeID = ?
            """, (q_effettiva, variance, batchopc, ingrediente, codice))
            conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        message = f"Error saving data to database: {e}, {traceback.print_exc()}"
        log_error(message)

def main():
    client = Client(f"opc.tcp://{ip}:4840")
    client.session_timeout = 30000
    connected = False

    while True:
        if not connected:
            try:
                client.connect()
                print("Connected to OPC UA Server. Service rcpmonitor running...")
                connected = True
            except Exception as e:
                print(f"Failed to connect to OPC UA Server: {e}")
                log_error(traceback.print_exc())
                time.sleep(5)
                continue

        try:
            nodeB = client.get_node(readyB)
            nodeC = client.get_node(readyC)
            nodeD = client.get_node(readyD)
            dataB = nodeB.get_value()
            dataC = nodeC.get_value()
            dataD = nodeD.get_value()
            readB = client.get_node(batchB).get_value()
            readC = client.get_node(batchC).get_value()
            readD = client.get_node(batchD).get_value()

            if dataB:
                print("Recipe B Ready, retrieving data.")
                batchopc = readB
                process_recipe(client, 'B', batchopc)
                
            if dataC:
                print("Recipe C Ready, retrieving data.")
                batchopc = readC
                process_recipe(client, 'C', batchopc)

            if dataD:
                print("Recipe D Ready, retrieving data.")
                batchopc = readD
                process_recipe(client, 'D', batchopc)

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            message = str(e)
            log_error(message)
            # Attempt to reconnect if the connection is lost
            try:
                client.disconnect()
                time.sleep(10)  # Wait before reconnecting
                client.connect()
                print("Reconnected to OPC UA Server.")
            except Exception as reconnect_error:
                print(f"Failed to reconnect to OPC UA Server: {reconnect_error}")
                log_error(str(reconnect_error))
                connected = False
                break  # Exit the loop if reconnection fails

        time.sleep(15)

def process_recipe(client, recipe_letter, batchopc):
    completion_tag = f'ns=3;s="REPORT"."Report_{recipe_letter}_Generato"'
    try:
        if recipe_letter in ['B','C']:
            active_ingredients_data = read_active_ingredients(client, recipe_letter)
            for ingredient_key, ingredient_details in active_ingredients_data.items():
                update_database(ingredient_details, batchopc, recipe_letter, client)

            # Write True to the correspondent boolean tag to indicate processing is done
            client.get_node(completion_tag).set_value(ua.DataValue(True))
            print(f"Update completed for line {recipe_letter}.")

        if recipe_letter == 'D':
            d_active_ingredients(client)
            client.get_node(completion_tag).set_value(ua.DataValue(True))
            print(f"Update completed for line {recipe_letter}.")

    except Exception as e:
        print(f"An error occurred while processing recipe {recipe_letter}: {traceback.print_exc()}")
        message = f"An error occurred while processing recipe {recipe_letter}: {traceback.print_exc()}"
        log_error(message)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("An unexpected error occurred:")
            traceback.print_exc()
            log_error(f"Unexpected error: {traceback.format_exc()}")
            time.sleep(10)
