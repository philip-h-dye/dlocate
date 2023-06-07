   if sys.platform == "win32":
        from win32api import GenerateConsoleCtrlEvent
        GenerateConsoleCtrlEvent(0, 0)  # send Ctrl+C to current TTY
    else:
        os.kill(0, signal.SIGINT)
