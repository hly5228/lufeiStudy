class PricePolicyInvalid(Exception):

    def __init__(self, msg):
        self.msg = msg


class CourseNotExistInCar(Exception):
    def __init__(self, msg):
        self.msg = msg