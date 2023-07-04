import os
import zipfile
import pandas as pd

os.chdir(r"D:\SynologyDrive\Data\High Resolution Events Data\Indian School")

folder_name = '2023_05_ISR_19Ave'
file_list = os.listdir(folder_name)

device_list = []
for file in file_list:
    device_list.append(file[5:7])

cols = ['TimeStamp', 'EventID', 'Parameter']
df = []
i = 0

for file in file_list:
    if file.endswith('.zip'):
        zip_file = os.path.join(folder_name, file)
        zf = zipfile.ZipFile(zip_file)
        temp = pd.read_csv(zf.open(zf.namelist()[0]), names = cols)
        temp['DeviceID'] = device_list[i]
        df += [temp]
    i += 1
        
output_path = folder_name + '.txt'

pd.concat(df, ignore_index = True).to_csv(output_path, index = False, sep = '\t')
