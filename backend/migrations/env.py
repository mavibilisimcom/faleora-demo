from alembic import context
from sqlalchemy import engine_from_config,pool
import os
from schema_registry import metadata
config=context.config
url=os.getenv('DATABASE_URL',config.get_main_option('sqlalchemy.url'))
config.set_main_option('sqlalchemy.url',url)
target_metadata=metadata
def offline():
 context.configure(url=url,target_metadata=target_metadata,literal_binds=True,compare_type=True,render_as_batch=url.startswith('sqlite'))
 with context.begin_transaction():context.run_migrations()
def online():
 eng=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
 with eng.connect() as conn:
  context.configure(connection=conn,target_metadata=target_metadata,compare_type=True,render_as_batch=url.startswith('sqlite'))
  with context.begin_transaction():context.run_migrations()
offline() if context.is_offline_mode() else online()
