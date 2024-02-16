'''
This is a main file to start it all
'''
import os
import sys
import signal  # Import the signal module without using it directly
import ftptomongo

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def signal_handler(sig, frame):  # pylint: disable=unused-argument
    """
    Signal handler function to handle KeyboardInterrupt (Ctrl+C).
    """
    print("Ctrl+C detected. Exiting...")
    sys.exit(0)


def main():
    """
    Main function to start
    """
    print("Executing ftptomongo package as a script")

    # Set the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Your main application logic goes here
    ftptomongo.run_ftp_server()


if __name__ == "__main__":
    main()
