import os, unittest
import psycopg2

from app.db import get_connection


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE") == "1", "requires isolated WYE_TEST_DATABASE migrated to 0005")
class LabelExtractionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.conn=get_connection(); self.conn.autocommit=False; self.cur=self.conn.cursor()
    def tearDown(self):
        self.conn.rollback(); self.cur.close(); self.conn.close()

    def test_0005_columns_and_status_constraints(self):
        self.cur.execute("""SELECT column_name FROM information_schema.columns
            WHERE table_name='label_extraction_runs'""")
        columns={row[0] for row in self.cur.fetchall()}
        self.assertTrue({"extracted_raw_text","error_code","provider_request_id","schema_version","prompt_hash",
                         "idempotency_key","request_fingerprint","started_at","completed_at"}.issubset(columns))
        self.cur.execute("SELECT document_type FROM product_label_documents LIMIT 0")

    def test_document_type_must_match_supported_image_type(self):
        self.cur.execute("INSERT INTO products(product_name,category,source) VALUES('phase4','food','manual') RETURNING id")
        product=self.cur.fetchone()[0]
        self.cur.execute("""INSERT INTO storage_objects(storage_provider,bucket,object_key)
            VALUES('test','phase4','object') RETURNING id""")
        storage=self.cur.fetchone()[0]
        self.cur.execute("""INSERT INTO product_images(product_id,image_type,storage_object_id,mime_type,checksum,source)
            VALUES(%s,'ingredients',%s,'image/jpeg',%s,'user_submission') RETURNING id""",(product,storage,'a'*64))
        image=self.cur.fetchone()[0]
        self.cur.execute("SAVEPOINT mismatch")
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.cur.execute("""INSERT INTO product_label_documents(product_image_id,source_type,document_type)
                VALUES(%s,'image_derived','nutrition')""",(image,))
        self.cur.execute("ROLLBACK TO SAVEPOINT mismatch")
        self.cur.execute("""INSERT INTO product_label_documents(product_image_id,source_type,document_type)
            VALUES(%s,'image_derived','ingredients') RETURNING id""",(image,))
        self.assertIsNotNone(self.cur.fetchone()[0])


if __name__ == "__main__": unittest.main()
