"""Create the initial takt schema on MariaDB.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create every takt table and index."""
    op.create_table(
        'takt_suite',
        sa.Column('hash', sa.CHAR(64), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('format_version', sa.String(16), nullable=False),
        sa.Column('source', sa.String(16), nullable=False),
        sa.Column('result_date', mysql.DATETIME(fsp=6), nullable=True),
        sa.Column('loaded_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.PrimaryKeyConstraint('hash', name='pk_takt_suite'),
        mariadb_engine='InnoDB',
        mariadb_charset='utf8mb4',
    )
    op.create_table(
        'takt_benchmark',
        sa.Column('suite_hash', sa.CHAR(64), nullable=False),
        sa.Column(
            'benchmark_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(
            ['suite_hash'],
            ['takt_suite.hash'],
            name='fk_takt_benchmark_suite_hash_takt_suite',
        ),
        sa.PrimaryKeyConstraint(
            'suite_hash',
            'benchmark_position',
            name='pk_takt_benchmark',
        ),
        mariadb_engine='InnoDB',
        mariadb_charset='utf8mb4',
    )
    op.create_table(
        'takt_worker_run',
        sa.Column('suite_hash', sa.CHAR(64), nullable=False),
        sa.Column(
            'benchmark_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column(
            'run_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.ForeignKeyConstraint(
            ['suite_hash', 'benchmark_position'],
            [
                'takt_benchmark.suite_hash',
                'takt_benchmark.benchmark_position',
            ],
            name='fk_takt_worker_run_suite_hash_takt_benchmark',
        ),
        sa.PrimaryKeyConstraint(
            'suite_hash',
            'benchmark_position',
            'run_position',
            name='pk_takt_worker_run',
        ),
        mariadb_engine='InnoDB',
        mariadb_charset='utf8mb4',
    )
    op.create_table(
        'takt_measurement',
        sa.Column('suite_hash', sa.CHAR(64), nullable=False),
        sa.Column(
            'benchmark_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column(
            'run_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column('kind', sa.String(8), nullable=False),
        sa.Column(
            'position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column('loops', sa.Integer(), nullable=True),
        sa.Column('value', sa.Double(), nullable=False),
        sa.ForeignKeyConstraint(
            ['suite_hash', 'benchmark_position', 'run_position'],
            [
                'takt_worker_run.suite_hash',
                'takt_worker_run.benchmark_position',
                'takt_worker_run.run_position',
            ],
            name='fk_takt_measurement_suite_hash_takt_worker_run',
        ),
        sa.PrimaryKeyConstraint(
            'suite_hash',
            'benchmark_position',
            'run_position',
            'kind',
            'position',
            name='pk_takt_measurement',
        ),
        mariadb_engine='InnoDB',
        mariadb_charset='utf8mb4',
    )
    op.create_table(
        'takt_run_metadata',
        sa.Column('suite_hash', sa.CHAR(64), nullable=False),
        sa.Column(
            'benchmark_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column(
            'run_position',
            sa.Integer(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('unit', sa.Text(), nullable=True),
        sa.Column('loops', sa.BigInteger(), nullable=True),
        sa.Column('inner_loops', sa.BigInteger(), nullable=True),
        sa.Column('date', sa.Text(), nullable=True),
        sa.Column('duration', sa.Double(), nullable=True),
        sa.Column('timer', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('calibrate_loops', sa.BigInteger(), nullable=True),
        sa.Column('recalibrate_loops', sa.BigInteger(), nullable=True),
        sa.Column('calibrate_warmups', sa.BigInteger(), nullable=True),
        sa.Column('recalibrate_warmups', sa.BigInteger(), nullable=True),
        sa.Column('python_version', sa.Text(), nullable=True),
        sa.Column('python_implementation', sa.Text(), nullable=True),
        sa.Column('python_executable', sa.Text(), nullable=True),
        sa.Column('python_compiler', sa.Text(), nullable=True),
        sa.Column('python_cflags', sa.Text(), nullable=True),
        sa.Column('python_config_args', sa.Text(), nullable=True),
        sa.Column('python_hash_seed', sa.Text(), nullable=True),
        sa.Column('python_gc', sa.Text(), nullable=True),
        sa.Column('mem_max_rss', sa.BigInteger(), nullable=True),
        sa.Column('command_max_rss', sa.BigInteger(), nullable=True),
        sa.Column('mem_peak_pagefile_usage', sa.BigInteger(), nullable=True),
        sa.Column('cpu_count', sa.BigInteger(), nullable=True),
        sa.Column('cpu_affinity', sa.Text(), nullable=True),
        sa.Column('cpu_config', sa.Text(), nullable=True),
        sa.Column('cpu_freq', sa.Text(), nullable=True),
        sa.Column('cpu_machine', sa.Text(), nullable=True),
        sa.Column('cpu_model_name', sa.Text(), nullable=True),
        sa.Column('cpu_temp', sa.Text(), nullable=True),
        sa.Column('aslr', sa.Text(), nullable=True),
        sa.Column('hostname', sa.Text(), nullable=True),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('boot_time', sa.Text(), nullable=True),
        sa.Column('uptime', sa.Double(), nullable=True),
        sa.Column('load_avg_1min', sa.Double(), nullable=True),
        sa.Column('runnable_threads', sa.BigInteger(), nullable=True),
        sa.Column('perf_version', sa.Text(), nullable=True),
        sa.Column('performance_version', sa.Text(), nullable=True),
        sa.Column('timeit_stmt', sa.Text(), nullable=True),
        sa.Column('timeit_setup', sa.Text(), nullable=True),
        sa.Column('timeit_teardown', sa.Text(), nullable=True),
        sa.Column('timeit_duplicate', sa.BigInteger(), nullable=True),
        sa.Column('commit_id', sa.Text(), nullable=True),
        sa.Column('commit_branch', sa.Text(), nullable=True),
        sa.Column('commit_date', sa.Text(), nullable=True),
        sa.Column('patch_file', sa.Text(), nullable=True),
        sa.Column('hooks', sa.Text(), nullable=True),
        sa.Column('custom', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ['suite_hash', 'benchmark_position', 'run_position'],
            [
                'takt_worker_run.suite_hash',
                'takt_worker_run.benchmark_position',
                'takt_worker_run.run_position',
            ],
            name='fk_takt_run_metadata_suite_hash_takt_worker_run',
        ),
        sa.PrimaryKeyConstraint(
            'suite_hash',
            'benchmark_position',
            'run_position',
            name='pk_takt_run_metadata',
        ),
        mariadb_engine='InnoDB',
        mariadb_charset='utf8mb4',
    )
    op.create_table(
        'takt_loaded_hash',
        sa.Column('hash', sa.CHAR(64), nullable=False),
        sa.PrimaryKeyConstraint('hash', name='pk_takt_loaded_hash'),
        mariadb_engine='InnoDB',
        mariadb_charset='utf8mb4',
    )
    op.create_index('ix_takt_suite_name', 'takt_suite', ['name'])
    op.create_index('ix_takt_suite_result_date', 'takt_suite', ['result_date'])


def downgrade() -> None:
    """Drop every takt table and index."""
    op.drop_index('ix_takt_suite_result_date', table_name='takt_suite')
    op.drop_index('ix_takt_suite_name', table_name='takt_suite')
    op.drop_table('takt_loaded_hash')
    op.drop_table('takt_run_metadata')
    op.drop_table('takt_measurement')
    op.drop_table('takt_worker_run')
    op.drop_table('takt_benchmark')
    op.drop_table('takt_suite')
