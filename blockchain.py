class blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

    def new_block( self ):
        pass

    def new_transaction( self ):
        pass

    def proof_of_work( self ):
        pass

    @property
    def last_block( self ):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        pass

