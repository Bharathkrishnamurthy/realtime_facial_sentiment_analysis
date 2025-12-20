# src/train.py
import torch
from torch.utils.data import DataLoader
from torchvision import transforms, datasets
from pathlib import Path
from model import SimpleFERNet

# ---------------- CONFIG ----------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_preprocessed"
SAVE_PATH = ROOT / "best_fer_model.pth"

torch.backends.cudnn.benchmark = True

# ---------------- DATA ----------------
def get_loaders(data_dir, batch_size=64):
    transform = transforms.Compose([
        transforms.Resize((48, 48)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])

    train_ds = datasets.ImageFolder(
        root=str(data_dir / "train"),
        transform=transform
    )
    val_ds = datasets.ImageFolder(
        root=str(data_dir / "val"),
        transform=transform
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,        # ✅ Windows-safe
        pin_memory=True
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True
    )

    return train_loader, val_loader, train_ds.classes

# ---------------- TRAIN ----------------
def train(epochs=20, lr=1e-3):
    train_loader, val_loader, classes = get_loaders(DATA_DIR)

    model = SimpleFERNet(n_classes=len(classes)).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()

    best_val_acc = 0.0

    for ep in range(epochs):
        # ---- Train ----
        model.train()
        train_loss = 0.0

        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)

            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        # ---- Validate ----
        model.eval()
        correct, total = 0, 0

        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(DEVICE), y.to(DEVICE)
                out = model(x)
                preds = out.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        val_acc = correct / total

        print(
            f"Epoch {ep+1:02d}/{epochs} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Acc: {val_acc:.4f}"
        )

        # ---- Save Best ----
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "classes": classes
                },
                SAVE_PATH
            )
            print("✅ Saved best model")

    print("🎯 Training complete | Best Val Acc:", best_val_acc)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    train(epochs=20, lr=1e-3)
