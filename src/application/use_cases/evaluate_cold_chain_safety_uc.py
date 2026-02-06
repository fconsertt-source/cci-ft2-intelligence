from src.application.dtos.evaluate_cold_chain_safety_request import EvaluateColdChainSafetyRequest
from src.application.use_cases.evaluate_cold_chain_safety_use_case import EvaluateColdChainSafetyUseCase

class EvaluateColdChainSafetyUC:
    def __init__(self, reader, repo=None):
        self.reader = reader
        self.repo = repo

    def execute(self):
        vaccines = self.reader.get_vaccines() if hasattr(self.reader, 'get_vaccines') else ()
        readings = self.reader.read_all()
        request = EvaluateColdChainSafetyRequest(
            vaccines=vaccines,
            readings=readings
        )
        return EvaluateColdChainSafetyUseCase().execute(request)