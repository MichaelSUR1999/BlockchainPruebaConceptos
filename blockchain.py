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





