import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('manager', Path(__file__).parents[1] / 'manager/qnap_app.py')
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_patch = patch.object(manager, 'STATE', str(Path(self.temp.name) / 'settings.json'))
        self.state_patch.start()
        self.client = manager.app.test_client()

    def tearDown(self):
        self.state_patch.stop()
        self.temp.cleanup()

    def test_setup_rejects_cross_origin(self):
        self.assertEqual(self.client.post('/setup', headers={'Origin': 'https://evil.example'}).status_code, 403)

    def test_setup_enforces_password_length(self):
        response = self.client.post('/setup', headers={'Origin': 'http://localhost'}, data={'password': 'short'})
        self.assertEqual(response.status_code, 400)

    def test_setup_persists_credentials_and_requires_auth(self):
        with patch.object(manager, 'deploy'):
            response = self.client.post('/setup', headers={'Origin': 'http://localhost'}, data={
                'password': 'a-long-test-password', 'url': 'http://192.168.1.10:2368', 'port': '2368'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/').status_code, 401)
        self.assertEqual(self.client.get('/backups').status_code, 401)

    def test_rejects_unsafe_urls_and_manager_port(self):
        for url in ('javascript:alert(1)', 'http://user:pass@host', 'http://host/<script>', 'http://host?x=y'):
            with self.assertRaises(ValueError):
                manager.values({'url': url, 'port': '2368'})
        with self.assertRaises(ValueError):
            manager.values({'url': 'http://localhost', 'port': '2380'})

    def test_failed_backup_does_not_pull_or_recreate(self):
        calls = []
        with patch.object(manager, 'load', return_value={}), patch.object(manager, 'run', side_effect=lambda *a, **k: calls.append(a)), patch.object(manager, 'backup', side_effect=RuntimeError('failure')), patch.object(manager, 'deploy') as deploy:
            with self.assertRaises(RuntimeError):
                manager.update()
        self.assertEqual(calls, [('stop', 'ghost-qnap-app'), ('start', 'ghost-qnap-app')])
        deploy.assert_not_called()


if __name__ == '__main__':
    unittest.main()
