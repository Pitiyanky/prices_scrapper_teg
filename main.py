import schedule
import time
import logging
import threading
from shared_context import app_context
from config import DB_CONFIG

from database_manager import PostgresManager
from orchestator import execute_orchestrator
from data_analysis.analyzer import Analyzer
from dashboard_app.app import app as dash_app


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - [%(levelname)s] [%(threadName)s] %(message)s')
logger = logging.getLogger(__name__)

JOB_SCHEDULE_TIME_KEY = "MAIN_JOB_SCHEDULE_TIME"
DEFAULT_JOB_SCHEDULE_TIME = "18:30"
JOB_SCHEDULE_TIME_DESCRIPTION = "Hora de ejecución (HH:MM) para el job principal del scheduler."

def scheduled_job():
    """Función que se ejecutará según el schedule."""

    logger.info("SCHEDULER: Iniciando job programado...")
    try:

        with PostgresManager(DB_CONFIG) as db_manager_for_job:
            if db_manager_for_job.conn:
                execute_orchestrator(db_manager=db_manager_for_job,
                                     run_scrapers_flag=True,
                                     run_preprocessing_flag=True)
            else:
                logger.error("SCHEDULER: Job programado - No se pudo conectar a la base de datos. Omitiendo orquestador.")

    except Exception as e:
        logger.error(f"SCHEDULER: Error durante la ejecución del job: {e}", exc_info=True)
    logger.info("SCHEDULER: Job programado finalizado.")


def get_schedule_time_from_db(db_manager):
    """
    Función auxiliar para obtener y validar la hora de la BD.
    Devuelve la hora configurada o la hora por defecto.
    """
    schedule_time_from_db = db_manager.get_config_parameter(JOB_SCHEDULE_TIME_KEY)
    if schedule_time_from_db:
        try:
            time.strptime(schedule_time_from_db, '%H:%M')
            logger.info(f"SCHEDULER: Hora para el job obtenida de la BD: '{schedule_time_from_db}'")
            return schedule_time_from_db
        except ValueError:
            logger.error(f"SCHEDULER: Formato de hora '{schedule_time_from_db}' de BD no válido. Usando defecto: '{DEFAULT_JOB_SCHEDULE_TIME}'.")
            return DEFAULT_JOB_SCHEDULE_TIME
    else:
        logger.warning(f"SCHEDULER: Parámetro '{JOB_SCHEDULE_TIME_KEY}' no encontrado en BD. Insertando valor por defecto.")
        db_manager.upsert_config_parameter(
            JOB_SCHEDULE_TIME_KEY, DEFAULT_JOB_SCHEDULE_TIME, JOB_SCHEDULE_TIME_DESCRIPTION
        )
        return DEFAULT_JOB_SCHEDULE_TIME

def run_scheduler():
    """Configura y ejecuta el bucle del scheduler."""
    logger.info("SCHEDULER: Iniciando hilo del scheduler...")
    actual_job_schedule_time = DEFAULT_JOB_SCHEDULE_TIME

    with PostgresManager(DB_CONFIG) as db_manager:
        if not db_manager.conn:
            logger.error("SCHEDULER: No se pudo conectar a BD. Usando hora por defecto y sin posibilidad de recarga.")
            actual_job_schedule_time = DEFAULT_JOB_SCHEDULE_TIME
        else:
            actual_job_schedule_time = get_schedule_time_from_db(db_manager)
    
    schedule.every().day.at(actual_job_schedule_time).do(scheduled_job).tag('main_job')

    while True:
        if app_context.scheduler_event.is_set():
            logger.info("SCHEDULER: Se detectó solicitud de actualización desde el contexto.")
            
            with PostgresManager(DB_CONFIG) as db_manager:
                if db_manager.conn:
                    new_schedule_time = get_schedule_time_from_db(db_manager)
                    if new_schedule_time != actual_job_schedule_time:
                        logger.info(f"Reprogramando job de '{actual_job_schedule_time}' a '{new_schedule_time}'.")
                        actual_job_schedule_time = new_schedule_time
                        schedule.clear('main_job')
                        schedule.every().day.at(actual_job_schedule_time).do(scheduled_job).tag('main_job')
                    else:
                        logger.info("SCHEDULER: La hora en BD no cambió. No se reprograma.")
            app_context.scheduler_event.clear()
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':

    logger.info("APLICACIÓN: Iniciando aplicación principal...")
    scheduler_thread = threading.Thread(target=run_scheduler, name="SchedulerThread", daemon=True)
    scheduler_thread.start()

    logger.info("APLICACIÓN: Hilo del scheduler iniciado.")
    analyzer = Analyzer(db_config=DB_CONFIG) 
    analyzer.load_model_and_data()
    dash_app.server.config['CENTRAL_ANALYZER'] = analyzer

    logger.info("APLICACIÓN: Iniciando servidor Dash...")
    dash_app.run(debug=False, host='0.0.0.0', port=8050, use_reloader=False)

    logger.info("APLICACIÓN: Servidor Dash detenido.")

