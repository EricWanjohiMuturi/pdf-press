import json

from django.test import TestCase


class APIDocumentationTests(TestCase):
    def _resolve_schema(self, payload, schema):
        ref = schema.get("$ref")
        if not ref:
            return schema

        # Expected format: #/components/schemas/SchemaName
        parts = ref.strip("#/").split("/")
        resolved = payload
        for part in parts:
            resolved = resolved[part]
        return resolved

    def test_openapi_schema_exposes_compression_paths(self):
        response = self.client.get("/api/schema/?format=json")

        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.content)
        self.assertIn("openapi", payload)

        paths = payload.get("paths", {})
        self.assertIn("/compress/small-pdf", paths)
        self.assertIn("/compress/larger-pdf", paths)

        small_pdf_post = paths["/compress/small-pdf"]["post"]
        small_request = small_pdf_post["requestBody"]["content"]["multipart/form-data"]
        self.assertIn("schema", small_request)
        small_schema = self._resolve_schema(payload, small_request["schema"])
        small_props = small_schema.get("properties", {})
        self.assertIn("file", small_props)
        self.assertEqual(small_props["file"].get("type"), "string")
        self.assertEqual(small_props["file"].get("format"), "binary")

        large_pdf_post = paths["/compress/larger-pdf"]["post"]
        param_names = {param["name"] for param in large_pdf_post.get("parameters", [])}
        self.assertIn("quality", param_names)

        large_request = large_pdf_post["requestBody"]["content"]["multipart/form-data"]
        self.assertIn("schema", large_request)
        large_schema = self._resolve_schema(payload, large_request["schema"])
        large_props = large_schema.get("properties", {})
        self.assertIn("file", large_props)
        self.assertEqual(large_props["file"].get("type"), "string")
        self.assertEqual(large_props["file"].get("format"), "binary")

    def test_swagger_and_redoc_pages_render(self):
        swagger_response = self.client.get("/api/docs/")
        redoc_response = self.client.get("/api/redoc/")

        self.assertEqual(swagger_response.status_code, 200)
        self.assertEqual(redoc_response.status_code, 200)

        self.assertContains(swagger_response, 'id="swagger-ui"')
        self.assertContains(redoc_response, "<redoc")
