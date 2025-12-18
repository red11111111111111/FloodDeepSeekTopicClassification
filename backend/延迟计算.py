import pymysql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 设置字体：中文用宋体，英文和数字用Times New Roman
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 创建字体属性对象
times_font = fm.FontProperties(family='Times New Roman')


# ================== Database Configuration ==================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "chen55322697",
    "database": "weibo",
    "port": 3306
}
# ================== Establish Connection ==================
conn = pymysql.connect(**DB_CONFIG)

# ================== SQL Query ==================
sql = """
SELECT 
    w.id,
    w.insert_time AS t_weibo,
    c.insert_time AS t_clean,
    f.insert_time AS t_classified
FROM weibo w
JOIN weibo_cleaned c ON w.id = c.id
JOIN weibo_classified f ON w.id = f.id
"""
df = pd.read_sql(sql, conn, parse_dates=["t_weibo", "t_clean", "t_classified"])
conn.close()

# ================== Calculate Latency (in seconds) ==================
df["delay_clean"] = (df["t_clean"] - df["t_weibo"]).dt.total_seconds()
df["delay_classify"] = (df["t_classified"] - df["t_clean"]).dt.total_seconds()
df["delay_e2e"] = (df["t_classified"] - df["t_weibo"]).dt.total_seconds()

# ================== Statistics Function ==================
def get_stats(series):
    return {
        "mean": np.mean(series),
        "p50": np.percentile(series, 50),
        "p90": np.percentile(series, 90),
        "p95": np.percentile(series, 95),
        "p99": np.percentile(series, 99),
        "max": np.max(series)
    }

stats = {
    "Cleaning Latency": get_stats(df["delay_clean"]),
    "Classification Latency": get_stats(df["delay_classify"]),
    "End-to-End Latency": get_stats(df["delay_e2e"])
}

stats_df = pd.DataFrame(stats).T
print(stats_df)

# ================== Save Results ==================
stats_df.to_csv("latency_stats.csv", encoding="utf-8-sig")

# ================== Plotting ==================

# # 1. Bar chart: Average latency by stage
# avg_values = [
#     stats["Cleaning Latency"]["mean"],
#     stats["Classification Latency"]["mean"],
#     stats["End-to-End Latency"]["mean"]
# ]
# labels = ["Cleaning", "Classification", "End-to-End"]
#
# plt.figure(figsize=(8, 5))
# plt.bar(labels, avg_values, color=["skyblue", "lightgreen", "salmon"])
# plt.ylabel("Average Latency (seconds)", fontproperties=times_font, fontsize=12)
# plt.title("Average Latency by Processing Stage", fontproperties=times_font, fontsize=14)
# plt.xlabel("Processing Stage", fontproperties=times_font, fontsize=12)
#
# # 设置刻度标签字体
# ax = plt.gca()
# for label in ax.get_xticklabels() + ax.get_yticklabels():
#     label.set_fontproperties(times_font)
#
# plt.tight_layout()
# plt.savefig("latency_bar.png")
# plt.close()

# 2. CDF: End-to-end latency distribution
sorted_data = np.sort(df["delay_e2e"].dropna())
cdf = np.arange(len(sorted_data)) / float(len(sorted_data))

plt.figure(figsize=(8, 5))
plt.plot(sorted_data, cdf, color="blue")
plt.xlabel("End-to-End Latency (seconds)", fontproperties=times_font, fontsize=12)  # 中文用宋体
plt.ylabel("CDF", fontproperties=times_font, fontsize=12)  # 英文用Times New Roman
plt.grid(True)

# 设置刻度标签字体
ax = plt.gca()
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(times_font)

plt.tight_layout()
plt.savefig("latency_cdf.png")
plt.close()

# 3. Hourly average end-to-end latency
df["hour"] = df["t_weibo"].dt.hour
hourly = df.groupby("hour")["delay_e2e"].mean()

plt.figure(figsize=(10, 5))
plt.plot(hourly.index, hourly.values, marker="o", color="red")
plt.xlabel("Hour of Day", fontproperties=times_font, fontsize=12)  # 英文用Times New Roman
plt.ylabel("Average End-to-End Latency (seconds)", fontproperties=times_font, fontsize=12)
plt.title("Hourly End-to-End Latency", fontproperties=times_font, fontsize=14)
plt.grid(True)
plt.xticks(range(0, 24), fontsize=12)

# 设置刻度标签字体
ax = plt.gca()
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(times_font)

plt.tight_layout()
plt.savefig("latency_hourly.png")
plt.close()