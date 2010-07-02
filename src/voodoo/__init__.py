class MovementPlan:
    """
    Define a movement plan.
    """
    def __init__(self, timeline = []):
        self.timeline = timeline

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
