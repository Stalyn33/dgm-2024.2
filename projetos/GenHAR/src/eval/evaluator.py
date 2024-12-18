from sklearn.metrics import accuracy_score, pairwise_distances
from scipy.stats import wasserstein_distance
from utils import log
import os
import utils.report_ut as r_ut

# https://github.com/gretelai/public_research/blob/main/oss_doppelganger/analysis.ipynb
# https://nannyml.readthedocs.io/en/stable/how_it_works/univariate_drift_comparison.html
# https://itsudit.medium.com/the-jensen-shannon-divergence-a-measure-of-distance-between-probability-distributions-23b2b1146550


class Evaluator:
    def __init__(self, config, df_train, df_test, df_val, df_synthetic):
        self.df_train = df_train
        self.df_test = df_test
        self.df_val = df_val
        self.df_synthetic = df_synthetic
        self.config = config["evaluations"]
        self.dataset = config["dataset"]
        self.transform = config["transform"]
        self.model = config["model"]
        self.activity_names = ["sit", "stand", "walk", "stair up", "stair down", "run"]
        self.folder_reports = f"{self.config['folder_reports']}/reports/"
        self.folder_images = f"{self.config['folder_reports']}/images/"
        os.makedirs(self.folder_reports, exist_ok=True)
        os.makedirs(self.folder_images, exist_ok=True)

    def eval_dataset(self, dataset, title):
        from eval.metrics.unsupervised_metrics import UnsupervisedLearningMetrics

        print(dataset.columns)
        metrics_uns = UnsupervisedLearningMetrics(dataset)
        metrics_uns_val = metrics_uns.evaluate()
        log.print_debug(title)
        log.print_debug(metrics_uns_val)

        from eval.dataset_eval import TimeSeriesDatasetEvaluator

        evaluator = TimeSeriesDatasetEvaluator(
            dataset,
            label_col="label",
            label_names=["sit", "stand", "walk", "stair up", "stair down", "run"],
        )
        log.print_debug("....gerando graficos....")

        fig1 = evaluator.plot_samples()
        fig2 = evaluator.tsne_plot()
        fig3 = evaluator.plot_random_sensor_samples_single_dataset(
            dataset, self.activity_names, num_samples=6, sensor="gyro"
        )
        fig4 = evaluator.plot_random_sensor_samples_single_dataset(
            dataset, self.activity_names, num_samples=6, sensor="accel"
        )
        fig5 = evaluator.plot_i_samples(n_samples=10, reshape=True)
        thresholds = {
            "Silhouette Score": (-1, 1),  # prox 1 melhors ok
            # quanto mais prox zero melhor
            "Davies-Bouldin Index": (0, 100),
            "Calinski-Harabasz Index": (0, 500),  # maior melhor
            "Entropy": (0, 2),  # definir limites
            "Mutual Information": (0, 500),  # entre maior melhor
        }
        fig6 = evaluator.plot_metrics_comparison(metrics_uns_val, thresholds)
        # fig6=evaluator.plot_autocorrelation()
        # fig10 = evaluator.plot_pca_correlation()
        # fig3=evaluator.histogram_density()
        # fig4=evaluator.plot_acf_pacf_all()

        # Usar a função save_fig_pdf para salvar as figuras:
        r_ut.save_fig_pdf(f"{self.folder_reports}{title}.pdf", fig1, fig2, fig3, fig4, fig5, fig6)

    def ml_metrics(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC
        from eval.ml.Mach_learning import ModelEvaluator

        # Step 2: classifiers
        classifiers = {"Random Forest": RandomForestClassifier(), "SVM": SVC()}
        # Step 3: Initialize the evaluator
        evaluator_ml = ModelEvaluator(
            classifiers=classifiers,
            df_train=self.df_train,
            df_test=self.df_test,
            df_val=self.df_val,
            df_synthetic=self.df_synthetic,
            label="label",
            generator_name="example_generator",
            dataset_name="example_dataset",
            transformation_name="example_transformation",
        )

        # Step 4: Evaluate models
        metrics = evaluator_ml.evaluate_all_models()

        # Step 5: Plot metrics
        fig1 = evaluator_ml.plot_metrics(metrics)
        fig2 = evaluator_ml.plot_boxplots(metrics)
        r_ut.save_fig_pdf(
            f"{self.folder_reports}{self.dataset}_{self.transform}_{self.model}_ML.pdf",
            *fig1,
            *fig2,
        )
        # evaluator_ml.save_metrics_to_pdf(metrics,f"{self.folder_reports}{self.dataset}_{self.transform}_{self.model}_ML.pdf")
        # Step 6: Save metrics to CSV
        # evaluator_ml.save_metrics_to_csv(metrics, folder_name=f"{self.folder_reports}")

    def eval(self):
        if self.config["dataset_eval"]["original"]:
            title = f"{self.dataset}_{self.transform}_{self.model}_dataset_train"
            self.eval_dataset(self.df_train, title)
        if self.config["dataset_eval"]["synthetic"]:
            title = f"{self.dataset}_{self.transform}_{self.model}_dataset_synth"
            self.eval_dataset(self.df_synthetic, title)

        if self.config["gen_vs_orig_eval"]["visualizations"]:
            from eval.real_synthetic_eval import RealSyntheticComparator

            label_col = "label"

        if self.config["gen_vs_orig_eval"]["visualizations"]:
            print("orig s original")
            from eval.real_synthetic_eval import RealSyntheticComparator

            label_col = "label"

            comparator = RealSyntheticComparator(
                self.df_train, self.df_synthetic, label_col, self.activity_names
            )
            fig0=comparator.visualize_distribution("", "disti")
            fig0.savefig(f"{self.folder_images}{self.dataset}{self.transform}_{self.model}_distribution.jpg", format='jpg', dpi=300)
            # Comparar distribuição de classes
            fig1 = comparator.compare_class_distribution()

            # Comparar t-SNE
            fig2 = comparator.compare_tsne()
            fig3 = comparator.visualize_tsne_unlabeled()
            fig3.savefig(f"{self.folder_images}{self.dataset}{self.transform}_{self.model}_tsne.jpg", format='jpg', dpi=300)

            fig4 = comparator.tsne_subplots_by_labels()
            fig5 = comparator.plot_samplesT_by_label(num_samples=3)

            # Comparar amostras aleatórias
            fig6 = comparator.compare_images(reshape=True)
            # fig4=comparator.visualize_distribution()
            # Comparar matrizes de correlação

            fig7 = comparator.plot_random_sensor_samples_comparison()
            fig8 = comparator.plot_random_samples_comparison_by_labels(num_samples=5)
            r_ut.save_fig_pdf(
                f"{self.folder_reports}{self.dataset}_{self.transform}_{self.model}_real_vs_gen.pdf",
                fig0,
                fig1,
                fig2,
                fig3,
                fig4,
                fig5,
                fig6,
                fig7,
                fig8,
            )

            if self.config["gen_vs_orig_eval"]["ml"]:
                self.ml_metrics()
