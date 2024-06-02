import matplotlib.pyplot as plt
# from matplotlib import font_manager
import matplotlib
# fontP = font_manager.FontProperties()
# print(fontP.get_family())
# print(matplotlib.matplotlib_fname())
# raise
plt.rcParams['font.sans-serif'] = ['SimHei']
# fontP.set_family('SimHei')
# fontP.set_size(14)# 創建四分位距圖（箱線圖）


# 數據
abnormal_no3_final = [2.5, 2.5, 5, 10, 5, 2, 25, 25, 50, 25, 0, 0.7, 0.6, 0.6, 1.4, 0.9, 0.8, 2.3]
normal_no3_final = [5, 0.2, 0, 2.5, 5, 5, 2, 0, 10, 0.5, 0.8, 0.6, 0.5, 0.7, 1.7, 2.6]

# 創建箱線圖
data = [abnormal_no3_final, normal_no3_final]
labels_final = ['異常', '正常']

fig, ax = plt.subplots()
ax.boxplot(data, labels=labels_final, patch_artist=True, medianprops=dict(color='blue'))

ax.set_ylabel('硝酸鹽濃度 (ppm)')
ax.set_title('養殖狀況下硝酸鹽濃度的四分位距')

plt.show()


