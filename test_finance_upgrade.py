import unittest
from user_profiler import UserProfiler
from rag_explainability import RAGExplainabilityLayer

class TestFinanceUpgrade(unittest.TestCase):
    def setUp(self):
        self.profiler = UserProfiler()
        self.rag = RAGExplainabilityLayer(self.profiler)

    def test_category_spending(self):
        """Verify category spend accumulates correctly."""
        txn1 = {"user_id": "U1", "amount": 100, "category": "groceries"}
        txn2 = {"user_id": "U1", "amount": 50, "category": "groceries"}
        txn3 = {"user_id": "U1", "amount": 200, "category": "travel"}
        
        self.profiler.update_profile(txn1)
        self.profiler.update_profile(txn2)
        self.profiler.update_profile(txn3)
        
        profile = self.profiler.get_serializable_profile("U1")
        self.assertEqual(profile["category_spending"]["groceries"], 150)
        self.assertEqual(profile["category_spending"]["travel"], 200)

    def test_rag_finance_intents(self):
        """Verify RAG handles spending and rule queries."""
        profile = {
            "user_id": "U1",
            "average_spending": 100,
            "category_spending": {"groceries": 500, "travel": 200},
            "risk_history": []
        }
        
        # Test Spending Intent
        res1 = self.rag.chat_analysis("How much did I spend on groceries?", "U1", user_profile=profile)
        self.assertIn("₹500", res1["response"])
        self.assertIn("groceries", res1["response"])
        
        # Test Knowledge Base Intent
        res2 = self.rag.chat_analysis("What are the fraud rules?", "U1", user_profile=profile)
        self.assertIn("knowledge base", res2["response"].lower())
        self.assertIn("Rule 1", res2["response"])

    def test_embedding_simulation(self):
        """Verify semantic retrieval logs match expected behavior."""
        self.rag._semantic_retrieve("thresholds for risk")
        self.assertEqual(len(self.rag.embeddings_log), 1)
        self.assertGreater(self.rag.embeddings_log[0]["matches"], 0)

if __name__ == "__main__":
    unittest.main()
