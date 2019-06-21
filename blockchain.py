import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask , jsonify , request

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

    def register_node ( self , address ) :
        """
        Añadir un nuevo nodo a la lista de nodos
        :param address: Dirección del nodo.
        """
        parsed_url = urlparse ( address )
        if parsed_url.netloc :
            self.nodes.add ( parsed_url.netloc )
        elif parsed_url.path :
            # Acepta una URL sin esquema.
            self.nodes.add ( parsed_url.path )
        else :
            raise ValueError ( 'Invalid URL' )

    def valid_chain ( self , chain ) :
        """
        Determinar si una cadena de bloqueo determinada es válida
        :param chain: Una cadena de bloqueo
        :return: Verdadero si es válido, falso si no lo es
        """

        last_block = chain [ 0 ]
        current_index = 1

        while current_index < len ( chain ) :
            block = chain [ current_index ]
            print ( f'{last_block}' )
            print ( f'{block}' )
            print ( "\n-----------\n" )
            # Comprobar que el hash del bloque es correcto
            last_block_hash = self.hash ( last_block )
            if block [ 'previous_hash' ] != last_block_hash :
                return False

            # Verifique que la Prueba de Trabajo sea correcta
            if not self.valid_proof ( last_block [ 'proof' ] , block [ 'proof' ] , last_block_hash ) :
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts ( self ) :
        """
        Este es nuestro algoritmo de consenso, resuelve conflictos.
        reemplazando nuestra cadena por la más larga de la red.
        :return: True si nuestra cadena fue reemplazada, Falss si no
        """

        neighbours = self.nodes
        new_chain = None

        # Sólo buscamos cadenas más largas que las nuestras.
        max_length = len ( self.chain )

        # Agarrar y verificar las cadenas de todos los nodos de nuestra red
        for node in neighbours :
            response = requests.get ( f'http://{node}/chain' )

            if response.status_code == 200 :
                length = response.json ( ) [ 'length' ]
                chain = response.json ( ) [ 'chain' ]

                # Compruebe si la longitud es mayor y si la cadena es válida
                if length > max_length and self.valid_chain ( chain ) :
                    max_length = length
                    new_chain = chain

        # Reemplazar nuestra cadena si descubrimos una cadena nueva y válida más larga que la nuestra
        if new_chain :
            self.chain = new_chain
            return True

        return False

    def new_block ( self , proof , previous_hash ) :
        """
        Crear un nuevo Bloque en el Cadena de Bloques
        :param proof: La prueba dada por el algoritmo de Prueba de Trabajo
        :param previous_hash: Hash del Bloque anterior
        :return: Nuevo Bloque

        """

        block = {
            'index' : len ( self.chain ) + 1 ,
            'timestamp' : time ( ) ,
            'transactions' : self.current_transactions ,
            'proof' : proof ,
            'previous_hash' : previous_hash or self.hash ( self.chain [ -1 ] ) ,
        }

        # Anular la lista actual de transacciones
        self.current_transactions = [ ]

        self.chain.append ( block )
        return block

    def new_transaction ( self , sender , recipient , amount ) :
        """
        Crea una nueva transacción para ir al siguiente Bloque minado
        :param sender: Dirección del remitente
        :param recipient: Dirección del destinatario
        :param amount: Importe
        :return: El índice del Bloque que llevará a cabo esta transacción

       """
        self.current_transactions.append ( {
            'sender' : sender ,
            'recipient' : recipient ,
            'amount' : amount ,
        } )

        return self.last_block [ 'index' ] + 1

    @property
    def last_block ( self ) :
        return self.chain [ -1 ]

    @staticmethod
    def hash ( block ) :
        """
        Crea un hash de bloque SHA-256
        :param block: Bloque
        """

        # Debemos asegurarnos de que el Diccionario esté Ordenado, o tendremos hashes inconsistentes
        block_string = json.dumps ( block , sort_keys = True ).encode ( )
        return hashlib.sha256 ( block_string ).hexdigest ( )

    def proof_of_work ( self , last_block ) :
        """
        Algoritmo Simple de Prueba de Trabajo:
        -Buscar un número p' tal que hash(pp') contenga 4 ceros a la izquierda
        -Donde p es la prueba anterior, y p' es la nueva prueba

        :param last_block: <dict> último bloque
        :return: <int>
        """

        last_proof = last_block [ 'proof' ]
        last_hash = self.hash ( last_block )

        proof = 0
        while self.valid_proof ( last_proof , proof , last_hash ) is False :
            proof += 1

        return proof

    @staticmethod
    def valid_proof ( last_proof , proof , last_hash ) :
        """
        Valida la prueba
        :param last_proof: <int> Prueba Anterior
        :param proof: <int> Prueba de corriente
        :param last_hash: <str> El hash del bloque anterior
        :return: <bool> True si es correcto, False si no lo es.

        """

        guess = f'{last_proof}{proof}{last_hash}'.encode ( )
        guess_hash = hashlib.sha256 ( guess ).hexdigest ( )
        return guess_hash [ :4 ] == "0000"

# Instancia del nodo
app = Flask ( __name__ )

# Generar una dirección única globalmente para este nodo
node_identifier = str ( uuid4 ( ) ).replace ( '-' , '' )

# Instancia de la cadena de bloques
blockchain = Blockchain ( )

@app.route ( '/mine' , methods = [ 'GET' ] )
def mine () :
    # Ejecutamos el algoritmo de prueba de trabajo para obtener la siguiente prueba....
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work ( last_block )

    # Debemos recibir una recompensa por encontrar la prueba.
    # El remitente es "0" para indicar que este nodo ha extraído una nueva moneda.
    blockchain.new_transaction (
        sender = "0" ,
        recipient = node_identifier ,
        amount = 1 ,
    )

    # Forjar el nuevo bloque añadiéndolo a la cadena
    previous_hash = blockchain.hash ( last_block )
    block = blockchain.new_block ( proof , previous_hash )

    response = {
        'message' : "Nuevo Bloque Forjado" ,
        'index' : block [ 'index' ] ,
        'transactions' : block [ 'transactions' ] ,
        'proof' : block [ 'proof' ] ,
        'previous_hash' : block [ 'previous_hash' ] ,
    }
    return jsonify ( response ) , 200

@app.route ( '/transactions/new' , methods = [ 'POST' ] )
def new_transaction () :
    values = request.get_json ({
        "sender" : "sender" ,
        "recipient" : "recipient" ,
        "amount" : "amount"
    })
    """Compruebe que los campos obligatorios están en los datos POST."""
    required = [ 'sender' , 'recipient' , 'amount' ]
    if not all (k in values for k in required):
        return 'Valores que faltan' , 400
    # Crear una nueva transacción
    index = blockchain.new_transaction ( values [ 'sender' ] , values [ 'recipient' ] , values [ 'amount' ] )
    response = {'message' : f'La transacción se agregará al bloque {index}'}
    return jsonify ( response ) , 201

@app.route ( '/chain' , methods = [ 'GET' ] )
def full_chain () :
    response = {
        'chain' : blockchain.chain ,
        'length' : len ( blockchain.chain ) ,
    }
    return jsonify ( response ) , 200

@app.route ( '/nodes/register' , methods = [ 'POST' ] )
def register_nodes () :
    values = request.get_json ( )
    print(':::' , values)

    nodes = values.get ( 'nodes' )
    print('::::::::::::::', nodes)
    if nodes is None :
        return "Error: Por favor, proporcione una lista válida de nodos" , 400
    for node in nodes :
        blockchain.register_node ( node )

    response = {
        'message' : 'Se han añadido nuevos nodos' ,
        'total_nodes' : list ( blockchain.nodes ) ,
    }
    return jsonify ( response ) , 201

@app.route ( '/nodes/resolve' , methods = [ 'GET' ] )
def consensus () :
    replaced = blockchain.resolve_conflicts ( )

    if replaced :
        response = {
            'message' : 'Nuestra cadena fue reemplazada' ,
            'new_chain' : blockchain.chain
        }
    else :
        response = {
            'message' : 'Nuestra cadena tiene autoridad' ,
            'chain' : blockchain.chain
        }

    return jsonify ( response ) , 200

if __name__ == '__main__' :
    from argparse import ArgumentParser

    parser = ArgumentParser ( )
    parser.add_argument ( '-p' , '--port' , default = 5000 , type = int , help = 'port to listen on' )
    args = parser.parse_args ( )
    port = args.port

    #app.debug = True
    app.run ( host = 'localhost' , port = port )






