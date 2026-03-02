# ... (前面保持不變) ...

    def detect(self, data: np.ndarray, 
               domain: str = 'general',
               context: Optional[Dict] = None) -> ContaminationReport:
        
        # ... (前面的計算不變) ...
        
        # 修正污染等級計算
        if missing_ratio == 0 and outlier_ratio == 0 and noise_ratio == 0 and duplicate_ratio == 0:
            level = ContaminationLevel.PRISTINE
        else:
            total_pollution = (missing_ratio + outlier_ratio + 
                              noise_ratio + duplicate_ratio) / 4
            
            if total_pollution < 0.05:
                level = ContaminationLevel.LIGHT
            elif total_pollution < 0.15:
                level = ContaminationLevel.MODERATE
            elif total_pollution < 0.30:
                level = ContaminationLevel.HEAVY
            elif total_pollution < 0.50:
                level = ContaminationLevel.CRITICAL
            else:
                level = ContaminationLevel.TOXIC
        
        # ... (後續不變) ...
