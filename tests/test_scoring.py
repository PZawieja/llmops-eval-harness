from harness import scoring


def test_fact_found_plain_number():
    assert scoring.fact_found("800.00", "Acme's MRR jumped from $800 to $2,400.")


def test_fact_found_dollar_and_decimal_tolerance():
    assert scoring.fact_found("800", "the MRR was $800.00 before the upgrade")
    assert scoring.fact_found("2400.00", "MRR rose to $2,400 in April")


def test_fact_found_string_case_insensitive():
    assert scoring.fact_found("plan_upgrade", "Event E001 was a Plan_Upgrade.")


def test_fact_not_found():
    assert not scoring.fact_found("contraction_mrr", "this event was a plan upgrade")


def test_split_expected_answer():
    assert scoring.split_expected_answer("customer_id, month_date, mrr_amount.") == [
        "customer_id",
        "month_date",
        "mrr_amount",
    ]


def test_score_question_lookup_full_match():
    question = {
        "tier": "lookup",
        "expected_answer": "customer_id, month_date, mrr_amount.",
    }
    answer = "The model has customer_id, month_date, and mrr_amount columns."
    result = scoring.score_question(question, answer)
    assert result["score"] == 1.0
    assert result["passed"] is True


def test_score_question_investigation_partial_match():
    question = {
        "tier": "investigation",
        "expected_data": {
            "mar_mrr": 800.00,
            "apr_mrr": 2400.00,
            "event_id": "E001",
        },
    }
    answer = "MRR moved from $800 to $2,400 in April."  # no event_id mentioned
    result = scoring.score_question(question, answer)
    assert result["facts_found"] == 2
    assert result["facts_total"] == 3
    assert result["score"] == 2 / 3
    assert result["passed"] is False


def test_score_unanswerable_passes_on_decline_without_fabrication():
    answer = "This data isn't tracked here -- there's no pipeline model in this project."
    result = scoring.score_unanswerable(answer)
    assert result["passed"] is True


def test_score_unanswerable_fails_on_fabricated_figure():
    answer = "The open pipeline value is doesn't track but estimated at $50,000."
    result = scoring.score_unanswerable(answer)
    assert result["fabricated_figure_detected"] is True
    assert result["passed"] is False


def test_score_unanswerable_fails_without_decline():
    answer = "Acme Co's account is owned by Jane Smith."
    result = scoring.score_unanswerable(answer)
    assert result["passed"] is False
