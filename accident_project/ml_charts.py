# ml_charts.py - ML charts for the report
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from imblearn.over_sampling import SMOTE

# Load data as in train_model.py
from records.models import AccidentRecord

qs = AccidentRecord.objects.values(
    "hour", "is_night", "season", "festival", "cause",
    "vehicle_type", "location_name", "predicted_severity")
df = pd.DataFrame(list(qs))
df["hour"] = df["hour"].fillna(12)
df = df[df["predicted_severity"].isin(["Fatal", "Serious", "Slight"])]
df["festival"] = df["festival"].apply(lambda x: 1 if x == "Dashain-Tihar" else 0)

encoders = {}
for col in ["season", "cause", "vehicle_type", "location_name"]:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

X = df[["hour", "is_night", "festival", "season_enc",
        "cause_enc", "vehicle_type_enc", "location_name_enc"]].astype(int)
target_le = LabelEncoder()
y = target_le.fit_transform(df["predicted_severity"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y)

smote = SMOTE(k_neighbors=3, random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

rf = RandomForestClassifier(n_estimators=200, max_depth=12,
                            min_samples_leaf=3, class_weight="balanced",
                            random_state=42)
rf.fit(X_train_sm, y_train_sm)

# ---- Figure 1: Confusion Matrix ----
pred = rf.predict(X_test)
cm = confusion_matrix(y_test, pred)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(3))
ax.set_yticks(range(3))
ax.set_xticklabels(target_le.classes_)
ax.set_yticklabels(target_le.classes_)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion Matrix — Random Forest (SMOTE)", fontweight="bold")
for i in range(3):
    for j in range(3):
        ax.text(j, i, cm[i, j], ha="center", va="center",
                color="white" if cm[i, j] > cm.max()/2 else "black",
                fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("static/charts/confusion_matrix.png", dpi=150)
plt.close()
print("✅ confusion_matrix.png")

# ---- Figure 2: Feature Importance ----
imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(imp.index, imp.values, color="#1a3d6d")
ax.set_xlabel("Importance")
ax.set_title("Feature Importance — Random Forest", fontweight="bold")
for i, v in enumerate(imp.values):
    ax.text(v + 0.005, i, f"{v:.1%}", va="center", fontweight="bold")
plt.tight_layout()
plt.savefig("static/charts/feature_importance.png", dpi=150)
plt.close()
print("✅ feature_importance.png")