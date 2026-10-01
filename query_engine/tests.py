from django.test import TestCase
from .masker import SensitiveDataMasker


class SensitiveDataMaskerTests(TestCase):
    def test_mask_dictionary_sensitive_keys(self):
        data = {
            "id": "usr_12345",
            "username": "john_doe",
            "password": "supersecretpassword123",
            "password_hash": "$2b$12$e0MYzXy...",
            "pass_hash": "a8f92b...",
            "secret_key": "my-token-123",
            "api_key": "sk_live_xyz",
            "nest": {
                "user_password": "nested_secret",
                "normal_field": "visible_data"
            }
        }

        masked = SensitiveDataMasker.mask_data(data)

        self.assertEqual(masked["id"], "usr_12345")
        self.assertEqual(masked["username"], "john_doe")
        self.assertEqual(masked["password"], "********")
        self.assertEqual(masked["password_hash"], "********")
        self.assertEqual(masked["pass_hash"], "********")
        self.assertEqual(masked["secret_key"], "********")
        self.assertEqual(masked["api_key"], "********")
        self.assertEqual(masked["nest"]["user_password"], "********")
        self.assertEqual(masked["nest"]["normal_field"], "visible_data")

    def test_mask_connection_uri(self):
        uri = "mongodb+srv://pramod:1234@cluster0.h9lmv8j.mongodb.net/olaCarsFresh?appName=Cluster0"
        masked_uri = SensitiveDataMasker.mask_connection_uri(uri)
        self.assertEqual(masked_uri, "mongodb+srv://pramod:********@cluster0.h9lmv8j.mongodb.net/olaCarsFresh?appName=Cluster0")

