"""
This is a boilerplate pipeline 'train_model'
generated using Kedro 0.18.11
"""
import logging
from datetime import datetime
from typing import Dict

import lightgbm as ltb
import mlflow
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.svm import SVR


def split_data(data: pd.DataFrame, params: Dict):

    shuffled_data = data.sample(frac=1, random_state=params["random_state"])
    rows = shuffled_data.shape[0]

    train_ratio = params["train_ratio"]
    valid_ratio = params["valid_ratio"]

    train_idx = int(rows * train_ratio)
    valid_idx = train_idx + int(rows * valid_ratio)

    assert rows > valid_idx, "test split should not be empty"

    target = params["target"]
    X = shuffled_data.drop(columns=target)
    y = shuffled_data[[target]]

    X_train, y_train = X[:train_idx], y[:train_idx]
    X_valid, y_valid = X[train_idx:valid_idx], y[train_idx:valid_idx]
    X_test, y_test = X[valid_idx:], y[valid_idx:]

    return X_train, X_valid, X_test, y_train, y_valid, y_test


def get_best_model(experiment_id):
    runs = mlflow.search_runs(experiment_id)
    best_model_id = runs.sort_values("metrics.valid_mae")["run_id"].iloc[0]
    best_model = mlflow.sklearn.load_model("runs:/" + best_model_id + "/model")

    return best_model


def train_model(X_train, X_valid, y_train, y_valid):

    # Create and train models.
    linear_reg = LinearRegression()
    rf_reg = RandomForestRegressor()
    sv_reg = SVR()
    xgb_reg = xgb.XGBRegressor()
    ltb_reg = ltb.LGBMRegressor()

    # Create a new experiment
    models = [
        ["Linear Regression", linear_reg],
        ["Random Forest", rf_reg],
        ["Support Vector", sv_reg],
        ["XGBoost", xgb_reg],
        ["LGBM", ltb_reg],
    ]

    experiment_name = "Experiment " + str(datetime.now())
    experiment_id = mlflow.create_experiment(experiment_name)

    for m in models:
        mlflow.autolog()  # registrar automáticamente información del entrenamiento
        with mlflow.start_run(experiment_id=experiment_id, run_name=m[0]):
            # aquí comienza el run
            clf = m[1]
            # entrenamiento de los modelos
            clf.fit(X_train, y_train)

            # predicciones
            pred = clf.predict(X_valid)

            mae = mean_absolute_error(y_valid, pred)
            mlflow.log_metric("valid_mae", mae)

    best_model = get_best_model(experiment_id)

    return best_model


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series):
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    logger = logging.getLogger(__name__)
    logger.info(f"Model has a Mean Absolute Error of {mae} on test data.")
