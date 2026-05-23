from django.db import migrations


def drop_sinais_vitais_table(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        schema_editor.execute('DROP TABLE IF EXISTS sinais_vitais_sinalvital CASCADE;')
    else:
        schema_editor.execute('DROP TABLE IF EXISTS sinais_vitais_sinalvital;')


class Migration(migrations.Migration):

    dependencies = [
        ('triagens', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(drop_sinais_vitais_table, migrations.RunPython.noop),
    ]