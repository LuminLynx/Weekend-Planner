
import joblib, numpy as np
from lightgbm import LGBMClassifier
from .features import make_features

def train(rows: list[dict]):
    # rows: [{ "series": [...], "label": 0/1 }, ...]
    X, y, keys = [], [], None
    for r in rows:
        feats = make_features(r["series"], None)
        if keys is None: keys = list(feats.keys())
        X.append([feats[k] for k in keys])
        y.append(r["label"])
    clf = LGBMClassifier(n_estimators=200, max_depth=6, learning_rate=0.08)
    clf.fit(np.array(X), np.array(y))
    joblib.dump({"model": clf, "features": keys}, "app/models/price_drop/model.bin")
    return True
