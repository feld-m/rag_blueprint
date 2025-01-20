"""
This script is used to evaluate RAG system using langfuse datasets. To add a new item to datasets, visit Langfuse UI.
Qdrant vector storage should be running with ready collection of embeddings.
To run the script execute the following command from the root directory of the project:

> python src/evaluate.py
"""

import logging

from injector import Injector

from common.bootstrap.configuration.configuration import Configuration
from common.bootstrap.initializer import EvaluationInitializer
from evaluation.evaluators import LangfuseEvaluator


def main(
    injector: Injector,
):
    """Execute RAG system evaluation workflow.

    Args:
        injector: Dependency injection container

    Note:
        Evaluates both feedback and manual datasets
        Results are recorded in Langfuse
    """
    configuration = injector.get(Configuration)
    langfuse_evaluator = injector.get(LangfuseEvaluator)

    logging.info(f"Evaluating {langfuse_evaluator.run_name}...")

    langfuse_evaluator.evaluate(
        dataset_name=configuration.pipeline.augmentation.langfuse.datasets.feedback_dataset.name
    )
    langfuse_evaluator.evaluate(
        dataset_name=configuration.pipeline.augmentation.langfuse.datasets.manual_dataset.name
    )

    logging.info(
        f"Evaluation complete for {configuration.metadata.build_name}."
    )


if __name__ == "__main__":
    injector = EvaluationInitializer().init_injector()
    main(injector)
