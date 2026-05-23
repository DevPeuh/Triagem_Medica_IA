#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuracao.configuracoes')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError('Django não está instalado ou configurado corretamente.') from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
