
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

from pathlib import Path
import joblib
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, MiniBatchKMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import linkage, dendrogram

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 500)
