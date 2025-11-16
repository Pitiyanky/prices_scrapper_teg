import pandas as pd
import threading
import numpy as np
import logging
import joblib
import os
import re
import unicodedata
from sqlalchemy import create_engine
from thefuzz import fuzz
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from data_processor.utils import UDMExtractor
from config import DB_CONNECTION_URL, MARCAS_CONOCIDAS, SCORE_THRESHOLD, STOP_WORDS

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self, db_config):
        """
        Inicializa el analizador central.
        Requiere la configuración de la BD para poder obtener datos.
        """
        if not db_config:
            raise ValueError("Analyzer requiere db_config para funcionar.")
        
        self.db_config = db_config
        self._lock = threading.Lock()

        self.last_analysis_timestamp = None
        self.explainer = None
        self.X_reconstructed = None
        self.model = None
        self.products_df = None
        self.feature_names_for_model = None
        self._analysis_artifacts_cache = None
        self.is_data_updated = False

        self.marcas_conocidas_normalized = sorted(
            [self._normalize_text(b) for b in MARCAS_CONOCIDAS], key=len, reverse=True
        )

    def load_model_and_data(self):
        """
        Carga el modelo de predicción y el DataFrame pre-calculado al iniciar la app.
        """
        model_path = 'model/price_prediction_model.joblib'
        data_path = 'model/products_with_predictions.csv'
        
        if not os.path.exists(model_path) or not os.path.exists(data_path):
            logger.warning("Archivos del modelo o de datos no encontrados. Ejecute 'train_model.py' primero.")
            return

        try:
            with self._lock:
                self.model = joblib.load(model_path)
                self.products_df = pd.read_csv(data_path)
                self.feature_names_for_model = self.model.feature_names_in_.tolist()

                logger.info("Modelo de predicción y datos de productos cargados exitosamente.")
                logger.info(f"Características identificadas para el modelo: {self.feature_names_for_model}")
        except Exception as e:
            logger.error(f"Error al cargar el modelo o los datos: {e}", exc_info=True)
    
    def get_price_intelligence_data(self):
        """Devuelve el DataFrame con las predicciones."""
        return self.products_df.copy() if self.products_df is not None else pd.DataFrame()

    def get_model(self):
        """Devuelve el modelo de predicción."""
        return self.model
    
    def fetch_data(self, start_date=None, end_date=None, product_types=None, search_term=None, retailers=None):
        """
        Busca datos pre-filtrados en la BD y luego ejecuta el análisis sobre ellos.
        Este es ahora el método principal para obtener datos para el dashboard.
        """
        with self._lock:
            logger.info(f"Iniciando fetch_data con filtros: D:{start_date}-{end_date}, T:{product_types}, S:'{search_term}'")
            try:
                from database_manager import PostgresManager
                
                with PostgresManager(self.db_config) as db_manager:
                    if not db_manager.conn:
                        logger.error("Analyzer: No se pudo conectar a la BD.")
                        return pd.DataFrame()
                    
                    products_list = db_manager.get_preprocessed_products(
                        start_date=start_date,
                        end_date=end_date,
                        product_types=product_types,
                        search_term=search_term,
                        retailers=retailers
                    )
                    
                if not products_list:
                    logger.info("La consulta a la BD no devolvió resultados con los filtros aplicados.")
                    return pd.DataFrame()

                df_filtered_from_db = pd.DataFrame(products_list)
                
                return df_filtered_from_db

            except Exception as e:
                logger.error(f"Analyzer: Error durante fetch_data: {e}", exc_info=True)
                return pd.DataFrame()

    def get_initial_filter_options(self):
        """
        Método para obtener las opciones iniciales para los filtros del dashboard.
        Llama al método optimizado del PostgresManager.
        """
        try:
            from database_manager import PostgresManager
            with PostgresManager(self.db_config) as db_manager:
                if not db_manager.conn: return None
                return db_manager.get_filter_metadata()
        except Exception as e:
            logger.error(f"Analyzer: Error obteniendo opciones de filtros: {e}", exc_info=True)
            return None
    
    def predict_price(self, input_features:dict, real_price:float):
        """
        Recibe un diccionario con las características de un producto y devuelve una predicción de precio.
        
        Args:
            input_features (dict): Un diccionario donde las claves son los nombres de las 
                                   características y los valores son los datos ingresados.
            real_price (float): El precio real del producto para comparativa.
        
        Returns:
            tuple: (prediction, error_message). Si la predicción es exitosa, 
                   error_message es None. Si falla, prediction es None.
        """
        if self.model is None or self.feature_names_for_model is None:
            logger.error("Intento de predicción sin modelo o nombres de características cargados.")
            return None, "El modelo no está cargado correctamente."

        try:
            input_features['comp1_diff'] = real_price - input_features.get('comp1_diff', 0)
            input_features['comp2_diff'] = real_price - input_features.get('comp2_diff', 0)
            input_features['comp3_diff'] = real_price - input_features.get('comp3_diff', 0)
            input_df = pd.DataFrame([input_features])
            input_df = input_df[self.feature_names_for_model]
            prediction = self.model.predict(input_df)
            return prediction[0], None

        except KeyError as e:
            logger.error(f"Error de predicción: Falta la característica {e} en los datos de entrada.")
            return None, f"Falta una característica requerida por el modelo: {e}"
        except Exception as e:
            logger.error(f"Error inesperado durante la predicción: {e}", exc_info=True)
            return None, f"Ocurrió un error inesperado durante la predicción: {e}"
        
    def _compute_analysis_artifacts(self):
        """
        Calcula todos los artefactos de análisis a partir del CSV cargado.
        Este método se llama solo una vez y sus resultados se guardan en caché.
        """
        if self.model is None or self.products_df is None:
            logger.error("No se pueden calcular los artefactos porque el modelo o los datos no están cargados.")
            return None

        df = self.products_df.copy()

        metrics = {
            'r2': r2_score(df['precio_promedio_real'], df['precio_promedio_sugerido']),
            'mae': mean_absolute_error(df['precio_promedio_real'], df['precio_promedio_sugerido']),
            'mse': mean_squared_error(df['precio_promedio_real'], df['precio_promedio_sugerido'])
        }

        X_reconstructed = pd.DataFrame()
        X_reconstructed['total_ganancia'] = df['total_ganancia']
        X_reconstructed['comp1_diff'] = df['precio_promedio_real'] - df['precio_competencia_1']
        X_reconstructed['comp2_diff'] = df['precio_promedio_real'] - df['precio_competencia_2']
        X_reconstructed['comp3_diff'] = df['precio_promedio_real'] - df['precio_competencia_3']

        self.X_reconstructed = X_reconstructed
        if hasattr(self.model, 'feature_names_in_'):
             X_reconstructed = X_reconstructed[self.model.feature_names_in_]
        
        y = df['precio_promedio_real']

        self.explainer = shap.TreeExplainer(self.model)
        shap_values = self.explainer(self.X_reconstructed)
        shap_df = pd.DataFrame(shap_values.values, columns=self.X_reconstructed.columns)

        full_analysis_df = pd.concat([self.X_reconstructed, df['precio_promedio_real'].rename('precio_mes_actual')], axis=1)

        artifacts = {
            "metrics": metrics,
            "description": full_analysis_df.describe(),
            "correlation": full_analysis_df.corr(),
            "predictions": df.rename(columns={'diferencia_precio_vs_sugerido': 'residuals'}),
            "shap_values_df": shap_df,
            "shap_values_obj": shap_values,
            "full_dataset": full_analysis_df,
            "X_reconstructed": self.X_reconstructed
        }
        self.is_data_updated = True
        logger.info("Cálculo y caché de artefactos de análisis completado.")
        return artifacts
    
    def get_model_analysis_data(self):
        """
        Punto de entrada para la página de análisis.
        """
        if self._analysis_artifacts_cache is None or self.is_data_updated:
            self._analysis_artifacts_cache = self._compute_analysis_artifacts()
        
        return self._analysis_artifacts_cache
        
    def get_price_intelligence_data(self):
        """Devuelve el df principal para las otras páginas."""
        return self.products_df
    
    def _remove_emojis(self, text: str) -> str:
        emoji_pattern = re.compile("["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def _normalize_text(self, text: str) -> str:
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return re.sub(r'[^\w\s\.]', '', text).lower()

    def _normalize_name_advanced(self, name: str) -> str:
        name = self._remove_emojis(name)
        name = self._normalize_text(name)
        words = [w for w in name.split() if w not in STOP_WORDS]
        words.sort()
        return ' '.join(words)

    def _extract_brand(self, text: str, normalized_brands: list) -> str | None:
        normalized_text = self._normalize_text(text)
        for brand in normalized_brands:
            if re.search(r'\b' + re.escape(brand) + r'\b', normalized_text):
                return brand
        return None
    
    def _train_and_save_model(self, df: pd.DataFrame):
        
        df['comp1_diff'] = df['precio_mes_actual'] - df['precio_competidor_1']
        df['comp2_diff'] = df['precio_mes_actual'] - df['precio_competidor_2']
        df['comp3_diff'] = df['precio_mes_actual'] - df['precio_competidor_3']

        product_names = df[['product_id', 'name']].drop_duplicates().set_index('product_id')
        sum_df = df.groupby('product_id')[['total_ganancia']].sum().rename(columns={'total_ganancia': 'total_ganancia'})
        mean_df = df.groupby('product_id')[['comp1_diff', 'comp2_diff', 'comp3_diff', 'precio_mes_actual', 
                                             'precio_competidor_1', 'precio_competidor_2', 'precio_competidor_3']].mean()
        
        products = pd.concat([sum_df, mean_df], axis=1).reset_index()

        features = ['total_ganancia', 'comp1_diff', 'comp2_diff', 'comp3_diff']
        target = 'precio_mes_actual'
        
        X = products[features]
        y = products[target]
        
        model = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
        model.fit(X, y)
        logger.info("Modelo entrenado.")

        products['precio_promedio_sugerido'] = model.predict(X)
        products_with_names = products.merge(product_names, on='product_id')
        
        products_with_predictions = pd.DataFrame({
            'product_id': products_with_names['product_id'],
            'name': products_with_names['name'],
            'precio_promedio_real': products_with_names['precio_mes_actual'],
            'precio_promedio_sugerido': products_with_names['precio_promedio_sugerido'],
            'total_ganancia': products_with_names['total_ganancia'],
            'precio_competencia_1': products_with_names['precio_competidor_1'],
            'precio_competencia_2': products_with_names['precio_competidor_2'],
            'precio_competencia_3': products_with_names['precio_competidor_3'],
            'diferencia_precio_vs_sugerido': products_with_names['precio_mes_actual'] - products_with_names['precio_promedio_sugerido']
        })

        output_dir = 'model'
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump(model, os.path.join(output_dir, 'price_prediction_model.joblib'))
        products_with_predictions.to_csv(os.path.join(output_dir, 'products_with_predictions.csv'), index=False)
        logger.info(f"Modelo y predicciones guardados en la carpeta '{output_dir}'.")

        self.model = model
        self.products_df = products_with_predictions
        self.feature_names_for_model = model.feature_names_in_.tolist()
        self.is_data_updated = True
        self._analysis_artifacts_cache = None
        logger.info("Estado interno del Analyzer actualizado con el nuevo modelo.")

    def _perform_product_matching(self, market_products_df: pd.DataFrame, odoo_products_df: pd.DataFrame) -> pd.DataFrame:
        """Paso 2: Realiza el matching de productos entre las dos fuentes de datos."""
        logger.info("Pipeline (2/5): Ejecutando el algoritmo de matching de productos...")

        market_products_df['price_usd'] = market_products_df['price']
        odoo_products_df['price_usd'] = odoo_products_df['dollar_price']
        udm_extractor = UDMExtractor()
        for df in [market_products_df, odoo_products_df]:
            df['normalized_name'] = df['name'].apply(self._normalize_name_advanced)
            df['brand'] = df['name'].apply(lambda x: self._extract_brand(x, self.marcas_conocidas_normalized))
            df['quantity_unit'] = df['name'].apply(udm_extractor._extract_quantity_unit_pair)
        
        market_products = market_products_df.to_dict('records')
        odoo_products = odoo_products_df.to_dict('records')
        successful_matches = []
        total_market = len(market_products)

        for i, market_prod in enumerate(market_products, 1):
            if i % 200 == 0:
                logger.info(f"Procesando producto del mercado: {i}/{total_market}")
                
            best_match = None
            best_score = -1

            for odoo_prod in odoo_products:
                if market_prod['brand'] and odoo_prod['brand'] and market_prod['brand'] != odoo_prod['brand']:
                    continue

                market_qty_unit = market_prod['quantity_unit']
                odoo_qty_unit = odoo_prod['quantity_unit']
                if market_qty_unit and odoo_qty_unit:
                    if market_qty_unit[1] != odoo_qty_unit[1] or market_qty_unit[0] != odoo_qty_unit[0]:
                        continue
                current_score = fuzz.token_set_ratio(market_prod['normalized_name'], odoo_prod['normalized_name'])

                if current_score > best_score:
                    best_score = current_score
                    best_match = odoo_prod
            
            if best_match and best_score >= SCORE_THRESHOLD:
                successful_matches.append({
                    'cluster_id': best_match['id'],
                    'vendedor': market_prod['website_id'],
                    'producto': market_prod['name']
                })
                
        logger.info(f"Matching completado. Se encontraron {len(successful_matches)} coincidencias.")
        return pd.DataFrame(successful_matches)

    def _train_and_save_model(self, df: pd.DataFrame):
        """
        Paso final del pipeline: Toma el DataFrame de entrenamiento completo
        y entrena, predice y guarda el modelo.
        """
        logger.info("Pipeline (4/5): Entrenando el modelo...")
        
        df['comp1_diff'] = df['precio_mes_actual'] - df['precio_competidor_1']
        df['comp2_diff'] = df['precio_mes_actual'] - df['precio_competidor_2']
        df['comp3_diff'] = df['precio_mes_actual'] - df['precio_competidor_3']

        product_names = df[['product_id', 'name']].drop_duplicates().set_index('product_id')
        sum_df = df.groupby('product_id')[['total_ganancia']].sum()
        mean_df = df.groupby('product_id')[['comp1_diff', 'comp2_diff', 'comp3_diff', 'precio_mes_actual', 
                                             'precio_competidor_1', 'precio_competidor_2', 'precio_competidor_3']].mean()
        
        products = pd.concat([sum_df, mean_df], axis=1).reset_index()

        features = ['total_ganancia', 'comp1_diff', 'comp2_diff', 'comp3_diff']
        target = 'precio_mes_actual'
        
        X = products[features]
        y = products[target]
        
        model = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
        model.fit(X, y)
        logger.info("Modelo entrenado.")

        products['precio_promedio_sugerido'] = model.predict(X)
        products_with_names = products.merge(product_names, on='product_id')
        
        products_with_predictions = pd.DataFrame({
            'product_id': products_with_names['product_id'],
            'name': products_with_names['name'],
            'precio_promedio_real': products_with_names['precio_mes_actual'],
            'precio_promedio_sugerido': products_with_names['precio_promedio_sugerido'],
            'total_ganancia': products_with_names['total_ganancia'],
            'precio_competencia_1': products_with_names['precio_competidor_1'],
            'precio_competencia_2': products_with_names['precio_competidor_2'],
            'precio_competencia_3': products_with_names['precio_competidor_3'],
            'diferencia_precio_vs_sugerido': products_with_names['precio_mes_actual'] - products_with_names['precio_promedio_sugerido']
        })

        output_dir = 'model'
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump(model, os.path.join(output_dir, 'price_prediction_model.joblib'))
        products_with_predictions.to_csv(os.path.join(output_dir, 'products_with_predictions.csv'), index=False)
        logger.info(f"Pipeline (5/5): Modelo y predicciones guardados en la carpeta '{output_dir}'.")

        self.model = model
        self.products_df = products_with_predictions
        self.feature_names_for_model = model.feature_names_in_.tolist()
        self.is_data_updated = True
        self._analysis_artifacts_cache = None
        logger.info("Estado interno del Analyzer actualizado con el nuevo modelo.")

    def run_training_from_df(self, df_from_csv: pd.DataFrame):
        """
        Orquesta el pipeline completo de entrenamiento usando un CSV para los datos internos
        y la BBDD para los datos de la competencia.
        """
        with self._lock:
            engine = None
            try:
                logger.info("Pipeline (1/5): Obteniendo datos de la competencia desde la base de datos...")
                engine = create_engine(DB_CONNECTION_URL)
                competitor_query = """
                SELECT DISTINCT ON (p.id, w.id)
                    p.id as product_id, p.name, w.id as website_id, pp.price, pp.currency
                FROM products p
                JOIN preprocessed_products pp ON p.id = pp.product_id
                JOIN websites w ON pp.website_id = w.id
                ORDER BY p.id, w.id, pp.scrape_timestamp DESC;
                """
                market_df = pd.read_sql(competitor_query, engine)
                market_df['price'] = np.where(market_df['currency'] == 'BSD', market_df['price'] / 100, market_df['price'])

                internal_df = df_from_csv.copy()
                internal_df.rename(columns={'product_id': 'id', 'precio_promedio': 'dollar_price'}, inplace=True)

                clusters_df = self._perform_product_matching(market_df, internal_df)
                
                if clusters_df.empty:
                    raise ValueError("El proceso de matching no encontró ninguna coincidencia entre el archivo CSV y los datos de la competencia.")

                logger.info("Pipeline (3/5): Construyendo el dataset de entrenamiento final...")
                competitor_prices = pd.merge(
                    clusters_df, market_df[['name', 'website_id', 'price']],
                    left_on=['producto', 'vendedor'], right_on=['name', 'website_id']
                )

                competitor_pivot_df = competitor_prices.pivot_table(
                    index='cluster_id', columns='vendedor', values='price'
                ).fillna(0)
                
                num_competitors = len(competitor_pivot_df.columns)
                competitor_pivot_df.columns = [f'precio_competidor_{i+1}' for i in range(num_competitors)]
                for i in range(num_competitors + 1, 4):
                    competitor_pivot_df[f'precio_competidor_{i}'] = 0.0

                agg_dict = {
                    'name': 'first',
                    'total_ganancia': 'sum',
                    'dollar_price': 'mean'
                }
                internal_agg_df = internal_df.groupby('id').agg(agg_dict)
                
                training_df = pd.merge(
                    internal_agg_df, competitor_pivot_df,
                    left_on='id', right_index=True, how='inner'
                )
                
                training_df.reset_index(inplace=True)
                training_df.rename(columns={
                    'id': 'product_id',
                    'dollar_price': 'precio_mes_actual'
                }, inplace=True)
                
                if training_df.empty:
                    raise ValueError("El dataset de entrenamiento final está vacío. No se puede continuar.")

                self._train_and_save_model(training_df)

            except Exception as e:
                logger.error(f"Ocurrió un error fatal en el pipeline de entrenamiento desde CSV: {e}", exc_info=True)
                raise
            finally:
                if engine:
                    engine.dispose()