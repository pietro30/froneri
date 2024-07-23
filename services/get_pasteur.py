import time
import traceback
from opcua import Client
import pyodbc

# Default parameters
DEFAULT_PARAMS = {
    "server": "192.168.0.183",
    "database": "RecipeDB",
    "username": "PC_SERVER_MIX1",
    "password": "PASSWORD01",
    "ip": "192.168.0.4",
}

# Initialize variables with default values
server = DEFAULT_PARAMS["server"]
database = DEFAULT_PARAMS["database"]
username = DEFAULT_PARAMS["username"]
password = DEFAULT_PARAMS["password"]
ip = DEFAULT_PARAMS["ip"]

def log_error(message):
    with open("pasteur_log.txt", "a") as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {message}\n")

# Attempt to read the init file and extract the values
try:
    with open('init.txt', 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            if key in DEFAULT_PARAMS:
                locals()[key] = value.strip()
except FileNotFoundError:
    print("The 'init.txt' file was not found. Using default parameters.")
    message = traceback.print_exc()
    log_error(message)

# Tags to be read
tagsB = [
    'ns=3;s="SPV"."Pastorizzatore"[1]."Ricetta"', 
    'ns=3;s="REPORT"."RicettaPastB"."Descrizione"',
    'ns=3;s="REPORT"."RicettaPastB"."StampID"',
    'ns=3;s="REPORT"."RicettaPastB"."qTotale"',
    'ns=3;s="SPV"."Pastorizzatore"[1]."N_Serbatoio"', 
    'ns=3;s="SPV"."Pastorizzatore"[1]."StatusWord1"', 
    'ns=3;s="SPV"."Pastorizzatore"[1]."StatusWord2"', 
    'ns=3;s="SPV"."AI_Micro3_4"[158]."Val"', 
    'ns=3;s="SPV"."AI_Micro5"[58]."Val"', 
    'ns=3;s="SPV"."PID_Micro1_2"[0]."Par"."SetpointValue"', 
    'ns=3;s="SPV"."AI_Micro1_2"[29]."Val"', 
    'ns=3;s="SPV"."PID_Micro1_2"[1]."Par"."SetpointValue"', 
    'ns=3;s="SPV"."AI_Micro1_2"[46]."Val"', 
    'ns=3;s="SPV"."AI_Micro1_2"[30]."Val"', 
    'ns=3;s="DO"."OmoB_70"', 
]

tagsC = [
    'ns=3;s="SPV"."Pastorizzatore"[2]."Ricetta"', 
    'ns=3;s="REPORT"."RicettaPastC"."Descrizione"',
    'ns=3;s="REPORT"."RicettaPastC"."StampID"',
    'ns=3;s="REPORT"."RicettaPastC"."qTotale"',
    'ns=3;s="SPV"."Pastorizzatore"[2]."N_Serbatoio"', 
    'ns=3;s="SPV"."Pastorizzatore"[2]."StatusWord1"', 
    'ns=3;s="SPV"."Pastorizzatore"[2]."StatusWord2"', 
    'ns=3;s="SPV"."AI_Micro3_4"[159]."Val"', 
    'ns=3;s="SPV"."AI_Micro5"[59]."Val"', 
    'ns=3;s="SPV"."PID_Micro1_2"[2]."Par"."SetpointValue"', 
    'ns=3;s="SPV"."AI_Micro1_2"[36]."Val"', 
    'ns=3;s="SPV"."PID_Micro1_2"[3]."Par"."SetpointValue"', 
    'ns=3;s="SPV"."AI_Micro1_2"[47]."Val"', 
    'ns=3;s="SPV"."AI_Micro1_2"[37]."Val"', 
    'ns=3;s="DO"."OmoC_70"', 
]

# Database connection string
connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

curflagB = 0
curflagC = 0

def decimal_to_binary(decimal_num):
    if decimal_num < 0:
        raise ValueError("Input must be a non-negative integer.")
    binary_str = bin(decimal_num)[2:]
    binary_str = binary_str[:-1]
    position = binary_str.find('1')
    return len(binary_str) - position if position != -1 else -1

def status_name(value):
    statuses = [
        'ProntoPerSteril', 'InSpurgo', 'Bloccato', 'InAllarme', 'InSterilizzazione',
        'InProdAcqua', 'ProntoScorrim', 'ProntoAvvioProd', 'InScorrimento', 'InSpurgo',
        'InProduzione', 'InRicircolazione', 'InSpegnimento', 'ProntoPerLavaggio', 'InLavaggio'
    ]
    return statuses[value] if value < len(statuses) else value

def status_name2(value):
    statuses = ['InRipristinoAcqua', 'PrPastSSogliaO70', 'PastMaxRicircAtt']
    return statuses[value] if value < len(statuses) else value

def get_cycle(flag, current_flag):
    cycle = 0
    if flag == 1 and current_flag == 0:
        current_flag = 1
    elif flag == 0 and current_flag == 1:
        cycle = 1
        current_flag = 0
    return cycle, current_flag

def read_tags(client, tags):
    values = {}
    for tag in tags:
        try:
            node = client.get_node(tag)
            value = node.get_value()
            if 'StatusWord1' in tag:
                highest_position = decimal_to_binary(value)
                values['Stato_Past'] = status_name(highest_position)
                values['Stato_Value'] = highest_position
            elif 'StatusWord2' in tag:
                values['Stato2_Past'] = status_name2(value)
                values['Stato2_Value'] = value
            else:
                values[tag] = value
        except Exception as e:
            message = f"Error on tag: {tag}: {e}, {traceback.print_exc()}"
            log_error(message)
    return values

def save_to_database(data, id_value):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        sql_command = """
        INSERT INTO dbo.ReportPast (
            IDPast, IDRecipe, Descrizione, Batch, Quantita, IDSerb,
            Stato_Past, Stato_Value, Stato2_Past, Stato2_Value, Portata,
            Temp_Risc, SetP_Risc, Temp_Raff, SetP_Raff, Press_Linea,
            Press_Omo, Vel_Omo_70, Timestamp, UniID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), NEWID())
        """
        data_with_id = (id_value,) + data
        cursor.execute(sql_command, data_with_id)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        message = f"Error saving data with ID {id_value} to database: {e}, {traceback.print_exc()}"
        log_error(message)

def main():
    global curflagB, curflagC
    client = Client(f"opc.tcp://{ip}:4840")
    client.session_timeout = 30000
    connected = False

    while True:
        if not connected:
            try:
                client.connect()
                print("Connected to OPC UA Server. Service get_pasteur running...")
                connected = True
            except Exception as e:
                print(f"Could not connect to OPC UA Server: {e}")
                message = traceback.print_exc()
                log_error(message)
                time.sleep(5)
                continue

        try:
            triggerB = 'ns=3;s="REPORT"."PastorizzazioneInCorsoB"'
            triggerC = 'ns=3;s="REPORT"."PastorizzazioneInCorsoC"'
            nodeB = client.get_node(triggerB)
            trigB = nodeB.get_value()
            nodeC = client.get_node(triggerC)
            trigC = nodeC.get_value()

            if trigB:
                valuesB = read_tags(client, tagsB)
                dataB = tuple(valuesB.values())
                save_to_database(dataB, "B")
            
            if trigC:
                valuesC = read_tags(client, tagsC)
                dataC = tuple(valuesC.values())
                save_to_database(dataC, "C")

        except Exception as e:
            message = traceback.print_exc()
            log_error(message)
            print(message)
            connected = False
            client.disconnect()
        
        time.sleep(5)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("An unexpected error occurred:")
            traceback.print_exc()
            log_error(f"Unexpected error: {traceback.format_exc()}")
            time.sleep(10)
