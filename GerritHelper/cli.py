import click


@click.command()
@click.option('--as-cowboy', '-c', is_flag=True, help='Greet as a cowboy.')
@click.argument('operation', default='world', required=False)
def main(operation, as_cowboy):
    """My Tool does one thing, and one thing well."""
    greet = 'Howdy' if as_cowboy else 'Hello'
    click.echo('{0}, {1}.'.format(greet, operation))


if __name__ == '__main__':
    main()