from sklearn.metrics import accuracy_score
from tqdm import tqdm

from logitorch.datasets.proof_qa.proofwriter_dataset import (
    PROOFWRITER_LABEL_TO_ID,
    ProofWriterDataset,
)
from logitorch.datasets.qa.ruletaker_dataset import RuleTakerDataset
from logitorch.datasets.te.mnli_dataset import MNLIDataset
from logitorch.datasets.te.negated_mnli_dataset import NegatedMNLIDataset
from logitorch.datasets.te.negated_rte_dataset import NegatedRTEDataset
from logitorch.datasets.te.negated_snli_dataset import NegatedSNLIDataset
from logitorch.datasets.te.rte_dataset import RTEDataset
from logitorch.datasets.te.snli_dataset import SNLIDataset
from logitorch.pl_models.bertnot import PLBERTNOT
from logitorch.pl_models.proofwriter import PLProofWriter
from logitorch.pl_models.prover import PLPRover
from logitorch.pl_models.ruletaker import PLRuleTaker

MODEL = "ruletaker"
DEVICE = "cpu"


def parse_facts_rules(facts, rules):
    sentences = []
    for k, v in facts.items():
        sentences.append(f"{k}: {v}")
    for k, v in rules.items():
        sentences.append(f"{k}: {v}")
    context = "".join(sentences)
    return context


proofwriter_test_datasets = ["depth-5", "birds-electricity"]

if MODEL == "proofwriter":
    model = PLProofWriter.load_from_checkpoint(
        "models/best_proofwriter-epoch=05-val_loss=0.01.ckpt",
        pretrained_model="google/t5-v1_1-large",
    )
    model.to(DEVICE)
    model.eval()

    for d in proofwriter_test_datasets:
        test_dataset = ProofWriterDataset(d, "test", "proof_generation_all")
        depths_pred = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        depths_true = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        y_preds = []
        y_trues = []

        for i in tqdm(test_dataset):
            context = parse_facts_rules(i[0], i[1])
            y_pred = model.predict(context, i[2], device=DEVICE)
            if "True" in y_pred:
                y_pred = 1
            else:
                y_pred = 0
            y_true = PROOFWRITER_LABEL_TO_ID[str(i[3])]
            depths_pred[i[6]].append(y_pred)
            depths_true[i[6]].append(y_true)
            y_preds.append(y_pred)
            y_trues.append(y_true)

        for k in depths_pred:
            with open(f"proofwriter_{d}_{k}.txt", "w") as out:
                out.write(str(accuracy_score(depths_pred[k], depths_true[k])))

        with open(f"proofwriter_{d}.txt", "w") as out:
            out.write(str(accuracy_score(y_preds, y_trues)))

elif MODEL == "prover":
    model = PLPRover.load_from_checkpoint(
        "models/best_prover-epoch=09-val_loss=0.07.ckpt",
        pretrained_model="roberta-large",
    )
    model.to(DEVICE)
    model.eval()

    for d in proofwriter_test_datasets:
        test_dataset = ProofWriterDataset(d, "test", "proof_generation_all")
        depths_pred = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        depths_true = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        y_preds = []
        y_trues = []

        for i in tqdm(test_dataset):
            y_pred = model.predict(i[0], i[1], i[2], device=DEVICE)
            y_true = PROOFWRITER_LABEL_TO_ID[str(i[3])]
            depths_pred[i[6]].append(y_pred)
            depths_true[i[6]].append(y_true)
            y_preds.append(y_pred)
            y_trues.append(y_true)

        for k in depths_pred:
            with open(f"prover_{d}_{k}.txt", "w") as out:
                out.write(str(accuracy_score(depths_pred[k], depths_true[k])))

        with open(f"prover_{d}.txt", "w") as out:
            out.write(str(accuracy_score(y_preds, y_trues)))

elif MODEL == "ruletaker":
    model = PLRuleTaker.load_from_checkpoint(
        "models/best_ruletaker_ruletaker-epoch=05-val_loss=0.03.ckpt"
    )
    model.to(DEVICE)
    model.eval()

    for d in proofwriter_test_datasets:
        test_dataset = RuleTakerDataset(d, "test")
        depths_pred = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        depths_true = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        y_preds = []
        y_trues = []

        for i in tqdm(test_dataset):
            y_pred = model.predict(i[0], i[1], device=DEVICE)
            y_true = i[2]
            depths_pred[i[3]].append(y_pred)
            depths_true[i[3]].append(y_true)
            y_preds.append(y_pred)
            y_trues.append(y_true)

        for k in depths_pred:
            with open(f"ruletaker_1_{d}_{k}.txt", "w") as out:
                out.write(str(accuracy_score(depths_pred[k], depths_true[k])))

        with open(f"ruletaker_1_{d}.txt", "w") as out:
            out.write(str(accuracy_score(y_preds, y_trues)))

elif MODEL == "bertnot":
    model = PLBERTNOT.load_from_checkpoint(
        "models/snli_bertnot.ckpt", pretrained_model="bert-base-cased", num_labels=3
    )
    model.to(DEVICE)
    val_dataset = SNLIDataset("val")
    neg_dataset = NegatedSNLIDataset()

    with open("bertnot_val_snli.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in val_dataset:

            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))

    with open("bertnot_neg_snli.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in neg_dataset:
            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))

    model = PLBERTNOT.load_from_checkpoint(
        "models/mnli_bertnot.ckpt", pretrained_model="bert-base-cased", num_labels=3
    )
    model.to(DEVICE)
    val_dataset = MNLIDataset("val")
    neg_dataset = NegatedMNLIDataset()

    with open("bertnot_val_mnli.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in val_dataset:

            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))

    with open("bertnot_neg_mnli.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in neg_dataset:
            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))

    model = PLBERTNOT.load_from_checkpoint(
        "models/rte_bertnot.ckpt", pretrained_model="bert-base-cased", num_labels=2
    )
    model.to(DEVICE)
    val_dataset = RTEDataset("val")
    neg_dataset = NegatedRTEDataset()

    with open("bertnot_val_rte.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in val_dataset:

            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))

    with open("bertnot_neg_rte.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in neg_dataset:
            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))
elif MODEL == "rte":
    model = PLBERTNOT.load_from_checkpoint(
        "models/rte_bertnot.ckpt", pretrained_model="bert-base-cased", num_labels=2
    )
    model.to(DEVICE)
    val_dataset = RTEDataset("val")
    neg_dataset = NegatedRTEDataset()

    with open("bertnot_val_rte.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in val_dataset:

            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))

    with open("bertnot_neg_rte.txt", "w") as out:
        y_preds = []
        y_trues = []
        for p, h, l in neg_dataset:
            y_pred = model.predict(p, h, task="te", device=DEVICE)
            y_preds.append(y_pred)
            y_trues.append(l)
        out.write(str(accuracy_score(y_trues, y_preds)))
