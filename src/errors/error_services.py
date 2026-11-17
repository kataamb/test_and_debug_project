class DomainError(Exception):
    """
    Базовый класс для всех доменных ошибок сервисного слоя.
    Роутеры ловят DomainError и переводят в HTTP-коды,
    не зная про конкретные подклассы (если не нужно).
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AdvertNotFound(DomainError):
    def __init__(self, advert_id=None):
        if advert_id is not None:
            super().__init__(f"Advert with id={advert_id} not found")
        else:
            super().__init__("Advert not found")
        self.advert_id = advert_id


class CategoryNotFound(DomainError):
    def __init__(self, category_id=None):
        if category_id is not None:
            super().__init__(f"Category with id={category_id} not found")
        else:
            super().__init__("Category not found")
        self.category_id = category_id



class UserNotFound(DomainError):
    def __init__(self, user_id=None):
        if user_id is not None:
            super().__init__(f"User with id={user_id} not found")
        else:
            super().__init__("User not found")
        self.user_id = user_id


class AdvertUserNotOwn(DomainError):
    def __init__(self, user_id=None, advert_id=None):
        if user_id is not None and advert_id is not None:
            super().__init__(
                f"User id={user_id} is not the owner of advert id={advert_id}"
            )
        else:
            super().__init__("User does not own this advert")
        self.user_id = user_id
        self.advert_id = advert_id


class AdvertUserBuyOwn(DomainError):
    def __init__(self, user_id=None, advert_id=None):
        if user_id is not None and advert_id is not None:
            super().__init__(
                f"User id={user_id} cannot buy own advert id={advert_id}"
            )
        else:
            super().__init__("User cannot buy own advert")
        self.user_id = user_id
        self.advert_id = advert_id


class DealDoubleBuying(DomainError):
    def __init__(self, user_id=None, advert_id=None):
        if user_id is not None and advert_id is not None:
            super().__init__(
                f"User id={user_id} already bought advert id={advert_id}"
            )
        else:
            super().__init__("Advert already bought by this user")
        self.user_id = user_id
        self.advert_id = advert_id

class DealAlreadyBought(DomainError):
    def __init__(self, advert_id=None):
        if advert_id is not None:
            super().__init__(f"Advert id={advert_id} is already bought by another user")
        else:
            super().__init__("Advert is already bought by another user")
        self.advert_id = advert_id


class LikeDoubleAdding(DomainError):
    def __init__(self, user_id=None, advert_id=None):
        if user_id is not None and advert_id is not None:
            super().__init__(
                f"User id={user_id} already liked advert id={advert_id}"
            )
        else:
            super().__init__("User already liked this advert")
        self.user_id = user_id
        self.advert_id = advert_id



class LikeDoubleRemoving(DomainError):
    def __init__(self, user_id=None, advert_id=None):
        if user_id is not None and advert_id is not None:
            super().__init__(
                f"User id={user_id} don't contain in liked advert id={advert_id}"
            )
        else:
            super().__init__("User don't contain in liked this advert")
        self.user_id = user_id
        self.advert_id = advert_id




'''
class AdvertNotFound(Exception):
    pass


class CategoryNotFound(Exception):
    pass


class UserNotFound(Exception):
    pass

class AdvertUserNotOwn(Exception):
    pass

class AdvertUserBuyOwn(Exception):
    pass

class DealDoubleBuying(Exception):
    pass

class LikeDoubleAdding(Exception):
    pass

class DealAlreadyBought(Exception):
    pass
'''