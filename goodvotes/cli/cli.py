import click
from . import goodvotes_cli
from .. import db


@goodvotes_cli.cli.command("create-db")
@click.option("--overwrite", is_flag=True, show_default=True, default=False, help="Overwrite the old database.")
def create_db(overwrite):
    if overwrite:
        print("Dropping data.")
        db.drop_all()

    db.create_all()
    print("Database ready.")
