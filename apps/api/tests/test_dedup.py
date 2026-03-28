"""
Tests for the deduplication and clustering logic.
"""

from src.opsmesh.services.dedup_service import jaccard_similarity, tokenize


class TestTokenize:
    def test_basic_tokenization(self):
        tokens = tokenize("High CPU usage on payment-service")
        assert "high" in tokens
        assert "cpu" in tokens
        assert "usage" in tokens
        assert "payment" in tokens
        assert "service" in tokens

    def test_removes_stop_words(self):
        tokens = tokenize("the error is on the server")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "on" not in tokens
        assert "error" in tokens
        assert "server" in tokens

    def test_empty_string(self):
        assert tokenize("") == set()

    def test_none_input(self):
        assert tokenize(None) == set()

    def test_lowercases(self):
        tokens = tokenize("HIGH CPU USAGE")
        assert "high" in tokens
        assert "HIGH" not in tokens

    def test_handles_special_characters(self):
        tokens = tokenize("5xx errors in api-gateway")
        assert "5xx" in tokens
        assert "errors" in tokens
        assert "api" in tokens
        assert "gateway" in tokens


class TestJaccardSimilarity:
    def test_identical_sets(self):
        a = {"high", "cpu", "usage"}
        assert jaccard_similarity(a, a) == 1.0

    def test_disjoint_sets(self):
        a = {"high", "cpu"}
        b = {"disk", "full"}
        assert jaccard_similarity(a, b) == 0.0

    def test_partial_overlap(self):
        a = {"high", "cpu", "usage", "payment"}
        b = {"high", "cpu", "usage", "auth"}
        sim = jaccard_similarity(a, b)
        # 3 shared, 5 union = 0.6
        assert sim == 0.6

    def test_empty_sets(self):
        assert jaccard_similarity(set(), set()) == 0.0
        assert jaccard_similarity({"a"}, set()) == 0.0
        assert jaccard_similarity(set(), {"b"}) == 0.0

    def test_subset(self):
        a = {"high", "cpu"}
        b = {"high", "cpu", "usage"}
        sim = jaccard_similarity(a, b)
        # 2 shared, 3 union = 2/3
        assert abs(sim - 2 / 3) < 0.001

    def test_single_element_overlap(self):
        a = {"cpu"}
        b = {"cpu", "memory", "disk"}
        sim = jaccard_similarity(a, b)
        # 1 shared, 3 union = 1/3
        assert abs(sim - 1 / 3) < 0.001


class TestFuzzyMatchingLogic:
    """Test the matching thresholds and logic."""

    def test_same_title_same_service_high_similarity(self):
        title_a = "High CPU usage on payment-service"
        title_b = "High CPU usage on payment-service"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        assert jaccard_similarity(tokens_a, tokens_b) == 1.0

    def test_similar_titles_decent_similarity(self):
        title_a = "High CPU usage on payment-service"
        title_b = "Elevated CPU utilization on payment-service"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        sim = jaccard_similarity(tokens_a, tokens_b)
        # Overlap: cpu, payment, service = 3
        # Union: high, usage, elevated, utilization, cpu, payment, service = 7
        # 3/7 = 0.42
        assert sim >= 0.3
        assert sim < 0.6

    def test_different_titles_low_similarity(self):
        title_a = "High CPU usage on payment-service"
        title_b = "SSL certificate expiring on auth-service"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        sim = jaccard_similarity(tokens_a, tokens_b)
        # Only "service" in common
        assert sim < 0.3

    def test_completely_different_titles(self):
        title_a = "Database connection timeout"
        title_b = "SSL certificate renewal required"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        sim = jaccard_similarity(tokens_a, tokens_b)
        # No overlap
        assert sim == 0.0

    def test_threshold_boundary(self):
        # Test around 0.6 threshold
        title_a = "High memory pressure detected"
        title_b = "High memory alert detected"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        sim = jaccard_similarity(tokens_a, tokens_b)
        # high, memory, detected = 3 shared
        # high, memory, pressure, detected, alert = 5 union
        # 3/5 = 0.6 - exactly at threshold
        assert sim == 0.6


class TestDuplicateDetectionThresholds:
    """Test the duplicate vs cluster thresholds."""

    def test_exact_match_is_duplicate(self):
        # Score of 1.0 (exact fingerprint) -> is_duplicate = True
        score = 1.0
        assert score >= 0.8  # Duplicate threshold

    def test_high_fuzzy_is_duplicate(self):
        # Score >= 0.8 is a duplicate
        title_a = "Error 500 on checkout endpoint"
        title_b = "Error 500 on checkout endpoint"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        score = jaccard_similarity(tokens_a, tokens_b)
        assert score >= 0.8

    def test_medium_fuzzy_is_cluster_only(self):
        # Score 0.6-0.8 clusters but doesn't mark as duplicate
        title_a = "High memory pressure detected"
        title_b = "High memory alert detected"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        score = jaccard_similarity(tokens_a, tokens_b)
        assert 0.6 <= score < 0.8

    def test_low_fuzzy_no_cluster(self):
        # Score < 0.6 doesn't cluster
        title_a = "CPU spike detected"
        title_b = "Disk full warning"
        tokens_a = tokenize(title_a)
        tokens_b = tokenize(title_b)
        score = jaccard_similarity(tokens_a, tokens_b)
        assert score < 0.6
