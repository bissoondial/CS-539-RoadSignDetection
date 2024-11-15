import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import numpy as np
import matplotlib.pyplot as plt
import time
from sklearn.metrics import confusion_matrix
import seaborn as sns
from torchsummary import summary

from CNN import *
from DatasetLoaders import RoadSignDataset

transform = transforms.Compose([
    transforms.Resize((32, 32)),  # Resize images to 32x32
    transforms.RandomHorizontalFlip(),
    transforms.RandomCrop(32, padding=4),
    transforms.ToTensor(),  # Convert PIL Image to Tensor
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # Normalize to [-1, 1]
])

dataset = RoadSignDataset(root_dir='images', annotations_dir='annotations', transform=transform)
dataset.showClassStats()

train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])

# Create DataLoaders
batch_size = 4
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize the model
model = CNN_32x32().to(device)
summary(model, (3, 32, 32))

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training
print(f"Model: {model.name}, Device: {device}, Batch Size: {batch_size}")
time_start = time.time()
num_epochs = 15
total_step = len(train_loader)
train_loss_data = np.zeros(num_epochs)
test_loss_data = np.zeros(num_epochs)
test_accuracy_data = np.zeros(num_epochs)
confusion_matrices = []

for epoch in range(num_epochs):
    # Training loop
    model.train()
    train_loss = 0.0
    for i, (images, labels) in enumerate(train_loader):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()

    train_loss_data[epoch] = train_loss / len(train_loader)

    # Testing loop
    model.eval()
    test_loss = 0.0
    correct = 0
    total = 0
    all_labels = []
    all_predictions = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)
            test_loss += loss.item()

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            all_labels.extend(labels.cpu().numpy())
            all_predictions.extend(predicted.cpu().numpy())

    test_loss_data[epoch] = test_loss / len(test_loader)
    test_accuracy_data[epoch] = 100 * correct / total

    # Compute confusion matrix
    cm = confusion_matrix(all_labels, all_predictions)
    confusion_matrices.append(cm)

    print(f'Epoch [{epoch+1}/{num_epochs}], '
          f'Train Loss: {train_loss_data[epoch]:.4f}, '
          f'Test Loss: {test_loss_data[epoch]:.4f}, '
          f'Test Accuracy: {test_accuracy_data[epoch]:.2f}%')
    
dt = time.time() - time_start
print(f'Training finished in {dt:.1f} seconds')

torch.save(model.state_dict(), 'final_model.pth')

# Plotting the losses
plt.figure()
plt.plot(np.arange(num_epochs), train_loss_data, '-x', label='Training Loss')
plt.plot(np.arange(num_epochs), test_loss_data, '-x', label='Testing Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title(f'Training and Testing Loss over {num_epochs} Epochs with {model.name}')
plt.legend()
plt.grid()

# Plotting Testing Accuracy
plt.figure()
plt.plot(np.arange(num_epochs), test_accuracy_data, '-x', label='Testing Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title(f'Testing Accuracy over {num_epochs} Epochs with {model.name}')
plt.legend()
plt.grid()

# Plot Confusion Matrix
plt.figure(figsize=(10, 7))
sns.heatmap(confusion_matrices[-1], annot=True, fmt='d', cmap='Blues')
plt.title(f'Confusion Matrix over {num_epochs} Epochs with {model.name}')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()
