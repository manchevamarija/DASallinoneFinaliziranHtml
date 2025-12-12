from domashna1.pipeline.filter1_fetch_coins import Filter1FetchCoins
from domashna1.pipeline.filter2_check_last_date import Filter2FetchHistory


class Pipeline:

    def __init__(self, filters):
        self.filters = filters

    def run(self):
        data = None
        for f in self.filters:
            if data is None:
                data = f.process()
            else:
                data = f.process(data)
        print("\nPIPELINE FINISHED SUCCESSFULLY!")
        return data


if __name__ == "__main__":
    pipeline = Pipeline([
        Filter1FetchCoins(),
        Filter2FetchHistory()
    ])

    pipeline.run()
