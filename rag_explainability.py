class RAGExplainabilityLayer:
    """Retrieval-Augmented Generation layer for deep risk explainability."""
    
    def __init__(self, profiler):
        self.profiler = profiler

    def explain_transaction(self, transaction, question, current_analysis):
        """Retrieves context, builds a prompt, and generates a detailed explanation."""
        
        user_id = transaction["user_id"]
        # 1. Retrieval Phase
        profile = self.profiler.get_serializable_profile(user_id)
        history = profile.get("risk_history", [])[-10:] # Retrieve more for RAG
        avg_spending = profile.get("average_spending", 0)
        
        # 2. Context Building (for the LLM Prompt)
        context_str = self._build_llm_context(history, avg_spending, current_analysis)
        
        # 3. Prompt Generation
        prompt = self._generate_prompt(question, context_str)
        
        # 4. Simulated LLM Generation
        explanation, evidence = self._simulate_llm_response(transaction, current_analysis, profile)
        
        return {
            "prompt": prompt,
            "explanation": explanation,
            "supporting_evidence": evidence
        }

    def _build_llm_context(self, history, avg, analysis):
        """Constructs a structured text block for the LLM."""
        history_summary = "\n".join([f"- {h['timestamp']}: Score {h['score']}" for h in history])
        rules = "\n".join([f"- {r}" for r in analysis.get("reasons", [])])
        
        return f"""
        USER PROFILE DATA:
        - Average Spending: ${avg}
        - Risk Trend: {analysis.get('risk_trend', 'Unknown')}
        - Current Health Status: {analysis.get('health_score', 'Unknown')}
        
        RECENT RISK HISTORY:
        {history_summary}
        
        TRIGGERED FRAUD RULES:
        {rules}
        """

    def _generate_prompt(self, question, context):
        """Creates the final prompt for the LLM."""
        return f"""
        You are a financial risk analyst AI. 
        User Question: "{question}"
        
        Using the following context data:
        {context}
        
        Explain clearly why this transaction was flagged.
        Use simple English.
        Be precise and professional.
        Include a list of specific evidence points.
        """

    def _simulate_llm_response(self, transaction, analysis, profile):
        """Simulates an enterprise-grade LLM response with precise multipliers."""
        reasons = analysis.get("reasons", [])
        avg = profile.get("average_spending", 0)
        txn_amount = transaction.get("amount", 0)
        trend = analysis.get("risk_trend")
        
        if not reasons:
            return "Transaction parameters align with verified historical patterns. No further action required.", []

        # Calculate exact multiplier
        multiplier = round(txn_amount / avg, 1) if avg > 0 else 0
        multiplier_str = f"{multiplier}x"
        
        # Action-oriented narrative (Strictly 3-4 sentences)
        narrative = f"Action Required: High-risk anomaly detected due to significant behavioral deviation. "
        if any("amount" in r.lower() for r in reasons):
            narrative += f"The transaction amount is {multiplier_str} higher than the normal average of ${avg}. "
        
        if any("location" in r.lower() for r in reasons):
            location = transaction.get('location', 'Unknown')
            narrative += f"Origin at an unrecognized location ({location}) further compromises the risk profile. "
            
        narrative += f"Given the {trend} trend, initiate immediate secondary verification to secure the account."
        
        # Evidence extraction (Exact numbers)
        evidence = []
        for r in reasons:
            if "average" in r.lower():
                evidence.append(f"Spending deviation identified: Transaction volume is {multiplier_str} higher than historical baseline (${avg}).")
            if "location" in r.lower():
                evidence.append(f"Geographic Anomaly: Entry point ({transaction.get('location')}) has no recorded history for this user.")
            if "frequency" in r.lower():
                evidence.append("Velocity Trigger: Multiple high-frequency transactions detected within a 60-second window.")
        
        return narrative.strip(), evidence
