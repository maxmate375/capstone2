from streamlit.testing.v1 import AppTest

from src.config import PROJECT_ROOT


def test_streamlit_renders_profile_form_suggested_questions_and_chat():
    app = AppTest.from_file(str(PROJECT_ROOT / "main.py")).run(timeout=30)

    assert not app.exception
    assert any(button.label == "Use this profile" for button in app.button)
    assert len(app.number_input) == 2
    assert len(app.chat_input) == 1
    assert len(app.button) >= 5
