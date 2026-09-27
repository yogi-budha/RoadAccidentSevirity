# train_model.py - Surkhet local data ma RF + XGBoost train
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)
import xgboost as xgb

# ---- 1. DB bata data load ----
from records.models import AccidentRecord

qs = AccidentRecord.objects.values(
    "hour", "is_night", "season", "festival", "cause",
    "vehicle_type", "location_name", "predicted_severity",
)
df = pd.DataFrame(list(qs))
print(f"Loaded: {len(df)} records")
print(f"Severity distribution:\n{df['predicted_severity'].value_counts()}\n")

# ---- 2. Simple preprocessing ----
# Missing hour -> 12 (din)
df["hour"] = df["hour"].fillna(12)

# 'None' severity hataunay (predict garnay man chaiyo: Fatal/Serious/Slight)
df = df[df["predicted_severity"].isin(["Fatal", "Serious", "Slight"])]
print(f"After removing 'None': {len(df)} records")

# festival -> binary
df["festival"] = df["festival"].apply(
    lambda x: 1 if x == "Dashain-Tihar" else 0)

# ---- 3. Encode categorical features ----
encoders = {}
FEATURES = ["hour", "is_night", "festival", "season",
            "cause", "vehicle_type", "location_name"]

for col in ["season", "cause", "vehicle_type", "location_name"]:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

X = df[["hour", "is_night", "festival", "season_enc",
        "cause_enc", "vehicle_type_enc", "location_name_enc"]].astype(int)
y = df["predicted_severity"]

# target encoder pani save
target_le = LabelEncoder()
y_enc = target_le.fit_transform(y)

print(f"Features: {list(X.columns)}")
print(f"Classes: {list(target_le.classes_)}\n")

# ---- 4. Train/test split ----
X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.25, random_state=42, stratify=y_enc)

print(f"Train: {len(X_train)} | Test: {len(X_test)}\n")

# ---- 4b. SMOTE (mid-term report jastai!) ----
from imblearn.over_sampling import SMOTE
smote = SMOTE(k_neighbors=3, random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

from collections import Counter
print(f"Before SMOTE: {Counter(y_train)}")
print(f"After SMOTE:  {Counter(y_train_sm)}\n")

# ---- 5. Random Forest ----
print("=" * 50)
print("RANDOM FOREST")
print("=" * 50)
rf = RandomForestClassifier(
    n_estimators=200, max_depth=12, min_samples_leaf=3,
    class_weight="balanced", random_state=42)
rf.fit(X_train_sm, y_train_sm)

rf_pred = rf.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, rf_pred):.3f}")
print("\nClassification Report:")
print(classification_report(y_test, rf_pred,
                            target_names=target_le.classes_, zero_division=0))
print("Confusion Matrix (rows=actual, cols=predicted):")
print(pd.DataFrame(confusion_matrix(y_test, rf_pred),
                   index=target_le.classes_,
                   columns=target_le.classes_))

# ---- 6. XGBoost ----
print("\n" + "=" * 50)
print("XGBOOST")
print("=" * 50)
xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.05,
    subsample=0.8, random_state=42, eval_metric="mlogloss")
xgb_model.fit(X_train_sm, y_train_sm)

xgb_pred = xgb_model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, xgb_pred):.3f}")
print("\nClassification Report:")
print(classification_report(y_test, xgb_pred,
                            target_names=target_le.classes_, zero_division=0))
print("Confusion Matrix:")
print(pd.DataFrame(confusion_matrix(y_test, xgb_pred),
                   index=target_le.classes_,
                   columns=target_le.classes_))

# ---- 7. Feature importance ----
print("\n" + "=" * 50)
print("FEATURE IMPORTANCE (Random Forest)")
print("=" * 50)
importance = pd.Series(rf.feature_importances_, index=X.columns)
print(importance.sort_values(ascending=False))

# ---- 8. Save models ----
joblib.dump(rf, "models/model_rf.joblib")
joblib.dump(xgb_model, "models/model_xgb.joblib")
joblib.dump(encoders, "models/encoders.joblib")
joblib.dump(target_le, "models/target_encoder.joblib")

print("\n✅ Saved: models/model_rf.joblib, model_xgb.joblib, encoders.joblib, target_encoder.joblib")