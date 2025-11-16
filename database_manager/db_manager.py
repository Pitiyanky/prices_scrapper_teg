import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values, DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from datetime import datetime, date
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class PostgresManager:
    def __init__(self, db_config):
        """
        Inicializa el manejador de PostgreSQL.

        Args:
            db_config (dict): Diccionario con los parámetros de conexión
                              (host, port, dbname, user, password).
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        self._connect()
        if self.conn:
            self._create_tables_if_not_exist()
            self._create_initial_admin_if_not_exists()
            self.perform_initial_product_load()

    def _connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False # Controlar transacciones manualmente
            self.cursor = self.conn.cursor(cursor_factory=DictCursor) # Usar DictCursor para obtener resultados como diccionarios
            logger.info(f"Conectado exitosamente a PostgreSQL (DB: {self.db_config.get('dbname')})")
        except psycopg2.Error as e:
            logger.error(f"Error al conectar a PostgreSQL: {e}")
            self.conn = None
            self.cursor = None

    def _create_tables_if_not_exist(self):
        """Crea las tablas 'websites' y 'preprocessed_products' si no existen."""
        if not self.conn:
            logger.error("No hay conexión a la base de datos para crear tablas.")
            return

        commands = (
            """
            CREATE TABLE IF NOT EXISTS config_parameters (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(255) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                description TEXT -- Opcional, para documentar el propósito de cada parámetro
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS websites (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                last_scraped_at TIMESTAMP WITH TIME ZONE
            );
            """,
             """
            CREATE TABLE IF NOT EXISTS product_type (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS udm (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                product_type_id INTEGER REFERENCES product_type(id) NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS preprocessed_products (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
                website_id INTEGER REFERENCES websites(id) ON DELETE SET NULL,
                price DECIMAL(12, 2),
                currency VARCHAR(10),
                scrape_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                extracted_quantity FLOAT,
                udm_id INTEGER REFERENCES udm(id) ON DELETE SET NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'analista_precios', 'data_analyst'))
            );
            """
            ,
            # Índices para mejorar rendimiento de consultas comunes
            """CREATE INDEX IF NOT EXISTS idx_pp_timestamp ON preprocessed_products(scrape_timestamp);""",
            """CREATE INDEX IF NOT EXISTS idx_pp_website_id ON preprocessed_products(website_id);""",
            """CREATE INDEX IF NOT EXISTS idx_pp_udm_id ON preprocessed_products(udm_id);""",
            """CREATE INDEX IF NOT EXISTS idx_websites_name ON websites(name);"""
        )
        try:
            for command in commands:
                self.cursor.execute(command)
            self.conn.commit()
            logger.info("Tablas 'websites' y 'preprocessed_products' aseguradas/creadas exitosamente.")
        except psycopg2.Error as e:
            logger.error(f"Error al crear/asegurar tablas: {e}")
            if self.conn:
                self.conn.rollback() # Revertir si algo falla

    def _create_initial_admin_if_not_exists(self):
        """
        Verifica si el administrador inicial ya fue creado usando una bandera
        en config_parameters. Si no, lo crea.
        """
        config_key = 'INITIAL_ADMIN_CREATED'
        
        if self.get_config_parameter(config_key) == 'true':
            logger.info("El administrador inicial ya existe. Omitiendo creación.")
            return

        logger.info("Bandera de administrador inicial no encontrada. Creando usuario admin por primera vez...")

        default_username = 'admin'
        default_password = '1234'
        
        success = self.create_user(default_username, default_password, 'admin')
        
        if success:
            logger.warning(
                f"Usuario administrador inicial '{default_username}' creado con la contraseña por defecto. "
                "¡Se recomienda cambiar esta contraseña desde el panel de administración!"
            )
            description = "Bandera para asegurar que el usuario admin inicial se cree solo una vez."
            self.upsert_config_parameter(config_key, 'true', description)
        else:
            logger.error(
                f"No se pudo crear el usuario administrador inicial '{default_username}'. "
                "Es posible que ya existiera pero la bandera no se estableció correctamente."
            )

    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Conexión a PostgreSQL cerrada.")

    def __enter__(self):
        if not self.conn or self.conn.closed:
            self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
    
    def upsert_website(self, name, url, last_scraped_at=None):
        """
        Inserta un nuevo sitio web o actualiza 'url' y 'last_scraped_at' si ya existe por nombre.
        Devuelve el ID del sitio web.
        """
        if not self.conn: return None
        if last_scraped_at is None:
            last_scraped_at = datetime.now()

        query = sql.SQL("""
            INSERT INTO websites (name, url, last_scraped_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                url = EXCLUDED.url,
                last_scraped_at = EXCLUDED.last_scraped_at
            RETURNING id;
        """)
        try:
            self.cursor.execute(query, (name, url, last_scraped_at))
            website_id = self.cursor.fetchone()[0]
            self.conn.commit()
            logger.info(f"Sitio web '{name}' insertado/actualizado. ID: {website_id}")
            return website_id
        except psycopg2.Error as e:
            logger.error(f"Error en upsert_website para '{name}': {e}")
            self.conn.rollback()
            return None
        except TypeError:
            logger.error(f"Error en upsert_website para '{name}': no se pudo obtener el ID (posiblemente el registro no se insertó/actualizó).")
            self.conn.rollback()
            return None
        
    def upsert_product_type(self, name):
        """
        Inserta un nuevo tipo de producto o actualiza si ya existe por nombre.
        Devuelve el ID del tipo de producto.
        """
        if not self.conn: return None
        query = sql.SQL("""
            INSERT INTO product_type (name)
            VALUES (%s) 
            ON CONFLICT (name) DO NOTHING
            RETURNING id;
        """)
        try:
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone() 
            self.conn.commit()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error en upsert_product_type para '{name}': {e}")
            self.conn.rollback()
            return None
    
    def upsert_udm(self, name):
        """
        Inserta un nuevo UDM (Unidad de Medida) o actualiza si ya existe por nombre.
        """
        if not self.conn: return None
        query = sql.SQL("""
            INSERT INTO udm (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id;
        """)
        try:
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone() 
            self.conn.commit()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error en upsert_udm para '{name}': {e}")
            self.conn.rollback()
            return None 
    
    def get_udm_id_by_name(self, name):
        """Obtiene el ID de un UDM por su nombre."""
        if not self.conn: return None
        query = sql.SQL("SELECT id FROM udm WHERE name = %s;")
        try:
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error en get_udm_id_by_name para '{name}': {e}")
            return None


    def get_website_id_by_name(self, name):
        """Obtiene el ID de un sitio web por su nombre."""
        if not self.conn: return None
        query = sql.SQL("SELECT id FROM websites WHERE name = %s;")
        try:
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error en get_website_id_by_name para '{name}': {e}")
            return None
        
    def get_product_type_id_by_name(self,name):
        """Obtiene el ID de un tipo de producto por su nombre."""
        if not self.conn or name == '': return None

        query = sql.SQL("SELECT id FROM product_type WHERE name = %s;")
        try:
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error en get_product_type_id_by_name para '{name}': {e}")

    def update_website_last_scraped_at(self, website_id_or_name, last_scraped_at=None):
        """Actualiza la fecha del último scrapeo para un sitio web."""
        if not self.conn: return False
        if last_scraped_at is None:
            last_scraped_at = datetime.now()

        if isinstance(website_id_or_name, str):
            website_id = self.get_website_id_by_name(website_id_or_name)
            if not website_id:
                logger.warning(f"No se encontró el sitio '{website_id_or_name}' para actualizar last_scraped_at.")
                return False
        else:
            website_id = website_id_or_name

        query = sql.SQL("UPDATE websites SET last_scraped_at = %s WHERE id = %s;")
        try:
            self.cursor.execute(query, (last_scraped_at, website_id))
            self.conn.commit()
            logger.info(f"Actualizado last_scraped_at para website ID {website_id}.")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error actualizando last_scraped_at para website ID {website_id}: {e}")
            self.conn.rollback()
            return False
    
    def upsert_config_parameter(self, config_key, config_value, description=None):
        """Inserta o actualiza un parámetro de configuración."""
        if not self.conn: return False
        query = sql.SQL("""
            INSERT INTO config_parameters (config_key, config_value, description, last_updated)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (config_key) DO UPDATE SET
                config_value = EXCLUDED.config_value,
                description = EXCLUDED.description,
                last_updated = EXCLUDED.last_updated
            RETURNING id;
        """)
        try:
            self.cursor.execute(query, (config_key, config_value, description, datetime.now()))
            self.conn.commit()
            logger.info(f"Parámetro de configuración '{config_key}' insertado/actualizado.")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error en upsert_config_parameter para '{config_key}': {e}")
            self.conn.rollback()
            return False

    def get_config_parameter(self, config_key):
        """Obtiene el valor de un parámetro de configuración por su clave."""
        if not self.conn: return None
        query = sql.SQL("SELECT config_value FROM config_parameters WHERE config_key = %s;")
        try:
            self.cursor.execute(query, (config_key,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error obteniendo parámetro de configuración '{config_key}': {e}")
            return None
        
    
        
    def get_products(self):
        query = """
                    SELECT 
                        p.name as name, 
                        pt.name AS product_type
                    FROM products p
                    LEFT JOIN product_type pt ON p.product_type_id = pt.id;
                """
        if not self.conn: return []
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            logger.info(f"Obtenidos {len(results)} productos.")
            return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Error en get_products: {e}")
            return []
        
    def upsert_product(self, name, product_type):
        """
        Inserta un nuevo producto o actualiza su tipo si ya existe por nombre.
        Devuelve el ID del producto.
        """
        
        if not self.conn: return None

        product_type_id = self.get_product_type_id_by_name(product_type)

        if not product_type_id and product_type:
            product_type_id = self.upsert_product_type(product_type)
        query = sql.SQL("""
            INSERT INTO products (name, product_type_id)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET
                name = EXCLUDED.name
            RETURNING id;
        """)
        try:
            self.cursor.execute(query, (name, product_type_id))
            product_id = self.cursor.fetchone()[0]
            self.conn.commit()
            logger.info(f"Producto '{name}' insertado/actualizado. ID: {product_id}")
            return product_id
        except psycopg2.Error as e:
            logger.error(f"Error en upsert_product para '{name}': {e}")
            self.conn.rollback()
            return None
    
    def perform_initial_product_load(self):
        """
        Realiza una carga masiva inicial de productos a partir de una lista predefinida.
        Esta operación se ejecuta UNA SOLA VEZ, controlada por un flag en la tabla 'config_parameters'.
        """
        if not self.conn:
            return

        config_key = 'initial_product_load_completed'
        
        if self.get_config_parameter(config_key) == 'true':
            logger.info("La carga inicial de productos base ya se ha realizado anteriormente. Omitiendo.")
            return

        logger.info("No se encontró registro de carga inicial. Procediendo a cargar productos base...")

        try:
            import pandas as pd
            initial_products_data = pd.read_parquet('initial_data.parquet')
            if initial_products_data.empty:
                logger.warning("No se encontraron datos en 'initial_data.parquet'. Abortando carga inicial.")
                return
            
            count = 0
            for item in initial_products_data.to_dict('records'):
                print(item)
                product_name = item['name']
                product_type = item['type']
                product_id = self.upsert_product(product_name, product_type)
                if product_id:
                    count += 1
                else:
                    logger.warning(f"No se pudo insertar el producto inicial: {product_name}")
            
            logger.info(f"Se procesaron {count}/{len(initial_products_data)} productos iniciales.")

            description = "Flag booleano ('true'/'false') que indica si la carga de datos iniciales en la tabla 'products' ya se ha completado."
            self.upsert_config_parameter(config_key, 'true', description)
            
            logger.info("Carga inicial de productos completada y bandera de configuración establecida.")

        except Exception as e:
            logger.error(f"Ocurrió un error crítico durante la carga inicial de productos: {e}")
            self.conn.rollback()

    def get_product_id_by_name(self, name):
        """Obtiene el ID de un producto por su nombre."""
        if not self.conn: return None
        query = sql.SQL("SELECT id FROM products WHERE name = %s;")
        try:
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Error en get_product_id_by_name para '{name}': {e}")
            return None

    def insert_preprocessed_products_batch(self, products_data_list, date_time):
        """
        Inserta una lista de diccionarios de productos preprocesados.
        'products_data_list' debe ser una lista de diccionarios donde cada dict
        tiene claves que coinciden con las columnas de 'preprocessed_products'.
        Se espera que 'website_id' ya esté presente en los diccionarios.
        """
        if not self.conn or not products_data_list:
            logger.warning("No hay conexión o no hay datos de productos para insertar.")
            return 0

        cols = [
            'product_id', 'website_id', 'price', 'currency',
            'scrape_timestamp', 'extracted_quantity', 'udm_id'
        ]
        
        values_to_insert = []
        for product_dict in products_data_list:
            website_id = self.get_website_id_by_name(product_dict['site'])
            if not website_id:
                url = product_dict['url']
                website_root = urlparse(url).netloc
                website_id = self.upsert_website(product_dict['site'], website_root)

            product_id = self.get_product_id_by_name(product_dict.get('name', ''))
            if not product_id:
                product_id = self.upsert_product(product_dict.get('name', ''), product_dict.get('product_type'))
            
            udm_id = self.get_udm_id_by_name(product_dict.get('normalized_unit', ''))
            if not udm_id:
                udm_id = self.upsert_udm(product_dict.get('normalized_unit', ''))

            product_dict['product_id'] = product_id
            product_dict['website_id'] = website_id
            product_dict['scrape_timestamp'] = date_time
            product_dict['udm_id'] = udm_id

            values_to_insert.append(tuple(product_dict.get(col) for col in cols))

        if not values_to_insert:
            logger.info("No hay valores válidos para insertar en preprocessed_products.")
            return 0
        
        query = sql.SQL("INSERT INTO preprocessed_products ({}) VALUES %s").format(
            sql.SQL(', ').join(map(sql.Identifier, cols))
        )
        
        try:
            execute_values(self.cursor, query, values_to_insert)
            self.conn.commit()
            count = len(values_to_insert)
            logger.info(f"{count} productos preprocesados insertados exitosamente.")
            return count
        except psycopg2.Error as e:
            logger.error(f"Error en insert_preprocessed_products_batch: {e}")
            self.conn.rollback()
            return 0

    def get_preprocessed_products(self, start_date=None, end_date=None, product_types=None, search_term=None, retailers=None):
        """
        Obtiene productos preprocesados, filtrados directamente en la base de datos.
        Devuelve una lista de diccionarios.
        """
        if not self.conn: return []
        
        query_base = """SELECT p.name,
                            pp.price,
                            pp.currency,
                            pp.scrape_timestamp,
                            pp.extracted_quantity, 
                            w.name as website_table_name, 
                            pt.name as product_type, 
                            u.name as udm_name 
                        FROM preprocessed_products pp 
                        LEFT JOIN products p ON p.id = pp.product_id
                        LEFT JOIN websites w ON pp.website_id = w.id 
                        LEFT JOIN product_type pt ON p.product_type_id = pt.id
                        LEFT JOIN udm u ON pp.udm_id = u.id"""
        
        conditions = []
        params = []

        if start_date:
            conditions.append("pp.scrape_timestamp >= %s")
            params.append(datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            conditions.append("pp.scrape_timestamp <= %s")
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_of_day = end_date_dt.replace(hour=23, minute=59, second=59)
            params.append(end_of_day)

        if product_types and isinstance(product_types, (list, tuple)):
            conditions.append("pt.name = ANY(%s)")
            params.append(list(product_types))

        if search_term:
            conditions.append("p.name ILIKE %s")
            params.append(f"%{search_term}%")

        if retailers:
            conditions.append("w.name = ANY(%s)")
            params.append(list(retailers))

        if conditions:
            query_base += " WHERE " + " AND ".join(conditions)
        
        query_base += " ORDER BY pp.scrape_timestamp DESC"
            
        final_query = sql.SQL(query_base)

        try:
            self.cursor.execute(final_query, tuple(params) if params else None)
            results = self.cursor.fetchall() 
            logger.info(f"Obtenidos {len(results)} productos preprocesados (filtrados en DB).")
            return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Error en get_preprocessed_products (filtrado): {e}")
            return []
        
    def get_filter_metadata(self):
        """
        Obtiene eficientemente los metadatos necesarios para los filtros:
        rango de fechas y tipos de producto únicos.
        """
        if not self.conn:
            today = date.today()
            return today, today, []

        query = """
            SELECT
                MIN(scrape_timestamp)::date as min_date,
                MAX(scrape_timestamp)::date as max_date
            FROM preprocessed_products;
        """
        types_query = """
            SELECT DISTINCT name FROM product_type ORDER BY name;
        """
        retailers_query = """  
            SELECT DISTINCT name FROM websites ORDER BY name;
         """
        try:
            self.cursor.execute(query)
            date_res = self.cursor.fetchone()
            min_date_db = date_res['min_date'] if date_res and date_res['min_date'] else date.today()
            max_date_db = date_res['max_date'] if date_res and date_res['max_date'] else date.today()

            self.cursor.execute(types_query)
            type_res = self.cursor.fetchall()
            unique_types = [row['name'] for row in type_res]
            self.cursor.execute(retailers_query)
            retailer_res = self.cursor.fetchall()
            unique_retailers = [row['name'] for row in retailer_res]
            logger.info("Metadatos para filtros obtenidos de la BD.")
            return min_date_db, max_date_db, unique_types, unique_retailers
        except psycopg2.Error as e:
            logger.error(f"Error obteniendo metadatos para filtros: {e}")
            today = date.today()
            return today, today, []
        
    def create_user(self, username, password, role):
        """Crea un nuevo usuario con una contraseña hasheada."""
        if not self.conn:
            logger.error("No hay conexión a la BD para crear usuario.")
            return False
        
        if role not in ['admin', 'analista_precios', 'data_analyst']:
            logger.error(f"Rol inválido '{role}'. No se creará el usuario.")
            return False

        password_hash = generate_password_hash(password)
        query = sql.SQL("""
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, %s);
        """)
        try:
            self.cursor.execute(query, (username, password_hash, role))
            self.conn.commit()
            logger.info(f"Usuario '{username}' con rol '{role}' creado exitosamente.")
            return True
        except psycopg2.IntegrityError:
            logger.warning(f"El usuario '{username}' ya existe.")
            self.conn.rollback()
            return False
        except psycopg2.Error as e:
            logger.error(f"Error al crear el usuario '{username}': {e}")
            self.conn.rollback()
            return False

    def get_user(self, username):
        """
        Obtiene los datos de un usuario (incluyendo hash de contraseña y rol) por su nombre de usuario.
        """
        if not self.conn:
            return None
        query = sql.SQL("SELECT username, password_hash, role FROM users WHERE username = %s;")
        try:
            self.cursor.execute(query, (username,))
            user_data = self.cursor.fetchone()
            return dict(user_data) if user_data else None
        except psycopg2.Error as e:
            logger.error(f"Error al obtener el usuario '{username}': {e}")
            return None
    
    def get_all_users(self):
        """Obtiene una lista de todos los usuarios (id y username)."""
        if not self.conn: return []
        query = sql.SQL("SELECT id, username FROM users ORDER BY username;")
        try:
            self.cursor.execute(query)
            users = self.cursor.fetchall()
            return [dict(user) for user in users]
        except psycopg2.Error as e:
            logger.error(f"Error al obtener todos los usuarios: {e}")
            return []

    def update_user(self, user_id, new_username=None, new_password=None):
        """
        Actualiza el nombre de usuario y/o la contraseña de un usuario existente.
        """
        if not self.conn: return False
        if not new_username and not new_password:
            logger.warning("Intento de actualización de usuario sin nuevos datos.")
            return False

        updates = []
        params = []

        if new_username:
            updates.append(sql.SQL("username = %s"))
            params.append(new_username)
        
        if new_password:
            updates.append(sql.SQL("password_hash = %s"))
            params.append(generate_password_hash(new_password))

        params.append(user_id)

        query = sql.SQL("UPDATE users SET {} WHERE id = %s;").format(sql.SQL(', ').join(updates))

        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.info(f"Usuario con ID {user_id} actualizado exitosamente.")
            return True
        except psycopg2.IntegrityError:
            logger.error(f"Error de integridad al actualizar usuario ID {user_id}. El nuevo username '{new_username}' podría ya existir.")
            self.conn.rollback()
            return False
        except psycopg2.Error as e:
            logger.error(f"Error al actualizar usuario ID {user_id}: {e}")
            self.conn.rollback()
            return False

    def delete_user(self, user_id):
        """Elimina un usuario por su ID."""
        if not self.conn: return False
        
        query = sql.SQL("DELETE FROM users WHERE id = %s;")
        try:
            self.cursor.execute(query, (user_id,))
            if self.cursor.rowcount == 0:
                logger.warning(f"Intento de eliminar usuario con ID {user_id}, pero no fue encontrado.")
                return False
            self.conn.commit()
            logger.info(f"Usuario con ID {user_id} eliminado exitosamente.")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error al eliminar usuario ID {user_id}: {e}")
            self.conn.rollback()
            return False
    
    def get_all_config_parameters(self):
        """
        Obtiene todos los parámetros de configuración de la base de datos.
        """
        if not self.conn:
            return []
        
        query = sql.SQL("SELECT config_key, config_value, description, last_updated FROM config_parameters ORDER BY config_key;")
        
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Error al obtener todos los parámetros de configuración: {e}")
            return []