"""後方互換ラッパー。

今後手法ごとにファイルを分離するため、KMeans本体は `cluster_kmeans.py` に移動。
このファイルは従来の呼び出し名を維持するエントリポイントとして残す。
"""

from cluster_kmeans import main, run_analysis


if __name__ == "__main__":
    main()
