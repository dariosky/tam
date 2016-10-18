from utils.env_subs import perform_dict_substitutions


def test_folders_templates():
    d = dict(
        FOLDERS=dict(
            HOME='/home/user',
            REPOSITORY_FOLDER="{HOME}/repo/tam",
        ),

        GUNICORN=dict(
            RUN_GUNICORN_COMMAND="{REPOSITORY_FOLDER}/run_gunicorn",
        )
    )

    perform_dict_substitutions(d)

    assert d['GUNICORN']['RUN_GUNICORN_COMMAND'] == "/home/user/repo/tam/run_gunicorn"
