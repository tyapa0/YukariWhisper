import torch

# 有効なGPUのリストを表示
def get_gpu_list():

    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()

        print("Gpu_list:")

        for i in range(device_count):
            print(
                f"{i} : {torch.cuda.get_device_name()}, : {torch.cuda.get_device_capability()}"
            )

