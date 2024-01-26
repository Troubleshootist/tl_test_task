class YandexWeatherDataFetchError(BaseException):
    pass


class FileWithCoordsNotFound(BaseException):
    pass


class CoordsParsingException(BaseException):
    pass


class NoCityFound(BaseException):
    pass
