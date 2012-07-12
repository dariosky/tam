# Creo gli eventuali permessi mancanti
from django.contrib.auth.models import User, Group



def create_missing_permissions():
	from django.contrib.auth.management import create_permissions
	from django.db.models import get_apps
	for app in get_apps():
		create_permissions(app, None, 2)

def create_missing_groups():
	needed_groups = 	['Normale', 'Potente']
	for name in needed_groups:
		if not Group.objects.filter(name=name).exists():
			print "Creo il gruppo %s" % name
			group = Group(name=name)
			group.save()

def delete_all_permissions():
	from django.contrib.auth.models import Permission
	Permission.objects.all().delete()

def prettyPrintPermissions():
	from django.contrib.auth.models import User, Permission, Group
	lines = []
	for gruppo in Group.objects.all():
		lines.append(str(gruppo))
		for permesso in gruppo.permissions.all():
			lines.append("   ", permesso.codename)
	return lines

def setPermissions(groupName, permissions_codenames):
	from django.contrib.auth.models import User, Permission, Group
	group = Group.objects.get(name=groupName)
	if hasattr(permissions_codenames, "split"):
		permissions_codenames_string = permissions_codenames
		permissions_codenames = filter(lambda s: s <> '', map(lambda s: s.strip(), permissions_codenames_string.split("\n")))
	print "Avevo %d permessi per il gruppo %s." % (group.permissions.count(), group)
	group.permissions.clear()
	for permission_code in permissions_codenames:
		permission = Permission.objects.get(codename=permission_code)
		group.permissions.add(permission)
	print "Ora ne ho %d." % (group.permissions.count())

def setDefaultPermissions():
	setPermissions('Potente',
					"""	add_user
					    change_user
					    generate
					    view
					    add_bacino
					    change_bacino
					    delete_bacino
					    add_cliente
					    change_cliente
					    delete_cliente
					    add_conducente
					    change_classifiche_iniziali
					    change_conducente
					    delete_conducente
					    add_conguaglio
					    change_conguaglio
					    delete_conguaglio
					    add_listino
					    change_listino
					    delete_listino
					    add_luogo
					    change_luogo
					    delete_luogo
					    add_passeggero
					    change_passeggero
					    delete_passeggero
					    add_prezzolistino
					    change_prezzolistino
					    delete_prezzolistino
					    can_backup
					    get_backup
					    add_tratta
					    change_tratta
					    delete_tratta
					    add_viaggio
					    change_doppi
					    change_oldviaggio
					    change_viaggio
					    delete_viaggio
					    flat
					""")
	setPermissions('Normale',
					"""	smalledit
					    view
					    add_bacino
					    add_cliente
					    add_listino
					    add_luogo
					    add_passeggero
					    change_passeggero
					    add_prezzolistino
					    delete_prezzolistino
					    add_tratta
					    add_viaggio
					    change_viaggio
					    delete_viaggio
					""")


if __name__ == '__main__':
	#delete_all_permissions()
	#create_missing_permissions()
	create_missing_groups()
	setDefaultPermissions()
	#print "\n".join(prettyPrintPermissions())
