class AlertManager:
    """Manages storage and retrieval of high-risk transaction alerts."""
    
    def __init__(self, risk_threshold=60):
        self.risk_threshold = risk_threshold
        self.alerts = []

    def process_transaction_analysis(self, analysis_result):
        """Checks if a transaction is high-risk and saves it if necessary."""
        if analysis_result.get("risk_score", 0) > self.risk_threshold:
            self.alerts.append(analysis_result)
            return True
        return False

    def get_alerts(self):
        """Returns the list of all captured high-risk alerts."""
        return self.alerts

    def clear_alerts(self):
        """Clears the captured alerts list."""
        self.alerts = []
