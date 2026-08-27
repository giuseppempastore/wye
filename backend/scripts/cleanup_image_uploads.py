"""Abandon expired unfinished uploads; only staging objects are deleted."""
from app.db import get_connection
from app.storage import StorageSettings, get_storage_adapter
def cleanup(limit=100):
    settings=StorageSettings.from_env(); adapter=get_storage_adapter(settings); conn=get_connection(); keys=[]
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id,staging_object_key FROM product_image_uploads WHERE status IN ('initiated','verifying') AND expires_at<NOW() ORDER BY expires_at FOR UPDATE SKIP LOCKED LIMIT %s",(limit,))
            for upload_id,key in cur.fetchall(): cur.execute("UPDATE product_image_uploads SET status='abandoned',updated_at=NOW() WHERE id=%s",(str(upload_id),)); keys.append(key)
        conn.commit()
    except: conn.rollback(); raise
    finally: conn.close()
    for key in keys:
        try: adapter.delete_object(key)
        except Exception: pass
    return len(keys)
if __name__=="__main__": print(f"abandoned={cleanup()}")
