def print_red(*args, **kwargs) -> None:
    message = " ".join(str(a) for a in args)
    print(f"\033[31m{message}\033[0m", **kwargs)

def is_exact_match(content) -> bool:
  return False


def is_simhash_match(content) -> bool:
   return False