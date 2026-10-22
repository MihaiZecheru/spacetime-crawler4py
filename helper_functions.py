def print_with_color(*args, **kwargs) -> None:
    print(f"\033[31m{" ".join(args)}\033[0m", **kwargs)


def is_exact_match() -> bool:
  return False


def is_simhash_match() -> bool:
   return False