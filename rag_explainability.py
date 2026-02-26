import random
CURRENCY_SYMBOL = "₹"

class RAGExplainabilityLayer:
    """Retrieval-Augmented Generation layer for deep, human-readable risk explainability."""
    
    def __init__(self, profiler):
        self.profiler = profiler
        self.knowledge_base = {
            "fraud_rules": [
                "Rule 1: Transactions > 3x average spending are flagged as High Amount.",
                "Rule 2: Transactions from unknown locations are flagged as New Location.",
                "Rule 3: Multiple transactions within 60 seconds are flagged as High Frequency."
            ],
            "risk_thresholds": {
                "HIGH": "Risk score > 85. Immediate block enforced.",
                "MEDIUM": "Risk score 60-85. Verification required.",
                "LOW": "Risk score < 60. Standard approval."
            },
            "category_definitions": {
                "groceries": "Essential food and household items.",
                "travel": "Commuting, flights, and fuel expenses.",
                "entertainment": "Movies, streaming services, and leisure.",
                "shopping": "Retail purchases and e-commerce.",
                "crypto": "Highly volatile digital asset transactions.",
                "utilities": "Bills, electricity, and telecommunications."
            },
            "saving_tips": [
                "Limit entertainment spending to 10% of your monthly average.",
                "Monitor groceries for sudden spikes in bulk purchases.",
                "Utility bills can be optimized by reviewing subscription services."
            ]
        }
        self.embeddings_log = [] # Simulated embedding store (query, context)

    def _semantic_retrieve(self, query):
        """Simulates vector retrieval using keyword matching from the internal knowledge base."""
        q = query.lower()
        results = []
        
        # Search fraud rules
        if "rule" in q or "flag" in q or "why" in q:
            results.extend(self.knowledge_base["fraud_rules"])
        
        # Search thresholds
        if "threshold" in q or "score" in q or "level" in q:
            results.append(f"Standard Thresholds: {self.knowledge_base['risk_thresholds']}")
            
        # Search categories
        for cat, desc in self.knowledge_base["category_definitions"].items():
            if cat in q:
                results.append(f"{cat.capitalize()}: {desc}")
                
        # Search tips
        if "tip" in q or "save" in q or "budget" in q:
            results.extend(self.knowledge_base["saving_tips"])
            
        # Log embedding simulation
        self.embeddings_log.append({"query": query, "matches": len(results)})
        return results

    def _redact_pii(self, text):
        """Redacts PII like specific user IDs or exact amounts if needed for external logs, 
        though here we focus on masking user_id for the LLM simulation."""
        if not text: return text
        # Simple replacement for demonstration
        import re
        # Mask User IDs like U1, U2...
        return re.sub(r'U\d+', '[USER_ID_REDACTED]', text)

    def explain_transaction(self, transaction, question, current_analysis, user_profile=None):
        """Retrieves an evidence bundle, redacts PII, and generates a grounded explanation."""
        
        user_id = transaction.get("user_id")
        
        # 1. Retrieval Phase (Evidence Bundle)
        if user_profile is None:
            profile = self.profiler.get_serializable_profile(user_id)
        else:
            profile = user_profile

        # EVIDENCE BUNDLE: Grounding data for the explanation
        bundle = {
            "avg_spending": profile.get("average_spending", 0),
            "total_transactions": profile.get("total_transactions", 0),
            "location_history": profile.get("location_history", []),
            "current_location": transaction.get("location", "Unknown"),
            "current_amount": transaction.get("amount", 0),
            "triggered_reasons": current_analysis.get("reasons", []),
            "risk_score": current_analysis.get("final_risk_score", 0),
            "adaptive_factor": profile.get("adaptive_weight_factor", 1.0),
            "current_analysis": current_analysis
        }
        
        # 2. Redaction Layer (Internal Step)
        # In a real LLM call, we'd redact bundle values or the resulting prompt
        
        # 3. Grounded Explanation Generation
        explanation, evidence_list = self._generate_grounded_explanation(bundle)
        
        # 4. Structured Output
        insight_block = f"AI ANALYST INSIGHT:\n{explanation}"
        evidence_block = "SUPPORTING EVIDENCE:\n" + ("\n".join([f"• {e}" for e in evidence_list]) if evidence_list else "• Consistent with global safety baseline.")
        rules_block = "TRIGGERED RULES:\n" + ("\n".join([f"• {r}" for r in bundle['triggered_reasons']]) if bundle['triggered_reasons'] else "• Behavioral check passed.")

        return {
            "explanation": explanation,
            "supporting_evidence": evidence_list,
            "full_response": f"{insight_block}\n\n{evidence_block}\n\n{rules_block}",
            "evidence_bundle": bundle # For audit logs
        }

    def _generate_grounded_explanation(self, bundle):
        """Generates a clear, evidence-grounded explanation using structured metrics."""
        analysis = bundle.get("current_analysis", {})
        breakdown = analysis.get("risk_breakdown", {})
        tag = analysis.get("primary_tag", "Behavioral Drift")
        counterfactual = analysis.get("counterfactual", "")
        
        reasons = bundle["triggered_reasons"]
        avg = bundle["avg_spending"]
        curr_amt = bundle["current_amount"]
        
        narrative = f"This transaction has been flagged as '{tag}' due to several high-precision signals. "
        evidence = []

        # Structured Reasoning using breakdown
        if breakdown.get("amount_deviation", 0) > 30:
            multiplier = round(curr_amt / avg, 1) if avg > 0 else 1.0
            detail = f"The amount ({CURRENCY_SYMBOL}{curr_amt}) is a {multiplier}x deviation from your historical baseline of {CURRENCY_SYMBOL}{round(avg, 2)}."
            narrative += f"{detail} "
            evidence.append(detail)
            
        if breakdown.get("velocity_spike", 0) > 30:
            detail = "We detected a sudden surge in transaction frequency, suggesting automated or hurried activity."
            narrative += f"{detail} "
            evidence.append(detail)
            
        if breakdown.get("balance_drain", 0) > 30:
            detail = "Transfer patterns indicate an attempt to rapidly deplete account funds within a narrow time window."
            narrative += f"{detail} "
            evidence.append(detail)

        if counterfactual:
            narrative += f"\n💡 **Counterfactual Analysis**: {counterfactual}"

        return narrative.strip(), evidence

    def chat_analysis(self, query, user_id, transaction=None, user_profile=None):
        """Performs dynamic conversational RAG analysis based on a user query."""
        if user_profile is None:
            profile = self.profiler.get_serializable_profile(user_id)
        else:
            profile = user_profile

        # Retrieve deep context
        avg = profile.get("average_spending", 0)
        locations = profile.get("location_history", [])
        risk_hist = profile.get("risk_history", [])
        adaptive = profile.get("adaptive_weight_factor", 1.0)
        category_spend = profile.get("category_spending", {})
        
        # DEBUG LOGS
        print(f"DEBUG - Chat Analysis for {user_id}")
        print(f"DEBUG - Snapshot Amount: {transaction.get('amount') if transaction else 'N/A'}")
        
        # Build analytical response based on structured intent detection
        q = query.lower()
        response = ""
        
        # 1. INTENT: SPECIFIC SNAPSHOT ANALYSIS
        if ("why" in q or "flagged" in q or "reason" in q) and transaction:
            analysis = transaction.get("analysis", {})
            reasons = analysis.get("reasons", [])
            risk_score = analysis.get("final_risk_score", 0)
            response = f"This transaction ({CURRENCY_SYMBOL}{transaction['amount']} at {transaction['merchant']}) was flagged with a risk score of {risk_score}. "
            if reasons:
                response += "Main triggers: " + ", ".join(reasons) + ". "
            else:
                response += "It was flagged due to overall behavioral deviation. "
            if adaptive > 1.2:
                response += f"Your current sensitivity factor is {round(adaptive,2)}, making the system more cautious."

        # 2. INTENT: LAST HIGH TRANSACTION
        elif "high" in q and "last" in q:
            high_txns = sorted([r for r in risk_hist if r.get('amount')], key=lambda x: x['amount'], reverse=True)
            if high_txns:
                top = high_txns[0]
                response = f"Your highest recent risk-monitored transaction was {CURRENCY_SYMBOL}{top['amount']} at {top['merchant']} on {top['timestamp']}. It had a risk score of {top['score']}."
            else:
                response = "I don't have enough history to identify a significantly 'high' transaction yet."

        # 3. INTENT: RISK HISTORY
        elif "risk" in q and "history" in q:
            if risk_hist:
                scores = [r['score'] for r in risk_hist[-5:]]
                avg_risk = sum(scores) / len(scores)
                response = f"In your last {len(scores)} transactions, the average risk score was {round(avg_risk, 1)}. Recent scores: {', '.join(map(str, scores))}."
            else:
                response = "Your risk history is currently empty. I'm monitoring new transactions as they arrive."

        # 4. INTENT: LOCATION SAFETY
        elif "location" in q:
            response = f"I am monitoring your activity across {len(locations)} unique locations. "
            if transaction and transaction.get("location") not in locations:
                response += f"The current entry from '{transaction.get('location')}' is a new location, which contributed to its risk rating."
            else:
                response += f"Recent trusted locations include: {', '.join(locations[-3:])}."

        # 5. INTENT: AVERAGE SPENDING
        elif "average" in q:
            response = f"Your normal spending average is currently {CURRENCY_SYMBOL}{avg} per transaction based on {profile.get('total_transactions', 0)} events."

        # 6. INTENT: CATEGORY SPENDING (New)
        elif any(cat in q for cat in ["groceries", "travel", "entertainment", "shopping", "crypto", "utilities", "spend"]):
            found_cats = [cat for cat in category_spend if cat in q]
            if found_cats:
                total = sum(category_spend[cat] for cat in found_cats)
                response = f"You have spent a total of {CURRENCY_SYMBOL}{round(total, 2)} on {', '.join(found_cats)} this month. "
                # Add a tip from RAG
                tips = self._semantic_retrieve("tips")
                if tips:
                    response += f"Tip: {random.choice(tips)}"
            else:
                total_all = sum(category_spend.values())
                response = f"Your total recorded spending across all categories is {CURRENCY_SYMBOL}{round(total_all, 2)}. "
                if category_spend:
                    top_cat = max(category_spend, key=category_spend.get)
                    response += f"Your highest expense category is '{top_cat}' at {CURRENCY_SYMBOL}{round(category_spend[top_cat], 2)}."

        # 7. INTENT: KNOWLEDGE BASE QUERY (New)
        elif any(k in q for k in ["rule", "threshold", "define", "what is"]):
            kb_matches = self._semantic_retrieve(query)
            if kb_matches:
                response = "According to FinGuard AI's internal knowledge base: " + " ".join(kb_matches)
            else:
                response = "I couldn't find a direct match in my knowledge base, but I can tell you about your risk patterns and spending."

        # 8. DEFAULT (Contextual, no generic fallback)
        else:
            if transaction:
                response = f"I'm analyzing the transaction at {transaction['merchant']} for {CURRENCY_SYMBOL}{transaction['amount']}. It currently has a {transaction.get('analysis', {}).get('risk_level', 'LOW')} risk level. Ask me about why it was flagged or how it compares to your history."
            else:
                response = f"Hello! I'm your FinGuard Finance Analyst. I see you have {len(risk_hist)} events in your history. Your top category is '{max(category_spend, key=category_spend.get) if category_spend else 'N/A'}'. How can I help you today?"

        return {
            "response": f"AI ANALYST INSIGHT:\n{response}",
            "context_snapshot": {
                "avg": avg,
                "location_count": len(locations),
                "adaptive_factor": adaptive,
                "category_count": len(category_spend)
            }
        }
