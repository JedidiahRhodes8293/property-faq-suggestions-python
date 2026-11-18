from src.faq_suggestions import FaqSuggestion, choose_faq


def test_low_relevance_does_not_show_an_unrelated_answer() -> None:
    suggestions = [FaqSuggestion("How do I renew a lease?", "Contact leasing.", 0.61)]

    assert choose_faq(suggestions) is None


def test_best_relevant_answer_is_shown() -> None:
    suggestions = [
        FaqSuggestion("How do I renew a lease?", "Contact leasing.", 0.81),
        FaqSuggestion("How do I report a leak?", "Use maintenance.", 0.93),
    ]

    assert choose_faq(suggestions).question == "How do I report a leak?"
