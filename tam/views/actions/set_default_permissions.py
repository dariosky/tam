# coding=utf-8
# Creo gli eventuali permessi mancanti
import django
from django.db import transaction


def create_missing_permissions():
    from django.contrib.auth.management import create_permissions
    from django.apps import apps

    for name, app in apps.app_configs.iteritems():
        create_permissions(app, verbosity=0)


def create_missing_groups():
    from django.contrib.auth.models import Group

    needed_groups = ["Normale", "Potente"]
    for name in needed_groups:
        if not Group.objects.filter(name=name).exists():
            print("Creo il gruppo %s" % name)
            group = Group(name=name)
            group.save()


def delete_all_permissions():
    from django.contrib.auth.models import Permission

    Permission.objects.all().delete()


def pretty_print_permissions():
    from django.contrib.auth.models import Group

    lines = []
    for gruppo in Group.objects.all():
        lines.append(str(gruppo))
        for permesso in gruppo.permissions.all():
            lines.append(
                "  %s"
                % "|".join(
                    [
                        permesso.content_type.app_label,
                        permesso.content_type.model,
                        permesso.codename,
                    ]
                )
            )
    return lines


@transaction.atomic
def set_permissions(groupName, permission_pretty):
    from django.contrib.auth.models import Permission, Group

    group = Group.objects.get(name=groupName)
    permissions_codenames = filter(
        lambda s: s != "", map(lambda s: s.strip(), permission_pretty.split("\n"))
    )
    print("Avevo %d permessi per il gruppo %s." % (group.permissions.count(), group))
    group.permissions.clear()
    for full_code_name in permissions_codenames:
        app_label, model, codename = full_code_name.split("|")
        # permission = Permission.objects.get(codename=permission_code)
        permission = Permission.objects.get_by_natural_key(
            codename=codename, app_label=app_label, model=model
        )
        group.permissions.add(permission)

    print("Ora ne ho %d." % (group.permissions.count()))


def set_default_permissions():
    set_permissions(
        "Potente",
        """
  auth|user|add_user
  auth|user|change_user
  board|boardmessage|view
  codapresenze|codapresenze|editall
  codapresenze|codapresenze|view
  fatturazione|fattura|generate
  fatturazione|fattura|view
  tam|bacino|add_bacino
  tam|bacino|change_bacino
  tam|bacino|delete_bacino
  tam|cliente|add_cliente
  tam|cliente|change_cliente
  tam|cliente|delete_cliente
  tam|conducente|add_conducente
  tam|conducente|change_classifiche_iniziali
  tam|conducente|change_conducente
  tam|conducente|delete_conducente
  tam|conguaglio|add_conguaglio
  tam|conguaglio|change_conguaglio
  tam|conguaglio|delete_conguaglio
  tam|listino|add_listino
  tam|listino|change_listino
  tam|listino|delete_listino
  tam|luogo|add_luogo
  tam|luogo|change_luogo
  tam|luogo|delete_luogo
  tam|passeggero|add_passeggero
  tam|passeggero|change_passeggero
  tam|passeggero|delete_passeggero
  tam|passeggero|fastinsert_passenger
  tam|prezzolistino|add_prezzolistino
  tam|prezzolistino|change_prezzolistino
  tam|prezzolistino|delete_prezzolistino
  tam|profiloutente|can_backup
  tam|profiloutente|get_backup
  tam|tratta|add_tratta
  tam|tratta|change_tratta
  tam|tratta|delete_tratta
  tam|viaggio|add_viaggio
  tam|viaggio|change_doppi
  tam|viaggio|change_oldviaggio
  tam|viaggio|change_viaggio
  tam|viaggio|delete_viaggio
  tamArchive|viaggioarchive|archive
  tamArchive|viaggioarchive|flat
""",
    )
    set_permissions(
        "Normale",
        """
  board|boardmessage|view
  codapresenze|codapresenze|editall
  codapresenze|codapresenze|view
  fatturazione|fattura|smalledit
  fatturazione|fattura|view
  tam|bacino|add_bacino
  tam|cliente|add_cliente
  tam|listino|add_listino
  tam|luogo|add_luogo
  tam|passeggero|add_passeggero
  tam|passeggero|change_passeggero
  tam|prezzolistino|add_prezzolistino
  tam|prezzolistino|delete_prezzolistino
  tam|tratta|add_tratta
  tam|viaggio|add_viaggio
  tam|viaggio|change_viaggio
  tam|viaggio|delete_viaggio
""",
    )


if __name__ == "__main__":
    django.setup()
    # delete_all_permissions()
    # create_missing_permissions()
    # create_missing_groups()
    # setDefaultPermissions()
    print("\n".join(pretty_print_permissions()))
