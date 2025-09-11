from django.core.management.base import BaseCommand
from django.core.management import call_command
import sys


class Command(BaseCommand):
    help = 'Run all tests with detailed output'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Run tests for specific app (e.g., core, users)',
        )
        parser.add_argument(
            '--coverage',
            action='store_true',
            help='Run tests with coverage report',
        )

    def handle(self, *args, **options):
        app = options.get('app')
        coverage = options.get('coverage')
        
        if coverage:
            try:
                import coverage
                cov = coverage.Coverage()
                cov.start()
            except ImportError:
                self.stdout.write(
                    self.style.WARNING('Coverage not installed. Install with: pip install coverage')
                )
                coverage = False
        
        test_args = []
        if app:
            test_args.append(f'{app}.tests')
        
        try:
            call_command('test', *test_args, verbosity=2, interactive=False)
            self.stdout.write(
                self.style.SUCCESS('✅ All tests passed!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Tests failed: {e}')
            )
            sys.exit(1)
        finally:
            if coverage:
                cov.stop()
                cov.save()
                self.stdout.write(
                    self.style.SUCCESS('Coverage report saved to .coverage')
                )
