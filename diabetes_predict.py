import pickle
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score,roc_auc_score
from sklearn.model_selection import GridSearchCV, cross_validate
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import MinMaxScaler, LabelEncoder, StandardScaler, RobustScaler
import warnings
warnings.simplefilter(action="ignore")
import missingno as msno
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 170)
pd.set_option('display.max_rows', 20)
pd.set_option('display.float_format', lambda x: '%.3f' % x)




##################################
# GÖREV 1: KEŞİFCİ VERİ ANALİZİ
##################################

##################################
# ADIM1:GENEL RESİM
##################################4
def load():
    data = pd.read_csv("datasets/diabetes.csv")
    return data


df = load()
df.head()
df["Outcome"].value_counts()  # 500 diabet hastası olmayan, 268 diabet hastası var.
df.info()


##################################
# ADIM2:NUMERİK VE KATEGORİK DEĞİŞKENLERİN YAKALANMASI
##################################

def grab_col_names(dataframe, car_th=20, cat_th=10):
    cat_cols = [col for col in dataframe.columns if dataframe[col].dtypes == "O"]
    num_but_cat = [col for col in dataframe.columns if
                   dataframe[col].nunique() < cat_th and dataframe[col].dtypes != "O"]
    cat_but_car = [col for col in dataframe.columns if
                   dataframe[col].nunique() > car_th and dataframe[col].dtypes == "O"]
    cat_cols = cat_cols + num_but_cat
    cat_cols = [col for col in cat_cols if col not in cat_but_car]

    # num_cols
    num_cols = [col for col in dataframe.columns if dataframe[col].dtypes != "O"]
    num_cols = [col for col in num_cols if col not in num_but_cat]

    print(f"Observations: {dataframe.shape[0]}")
    print(f"Variables: {dataframe.shape[1]}")
    print(f'cat_cols: {len(cat_cols)}')
    print(f'num_cols: {len(num_cols)}')
    print(f'cat_but_car: {len(cat_but_car)}')
    print(f'num_but_cat: {len(num_but_cat)}')

    return cat_cols, num_cols, cat_but_car


cat_cols, num_cols, cat_but_car = grab_col_names(df)

# numerik kolonların grafik halinde gösterilmesi
for col in num_cols:
    fig, ax = plt.subplots(figsize=(7, 5))
    df.groupby("Outcome").agg({col: "mean"}).plot(kind="bar", rot=0, ax=ax)
    colors = ['#A71930', '#004687']
    for patch, color in zip(ax.patches, colors):
        patch.set_facecolor(color)
    plt.show()


##################################
# ADIM3:KATEGORİK DEĞİŞKENLERİN ANALİZİ
##################################
def cat_summary(dataframe, col_name, plot=False):
    print(pd.DataFrame({col_name: dataframe[col_name].value_counts(),
                        "Ratio": 100 * dataframe[col_name].value_counts() / len(dataframe)}))
    print("##########################################")
    if plot:
        sns.countplot(x=dataframe[col_name], data=dataframe)
        plt.show()


# num_but_cat olan outcome değişkeninin analizi
cat_summary(df, "Outcome", plot=True)


##################################
# ADIM3:NUMERİK DEĞİŞKENLERİN ANALİZİ
##################################

def num_summary(dataframe, numerical_col, plot=False):
    quantiles = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]
    print(dataframe[numerical_col].describe(quantiles).T)

    if plot:
        dataframe[numerical_col].hist(bins=20)
        plt.xlabel(numerical_col)
        plt.title(numerical_col)
        plt.show()


for col in num_cols:
    num_summary(df, col, plot=True)


##################################
# ADIM4:NUMERİK DEĞİŞKENLERİN TARGET GÖRE ANALİZİ
##################################
# Target burada Outcome değişkeni.

def target_summary_with_num(dataframe, target, numerical_col):
    print(dataframe.groupby(target).agg({numerical_col: "mean"}), end="\n\n\n")


for col in num_cols:
    target_summary_with_num(df, "Outcome", col)

##################################
# KORELASYON
##################################

df.corr()  # Korelasyonuna bakmak isteseydik.

# Korelasyon Matrisi
f, ax = plt.subplots(figsize=[18, 13])
sns.heatmap(df.corr(), annot=True, fmt=".2f", ax=ax, cmap="magma")
ax.set_title("Correlation Matrix", fontsize=20)
plt.show(block=True)

df.corrwith(df["Outcome"]).sort_values(ascending=False)


diabetic = df[df.Outcome == 1]
healthy = df[df.Outcome == 0]

plt.scatter(healthy.Age, healthy.Insulin, color="green", label="Healthy", alpha = 0.4)
plt.scatter(diabetic.Age, diabetic.Insulin, color="red", label="Diabetic", alpha = 0.4)
plt.xlabel("Age")
plt.ylabel("Insulin")
plt.legend()
plt.show()

##################################
# BASE MODEL KURULUMU
##################################

y = df["Outcome"]
X = df.drop("Outcome", axis=1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=17)

rf_model = RandomForestClassifier(random_state=46).fit(X_train, y_train)
y_pred = rf_model.predict(X_test)


print(f"Accuracy: {round(accuracy_score(y_pred, y_test), 2)}")
print(f"Recall: {round(recall_score(y_pred,y_test),3)}")
print(f"Precision: {round(precision_score(y_pred,y_test), 2)}")
print(f"F1: {round(f1_score(y_pred,y_test), 2)}")
print(f"Auc: {round(roc_auc_score(y_pred,y_test), 2)}")


##################################
# GÖREV 2: FEATURE ENGINEERING
##################################

###############################
# ADIM5:Aykırı Değer Analizi
###############################
def outlier_thresholds(dataframe, col_name, q1=0.25, q3=0.75):
    quartile1 = dataframe[col_name].quantile(q1)
    quartile3 = dataframe[col_name].quantile(q3)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def check_outlier(dataframe, col_name):
    low_limit, up_limit = outlier_thresholds(dataframe, col_name)
    if dataframe[(dataframe[col_name] > up_limit) | (dataframe[col_name] < low_limit)].any(axis=None):
        return True
    else:
        return False


def replace_with_thresholds(dataframe, variable, q1=0.05, q3=0.95):
    low_limit, up_limit = outlier_thresholds(dataframe, variable, q1=0.05, q3=0.95)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit

# Aykırı Değer Analizi ve Baskılama İşlemi
for col in num_cols:
    print(col, check_outlier(df, col))
    if check_outlier(df, col):
        replace_with_thresholds(df, col)

for col in df.columns:
    print(col, check_outlier(df, col))


#################################
# ADIM6: Eksik Değer Analizi
#################################
# Bir insanda Pregnancies ve Outcome dışındaki değişken değerleri 0 olamayacağı bilinmektedir.
# Bundan dolayı bu değerlerle ilgili aksiyon kararı alınmalıdır. 0 olan değerlere NaN atanabilir .
zero_columns = [col for col in df.columns if (df[col].min() == 0 and col not in ["Pregnancies", "Outcome"])]

# Gözlem birimlerinde 0 olan degiskenlerin her birisine gidip 0 iceren gozlem degerlerini NaN ile değiştirdik.
for col in zero_columns:
    df[col] = np.where(df[col] == 0, np.nan, df[col])

msno.heatmap(df)
plt.show()

msno.matrix(df)
plt.show()

#Eksik Değer olan değişkenlerin eksik değer sayılarını ve oranlarını gösteriyor.
def missing_values_table(dataframe, na_name=False):
    na_columns = [col for col in dataframe.columns if dataframe[col].isnull().sum() > 0]
    n_miss = dataframe[na_columns].isnull().sum().sort_values(ascending=False)
    ratio = (dataframe[na_columns].isnull().sum() / dataframe.shape[0] * 100).sort_values(ascending=False)
    missing_df = pd.concat([n_miss, np.round(ratio, 3)], axis=1, keys=['n_miss', 'ratio'])
    print(missing_df, end="\n")
    if na_name:
        return na_columns, missing_df


na_columns, missing_df = missing_values_table(df, na_name=True)


# Eksik Değerlerin Bağımlı Değişken ile İlişkisinin İncelenmesi
def missing_vs_target(dataframe, target, na_columns):
    temp_df = dataframe.copy()
    for col in na_columns:
        temp_df[col + '_NA_FLAG'] = np.where(temp_df[col].isnull(), 1, 0)
    na_flags = temp_df.loc[:, temp_df.columns.str.contains("_NA_")].columns
    for col in na_flags:
        print(pd.DataFrame({"TARGET_MEAN": temp_df.groupby(col)[target].mean(),
                            "Count": temp_df.groupby(col)[target].count()}), end="\n\n\n")


missing_vs_target(df, "Outcome", na_columns)

# Eksik Değerlerin Doldurulması
for col in zero_columns:
    df.loc[df[col].isnull(), col] = df[col].median()


######################
# ADIM2:Yeni Değişken oluşturma
######################

df["NEW_STHICKNESS_BMI"] = df["SkinThickness"] / df["BMI"]
df["NEW_AGE_DPEDIGREE"] = df["Age"] / df["DiabetesPedigreeFunction"]
df["NEW_GLUCOSE_BPRESSURE"] = (df["BloodPressure"] * df["Glucose"]) / 100

df.loc[(df['BMI'] < 18.5), 'NEW_BMI_CAT'] = "underweight"
df.loc[(df['BMI'] >= 18.5) & (df['BMI'] <= 24.9), 'NEW_BMI_CAT'] = 'normal'
df.loc[(df['BMI'] >= 25) & (df['BMI'] < 30), 'NEW_BMI_CAT'] = 'overweight'
df.loc[(df['BMI'] >= 30), 'NEW_BMI_CAT'] = 'obese'

df.loc[(df['Age'] < 21), 'NEW_AGE_CAT'] = 'young'
df.loc[(df['Age'] >= 21) & (df['Age'] < 56), 'NEW_AGE_CAT'] = 'mature'
df.loc[(df['Age'] >= 56), 'NEW_AGE_CAT'] = 'senior'

df.loc[(df['Pregnancies'] == 0), 'NEW_PREGNANCY_CAT'] = 'no_pregnancy'
df.loc[(df['Pregnancies'] == 1), 'NEW_PREGNANCY_CAT'] = 'one_pregnancy'
df.loc[(df['Pregnancies'] > 1), 'NEW_PREGNANCY_CAT'] = 'multi_pregnancy'

df.loc[(df['Glucose'] >= 170), 'NEW_GLUCOSE_CAT'] = 'dangerous'
df.loc[(df['Glucose'] >= 105) & (df['Glucose'] < 170), 'NEW_GLUCOSE_CAT'] = 'risky'
df.loc[(df['Glucose'] < 105) & (df['Glucose'] > 70), 'NEW_GLUCOSE_CAT'] = 'normal'
df.loc[(df['Glucose'] <= 70), 'NEW_GLUCOSE_CAT'] = 'low'

df.loc[(df['BloodPressure'] >= 110), 'NEW_BLOODPRESSURE_CAT'] = 'hypersensitive crisis'
df.loc[(df['BloodPressure'] >= 90) & (
        df['BloodPressure'] < 110), 'NEW_BLOODPRESSURE_CAT'] = 'hypertension'
df.loc[(df['BloodPressure'] < 90) & (df['BloodPressure'] > 70), 'NEW_BLOODPRESSURE_CAT'] = 'normal'
df.loc[(df['BloodPressure'] <= 70), 'NEW_BLOODPRESSURE_CAT'] = 'low'

df.loc[(df['Insulin'] >= 160), 'NEW_INSULIN_CAT'] = 'high'
df.loc[(df['Insulin'] < 160) & (df['Insulin'] >= 16), 'NEW_INSULIN_CAT'] = 'normal'
df.loc[(df['Insulin'] < 16), 'NEW_INSULIN_CAT'] = 'low'

df["Insulin"] = df["Insulin"].fillna(df.groupby("NEW_GLUCOSE_CAT")["Insulin"].transform("median"))

df.groupby("NEW_GLUCOSE_CAT")["Insulin"].median()

df["Insulin"].isna().sum()


##################################
# ENCODING
##################################

# LABEL ENCODING
binary_cols = [col for col in df.columns if df[col].dtypes == "O" and df[col].nunique() == 2]
binary_cols


def label_encoder(dataframe, binary_col):
    labelencoder = LabelEncoder()
    dataframe[binary_col] = labelencoder.fit_transform(dataframe[binary_col])
    return dataframe


for col in binary_cols:
    df = label_encoder(df, col)

# One-Hot Encoding İşlemi
# cat_cols listesinin güncelleme işlemi
cat_cols = [col for col in cat_cols if col not in binary_cols and col not in ["OUTCOME"]]
cat_cols


def one_hot_encoder(dataframe, categorical_cols, drop_first=False):
    dataframe = pd.get_dummies(dataframe, columns=categorical_cols, drop_first=drop_first)
    return dataframe


df = one_hot_encoder(df,cat_cols, drop_first=True)

df.head()

##################################
# STANDARTLAŞTIRMA
##################################

num_cols

scaler = StandardScaler()
df[num_cols] = scaler.fit_transform(df[num_cols])

scaler = RobustScaler()
df[num_cols] = scaler.fit_transform(df[num_cols])

### MODEL ###

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

y = df["Outcome"]
X = df.drop(["Outcome"], axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=123)
rf_model = RandomForestClassifier(random_state=46).fit(X_train, y_train)
y_pred = rf_model.predict(X_test)

print(f"Accuracy: {round(accuracy_score(y_pred, y_test), 2)}")
print(f"Recall: {round(recall_score(y_pred, y_test), 3)}")
print(f"Precision: {round(precision_score(y_pred, y_test), 2)}")
print(f"F1: {round(f1_score(y_pred, y_test), 2)}")
print(f"Auc: {round(roc_auc_score(y_pred, y_test), 2)}")



def plot_importance(model, X, num=len(X)):
    feature_imp = pd.DataFrame({'Value': model.feature_importances_, 'Feature': X.columns})
    plt.figure(figsize=(10, 15))
    sns.set(font_scale=1)
    sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value",
                                                                     ascending=False)[1:num])
    plt.title('Feature Importance')
    plt.tight_layout()
    # plt.savefig('importances-01.png')
    plt.show()


plot_importance(rf_model, X)
