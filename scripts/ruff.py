#!/usr/bin/env python3
import subprocess
import sys


def run_ruff_command(args, include_base_args=True):
    try:
        base_args = (
            [
                '--select',
                'F,E,I',
                '--ignore',
                'E501',
            ]
            if include_base_args
            else []
        )

        result = subprocess.run(['ruff'] + args + base_args, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f'Command failed with exit code {e.returncode}')
        sys.exit(e.returncode)


def format():
    run_ruff_command(
        [
            'format',
            '.',
        ],
        include_base_args=False,
    )


def lint():
    run_ruff_command(
        [
            'check',
            '.',
            '--fix',
        ],
        include_base_args=True,
    )


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'format':
            format()
        elif sys.argv[1] == 'lint':
            lint()
