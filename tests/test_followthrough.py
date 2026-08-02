from seven import config
from seven.agent.loop import Seven


def test_detects_action_promises_without_treating_capabilities_as_promises():
    assert Seven._promises_unexecuted_action(
        "I'll run Black now and report back."
    )
    assert Seven._promises_unexecuted_action(
        "Let me execute this command now."
    )
    assert Seven._promises_unexecuted_action(
        "I'll use the shell tool to check it."
    )
    assert Seven._promises_unexecuted_action(
        "Sure, let's open the calculator."
    )
    assert not Seven._promises_unexecuted_action(
        "I can run commands and inspect files when you ask."
    )
    assert not Seven._promises_unexecuted_action(
        "Black was not executed; there is no audit result."
    )


def test_appends_concise_verified_tool_outcomes():
    response = Seven._append_action_feedback(
        "I checked both commands.",
        [
            ("list_dir", '{"ok": true, "count": 2}'),
            ("run_shell", "ERROR: exit_code=1\nmissing executable"),
        ],
    )

    assert "Verified action results:" in response
    assert "list_dir: completed" in response
    assert "run_shell: failed" in response
    assert "missing executable" not in response


def test_work_status_reports_black_was_never_run(monkeypatch):
    class Memory:
        @staticmethod
        def recent_audit(_limit):
            return [
                {
                    "id": 33,
                    "tool": "run_shell",
                    "arguments": "autopep8 --in-place files.py",
                    "result_preview": "ERROR: autopep8 is not recognized",
                    "ok": 0,
                    "created_at": "2026-07-29T22:47:11+00:00",
                }
            ]

        @staticmethod
        def active_goals():
            return []

        @staticmethod
        def active_plans():
            return []

    monkeypatch.setattr(config, "BACKGROUND_LLM", False)
    agent = Seven.__new__(Seven)
    agent.memory = Memory()

    response = agent._format_work_status("Did Black work?")

    assert "Black was never executed" in response
    assert "autopep8 attempt failed" in response


def test_work_status_query_detection_is_specific():
    assert Seven._conversation_work_status("what are you busy with exactly?")
    assert Seven._conversation_work_status("interesting, did black work?")
    assert Seven._conversation_work_status("what have you been up to?")
    assert not Seven._conversation_work_status("how high is an elephant?")


def test_imperative_application_launch_is_tool_first_and_narrow():
    assert Seven._conversation_application_launch("open calculator") == "calculator"
    assert Seven._conversation_application_launch("Seven, please launch Notepad") == "Notepad"
    assert Seven._conversation_application_launch("could you start paint please?") == "paint"
    assert Seven._conversation_application_launch("open https://example.com") is None
    assert Seven._conversation_application_launch("open file report.docx") is None


def test_freewill_reports_failed_work_without_claiming_progress():
    from seven.mind.freewill import FreeWill

    freewill = FreeWill.__new__(FreeWill)

    response = freewill._summarize_work_for_voice(
        "Plan #1 step 1 — no successful outcome evidence; "
        "unchanged (failed_tools=1)."
    )

    assert response == "I'm stuck on a plan; say cancel plan if you want me to stop."
