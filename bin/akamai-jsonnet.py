import sys
from os.path import dirname, join, abspath
sys.path.append(abspath(join(dirname(__file__), "..")))

from src.main import main

main()