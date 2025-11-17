#!/usr/bin/env python3
import glob
import joblib
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


st.set_page_config(page_title="Customer Segmentation", layout="centered")


@st.cache_resource
def load_model():
    paths = glob.glob("customer_kmeans_model_*.pkl")
    if not paths:
        raise FileNotFoundError("Model file not found. Run train_customer_model.py first.")
    return joblib.load(paths[0])


@st.cache_resource
def load_metadata():
    return joblib.load("customer_metadata.pkl")


def main():
    st.title("Customer Segmentation Explorer")

    model = load_model()
    meta = load_metadata()

    data = np.array(meta["data"], dtype=float)
    feature_names = meta.get("feature_names", ["Annual Income (k$)", "Spending Score (1-100)"])

    st.sidebar.header("Input")
    income_min, income_max = float(np.min(data[:, 0])), float(np.max(data[:, 0]))
    score_min, score_max = float(np.min(data[:, 1])), float(np.max(data[:, 1]))

    default_income = int(np.median(data[:, 0]))
    default_score = int(np.median(data[:, 1]))

    annual_income = st.sidebar.slider("Annual Income (k$)", min_value=int(income_min), max_value=int(income_max),
                                      value=default_income, step=1)
    spending_score = st.sidebar.slider("Spending Score (1-100)", min_value=int(score_min), max_value=int(score_max),
                                       value=default_score, step=1)

    user_point = np.array([[annual_income, spending_score]], dtype=float)
    pred_cluster = int(model.predict(user_point)[0])

    st.metric(label="Predicted Cluster ID", value=str(pred_cluster))

    fig = plt.figure()
    plt.scatter(data[:, 0], data[:, 1], s=20, alpha=0.6)
    plt.scatter(user_point[0, 0], user_point[0, 1], s=140, marker="x")
    plt.xlabel(feature_names[0])
    plt.ylabel(feature_names[1])
    plt.title("Simulated Customers and Your Input")
    st.pyplot(fig)

    st.caption("Tip: move the sliders on the left to see how the predicted cluster changes.")


if __name__ == "__main__":
    main()
