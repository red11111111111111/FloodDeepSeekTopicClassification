import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

def load_model_results(model_name, result_dir='results'):
    result_path = os.path.join(result_dir, f"{model_name}_results.json")
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_bar_comparison(model1_name, model1_metrics, model2_name, model2_metrics, save_dir='static/images'):
    metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    model1_values = [model1_metrics[m] for m in metrics]
    model2_values = [model2_metrics[m] for m in metrics]

    x = np.arange(len(metrics))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, model1_values, width, label=model1_name)
    plt.bar(x + width/2, model2_values, width, label=model2_name)
    plt.xlabel('Metrics')
    plt.ylabel('Values')
    plt.title('Model Performance Comparison')
    plt.xticks(x, ['Accuracy', 'Precision', 'Recall', 'F1-Score'])
    plt.legend()
    plt.tight_layout()

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, 'bar_comparison.png')
    plt.savefig(save_path)
    plt.close('all')
    return save_path

def compare_models(model1_name, model1_metrics, model2_name, model2_metrics):
    bar_chart_path = plot_bar_comparison(model1_name, model1_metrics, model2_name, model2_metrics)
    metrics = {
        'metrics': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
        model1_name: [
            model1_metrics['accuracy'],
            model1_metrics['precision'],
            model1_metrics['recall'],
            model1_metrics['f1_score']
        ],
        model2_name: [
            model2_metrics['accuracy'],
            model2_metrics['precision'],
            model2_metrics['recall'],
            model2_metrics['f1_score']
        ]
    }
    return {
        'bar_chart': bar_chart_path,
        'metrics': metrics
    }