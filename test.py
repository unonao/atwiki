try:
    raise ValueError("error!")
except ValueError as e:
        print(e.args)
