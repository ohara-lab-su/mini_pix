from mini_pix.config import Config


def main():
    config = Config("mini_pix.yaml")

    print("config =", config)
    print()

    print("SERVER_IP")
    print("  value =", config.SERVER_IP)
    print("  type  =", type(config.SERVER_IP))
    print()

    print("SERVER_PORT")
    print("  value =", config.SERVER_PORT)
    print("  type  =", type(config.SERVER_PORT))
    print()

    print("CLIENT_LOGGER_NAME")
    print("  value =", config.CLIENT_LOGGER_NAME)
    print("  type  =", type(config.CLIENT_LOGGER_NAME))
    print()

    print("SERVER_LOGGER_NAME")
    print("  value =", config.SERVER_LOGGER_NAME)
    print("  type  =", type(config.SERVER_LOGGER_NAME))
    print()

    print("TIMEOUT")
    print("  value =", config.TIMEOUT)
    print("  type  =", type(config.TIMEOUT))
    print()

    print("LOGGER_LEVEL")
    print("  value =", config.LOGGER_LEVEL)
    print("  type  =", type(config.LOGGER_LEVEL))
    print()

    print("ASYNC_MODE")
    print("  value =", config.ASYNC_MODE)
    print("  type  =", type(config.ASYNC_MODE))


if __name__ == "__main__":
    main()
