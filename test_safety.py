import unittest
import copy
from fraud_detection_engine import FraudDetectionEngine
from user_profiler import UserProfiler

class TestFinGuardSafety(unittest.TestCase):
    def setUp(self):
        self.engine = FraudDetectionEngine()
        self.profiler = UserProfiler()

    def test_empty_data_handling(self):
        """Rule 1: No KeyErrors on empty/malformed data."""
        empty_txn = {}
        empty_profile = {}
        
        try:
            # Test Engine
            result = self.engine.analyze_transaction(empty_txn, empty_profile)
            self.assertIn("final_risk_score", result)
            self.assertEqual(result["transaction_id"], "Unknown")
            
            # Test Profiler
            profile = self.profiler.update_profile(empty_txn)
            self.assertEqual(profile["user_id"], "Unknown")
            self.assertEqual(profile["average_spending"], 0.0)
            
        except KeyError as e:
            self.fail(f"Safety Breach: KeyError triggered on empty data: {e}")
        except Exception as e:
            self.fail(f"Safety Breach: unexpected error on empty data: {e}")

    def test_simulation_immutability(self):
        """Rule 2: Simulation does not alter real user state."""
        user_id = "U_TEST"
        txn = {"user_id": user_id, "amount": 100, "location": "NY", "merchant": "Shop", "timestamp": "2024-01-01 10:00:00"}
        
        # Initialize real state
        self.profiler.update_profile(txn)
        original_factor = self.profiler.get_serializable_profile(user_id)["adaptive_weight_factor"]
        
        # Perform Simulation (using snapshot)
        snapshot = self.profiler.get_profile_snapshot(user_id)
        # Mock a 'learning' event in the simulation copy
        fake_fb_txn = {"transaction_id": "SIM-1", "location": "Mars", "merchant": "AlienStore"}
        # Note: We don't apply it to the profiler instance directly for 'real' state
        snapshot["adaptive_weight_factor"] = 2.0 
        
        # Verify real state remains unchanged
        real_profile = self.profiler.get_serializable_profile(user_id)
        self.assertEqual(real_profile["adaptive_weight_factor"], original_factor)
        self.assertNotEqual(real_profile["adaptive_weight_factor"], 2.0)

    def test_gradual_adaptive_update_and_caps(self):
        """Rule 3: Gradual sensitivity updates with strict caps (0.7 - 2.0)."""
        user_id = "U1"
        txn = {"user_id": user_id, "amount": 50, "location": "London", "merchant": "Cafe", "transaction_id": "TXN1"}
        
        # 1. Test Multiple LEGITIMATE feedback (Gradual reduction)
        for _ in range(20):
            self.profiler.apply_feedback(user_id, txn, "LEGITIMATE")
        
        final_factor = self.profiler.get_serializable_profile(user_id)["adaptive_weight_factor"]
        self.assertGreaterEqual(final_factor, 0.7, "Adaptive factor dropped below 0.7 cap")
        self.assertLess(final_factor, 1.0, "Adaptive factor did not reduce on legitimate feedback")

        # 2. Test Multiple FRAUD feedback (Gradual increase)
        for _ in range(40):
            self.profiler.apply_feedback(user_id, txn, "FRAUD")
            
        final_factor = self.profiler.get_serializable_profile(user_id)["adaptive_weight_factor"]
        self.assertLessEqual(final_factor, 2.0, "Adaptive factor exceeded 2.0 cap")
        self.assertGreater(final_factor, 1.0, "Adaptive factor did not increase on fraud feedback")

if __name__ == "__main__":
    unittest.main()
