class metadata(dict):
    def __init__(self, dictionary):
        dictionary = dictionary.copy()
        self.__dict__ = self
        for key, value in dictionary.items():
            if type(value) == dict:
                value = metadata(value)

            self.__setitem__(key, value)
