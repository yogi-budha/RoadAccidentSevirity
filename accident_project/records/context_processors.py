# records/context_processors.py - navbar lai sab template ma data dinchha
import os
from records.models import AccidentRecord

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAST_TRAIN_FILE = os.path.join(BASE_DIR, "last_train_count.txt")


def get_last_train_count():
    try:
        with open(LAST_TRAIN_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_train_count(n):
    with open(LAST_TRAIN_FILE, "w") as f:
        f.write(str(n))


def nav_context(request):
    current = AccidentRecord.objects.count()
    last = get_last_train_count()
    new = current - last
    return {
        "show_retrain": new > 0,
        "new_records_count": new,
    }