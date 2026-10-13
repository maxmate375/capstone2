from src.tools.feedback_store import FeedbackStore


def test_feedback_is_persisted(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")

    feedback_id = store.save("session-1", "A question?", -1, "Please cite the source.")

    assert feedback_id > 0
    connection = store._connect()
    try:
        row = connection.execute(
            "SELECT session_id, query, rating, correction FROM feedback WHERE id = ?",
            (feedback_id,),
        ).fetchone()
    finally:
        connection.close()
    assert row == ("session-1", "A question?", -1, "Please cite the source.")
