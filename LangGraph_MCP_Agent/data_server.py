from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, root_mean_squared_error
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

mcp = FastMCP("DataAnalysis")

@mcp.tool()
def describe_column(csv_path: str, column: str) -> dict:
    """
    CSV 파일의 특정 열에 대한 요약 통계 정보를 반환합니다.
    
    Args:
        csv_path (str): CSV 파일의 경로입니다.
        column (str): 통계를 계산할 열의 이름입니다.

    Returns:
        dict: 지정된 열의 요약 통계 정보를 포함하는 딕셔너리입니다.
    """
    df = pd.read_csv(csv_path)
    if column not in df.columns:
        raise ValueError(f"Column {column} not found in the CSV file.")
    return df[column].describe().to_dict()

@mcp.tool()
def plot_histogram(csv_path: str, column: str, bins: int = 10) -> dict:
    """
    CSV 파일의 특정 열에 대한 히스토그램을 생성합니다.
    
    Args:
        csv_path (str): CSV 파일의 경로입니다.
        column (str): 히스토그램을 그릴 열의 이름입니다.
        bins (int, optional): 히스토그램에서 사용할 구간(bin)의 수입니다.
        
    Returns:
        dict: 히스토그램 이미지의 경로를 포함하는 딕셔너리입니다.
    """
    df = pd.read_csv(csv_path)
    if column not in df.columns:
        raise ValueError(f"Column {column} not found in the CSV file.")
    
    plt.figure(figsize=(8, 6))
    sns.histplot(df[column].dropna(), bins=bins, kde=True, stat="density")
    plt.xlabel(column)
    plt.ylabel("Density")
    plt.title(f"Density Histogram of {column}")
    
    output_path = f"histogram_{column}.png"
    plt.savefig(output_path)
    plt.close()
    
    return output_path

@mcp.tool()
def model(csv_path: str, x_columns: list, y_column: str) -> dict:
    """
    대상 열의 유형에 따라 자동으로 모델(분류 또는 회귀)을 학습합니다.

    Args:
        csv_path: CSV 파일의 경로입니다.
        x_columns: 특성 열 이름들의 리스트입니다.
        y_column: 대상 열 이름입니다.

    Returns:
        모델 유형, 성능 지표, 점수를 포함하는 딕셔너리입니다.
    """
    df = pd.read_csv(csv_path)
    
    for col in x_columns + [y_column]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in CSV.")

    X = df[x_columns]
    y = df[y_column]

    # 범주형(object) 데이터를 숫자형으로 변환
    # LabelEncoder를 사용하여 각 고유 값에 숫자 레이블을 할당
    for col in X.select_dtypes(include=["object"]).columns:
        X[col] = LabelEncoder().fit_transform(X[col])

    # 대상 변수가 범주형(object)이거나 고유값이 10개 이하인 경우 분류 문제로 판단
    is_classification = y.dtype == "object" or len(y.unique()) <= 10

    if is_classification:
        y = LabelEncoder().fit_transform(y)
        model = RandomForestClassifier()
        metric_name = "accuracy"
    else:
        model = RandomForestRegressor()
        metric_name = "rmse"

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    if is_classification:
        score = accuracy_score(y_test, y_pred)
        model_type = "classification"
    else:
        score = root_mean_squared_error(y_test, y_pred, squared=False)
        model_type = "regression"

    return {"model_type": model_type, "metric": metric_name, "score": score}

@mcp.prompt()
def default_prompt(message: str) -> list[base.Message]:
    return [
        base.AssistantMessage(
            "You are a helpful data analysis assistant. \n"
            "Please clearly organize and return the results of the tool calling and the data analysis."
        ),
        base.UserMessage(message),
    ]

if __name__ == "__main__":
    print("MCP Server is running...")
    mcp.run(transport="stdio")