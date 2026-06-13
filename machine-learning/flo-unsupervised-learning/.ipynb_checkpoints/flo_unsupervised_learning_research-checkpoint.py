################################################
# FLO Customer Segmentation - Unsupervised Learning Pipeline
################################################
# Amaç:
# - FLO müşteri verisini temizlemek
# - Tarih ve kategorik kolonlardan modelin anlayacağı feature'lar üretmek
# - KMeans / Hierarchical Clustering / PCA için hazır veri oluşturmak
#
# Not:
# Bu veri setinde target/label yoktur. Bu yüzden LogisticRegression,
# RandomForestClassifier, XGBClassifier gibi supervised modeller kullanılmaz.
################################################

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


################################################
# 1. Exploratory Data Analysis
################################################

def check_df(dataframe, head=5):
    print("##################### Shape #####################")
    print(dataframe.shape)
    print("##################### Types #####################")
    print(dataframe.dtypes)
    print("##################### Head #####################")
    print(dataframe.head(head))
    print("##################### Tail #####################")
    print(dataframe.tail(head))
    print("##################### NA #####################")
    print(dataframe.isnull().sum().sort_values(ascending=False))
    print("##################### Quantiles #####################")
    numeric_df = dataframe.select_dtypes(include=["number"])
    print(numeric_df.quantile([0, 0.05, 0.50, 0.95, 0.99, 1]).T)


def cat_summary(dataframe, col_name, plot=False):
    print(pd.DataFrame({col_name: dataframe[col_name].value_counts(),
                        "Ratio": 100 * dataframe[col_name].value_counts() / len(dataframe)}))
    print("##########################################")
    if plot:
        sns.countplot(x=dataframe[col_name], data=dataframe)
        plt.show(block=True)


def num_summary(dataframe, numerical_col, plot=False):
    quantiles = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50,
                 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]
    print(dataframe[numerical_col].describe(quantiles).T)

    if plot:
        dataframe[numerical_col].hist(bins=20)
        plt.xlabel(numerical_col)
        plt.title(numerical_col)
        plt.show(block=True)


def correlation_matrix(dataframe, cols):
    plt.figure(figsize=(12, 10))
    sns.heatmap(dataframe[cols].corr(), annot=True, linewidths=0.5, cmap="RdBu")
    plt.show(block=True)


def grab_col_names(dataframe, cat_th=10, car_th=20):
    """
    Veri setindeki kategorik, numerik ve kategorik fakat kardinal değişkenleri ayırır.
    Pandas 3 uyumluluğu için object + string beraber kontrol edilir.
    """

    string_cols = dataframe.select_dtypes(include=["object", "string"]).columns.tolist()

    cat_cols = [col for col in string_cols]
    num_but_cat = [col for col in dataframe.columns
                   if dataframe[col].nunique() < cat_th and
                   col not in string_cols]
    cat_but_car = [col for col in string_cols
                   if dataframe[col].nunique() > car_th]

    cat_cols = cat_cols + num_but_cat
    cat_cols = [col for col in cat_cols if col not in cat_but_car]

    num_cols = [col for col in dataframe.columns
                if col not in cat_cols and col not in cat_but_car]

    return cat_cols, num_cols, cat_but_car


################################################
# 2. Data Preprocessing & Feature Engineering
################################################

def load_flo_data(path="dataset/flo_data_20k.csv"):
    """Veri setini okur. Dosya farklı klasördeyse path'i değiştir."""
    path = Path(path)

    if path.exists():
        return pd.read_csv(path)

    # Bu .py dosyası ile csv aynı klasördeyse otomatik yakalar.
    alternative_path = Path(__file__).resolve().parent / "flo_data_20k.csv"
    if alternative_path.exists():
        return pd.read_csv(alternative_path)

    raise FileNotFoundError(
        f"Veri seti bulunamadı: {path}. Dosya yolunu kontrol et veya csv'yi .py dosyasıyla aynı klasöre koy."
    )


def create_date_features(dataframe):
    """Tarih kolonlarını datetime'a çevirir ve segmentasyon için sayısal feature üretir."""
    dataframe = dataframe.copy()

    date_cols = [
        "first_order_date",
        "last_order_date",
        "last_order_date_online",
        "last_order_date_offline"
    ]

    for col in date_cols:
        dataframe[col] = pd.to_datetime(dataframe[col])

    # Veri setindeki son alışveriş tarihinden 2 gün sonrasını analiz tarihi kabul ediyoruz.
    # İstersen sabit de yazabilirsin: pd.to_datetime("2021-06-01")
    analysis_date = dataframe["last_order_date"].max() + pd.Timedelta(days=2)

    dataframe["recency"] = (analysis_date - dataframe["last_order_date"]).dt.days
    dataframe["customer_age"] = (dataframe["last_order_date"] - dataframe["first_order_date"]).dt.days
    dataframe["online_recency"] = (analysis_date - dataframe["last_order_date_online"]).dt.days
    dataframe["offline_recency"] = (analysis_date - dataframe["last_order_date_offline"]).dt.days

    dataframe.drop(date_cols, axis=1, inplace=True)
    return dataframe


def create_customer_features(dataframe):
    """Online/offline sipariş ve harcama kolonlarından toplam ve oran feature'ları üretir."""
    dataframe = dataframe.copy()

    dataframe["total_order"] = (
        dataframe["order_num_total_ever_online"] +
        dataframe["order_num_total_ever_offline"]
    )

    dataframe["total_value"] = (
        dataframe["customer_value_total_ever_online"] +
        dataframe["customer_value_total_ever_offline"]
    )

    dataframe["avg_order_value"] = dataframe["total_value"] / dataframe["total_order"]

    dataframe["online_order_ratio"] = (
        dataframe["order_num_total_ever_online"] / dataframe["total_order"]
    )

    dataframe["online_value_ratio"] = (
        dataframe["customer_value_total_ever_online"] / dataframe["total_value"]
    )

    return dataframe


def encode_category_interests(dataframe):
    """[KADIN, ERKEK] gibi çoklu kategori kolonunu ayrı dummy kolonlara ayırır."""
    dataframe = dataframe.copy()

    dataframe["interested_in_categories_12"] = (
        dataframe["interested_in_categories_12"]
        .str.replace("[", "", regex=False)
        .str.replace("]", "", regex=False)
    )

    category_dummies = dataframe["interested_in_categories_12"].str.get_dummies(sep=", ")

    dataframe = pd.concat([dataframe, category_dummies], axis=1)
    dataframe.drop("interested_in_categories_12", axis=1, inplace=True)

    return dataframe


def one_hot_encoder(dataframe, categorical_cols, drop_first=True):
    dataframe = pd.get_dummies(dataframe, columns=categorical_cols, drop_first=drop_first)

    # Pandas yeni sürümlerde dummy kolonları bool döndürebilir.
    # StandardScaler / quantile gibi işlemlerde hata olmaması için int'e çeviriyoruz.
    bool_cols = dataframe.select_dtypes(include="bool").columns
    dataframe[bool_cols] = dataframe[bool_cols].astype(int)

    return dataframe


def flo_preprocessing(dataframe):
    """Ham FLO datasını modellemeye hazır numerik dataframe'e çevirir."""
    dataframe = dataframe.copy()

    # ID kolonu model için anlamlı değildir.
    if "master_id" in dataframe.columns:
        dataframe.drop("master_id", axis=1, inplace=True)

    dataframe = create_date_features(dataframe)
    dataframe = create_customer_features(dataframe)
    dataframe = encode_category_interests(dataframe)

    dataframe = one_hot_encoder(
        dataframe,
        categorical_cols=["order_channel", "last_order_channel"],
        drop_first=True
    )

    # Son güvenlik kontrolleri
    bool_cols = dataframe.select_dtypes(include="bool").columns
    dataframe[bool_cols] = dataframe[bool_cols].astype(int)

    object_cols = dataframe.select_dtypes(include=["object", "string"]).columns
    if len(object_cols) > 0:
        raise ValueError(f"Model öncesi string kolon kaldı: {list(object_cols)}")

    if dataframe.isnull().sum().sum() > 0:
        raise ValueError("Model öncesi eksik değer var. df.isnull().sum() ile kontrol et.")

    return dataframe


################################################
# 3. Outlier Analysis
################################################

def outlier_thresholds(dataframe, col_name, q1=0.25, q3=0.75):
    quartile1 = dataframe[col_name].quantile(q1)
    quartile3 = dataframe[col_name].quantile(q3)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


def check_outlier(dataframe, col_name, q1=0.25, q3=0.75):
    low_limit, up_limit = outlier_thresholds(dataframe, col_name, q1, q3)
    return dataframe[(dataframe[col_name] > up_limit) | (dataframe[col_name] < low_limit)].any(axis=None)


################################################
# 4. Scaling
################################################

def scale_data(dataframe):
    scaler = StandardScaler()
    scaled_array = scaler.fit_transform(dataframe)
    scaled_df = pd.DataFrame(scaled_array, columns=dataframe.columns, index=dataframe.index)
    return scaled_df, scaler


################################################
# 5. KMeans Clustering
################################################

def plot_elbow_method(dataframe, max_k=10):
    ssd = []
    k_values = range(2, max_k + 1)

    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=17, n_init=10)
        kmeans.fit(dataframe)
        ssd.append(kmeans.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(k_values, ssd, marker="o")
    plt.xlabel("K Values")
    plt.ylabel("SSD / Inertia")
    plt.title("Elbow Method")
    plt.show(block=True)


def kmeans_clustering(dataframe, n_clusters=4):
    kmeans = KMeans(n_clusters=n_clusters, random_state=17, n_init=10, max_iter=300)
    clusters = kmeans.fit_predict(dataframe)
    return clusters, kmeans


def compare_kmeans_scores(dataframe, min_k=2, max_k=10, sample_size=500):
    """
    K değerlerini karşılaştırır.
    Silhouette score büyük veride yavaş olabildiği için gerekirse örneklem üzerinden hesaplanır.
    """
    results = []

    score_df = dataframe.sample(sample_size, random_state=17) if len(dataframe) > sample_size else dataframe

    for k in range(min_k, max_k + 1):
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=17, n_init=5, batch_size=256, max_iter=100)
        labels = kmeans.fit_predict(score_df)
        score = silhouette_score(score_df, labels)
        results.append({"k": k, "inertia": kmeans.inertia_, "silhouette_score": score})

    return pd.DataFrame(results)


################################################
# 6. PCA
################################################

def pca_analysis(dataframe, n_components=2):
    pca = PCA(n_components=n_components, random_state=17)
    pca_array = pca.fit_transform(dataframe)

    pca_df = pd.DataFrame(
        pca_array,
        columns=[f"PC{i+1}" for i in range(n_components)],
        index=dataframe.index
    )

    print("Explained variance ratio:")
    print(pca.explained_variance_ratio_)
    print("Total explained variance:")
    print(pca.explained_variance_ratio_.sum())

    return pca_df, pca


def plot_pca_clusters(pca_df, cluster_col="cluster"):
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=pca_df, x="PC1", y="PC2", hue=cluster_col, palette="tab10")
    plt.title("PCA Cluster Visualization")
    plt.show(block=True)


################################################
# 7. Hierarchical Clustering
################################################

def plot_dendrogram(dataframe, method="average", sample_size=500):
    # Dendrogram büyük veride çok yavaş olabilir. Bu yüzden örneklem alıyoruz.
    sample_df = dataframe.sample(sample_size, random_state=17) if len(dataframe) > sample_size else dataframe
    hc = linkage(sample_df, method=method)

    plt.figure(figsize=(12, 7))
    dendrogram(hc)
    plt.title("Hierarchical Clustering Dendrogram")
    plt.show(block=True)


def hierarchical_clustering(dataframe, n_clusters=4):
    hc = AgglomerativeClustering(n_clusters=n_clusters, linkage="average")
    clusters = hc.fit_predict(dataframe)
    return clusters, hc


################################################
# 8. Cluster Profiling
################################################

def cluster_profile(original_df, cluster_labels, cluster_name="cluster"):
    profiled_df = original_df.copy()
    profiled_df[cluster_name] = cluster_labels

    print(profiled_df.groupby(cluster_name).agg(["mean", "median", "count"]).T)
    return profiled_df


################################################
# 9. Main Flow
################################################

# PyCharm'da dosya yolu hata verirse aşağıdaki path'i kendi klasörüne göre değiştir.
# Örn: df_raw = load_flo_data("/Users/aydinerkut/Desktop/.../flo_data_20k.csv")
df_raw = load_flo_data("dataset/flo_data_20k.csv")

print("\nRAW DATA CHECK")
check_df(df_raw)

# Ham veri üzerinde EDA yapmak istersen:
cat_cols_raw, num_cols_raw, cat_but_car_raw = grab_col_names(df_raw, cat_th=5, car_th=20)

print("\nRAW CATEGORICAL COLS:", cat_cols_raw)
print("RAW NUMERICAL COLS:", num_cols_raw)
print("RAW CAT BUT CARDINAL COLS:", cat_but_car_raw)

# Modellemeye hazır dataframe
df_model = flo_preprocessing(df_raw)

print("\nMODEL DATA CHECK")
check_df(df_model)

# Kolon isimlerini istersen büyük harfe çevirebilirsin.
# Ben burada model aşamasında karışmasın diye küçük bıraktım.
# df_model.columns = [col.upper() for col in df_model.columns]

# Sayısal kolonlar
num_cols = df_model.columns.tolist()

# Korelasyon matrisi isteğe bağlıdır, çok kolon varsa karmaşık görünebilir.
# correlation_matrix(df_model, num_cols)

# Outlier kontrolü ve baskılama
# Dummy kolonlarda outlier aranmaz; sadece sürekli sayısal kolonlarda bakmak daha mantıklıdır.
continuous_cols = [
    "order_num_total_ever_online",
    "order_num_total_ever_offline",
    "customer_value_total_ever_offline",
    "customer_value_total_ever_online",
    "recency",
    "customer_age",
    "online_recency",
    "offline_recency",
    "total_order",
    "total_value",
    "avg_order_value",
    "online_order_ratio",
    "online_value_ratio"
]

for col in continuous_cols:
    print(col, check_outlier(df_model, col))

# Aykırı değerleri baskılamak istersen aç:
def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)

    if variable in ["recency", "online_recency", "offline_recency", "customer_age"]:
        low_limit = max(low_limit, 0)

    dataframe[variable] = dataframe[variable].astype(float)

    dataframe.loc[dataframe[variable] < low_limit, variable] = low_limit
    dataframe.loc[dataframe[variable] > up_limit, variable] = up_limit
# Scaling
scaled_df, scaler = scale_data(df_model)

print("\nSCALED DATA CHECK")
check_df(scaled_df)

# KMeans skor karşılaştırması
# # Not: Bu bölüm bazı bilgisayarlarda uzun sürebilir. Önce küçük sample ile dene.
# sample_scaled_df = scaled_df.sample(5000, random_state=17)
# kmeans_scores = compare_kmeans_scores(sample_scaled_df, min_k=2, max_k=6, sample_size=500)
# print("\nKMEANS SCORE COMPARISON")
# print(kmeans_scores)

# Elbow grafiği
# plot_elbow_method(scaled_df.sample(5000, random_state=17), max_k=10)

# Örnek final KMeans modeli
# kmeans_clusters, kmeans_model = kmeans_clustering(scaled_df, n_clusters=4)

# Cluster profilini orijinal ölçekli df_model üzerinde incele
# kmeans_profiled_df = cluster_profile(df_model, kmeans_clusters, cluster_name="kmeans_cluster")

# PCA ile 2 boyuta indirip görselleştirme
# pca_df, pca_model = pca_analysis(scaled_df, n_components=2)
# pca_df["cluster"] = kmeans_clusters
# plot_pca_clusters(pca_df, cluster_col="cluster")

# Hierarchical clustering dendrogramı büyük veride yavaş olur, örneklemle çiz.
# plot_dendrogram(scaled_df, method="average", sample_size=500)

# Hierarchical clustering tüm veri üzerinde yavaş olabilir.
# İstersen önce örneklemle dene:
# sample_scaled_df = scaled_df.sample(2000, random_state=17)
# hc_clusters, hc_model = hierarchical_clustering(sample_scaled_df, n_clusters=4)

# Model ve scaler kaydetmek istersen:
# joblib.dump(kmeans_model, "kmeans_model.pkl")
# joblib.dump(scaler, "scaler.pkl")
