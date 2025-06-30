
import sys
from main import recognize

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scan.py YYYY-MM-DD")
        sys.exit(1)

    date_str = sys.argv[1]
    print(f"📅 Starting scan for attendance date: {date_str}")
    recognize(date_str)
