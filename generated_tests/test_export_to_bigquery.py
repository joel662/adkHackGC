import unittest
import unittest.mock
from unittest.mock import patch
from google.cloud import bigquery
from export_to_bigquery import row, table_id, errors, client, project_id
from datetime import datetime, timezone
import os


class TestExportToBigQuery(unittest.TestCase):

    @patch('export_to_bigquery.bigquery.Client')
    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_insert_rows_json_success(self, mock_bigquery_client):
        mock_client_instance = mock_bigquery_client.return_value
        mock_client_instance.insert_rows_json.return_value = []  # Simulate success
        from export_to_bigquery import row, table_id

        with unittest.mock.patch('builtins.print') as mock_print:
            from export_to_bigquery import errors
            self.assertEqual(errors, [])
            mock_print.assert_called_with("✅ Logged CI event to BigQuery.")


    @patch('export_to_bigquery.bigquery.Client')
    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_insert_rows_json_failure(self, mock_bigquery_client):
        mock_client_instance = mock_bigquery_client.return_value
        mock_client_instance.insert_rows_json.return_value = ["error"]  # Simulate failure
        from export_to_bigquery import row, table_id

        with unittest.mock.patch('builtins.print') as mock_print:
            from export_to_bigquery import errors
            self.assertEqual(errors, ["error"])
            mock_print.assert_called_with("❌ BigQuery insert failed:", ["error"])


    def test_row_data(self):
        self.assertIsInstance(row, dict)
        self.assertEqual(row["file_path"], "CI Pipeline")
        self.assertEqual(row["language"], "n/a")
        self.assertEqual(row["test_output"], "CI completed without test execution.")
        self.assertEqual(row["deps"], "none")
        self.assertEqual(row["review_summary"], "{}")
        self.assertIsInstance(datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")), datetime) # Ensure timestamp is valid format


    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_table_id_format(self):
        self.assertEqual(table_id, "test-project.devops_logs.test_results")


    def test_project_id_retrieval(self):
        self.assertEqual(project_id, os.getenv("GOOGLE_CLOUD_PROJECT"))