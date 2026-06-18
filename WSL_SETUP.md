# Configuración WSL para PyTorch con CUDA ✅

## Estado: CUDA DISPONIBLE! 🎉
- **GPU Detectada**: NVIDIA GeForce GTX 1650
- **Versión PyTorch**: 2.5.1+cu121
- **CUDA Disponible**: True

## Cómo usar el entorno WSL

1. Abrir Ubuntu WSL:
   ```bash
   wsl -d Ubuntu
   ```

2. Navegar al directorio del proyecto:
   ```bash
   cd /mnt/c/Users/gamur/Documents/ESPE\ VII\ SI\ 2026/Desarrollo\ Seguro/U2/p/proyectosegundoparcialswseguro
   ```

3. Activar el entorno virtual (ubicado en el sistema de archivos WSL para mejor rendimiento):
   ```bash
   source ~/.venv_seguro/bin/activate
   ```

4. Verificar que PyTorch y CUDA estén disponibles:
   ```bash
   python check_cuda.py
   ```

## "Los demás" (models/datasets/GPU)

- **Datasets**: TODOS los datasets (CVEFixes, OWASP, CodeXGLUE, D2A, ReVeal, VulBERTa, combined) funcionan con ambos modelos.
- **Modelos**:
  - **Random Forest**: sigue siendo CPU-only (scikit-learn), pero es rápido.
  - **VulBERTa**: usa PyTorch y ahora sí usa tu GPU NVIDIA GeForce GTX 1650! 🚀
- **GPU**: Solo VulBERTa usa la GPU; datasets y Random Forest siguen en CPU.

