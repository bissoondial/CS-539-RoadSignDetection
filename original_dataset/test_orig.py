import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import time


from CNN import *
from DatasetLoaders import RoadSignDataset


# transform = transforms.Compose([
#     transforms.Resize((32, 32)),  # Resize images to 32x32
#     transforms.ToTensor(),  # Convert PIL Image to Tensor
#     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # Normalize to [-1, 1]
# ])

transform = transforms.Compose([
    transforms.Resize((32, 32)),  # Resize images to 32x32
    transforms.RandomHorizontalFlip(),
    transforms.RandomCrop(32, padding=4),
    transforms.ToTensor(),  # Convert PIL Image to Tensor
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # Normalize to [-1, 1]
])

# Assuming RoadSignDataset is your custom dataset class
dataset = RoadSignDataset(root_dir='images', annotations_dir='annotations', transform=transform)
dataset.showClassStats()

# Extracting the labels
targets = np.array([dataset[i][1] for i in range(len(dataset))])

# Group indices by class
class_indices = defaultdict(list)
for idx, target in enumerate(targets):
    class_indices[target].append(idx)

# Determine the minimum class count
min_class_count = min(len(indices) for indices in class_indices.values())

# Sample the same number of instances from each class
balanced_indices = []
for indices in class_indices.values():
    balanced_indices.extend(np.random.choice(indices, min_class_count, replace=False))

# Shuffle the balanced indices
np.random.shuffle(balanced_indices)

# Define the split ratio
split_ratio = 0.8
train_size = int(split_ratio * len(balanced_indices))
train_indices = balanced_indices[:train_size]
test_indices = balanced_indices[train_size:]

# Create the balanced train and test datasets
train_dataset = torch.utils.data.Subset(dataset, train_indices)
test_dataset = torch.utils.data.Subset(dataset, test_indices)

# Verify class distribution
train_labels = [train_dataset[i][1] for i in range(len(train_dataset))]
test_labels = [test_dataset[i][1] for i in range(len(test_dataset))]
print(f"Training set class distribution: {np.bincount(train_labels)}")
print(f"Test set class distribution: {np.bincount(test_labels)}")

# Uses all of dataset
# train_size = int(0.8 * len(dataset))
# test_size = len(dataset) - train_size
# train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])

# Create DataLoaders
batch_size = 4
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize the model
model = CNN_32x32_Paul().to(device)
# model = CNN_300x400().to(device)

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training
print(f"Model: {model.name}, Device: {device}, Batch Size: {batch_size}")
time_start = time.time()
num_epochs = 200
total_step = len(train_loader)
train_loss_data = np.zeros(num_epochs)
test_loss_data = np.zeros(num_epochs)
test_accuracy_data = np.zeros(num_epochs)

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
    model.eval()  # Set model to evaluation mode
    test_loss = 0.0
    correct = 0
    total = 0
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

    test_loss_data[epoch] = test_loss / len(test_loader)
    test_accuracy_data[epoch] = 100 * correct / total

    print(f'Epoch [{epoch+1}/{num_epochs}], '
          f'Train Loss: {train_loss_data[epoch]:.4f}, '
          f'Test Loss: {test_loss_data[epoch]:.4f}, '
          f'Test Accuracy: {test_accuracy_data[epoch]:.2f}%')
    
dt = time.time() - time_start
print(f'Training finished in {dt:.1f} seconds')

# Plotting the losses
plt.figure()
plt.plot(np.arange(num_epochs), train_loss_data, '-x', label='Training Loss')
plt.plot(np.arange(num_epochs), test_loss_data, '-x', label='Testing Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title(f'Training and Testing Loss over {num_epochs} Epochs with {model.name}')
plt.legend()
plt.grid()
# plt.show()

# Plotting Testing Accuracy
plt.figure()
plt.plot(np.arange(num_epochs), test_accuracy_data, '-x', label='Testing Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title(f'Testing Accuracy over {num_epochs} Epochs with {model.name}')
plt.legend()
plt.grid()
plt.show()