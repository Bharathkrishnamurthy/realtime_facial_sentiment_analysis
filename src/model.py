import torch
import torch.nn as nn

class SimpleFERNet(nn.Module):
    def __init__(self, n_classes=7):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        # Dynamic feature size
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 48, 48)
            n_features = self.features(dummy).view(1, -1).size(1)

        # 🔥 IMPORTANT: name MUST be "classifier"
        self.classifier = nn.Sequential(
            nn.Linear(n_features, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, n_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)
