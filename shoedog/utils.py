def peek(g, error=None):
    """ Peeks at the next object in a generator

    Requires:
        g: generator
        error: optional Error to be raised in place of StopIteration
    Returns:
        obj: Next object in generator
        stream: stream with object placed back in front
    Raises:
        StopIteration if reached end of generator or custom error if provided
    """
    try:
        obj = next(g)
    except StopIteration:
        if error:
            raise error
        else:
            raise StopIteration

    new_gen = (value for gen in ((obj,), g) for value in gen)
    return obj, new_gen
