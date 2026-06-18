import torch
print("CUDA disponible:", torch.cuda.is_available())
print("Versión PyTorch:", torch.__version__)
print("Número de GPUs:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
else:
    print("GPU: N/A")
