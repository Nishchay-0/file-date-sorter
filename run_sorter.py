import sys

def main():
    # If command line arguments were passed (beyond script name), launch CLI
    if len(sys.argv) > 1:
        import cli
        cli.main()
    else:
        # Otherwise launch GUI
        import gui
        gui.main()

if __name__ == '__main__':
    main()
