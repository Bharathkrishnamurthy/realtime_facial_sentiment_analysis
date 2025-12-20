# src/evaluate.py
import torch
from torchvision import transforms, datasets
from torch.utils.data import DataLoader
import numpy as np
import sklearn.metrics as skm
from src.model import SimpleFERNet
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "best_fer_model.pth"

def evaluate(batch_size=64):
    data_dir = ROOT/"data_preprocessed"
    transform = transforms.Compose([
        transforms.Resize((48,48)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])
    test_ds = datasets.ImageFolder(root=str(data_dir/'test'), transform=transform)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    ckpt = torch.load(MODEL_PATH, map_location='cpu')
    classes = ckpt['classes']
    model = SimpleFERNet(n_classes=len(classes))
    model.load_state_dict(ckpt['model_state'])
    model.eval()
    preds=[]; trues=[]
    with torch.no_grad():
        for x,y in test_loader:
            out = model(x)
            preds.extend(out.argmax(dim=1).numpy().tolist())
            trues.extend(y.numpy().tolist())
    acc = (np.array(preds)==np.array(trues)).mean()
    cm = skm.confusion_matrix(trues, preds)
    report = skm.classification_report(trues, preds, target_names=classes, digits=4)
    print("Test acc:", acc)
    print(report)
    print("Confusion matrix:\n", cm)

if __name__ == "__main__":
    evaluate()

