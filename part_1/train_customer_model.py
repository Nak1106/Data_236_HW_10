#!/usr/bin/env python3
"""
Simple trainer for a synthetic customer segmentation model.
Generates 200 rows with two features:
- Annual Income (k$)
- Spending Score (1-100)
Trains KMeans with k=5 and saves the model and metadata.
"""

import os
import numpy as np
from sklearn.cluster import KMeans
import joblib


def simulate_data(seed=42, n_samples=200):
    rng = np.random.default_rng(seed)
    income = rng.normal(loc=60.0, scale=20.0, size=n_samples)
    income = np.clip(income, 10.0, 150.0)
    score = rng.uniform(1.0, 100.0, size=n_samples)
    X = np.column_stack([income, score])
    return X


def main():
    # You can set STUDENT_NAME in your shell, for example:
    # export STUDENT_NAME="jane_doe"
    seed = int(os.getenv("RANDOM_SEED", "42"))
    student_name = os.getenv("STUDENT_NAME", "yourname").strip().lower().replace(" ", "_")

    X = simulate_data(seed=seed, n_samples=200)

    model = KMeans(n_clusters=5, n_init=10, random_state=seed)
    model.fit(X)

    model_path = f"customer_kmeans_model_{student_name}.pkl"
    joblib.dump(model, model_path)

    metadata = {
        "feature_names": ["Annual Income (k$)", "Spending Score (1-100)"],
        "cluster_centers": model.cluster_centers_.tolist(),
        "random_seed": seed,
        "data": X.tolist()
    }
    joblib.dump(metadata, "customer_metadata.pkl")

    print(f"Saved model to {model_path}")
    print("Saved metadata to customer_metadata.pkl")


if __name__ == "__main__":
    main()
