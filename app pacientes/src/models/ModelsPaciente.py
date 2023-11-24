from .entities.Paciente import Paciente 
from werkzeug.security import generate_password_hash
from database.db import get_connection

class PacienteModel():

    @classmethod
    def login(self,  user):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = '''SELECT id, dni, nombre, apellido, contrasenia, email, domicilio, fecha_nacimiento FROM pacientes WHERE 
                dni = %s'''
                cursor.execute(sql, (user.dni,))
                row = cursor.fetchone()
                if row != None: 
                    paciente = Paciente(row[0], row[1], row[2], row[3], Paciente.check_password(row[4], user.contrasenia), row[5], row[6], row[7])
                    return paciente
                else:
                    return None
        except Exception as ex: 
            raise Exception(ex)


    @classmethod
    def buscar_paciente(self,dni):
        try:
            with get_connection() as conn:
             with conn.cursor() as cursor:
                sql = '''SELECT id, dni, nombre, apellido, contrasenia, email, domicilio, fecha_nacimiento FROM pacientes WHERE dni = %s'''
                cursor.execute(sql, (dni,))
                row = cursor.fetchone()
                if row != None: 
                  return row
                else:
                  return None
        except Exception as ex: 
            print(f"Error al buscar paciente: {ex}")
            raise Exception(ex)



    @classmethod
    def get_by_id(self, id):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                sql = """SELECT id, dni, nombre, apellido, contrasenia, email, domicilio, fecha_nacimiento FROM pacientes WHERE 
                id = {}""".format(id)
                cursor.execute(sql)
                row = cursor.fetchone()
                if row != None: 
                    return Paciente(row[0], row[1], row[2], row[3], None, row[5], row[6], row[7])
                else:
                    None
        except Exception as ex: 
            raise Exception(ex)


    @classmethod
    def agregar_paciente(self, paciente): 
        try:
            connection = get_connection()
            
            hashed_password = generate_password_hash(paciente.contrasenia)
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO pacientes (
                        dni,
                        nombre,
                        apellido,
                        contrasenia,
                        email,
                        domicilio,
                        fecha_nacimiento
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )""",
                    (paciente.dni, paciente.nombre, paciente.apellido, hashed_password, paciente.email, paciente.domicilio, paciente.fecha_nacimiento)
                )
                affected_rows = cursor.rowcount
                connection.commit()
            cursor.close()
            return affected_rows
        except Exception as ex: 
            raise Exception(ex)