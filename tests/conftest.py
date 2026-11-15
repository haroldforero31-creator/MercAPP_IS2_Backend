import os
import sys

# Configure isolated test database BEFORE app is imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

TEST_DB_PATH = os.path.join(BASE_DIR, 'test_suite.db')
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_PATH}'
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'
os.environ['WTF_CSRF_ENABLED'] = 'False'
