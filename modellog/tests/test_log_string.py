import datetime

from modellog.models import ActionLog


def test_log_string():
    user_id = 'dario'
    modification = ActionLog(
        data=datetime.datetime.utcnow(),
        user_id=user_id,
        action_type='Q',
        description='This is an example',
        modelName='Viaggio',
        instance_id=42,
    )
    assert str(modification) == 'Presenze - dario. This is an example'
