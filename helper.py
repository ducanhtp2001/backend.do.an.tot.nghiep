import uuid
import random

def generate_user_id():
    uuid_str = str(uuid.uuid4())
    print(uuid_str)
    user_id = ''.join(random.choice('0123456789') if char == '-' else char for char in uuid_str)
    return user_id
