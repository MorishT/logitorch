from typing import Dict, List, Optional, Tuple, Union, Any

from logitorch.datasets.base import AbstractProofQADataset
from logitorch.datasets.exceptions import (
    DatasetNameError,
    SplitSetError,
    TaskError,
)
from logitorch.datasets.utils import SPLIT_SETS
from datasets import load_dataset
from FLD_task import load_deduction
from FLD_task.hf_dataset import serialize_transform

FLD_SUB_DATASETS = [
    "hitachi-nlp/FLD.v2",
    "hitachi-nlp/FLD_star.v2",
]
FLD_TASKS = [
    "proof_generation_all",
    # "proof_generation_iter",
    # "implication_enumeration",
    # "abduction",
]


class FLDDataset(AbstractProofQADataset):
    def __init__(
        self,
        dataset_name: str,
        split_set: str,
        task: str,
        max_samples: Optional[int] = None,
    ) -> None:
        try:
            if dataset_name not in FLD_SUB_DATASETS:
                raise DatasetNameError()

            if split_set == "val":
                split_set = "dev"
            elif split_set not in SPLIT_SETS:
                raise SplitSetError(SPLIT_SETS)

            if task not in FLD_TASKS:
                raise TaskError()

            self.dataset_name = dataset_name
            self.split_set = split_set
            self.task = task

            hf_split = 'validation' if split_set == 'dev' else split_set
            hf_dataset = load_dataset(
                dataset_name,
                split=hf_split,
            )
            # load and dump once to normalize dataset format to the latest version.
            hf_dataset = hf_dataset.map(
                lambda example: load_deduction(example).dict(),
                batched=False,
            )
            if max_samples is not None:
                hf_dataset = hf_dataset.select(range(max_samples))
            self._hf_dataset = hf_dataset

        except DatasetNameError as err:
            print(err.message)
            print(f"The FLD datasets are: {FLD_SUB_DATASETS}")
            raise err
        except SplitSetError as err:
            print(err.message)
            raise err
        except TaskError as err:
            print(err.message)
            print(f"The FLD tasks are: {FLD_TASKS}")
            raise err

    def __getitem__(
        self, index: int
    ) -> Union[
        Tuple[
            Dict[str, str],
            Dict[str, str],
            List[str],
            List[str],
            List[str],
            List[str],
            List[int],
        ],
        Tuple[Dict[str, str], Dict[str, str], List[str], List[str], List[str]],
        Tuple[Dict[str, str], Dict[str, str], List[str], List[str]],
        Tuple[Dict[str, str], Dict[str, str], List[str]],

        Dict[str, Any],  # FLD dataset
    ]:
        batch_example = {
            'context': [self._hf_dataset[index]['context']],
            'hypothesis': [self._hf_dataset[index]['hypothesis']],
            'world_assump_label': [self._hf_dataset[index]['world_assump_label']],
            'proofs': [self._hf_dataset[index]['proofs']],
            'original_tree_depth': [self._hf_dataset[index]['original_tree_depth']],
        }

        if self.task == "proof_generation_all":
            batch_example = serialize_transform(
                batch_example,
                'train',
                proof_sampling='all_at_once',
                sample_negative_proof=True,
            )
        elif self.task == "proof_generation_iter":
            pass
        else:
            raise ValueError()

        return {
            key: vals[0]
            for key, vals in batch_example.items()
        }


    def __str__(self) -> str:
        return f'The {self.split_set} set of {self.dataset_name}\'s FLD for the task of "{self.task}" has {self.__len__()} instances'

    def __len__(self) -> int:
        # return len(self.triples)
        return len(self._hf_dataset)


    def _extract_serials(self, examples: Dict[str, List[Any]]) -> Tuple[List[str], List[str], List[str]]:
        if self.log_examples:
            logger.info('')
            logger.info('============================= extract_inputs_targets() =============================')

        inputs: List[str] = []
        targets: List[str] = []
        gold_proofs: List[str] = []
        for i_example in range(len(examples['context'])):
            context = examples['context'][i_example]
            next_step = examples['next_step'][i_example]
            gold_proof = random.choice(examples['gold_proof'][i_example])

            inputs.append(context)
            targets.append(next_step)
            gold_proofs.append(gold_proof)
            if self.log_examples:
                logger.info('context    [%d] : "%s"', i_example, context)
                logger.info('next_step [%d] : "%s"', i_example, next_step)
                logger.info('gold_proof [%d] : "%s"', i_example, gold_proof)

        inputs = [self.prefix + inp for inp in inputs]

        return inputs, targets, gold_proofs
