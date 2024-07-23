import time
import traceback
from opcua import Client, ua
import pyodbc
import os
import uuid

# Default parameters
DEFAULT_PARAMS = {
    "server": "ITFERL0003\FRONERI",
    "database": "RecipeDB",
    "username": "aima",
    "password": "aima123",
    "ip": "10.17.32.188",
}

# Initialize variables with default values
params = DEFAULT_PARAMS.copy()

connection_string = (
    f"DRIVER={{SQL Server}};SERVER={params['server']};DATABASE={params['database']};UID={params['username']};PWD={params['password']}"
)

def log_error(message):
    with open("cip_log.txt", "a") as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {message}\n")

# Attempt to read the init file and extract the values
try:
    with open('init.txt', 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            if key in DEFAULT_PARAMS:
                params[key] = value.strip()
except FileNotFoundError:
    print("The 'init.txt' file was not found. Using default parameters.")
except Exception as e:
    print("An error occurred while reading 'init.txt'. Using default parameters.")
    message = traceback.print_exc()
    log_error(message)

def get_linea(x):
    if x == 0:
        return "E91"
    elif x == 1:
        return "E92"
    elif x == 2:
        return "E93"
    elif x == 3:
        return "E94"
    elif x == 4:
        return "E95"
    elif x == 5:
        return "E96"
    elif x == 6:
        return "ServiceCIP7"
    elif x == 7:
        return "ServiceCIP5"
    elif x == 8:
        return "Freezer W"
    elif x == 9:
        return "Freezer X"
    elif x == 10:
        return "Freezer Y"
    elif x == 11:
        return "Freezer Z"

def get_fase(faseN):
    if faseN == 1:
        return 1
    elif faseN == 2:
        return 2
    elif faseN == 4:
        return 4
    elif faseN == 8:
        return 3
    elif faseN == 16:
        return 5
    elif faseN == 32:
        return 6
    elif faseN == 64:
        return 7

def get_tipo(faseN):
    if faseN == 1:
        return "Iniziale"
    elif faseN == 2:
        return "Soda"
    elif faseN == 3:
        return "Acqua/Soda"
    elif faseN == 4:
        return "Acido"
    elif faseN == 5:
        return "Acqua/Acido"
    elif faseN == 6:
        return "Risciacquo"
    elif faseN == 7:
        return "Aria"
    else:
        return faseN

def get_status(status):
    if status == 5:
        return "IN ALLARME"
    elif status == 4:
        return "IN PAUSA"
    elif status == 1:
        return "IN CORSO"
    else:
        return "UNKNOWN"

def get_target(linea, target_value):
    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            sql_query = """
            SELECT [Nome] FROM dbo.ReportCIP_A
            WHERE [Linea] = ? AND [Target] = ?
            """
            cursor.execute(sql_query, (linea, target_value))
            row = cursor.fetchone()
            return row[0] if row else None

def get_curid(linea, target_value):
    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                sql_query = """
                SELECT [CurID] FROM dbo.ReportCIP_A
                WHERE [Linea] = ? AND [Target] = ?
                """
                cursor.execute(sql_query, (linea, target_value))
                row = cursor.fetchone()
                return row[0] if row else None
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        log_error(f"Database error: {traceback.format_exc()}")

def new_curid(uniid, linea, target_value):
    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                sql_query = """
                UPDATE dbo.ReportCIP_A
                SET [CurID] = ?
                WHERE [Linea] = ? AND [Target] = ?
                """
                cursor.execute(sql_query, (uniid, linea, target_value))
                conn.commit()
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        log_error(f"Database error: {traceback.format_exc()}")

def get_last_tipo(linea, target_value):
    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            sql_query = """
            SELECT TOP 1 [Tipo] FROM dbo.ReportCIP
            WHERE [Linea] = ? AND [Target] = ?
            ORDER BY Timestamp DESC
            """
            cursor.execute(sql_query, (linea, target_value))
            row = cursor.fetchone()
            return row[0] if row else None

def delete_curid(linea, target_value):
    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                sql_query = """
                UPDATE dbo.ReportCIP_A
                SET [CurID] = NULL
                WHERE [Linea] = ? AND [Target] = ?
                """
                cursor.execute(sql_query, (linea, target_value))
                conn.commit()
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        log_error(f"Database error: {traceback.format_exc()}")

def decimal_to_binary(decimal_num):
    if decimal_num < 0:
        raise ValueError("Input must be a non-negative integer.")
    binary_str = bin(decimal_num)[2:]
    if len(binary_str) == 1:
        return 1
    binary_str_trimmed = binary_str[:-1]
    position = binary_str_trimmed.find('1')
    return len(binary_str_trimmed) - position if position != -1 else -1

def freezer_dtb(decimal_num):
    if decimal_num < 0:
        raise ValueError("Input must be a non-negative integer.")
    
    binary_str = bin(decimal_num)[2:]  # Convert to binary and strip the '0b' prefix
    
    # Reverse the binary string to process from right to left
    reversed_binary_str = binary_str[::-1]
    
    # Find the position of the first '0' in the reversed binary string
    first_zero_position = reversed_binary_str.find('0')
    
    if first_zero_position == -1:
        return ""  # If there's no '0', return an empty string

    positions = []

    # Calculate the positions of '1's relative to the first '0'
    for i, bit in enumerate(reversed_binary_str):
        if bit == '1':
            relative_position = i - first_zero_position
            positions.append(str(relative_position) if relative_position >= 0 else '-1')

    return positions

def freezer_nome(linea, targets):
    nomes = []
    for target in targets:
        nome = get_target(linea, target)
        if nome:  # Check if nome is not None or empty
            nomes.append(nome)

    return ', '.join(nomes)

def main():
    opc_endpoint = f"opc.tcp://{params['ip']}:4840"
    client = Client(opc_endpoint)
    client.session_timeout = 30000

    n_values = {
        0: [46, 47, 30, 31, 0, 12],
        1: [48, 49, 32, 33, 1, 13],
        2: [50, 51, 34, 35, 2, 14],
        3: [52, 53, 36, 37, 3, 15],
        4: [54, 55, 38, 39, 4, 16],
        5: [56, 57, 40, 41, 5, 17],
        #6: [6, 7, 8, 9, 10],
        #7: [6, 7, 8, 9, 10],
        8: [42, 42, 120, 120, 24, 24],
        9: [43, 43, 121, 121, 25, 25],
        10: [44, 44, 123, 123, 27, 27],
        11: [45, 45, 122, 122, 26, 26]
    }

    connected = False

    while True:
        if not connected:
            try:
                client.connect()
                connected = True
                print("Connected to OPC UA Server. Service get_cip running...")
            except Exception as e:
                print("Failed to connect to OPC UA server:")
                log_error(f"Unexpected error: {traceback.format_exc()}")
                time.sleep(5)
                continue

        try:
            target_tag = None
            target_node = None
            target_read = None
            target_value = None
            setpoint_tag = None
            for x in range(12):
                if x == 6 or x == 7:
                    continue
                elif x == 8:
                    target_tag = f'ns=3;s="REPORT"."Freezer_CircW"'
                elif x == 9:
                    target_tag = f'ns=3;s="REPORT"."Freezer_CircX"'
                elif x == 10:
                    target_tag = f'ns=3;s="REPORT"."Freezer_CircY"'
                elif x == 11:
                    target_tag = f'ns=3;s="REPORT"."Freezer_CircZ"'
                else:
                    target_tag = f'ns=3;s="SPV"."GenLavaggi"."Sts"[{x}]."Target"'
                    setpoint_tag = f'ns=3;s="SPV"."PID_Micro5"[{x}]."Par"."SetpointValue"'

                fase_tag = f'ns=3;s="SPV"."GenLavaggi"."Sts"[{x}]."Fase"'
                status_tag = f'ns=3;s="SPV"."GenLavaggi"."Sts"[{x}]."StatusWord"'
                stampid_tag = f'ns=3;s="REPORT"."StampIDLavaggi{x}"'
                
                try:
                    linea = get_linea(x)
                    setpoint_value = None

                    if x in [8,9,10,11]:
                        target_node = client.get_node(target_tag)
                        target_read = target_node.get_value()
                        target_value = freezer_dtb(target_read) if target_read is not None else None
                        setpoint_value = 0
                        
                    else:
                        target_node = client.get_node(target_tag)
                        target_value = target_node.get_value()
                        setpoint_node = client.get_node(setpoint_tag)
                        setpoint_value = setpoint_node.get_value()

                    fase_node = client.get_node(fase_tag)
                    status_node = client.get_node(status_tag)
                    stampid_node = client.get_node(stampid_tag)

                    fase_value = fase_node.get_value()
                    status_value = status_node.get_value()
                    stampid_value = stampid_node.get_value()

                    rstatus_value = decimal_to_binary(status_value) if status_value != 0 else 0
                    rfase_value = get_fase(fase_value)
                    
                    tipo = get_tipo(rfase_value)

                    if rstatus_value != 0:
                        nome = None
                        stampid = str(x)+'-'+str(target_value)+'-'+str(stampid_value)
                        if x in [8,9,10,11]:
                            nome = freezer_nome(linea, target_value)
                        else:
                            nome = get_target(linea, target_value)
                            
                        data = []

                        for i in range(6):
                            val_tag = f'ns=3;s="SPV"."AI_Micro5"[{n_values[x][i]}]."Val"'
                            val_node = client.get_node(val_tag)
                            val_value = val_node.get_value()
                            data.append(float(val_value) if val_value is not None else 0.0)

                        with pyodbc.connect(connection_string) as conn:
                            with conn.cursor() as cursor:
                                sql_query = """
                                INSERT INTO dbo.ReportCIP (Linea, Target, Nome, Tipo, Fase, FaseVal, Status, Uniid, Setpoint, FlussMandata, FlussRitorno, ConcMandata, ConcRitorno, Temperatura, TempRit, Timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                                """
                                cursor.execute(sql_query, (linea, str(target_value), str(nome), str(tipo), rfase_value, 1, str(rstatus_value), str(stampid), setpoint_value, *data))
                                conn.commit()

                except Exception as e:
                    print(f"Error processing tag {x}:")
                    message = f"Error on tag: {x}: {e}, {traceback.print_exc()}"
                    log_error(message)

        except Exception as e:
            print("An error occurred during data processing:")
            log_error(f"Unexpected error: {traceback.format_exc()}")
            connected = False
            client.disconnect()
            print("Disconnected from OPC UA server.")
            time.sleep(5)

        time.sleep(30)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("An unexpected error occurred:")
            log_error(f"Unexpected error: {traceback.format_exc()}")
            time.sleep(10)