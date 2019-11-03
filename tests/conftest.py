import sys
from os.path import abspath
from os.path import dirname
from os.path import join

root_dir = dirname(dirname(abspath(__file__)))

sys.path.append(join(root_dir, "src"))
