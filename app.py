from flask import Flask, render_template, request,jsonify, session, redirect, url_for
from flask_restful import Resource, Api
import pandas as pd
import networkx as nx

app = Flask(__name__)



@app.route('/salud')
def salud():
    data = {
        'mensaje':'alwin csmr'
    }
    return jsonify(data), 200

@app.route('/aeropuertos')
def aeropuertos():
    iata_spain = pd.read_csv('static/csv/iata_spain.csv')
    data_iata_spain = iata_spain.to_dict(orient='records')
    data = {
        'aeropuertos':data_iata_spain
    }
    return jsonify(data), 200



#OBTENGO TODOS LOS GRAFOS DIRIGIDOS
def obtener_grafos():
    spain_flights = pd.read_csv('static/csv/spain_flights.csv')
    DG=nx.DiGraph()
    for row in spain_flights.iterrows():
        DG.add_edge(row[1]["origin"],
                    row[1]["destination"],
                    duration=row[1]["duration"],
                    price=row[1]["price"])
    return DG


# Función para mostrar los detalles en cada escala
def show_path(iata_spain, path, DG):
    print(f"nodos:{DG.nodes}")
    total_price = 0
    total_duration = 0
    detalles = []
    print(f"ruta{path}")
    print(iata_spain)
    try:
        for i in range(len(path)-1):
            origin = path[i]
            destination = path[i+1]
            # Verifica si los nodos están presentes en el índice de iata_spain
            if origin not in iata_spain.index or destination not in iata_spain.index:
                raise Exception('Los nodos no están presentes en el índice de iata_spain')

            duration = DG[origin][destination]["duration"]
            price = DG[origin][destination]["price"]
            print(f"{duration} and {price}")
            total_price += price
            total_duration += duration

            detalle = {
                'origen': iata_spain.loc[origin]["name"],
                'destino': iata_spain.loc[destination]["name"],
                'duration': duration,
                'price': price
            }

            detalles.append(detalle)

        resultado = {
            'detalles': detalles,
            'total_duration': total_duration,
            'total_price': total_price
        }

        return resultado

    except Exception as e:
        # En caso de excepción, devuelve un objeto de respuesta con el mensaje de error
        return jsonify(error=str(e)), 400


# Función para obtener todos los caminos más cortos
# Función para obtener todos los caminos más cortos
def get_all_shortest_paths(DG, origin, destination, criterio, iata_spain):
    print(f"*** El camino más corto - Origen: {origin} Destino: {destination}")

    resultados = []  # Lista para almacenar todos los resultados

    weight = criterio

    if weight == "price":
        print(f"* Ordenando por: {weight}")
        paths = list(nx.all_shortest_paths(DG,
                                           source=origin,
                                           target=destination,
                                           weight="price"))
        for path in paths:
            print(f"   Camino óptimo: {path}")
            resultado = show_path(iata_spain, path, DG)
            if isinstance(resultado, dict):  # Verifica si es un diccionario
                resultados.append(resultado)
            else:
                # Maneja el caso en el que show_path devuelve algo diferente a un diccionario
                print(f"Resultado no válido: {resultado}")

    elif weight == "duration":
        print(f"* Ordenando por: {weight}")
        paths = list(nx.all_shortest_paths(DG,
                                        source=origin,
                                        target=destination,
                                        weight="duration"))
        for path in paths:
            print(f"   Camino óptimo: {path}")
            resultado = show_path(iata_spain, path, DG)
            if isinstance(resultado, dict):  # Verifica si es un diccionario
                resultados.append(resultado)
            else:
                # Maneja el caso en el que show_path devuelve algo diferente a un diccionario
                error_message = resultado.get_json(force=True)  # Obtiene el mensaje de error del objeto de respuesta
                print(f"Resultado no válido: {error_message}")
                return {'error': error_message}, 400  # Devuelve un diccionario con el mensaje de error
    
    elif weight is None:
        print(f"* Ordenando por: Escala")
        for path in list(nx.all_shortest_paths(DG, source=origin, target=destination, weight=None)):
            print(f"   Camino óptimo: {path}")
            resultado = show_path(iata_spain, path, DG)
            if isinstance(resultado, dict):  # Verifica si es un diccionario
                resultados.append(resultado)
            else:
                # Maneja el caso en el que show_path devuelve algo diferente a un diccionario
                print(f"Resultado no válido: {resultado}")

    return resultados


@app.route('/ejemplo', methods=['GET'])
def ejemplo():
    DG = obtener_grafos()

    # Obtén los parámetros de la consulta desde la URL
    code_origen = request.args.get('codeOrigen')
    code_destino = request.args.get('codeDestino')
    criterio = request.args.get('criterio')

    # Verifica si todos los parámetros están presentes
    if code_origen not in DG.nodes or code_destino not in DG.nodes:
        return jsonify(error='Los códigos de origen y destino deben estar presentes en el gráfico dirigido'), 400

    iata_spain = pd.read_csv('static/csv/iata_spain.csv')

    # Ejecuta la función correspondiente según el valor de 'criterio'
    if criterio == '1':
        resultados = get_all_shortest_paths(DG, code_origen, code_destino, "price", iata_spain)
    elif criterio == '2':
        resultados = get_all_shortest_paths(DG, code_origen, code_destino, "duration", iata_spain)
    elif criterio == '3':
        resultados = get_all_shortest_paths(DG, code_origen, code_destino, None, iata_spain)
    else:
        return jsonify(error='El valor de "criterio" debe ser 1, 2 o 3'), 400

    return jsonify(resultados), 200

if __name__ == '__main__':
    app.run(debug = True, port = 5000)