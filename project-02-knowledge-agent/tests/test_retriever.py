import unittest

from retriever import (
    format_context,
    get_knowledge_collection,
    retrieve_knowledge,
)


class TestKnowledgeRetriever(unittest.TestCase):
    def test_collection_contains_chunks(self):
        collection = get_knowledge_collection()

        self.assertGreater(collection.count(), 0)

    def test_dp_capacity_question_retrieves_installation_sop(self):
        results = retrieve_knowledge(
            "What should happen when all DP ports are occupied?",
            top_k=4,
        )

        self.assertEqual(len(results), 4)
        self.assertEqual(
            results[0].source,
            "installation_sop.md",
        )
        self.assertIn(
            "DP Port Capacity",
            results[0].content,
        )

    def test_signal_question_retrieves_fiber_document(self):
        results = retrieve_knowledge(
            "What should be checked when the ONU has a red LOS light?",
            top_k=4,
        )

        retrieved_sources = {
            result.source for result in results
        }

        self.assertIn(
            "fiber_troubleshooting.md",
            retrieved_sources,
        )

    def test_top_k_limits_result_count(self):
        results = retrieve_knowledge(
            "What are the installation signal requirements?",
            top_k=2,
        )

        self.assertEqual(len(results), 2)

    def test_empty_question_is_rejected(self):
        with self.assertRaises(ValueError):
            retrieve_knowledge("")

    def test_invalid_top_k_is_rejected(self):
        with self.assertRaises(ValueError):
            retrieve_knowledge(
                "Test question",
                top_k=0,
            )

    def test_context_formatter_includes_source(self):
        results = retrieve_knowledge(
            "How is available DP capacity calculated?",
            top_k=1,
        )

        context = format_context(results)

        self.assertIn("Document:", context)
        self.assertIn("installation_sop.md", context)
        self.assertIn(results[0].content, context)


if __name__ == "__main__":
    unittest.main()