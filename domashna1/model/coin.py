class Coin:
    def __init__(self, id, symbol, name, market_cap=None, market_cap_rank=None):
        self.id = id
        self.symbol = symbol
        self.name = name
        self.market_cap = market_cap
        self.market_cap_rank = market_cap_rank

    def __repr__(self):
        # kratko i jasno za debug printing
        return f"Coin(id='{self.id}', symbol='{self.symbol}', rank={self.market_cap_rank})"
