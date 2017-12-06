from modellog.models import ActionLog
from tam.tamdates import ita_now


def test_log_string():
    user_id = 'dario'
    modification = ActionLog(
        data=ita_now,
        user_id=user_id,
        action_type='Q',
        description='This is an example',
        modelName='Viaggio',
        instance_id=42,
    )
    assert str(modification) == 'Presenze - dario. This is an example'
