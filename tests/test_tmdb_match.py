from src.tmdb_match import build_search_variants, normalize_title


def test_build_search_variants_tries_english_half_for_german_then_english_title():
    normalized = normalize_title("Der Astronaut - Project Hail Mary")

    assert build_search_variants(normalized) == [
        "Der Astronaut - Project Hail Mary",
        "Project Hail Mary",
    ]


def test_build_search_variants_keeps_english_half_for_english_then_german_title():
    normalized = normalize_title("The Housemaid - Wenn sie wüsste")

    assert build_search_variants(normalized) == [
        "The Housemaid - Wenn sie wüsste",
        "The Housemaid",
    ]
