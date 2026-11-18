from src.faq_suggestions import FaqSuggestion, MaintenanceRequest, choose_faq


def main() -> None:
    request = MaintenanceRequest(unit="B-204", summary="The bathroom tap is dripping.")
    suggestions = [FaqSuggestion("How do I report a leak?", "Use the maintenance form.", 0.91)]
    selected = choose_faq(suggestions)
    print({"request": request.summary, "suggestion": selected.question if selected else None})


if __name__ == "__main__":
    main()
