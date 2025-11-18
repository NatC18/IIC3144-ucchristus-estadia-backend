"""
Importador para insertar/actualizar datos en la base de datos
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
else:
    AbstractUser = None
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from api.models import Cama, Episodio, Gestion, Paciente, Transferencia

logger = logging.getLogger(__name__)
User = get_user_model()


class DatabaseImporter:
    """
    Maneja la inserción y actualización de datos en la base de datos
    """

    def __init__(self):
        self.results = {
            "pacientes": {"created": 0, "updated": 0, "errors": 0},
            "camas": {"created": 0, "updated": 0, "errors": 0},
            "episodios": {"created": 0, "updated": 0, "errors": 0},
            "gestiones": {"created": 0, "updated": 0, "errors": 0},
            "transferencias": {"created": 0, "updated": 0, "errors": 0},
        }
        self.error_details = []
        # Mapeos para facilitar búsquedas
        self.episodio_to_paciente = {}
        self.codigo_cama_to_cama = {}

    def import_all_data(self, mapped_data: Dict[str, List[Dict]]) -> Dict:
        """
        Importa todos los datos usando transacciones

        Args:
            mapped_data: Datos mapeados listos para Django

        Returns:
            Dict con resultados del proceso
        """
        try:
            logger.info("Iniciando importación de datos a la base de datos...")

            # Usar transacción atómica para todo el proceso
            with transaction.atomic():
                # 1. Importar pacientes primero
                if "pacientes" in mapped_data:
                    self._import_pacientes(mapped_data["pacientes"])

                # 2. Importar camas (independientes)
                if "camas" in mapped_data:
                    self._import_camas(mapped_data["camas"])

                # 3. Importar episodios (dependen de pacientes y camas)
                if "episodios" in mapped_data:
                    self._import_episodios(mapped_data["episodios"])

                # 4. Importar gestiones (dependen de episodios)
                if "gestiones" in mapped_data:
                    self._import_gestiones(mapped_data["gestiones"])

                # 5. Importar transferencias (dependen de episodios)
                if "transferencias" in mapped_data:
                    self._import_transferencias(mapped_data["transferencias"])

            logger.info("Importación completada exitosamente")

            return self._get_results_summary()

        except Exception as e:
            logger.error(f"Error durante importación: {str(e)}")
            self.error_details.append(f"Error global: {str(e)}")
            return self._get_results_summary()

    def _import_pacientes(self, pacientes_data: List[Dict]) -> None:
        """
        Importa datos de pacientes

        Args:
            pacientes_data: Lista de datos de pacientes
        """
        logger.info(f"Importando {len(pacientes_data)} pacientes...")

        for paciente_data in pacientes_data:
            try:
                # Buscar paciente existente por RUT
                rut = paciente_data.get("rut")
                if not rut:
                    self.results["pacientes"]["errors"] += 1
                    self.error_details.append(
                        f"Paciente sin RUT en episodio {paciente_data.get('episodio_cmbd')}"
                    )
                    continue

                # Log para debug
                logger.debug(f"Procesando paciente {rut}: {paciente_data}")

                # Intentar obtener paciente existente
                paciente, created = Paciente.objects.get_or_create(
                    rut=rut,
                    defaults={
                        "nombre": paciente_data.get("nombre", ""),
                        "sexo": paciente_data.get("sexo", "O"),
                        "fecha_nacimiento": paciente_data.get("fecha_nacimiento"),
                        "prevision_1": str(paciente_data.get("prevision_1", "OTRO"))[
                            :20
                        ],
                        "prevision_2": (
                            str(paciente_data.get("prevision_2", ""))[:20]
                            if paciente_data.get("prevision_2")
                            else None
                        ),
                        "convenio": paciente_data.get("convenio"),
                        "score_social": paciente_data.get("score_social"),
                    },
                )

                if created:
                    self.results["pacientes"]["created"] += 1
                    logger.debug(f"Paciente creado: {rut}")
                else:
                    # Actualizar datos si es necesario
                    updated = False

                    # Actualizar nombre si es diferente y no está vacío
                    new_name = paciente_data.get("nombre", "").strip()
                    if new_name and new_name != paciente.nombre:
                        paciente.nombre = new_name
                        updated = True

                    # Actualizar fecha de nacimiento si no existe o si tenemos nueva información
                    if not paciente.fecha_nacimiento and paciente_data.get(
                        "fecha_nacimiento"
                    ):
                        paciente.fecha_nacimiento = paciente_data.get(
                            "fecha_nacimiento"
                        )
                        updated = True

                    # Actualizar previsión si no es 'OTRO' o si tenemos mejor información
                    new_prevision_1 = paciente_data.get("prevision_1", "")[
                        :20
                    ]  # Truncar a 20 chars
                    if new_prevision_1 and (
                        paciente.prevision_1 == "OTRO" or not paciente.prevision_1
                    ):
                        paciente.prevision_1 = new_prevision_1
                        updated = True

                    # Actualizar previsión 2 si no existe
                    new_prevision_2 = paciente_data.get("prevision_2")
                    if new_prevision_2:
                        new_prevision_2 = str(new_prevision_2)[
                            :20
                        ]  # Truncar a 20 chars
                        if not paciente.prevision_2:
                            paciente.prevision_2 = new_prevision_2
                            updated = True

                    # Actualizar convenio si no existe
                    if paciente_data.get("convenio") and not paciente.convenio:
                        paciente.convenio = paciente_data.get("convenio")
                        updated = True

                    # Actualizar sexo si no es 'O' y tenemos nueva información
                    new_sexo = paciente_data.get("sexo", "O")
                    logger.debug(
                        f"Comparando sexo para {rut}: actual='{paciente.sexo}', nuevo='{new_sexo}'"
                    )
                    if new_sexo != "O" and paciente.sexo == "O":
                        logger.info(
                            f"Actualizando sexo de {rut}: '{paciente.sexo}' -> '{new_sexo}'"
                        )
                        paciente.sexo = new_sexo
                        updated = True

                    # Actualizar score social si no existe
                    if paciente_data.get("score_social") and not paciente.score_social:
                        paciente.score_social = paciente_data.get("score_social")
                        updated = True
                        logger.info(
                            f"Actualizando score social de {rut}: '{paciente.score_social}'"
                        )

                    if updated:
                        paciente.save()
                        self.results["pacientes"]["updated"] += 1
                        logger.debug(f"Paciente actualizado: {rut}")

                # Guardar relación episodio_cmbd -> paciente
                episodio_cmbd = paciente_data.get("episodio_cmbd")
                if episodio_cmbd:
                    self.episodio_to_paciente[episodio_cmbd] = paciente

            except ValidationError as e:
                self.results["pacientes"]["errors"] += 1
                error_msg = f"Error validación paciente {rut}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

            except Exception as e:
                self.results["pacientes"]["errors"] += 1
                error_msg = f"Error procesando paciente {paciente_data.get('rut', 'SIN_RUT')}: {str(e)}"
                error_detail = f"Datos del paciente: {paciente_data}"
                self.error_details.append(error_msg)
                self.error_details.append(error_detail)
                logger.error(error_msg)
                logger.error(error_detail)
                # Imprimir el traceback completo
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

    def _import_camas(self, camas_data: List[Dict]) -> None:
        """
        Importa datos de camas

        Args:
            camas_data: Lista de datos de camas
        """
        logger.info(f"Importando {len(camas_data)} camas...")

        for cama_data in camas_data:
            try:
                codigo_cama = cama_data.get("codigo_cama")
                if not codigo_cama:
                    self.results["camas"]["errors"] += 1
                    self.error_details.append("Cama sin código")
                    continue

                # Intentar obtener o crear cama
                habitacion = cama_data.get("habitacion")
                if not habitacion or habitacion.strip() == "":
                    # Generar habitación por defecto basada en el código de cama
                    habitacion = f"HAB-{codigo_cama}"

                cama, created = Cama.objects.get_or_create(
                    codigo_cama=codigo_cama,
                    defaults={
                        "habitacion": habitacion,
                    },
                )

                if created:
                    self.results["camas"]["created"] += 1
                    logger.debug(f"Cama creada: {codigo_cama}")
                else:
                    # Actualizar datos si es necesario
                    updated = False

                    if (
                        cama_data.get("habitacion")
                        and cama_data["habitacion"] != cama.habitacion
                    ):
                        cama.habitacion = cama_data["habitacion"]
                        updated = True

                    if updated:
                        cama.save()
                        self.results["camas"]["updated"] += 1
                        logger.debug(f"Cama actualizada: {codigo_cama}")

                # Guardar en mapeo para facilitar búsquedas
                self.codigo_cama_to_cama[codigo_cama] = cama

            except ValidationError as e:
                self.results["camas"]["errors"] += 1
                error_msg = f"Error validación cama {cama_data.get('codigo_cama', 'SIN_CODIGO')}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

            except Exception as e:
                self.results["camas"]["errors"] += 1
                error_msg = f"Error procesando cama {cama_data.get('codigo_cama', 'SIN_CODIGO')}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

    def _import_episodios(self, episodios_data: List[Dict]) -> None:
        """
        Importa datos de episodios

        Args:
            episodios_data: Lista de datos de episodios
        """
        logger.info(f"Importando {len(episodios_data)} episodios...")

        for episodio_data in episodios_data:
            try:
                episodio_cmbd = episodio_data.get("episodio_cmbd")
                if not episodio_cmbd:
                    self.results["episodios"]["errors"] += 1
                    self.error_details.append("Episodio sin número CMBD")
                    continue

                # Buscar paciente por RUT o por episodio_cmbd ya procesado
                paciente = self._find_paciente_for_episodio(
                    episodio_data, episodio_cmbd
                )
                if not paciente:
                    self.results["episodios"]["errors"] += 1
                    self.error_details.append(
                        f"No se encontró paciente para episodio {episodio_cmbd}"
                    )
                    continue

                # Buscar cama si se especifica
                cama = self._find_cama(episodio_data)

                # Verificar si episodio ya existe
                episodio, created = Episodio.objects.get_or_create(
                    episodio_cmbd=episodio_cmbd,
                    defaults={
                        "paciente": paciente,
                        "cama": cama,
                        "fecha_ingreso": episodio_data.get("fecha_ingreso"),
                        "fecha_egreso": episodio_data.get("fecha_egreso"),
                        "tipo_actividad": episodio_data.get(
                            "tipo_actividad", "Hospitalización"
                        ),
                        "especialidad": episodio_data.get("especialidad"),
                        "inlier_outlier_flag": episodio_data.get("inlier_outlier_flag"),
                        "estancia_prequirurgica": episodio_data.get(
                            "estancia_prequirurgica"
                        ),
                        "estancia_postquirurgica": episodio_data.get(
                            "estancia_postquirurgica"
                        ),
                        "estancia_norma_grd": episodio_data.get("estancia_norma_grd"),
                    },
                )

                if created:
                    self.results["episodios"]["created"] += 1
                    logger.debug(f"Episodio creado: {episodio_cmbd}")
                else:
                    # Actualizar si es necesario
                    updated = False

                    # Actualizar cama si no tenía y ahora sí
                    if not episodio.cama and cama:
                        episodio.cama = cama
                        updated = True

                    # Actualizar fecha de egreso si no tenía
                    if not episodio.fecha_egreso and episodio_data.get("fecha_egreso"):
                        episodio.fecha_egreso = episodio_data.get("fecha_egreso")
                        updated = True

                    if updated:
                        episodio.save()
                        self.results["episodios"]["updated"] += 1
                        logger.debug(f"Episodio actualizado: {episodio_cmbd}")

                # Actualizar el mapeo para otros episodios
                self.episodio_to_paciente[episodio_cmbd] = paciente

            except ValidationError as e:
                self.results["episodios"]["errors"] += 1
                error_msg = f"Error validación episodio {episodio_cmbd}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

            except Exception as e:
                self.results["episodios"]["errors"] += 1
                error_msg = f"Error procesando episodio {episodio_data.get('episodio_cmbd', 'SIN_CMBD')}: {str(e)}"
                error_detail = f"Datos del episodio: {episodio_data}"
                self.error_details.append(error_msg)
                self.error_details.append(error_detail)
                logger.error(error_msg)
                logger.error(error_detail)
                # Imprimir el traceback completo
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

        logger.info(
            f"Importación de episodios completada: {self.results['episodios']['created']} creados, {self.results['episodios']['updated']} actualizados, {self.results['episodios']['errors']} errores"
        )

    def _import_gestiones(self, gestiones_data: List[Dict]) -> None:
        """
        Importa datos de gestiones

        Args:
            gestiones_data: Lista de datos de gestiones
        """
        logger.info(f"Importando {len(gestiones_data)} gestiones...")

        for gestion_data in gestiones_data:
            try:
                episodio_cmbd = gestion_data.get("episodio_cmbd")
                if not episodio_cmbd:
                    continue

                # Buscar episodio
                try:
                    episodio = Episodio.objects.get(episodio_cmbd=episodio_cmbd)
                except Episodio.DoesNotExist:
                    self.results["gestiones"]["errors"] += 1
                    self.error_details.append(
                        f"No se encontró episodio {episodio_cmbd} para gestión"
                    )
                    continue

                # Buscar usuario si se especifica
                usuario = self._find_usuario(gestion_data.get("usuario_email"))

                # Crear gestión
                gestion_data_clean = {
                    "episodio": episodio,
                    "usuario": usuario,
                    "tipo_gestion": gestion_data.get("tipo_gestion", "GESTION_CLINICA"),
                    "estado_gestion": gestion_data.get("estado_gestion", "INICIADA"),
                    "fecha_inicio": gestion_data.get("fecha_inicio"),
                    "fecha_fin": gestion_data.get("fecha_fin"),
                    "informe": gestion_data.get("informe"),
                }

                # Filtrar valores None
                gestion_data_clean = {
                    k: v for k, v in gestion_data_clean.items() if v is not None
                }

                gestion = Gestion.objects.create(**gestion_data_clean)
                self.results["gestiones"]["created"] += 1
                logger.debug(f"Gestión creada para episodio: {episodio_cmbd}")

            except ValidationError as e:
                self.results["gestiones"]["errors"] += 1
                error_msg = (
                    f"Error validación gestión para episodio {episodio_cmbd}: {str(e)}"
                )
                self.error_details.append(error_msg)
                logger.error(error_msg)

            except Exception as e:
                self.results["gestiones"]["errors"] += 1
                error_msg = f"Error procesando gestión para episodio {gestion_data.get('episodio_cmbd', 'SIN_CMBD')}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

    def _find_paciente_for_episodio(
        self, episodio_data: Dict, episodio_cmbd: int
    ) -> Optional[Paciente]:
        """
        Busca paciente asociado al episodio

        Args:
            episodio_data: Datos del episodio
            episodio_cmbd: Número del episodio

        Returns:
            Paciente o None si no se encuentra
        """
        # Primero buscar en el mapeo interno (más eficiente)
        if episodio_cmbd in self.episodio_to_paciente:
            return self.episodio_to_paciente[episodio_cmbd]

        # Buscar en episodios ya existentes
        try:
            episodio_existente = Episodio.objects.get(episodio_cmbd=episodio_cmbd)
            return episodio_existente.paciente
        except Episodio.DoesNotExist:
            pass

        # Si no existe episodio, buscar paciente por datos disponibles
        # (esto requiere que los pacientes ya hayan sido procesados)

        # Buscar por RUT si está disponible en los datos del episodio
        rut_paciente = episodio_data.get("rut_paciente")
        if rut_paciente:
            try:
                return Paciente.objects.get(rut=rut_paciente)
            except Paciente.DoesNotExist:
                pass

        # Como último recurso, intentar encontrar por nombre
        nombre_paciente = episodio_data.get("nombre_paciente")
        if nombre_paciente:
            try:
                return Paciente.objects.filter(
                    nombre__icontains=nombre_paciente
                ).first()
            except:
                pass

        return None

    def _find_cama(self, episodio_data: Dict) -> Optional[Cama]:
        """
        Busca cama para el episodio

        Args:
            episodio_data: Datos del episodio

        Returns:
            Cama o None si no se encuentra
        """
        cama_codigo = episodio_data.get("codigo_cama")  # Corregido: era 'cama_codigo'
        habitacion = episodio_data.get("habitacion")

        if not cama_codigo:
            return None

        try:
            # Buscar por código y habitación si ambos están disponibles
            if habitacion:
                return Cama.objects.get(codigo_cama=cama_codigo, habitacion=habitacion)
            else:
                # Buscar solo por código
                return Cama.objects.get(codigo_cama=cama_codigo)
        except Cama.DoesNotExist:
            logger.warning(
                f"No se encontró cama {cama_codigo} en habitación {habitacion}"
            )
            return None
        except Cama.MultipleObjectsReturned:
            # Si hay múltiples camas con el mismo código, tomar la primera
            logger.warning(
                f"Múltiples camas con código {cama_codigo}, tomando la primera"
            )
            return Cama.objects.filter(codigo_cama=cama_codigo).first()

    def _find_usuario(self, email: str):
        """
        Busca usuario por email

        Args:
            email: Email del usuario

        Returns:
            Usuario o None si no se encuentra
        """
        if not email:
            return None

        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            logger.debug(f"No se encontró usuario con email: {email}")
            return None

    def _import_transferencias(self, transferencias_data: List[Dict]) -> None:
        """
        Importa datos de transferencias

        Args:
            transferencias_data: Lista de datos de transferencias
        """
        logger.info(f"Importando {len(transferencias_data)} transferencias...")

        for transferencia_data in transferencias_data:
            try:
                episodio_cmbd = transferencia_data.get("episodio_cmbd")
                if not episodio_cmbd:
                    self.results["transferencias"]["errors"] += 1
                    self.error_details.append("Transferencia sin episodio_cmbd")
                    continue

                # Buscar episodio correspondiente
                try:
                    episodio = Episodio.objects.get(episodio_cmbd=episodio_cmbd)
                except Episodio.DoesNotExist:
                    self.results["transferencias"]["errors"] += 1
                    self.error_details.append(
                        f"No se encontró episodio {episodio_cmbd} para transferencia"
                    )
                    continue

                # Buscar o crear gestión asociada
                gestion, gestion_created = Gestion.objects.get_or_create(
                    episodio=episodio,
                    tipo_gestion="TRANSFERENCIA",
                    defaults={
                        "episodio": episodio,
                        "fecha_inicio": transferencia_data.get("fecha_solicitud"),
                    },
                )

                if gestion_created:
                    logger.debug(
                        f"Gestión de transferencia creada para episodio {episodio_cmbd}"
                    )

                # Verificar si ya existe transferencia para esta gestión
                transferencia, created = Transferencia.objects.get_or_create(
                    gestion=gestion,
                    defaults={
                        "estado": transferencia_data.get("estado", "PENDIENTE"),
                        "motivo_cancelacion": transferencia_data.get(
                            "motivo_cancelacion"
                        ),
                        "motivo_rechazo": transferencia_data.get("motivo_rechazo"),
                        "tipo_traslado": transferencia_data.get("tipo_traslado", ""),
                        "motivo_traslado": transferencia_data.get(
                            "motivo_traslado", ""
                        ),
                        "centro_destinatario": transferencia_data.get(
                            "centro_destinatario", ""
                        ),
                    },
                )

                if created:
                    self.results["transferencias"]["created"] += 1
                    logger.debug(f"Transferencia creada para episodio {episodio_cmbd}")
                else:
                    # Actualizar datos si es necesario
                    updated = False
                    if transferencia_data.get(
                        "estado"
                    ) and transferencia.estado != transferencia_data.get("estado"):
                        transferencia.estado = transferencia_data.get("estado")
                        updated = True
                    if transferencia_data.get(
                        "motivo_cancelacion"
                    ) and transferencia.motivo_cancelacion != transferencia_data.get(
                        "motivo_cancelacion"
                    ):
                        transferencia.motivo_cancelacion = transferencia_data.get(
                            "motivo_cancelacion"
                        )
                        updated = True
                    if transferencia_data.get(
                        "motivo_rechazo"
                    ) and transferencia.motivo_rechazo != transferencia_data.get(
                        "motivo_rechazo"
                    ):
                        transferencia.motivo_rechazo = transferencia_data.get(
                            "motivo_rechazo"
                        )
                        updated = True
                    if transferencia_data.get(
                        "tipo_traslado"
                    ) and transferencia.tipo_traslado != transferencia_data.get(
                        "tipo_traslado"
                    ):
                        transferencia.tipo_traslado = transferencia_data.get(
                            "tipo_traslado"
                        )
                        updated = True
                    if transferencia_data.get(
                        "motivo_traslado"
                    ) and transferencia.motivo_traslado != transferencia_data.get(
                        "motivo_traslado"
                    ):
                        transferencia.motivo_traslado = transferencia_data.get(
                            "motivo_traslado"
                        )
                        updated = True
                    if transferencia_data.get(
                        "centro_destinatario"
                    ) and transferencia.centro_destinatario != transferencia_data.get(
                        "centro_destinatario"
                    ):
                        transferencia.centro_destinatario = transferencia_data.get(
                            "centro_destinatario"
                        )
                        updated = True

                    if updated:
                        transferencia.save()
                        self.results["transferencias"]["updated"] += 1
                        logger.debug(
                            f"Transferencia actualizada para episodio {episodio_cmbd}"
                        )

            except ValidationError as e:
                self.results["transferencias"]["errors"] += 1
                error_msg = f"Error validación transferencia para episodio {episodio_cmbd}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

            except Exception as e:
                self.results["transferencias"]["errors"] += 1
                error_msg = f"Error procesando transferencia para episodio {episodio_cmbd}: {str(e)}"
                self.error_details.append(error_msg)
                logger.error(error_msg)

    def _get_results_summary(self) -> Dict:
        """
        Genera resumen de resultados

        Returns:
            Dict con resumen completo de la importación
        """
        total_processed = sum(
            self.results[model]["created"]
            + self.results[model]["updated"]
            + self.results[model]["errors"]
            for model in self.results
        )

        total_success = sum(
            self.results[model]["created"] + self.results[model]["updated"]
            for model in self.results
        )

        total_errors = sum(self.results[model]["errors"] for model in self.results)

        return {
            "summary": {
                "total_processed": total_processed,
                "total_success": total_success,
                "total_errors": total_errors,
                "success_rate": (
                    (total_success / total_processed * 100)
                    if total_processed > 0
                    else 0
                ),
            },
            "details": self.results,
            "errors": self.error_details[
                :50
            ],  # Limitar a 50 errores para no saturar logs
        }

    def import_data(self, mapped_data: Dict[str, List[Dict]]) -> Dict:
        """
        Método alias para import_all_data para compatibilidad

        Args:
            mapped_data: Datos mapeados listos para Django

        Returns:
            Dict con resultados del proceso
        """
        return self.import_all_data(mapped_data)
