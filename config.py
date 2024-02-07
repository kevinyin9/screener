"""
integrate configparser with some custom getter
"""
import configparser


class Config(configparser.ConfigParser):
    """
    Config wrapper for config parser
    """

    def __init__(self):
        super(Config, self).__init__()
        self.optionxform = str

    def getlist(self, section, option, **kwargs) -> list:
        """
        get a str list from raw string
        """
        raw_str = self.get(section, option, **kwargs)
        if "[" in raw_str[0] and "]" in raw_str[-1]:
            raw_str = raw_str[1:-1]
        if len(raw_str) == 0:
            return []
        raw_ss = raw_str.split(",")
        if "" in raw_ss:
            raise ValueError("Invalid string %s" % raw_str)
        try:
            return [int(s.strip().strip("'\"")) for s in raw_ss]
        except ValueError:
            try:
                return [float(s.strip().strip("'\"")) for s in raw_ss]
            except ValueError:
                return [str(s.strip().strip("'\"")) for s in raw_ss]

    def getset(self, section, option, **kwargs) -> set:
        """
        get a str set from raw string
        """
        raw_str = self.get(section, option, **kwargs)
        if "[" in raw_str[0] and "]" in raw_str[-1]:
            raw_str = raw_str[1:-1]
        res = set()
        if len(raw_str) == 0:
            return res
        raw_ss = raw_str.split(",")
        if "" in raw_ss:
            raise ValueError("Invalid string %s" % raw_str)
        for _s in raw_ss:
            try:
                res.add(int(_s.strip().strip("'")))
            except ValueError:
                try:
                    res.add(float(_s.strip().strip("'")))
                except ValueError:
                    res.add(str(_s.strip().strip("'")))
        return res
