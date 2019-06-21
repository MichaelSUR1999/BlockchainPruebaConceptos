import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask , jsonify , request

class blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

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






