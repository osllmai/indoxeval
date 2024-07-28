from typing import List
from loguru import logger
import sys
from .metrics import Faithfulness
from .metrics import AnswerRelevancy
from .metrics import Bias
from .metrics import ContextualRelevancy
from .metrics import GEval
from .metrics import Hallucination
from .metrics import KnowledgeRetention
from .metrics import Toxicity
from .metrics import BertScore
from .metrics import BLEU
from .metrics import Rouge
from .metrics import METEOR
from .metrics import Gruen
# Set up logging
logger.remove()  # Remove the default logger
logger.add(sys.stdout,
           format="<green>{level}</green>: <level>{message}</level>",
           level="INFO")
logger.add(sys.stdout,
           format="<red>{level}</red>: <level>{message}</level>",
           level="ERROR")


class Evaluator:
    """
    The Evaluator class is designed to evaluate various aspects of language model outputs using specified metrics.

    It supports metrics such as Faithfulness, Answer Relevancy, Bias, Contextual Relevancy, GEval, Hallucination,
    Knowledge Retention, Toxicity, BertScore, BLEU, Rouge, and METEOR.
    """

    def __init__(self, model, metrics: List):
        """
        Initializes the Evaluator with a language model and a list of metrics.

        Args:
            model: The language model to be evaluated.
            metrics (List): A list of metric instances to evaluate the model.
        """
        self.model = model
        self.metrics = metrics
        logger.info("Evaluator initialized with model and metrics.")
        self.set_model_for_metrics()

    def set_model_for_metrics(self):
        """
        Sets the language model for each metric that requires it.
        """
        for metric in self.metrics:
            if hasattr(metric, 'set_model'):
                metric.set_model(self.model)
        logger.info("Model set for all metrics.")

    def evaluate(self):
        """
        Evaluates the language model using the provided metrics and returns the results.

        Returns:
            dict: A dictionary containing the evaluation results for each metric.
        """
        results = {}
        for metric in self.metrics:
            metric_name = metric.__class__.__name__
            try:
                logger.info(f"Evaluating metric: {metric_name}")
                if isinstance(metric, Faithfulness):
                    claims = metric.evaluate_claims()
                    truths = metric.evaluate_truths()
                    verdicts = metric.evaluate_verdicts(claims.claims)
                    reason = metric.evaluate_reason(verdicts, truths.truths)
                    results['faithfulness'] = {
                        'claims': claims.claims,
                        'truths': truths.truths,
                        'verdicts': [verdict.__dict__ for verdict in verdicts.verdicts],
                        'reason': reason.reason
                    }
                elif isinstance(metric, AnswerRelevancy):
                    score = metric.measure()
                    results['answer_relevancy'] = {
                        'score': score,
                        'reason': metric.reason,
                        'statements': metric.statements,
                        'verdicts': [verdict.dict() for verdict in metric.verdicts]
                    }
                elif isinstance(metric, Bias):
                    score = metric.measure()
                    results['bias'] = {
                        'score': score,
                        'reason': metric.reason,
                        'opinions': metric.opinions,
                        'verdicts': [verdict.dict() for verdict in metric.verdicts]
                    }
                elif isinstance(metric, ContextualRelevancy):
                    # Set the language model if not already set
                    irrelevancies = metric.get_irrelevancies(metric.query, metric.retrieval_contexts)
                    metric.set_irrelevancies(irrelevancies)
                    verdicts = metric.get_verdicts(metric.query, metric.retrieval_contexts)
                    # Determine the score, e.g., based on the number of relevant contexts
                    score = 1.0 if not irrelevancies else max(0,
                                   1.0 - len(irrelevancies) / len(metric.retrieval_contexts))
                    reason = metric.get_reason(irrelevancies, score)
                    results['contextual_relevancy'] = {
                        'verdicts': [verdict.dict() for verdict in verdicts.verdicts],
                        'reason': reason.dict()
                    }
                elif isinstance(metric, GEval):
                    eval_result = metric.g_eval()
                    results['geval'] = eval_result
                elif isinstance(metric, Hallucination):
                    score = metric.measure()
                    results['hallucination'] = {
                        'score': score,
                        'reason': metric.reason,
                        'verdicts': [verdict.dict() for verdict in metric.verdicts]
                    }
                elif isinstance(metric, KnowledgeRetention):
                    score = metric.measure()
                    results['knowledge_retention'] = {
                        'score': score,
                        'reason': metric.reason,
                        'verdicts': [verdict.dict() for verdict in metric.verdicts],
                        'knowledges': [knowledge.data for knowledge in metric.knowledges]
                    }
                elif isinstance(metric, Toxicity):
                    score = metric.measure()
                    results['toxicity'] = {
                        'score': score,
                        'reason': metric.reason,
                        'opinions': metric.opinions,
                        'verdicts': [verdict.dict() for verdict in metric.verdicts]
                    }
                elif isinstance(metric, BertScore):
                    score = metric.measure()
                    results['BertScore'] = {
                        'score': score
                    }
                elif isinstance(metric, BLEU):
                    score = metric.measure()
                    results['BLEU'] = {
                        'score': score
                    }
                elif isinstance(metric, Rouge):
                    score = metric.measure()
                    results['Rouge'] = {
                        'score': score
                    }
                elif isinstance(metric, METEOR):
                    score = metric.measure()
                    results['Meteor'] = {
                        'score': score
                    }
                elif isinstance(metric, Gruen):
                    score = metric.measure()
                    results['Gruen'] = {
                        'score': score
                    }
                logger.info(f"Completed evaluation for metric: {metric_name}")
            except Exception as e:
                logger.error(f"Error evaluating metric {metric_name}: {str(e)}")
        return results
