from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from models.ModelsPaciente import PacienteModel
from models.entities.Paciente import Paciente
from config import config
import random
import io 
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from firmador import firmar
from reportlab.pdfgen import canvas
import os
import smtplib
from flask_sqlalchemy import SQLAlchemy
from database import db
from database.db import get_connection



app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:murillo@localhost:5432/pacientes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager_app = LoginManager(app)
csrf = CSRFProtect()



@login_manager_app.user_loader
def load_user(id):
   return PacienteModel.get_by_id(id)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni = request.form['dni']
        if not dni.isdigit():
          flash("El DNI debe ser un numero entero.", "error")
          return redirect(url_for('login'))
        paciente = Paciente(0, request.form['dni'],0, 0, request.form['password'],0,0,0)
        logged_user = PacienteModel.login(paciente)
        if logged_user != None:
            if logged_user.contrasenia:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("contraseña incorrecta...")
                return render_template('auth/login.html')
        else:
            flash("DNI no existe...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@app.route ('/logout')
def logout(): 
   logout_user()
   return redirect (url_for('login'))


def enviar_correo2(texto, email):
   remitente = "aemurillo92@gmail.com"
   contrasenia = "krdcxcrxiypiqwea"
   mensaje = MIMEMultipart()
   mensaje["From"] = remitente
   mensaje["To"]= email
   mensaje["Subject"]= "BIENBENIDO"
   cuerpo = texto
   mensaje.attach(MIMEText(cuerpo, "plain"))


   try:
      server = smtplib.SMTP("smtp.gmail.com",587)
      server.starttls()
      server.login(remitente,contrasenia)
      server.sendmail(remitente,email,mensaje.as_string())
      server.quit()
   except Exception as e:
      print("no se puedo enviar el correo")
   

def crear_registro():
   paciente = Paciente(0, request.form['dni'], request.form['nombre'], request.form['apellido'], request.form['password'], 
                       request.form['email'], request.form['domicilio'], request.form['fecha_nacimiento'])
   paciente_registry = PacienteModel.agregar_paciente(paciente)
   if paciente_registry == 1: 
      flash("Paciente registrado exitosamente.", "success")
      texto= f'Bienvenido {paciente.nombre} {paciente.apellido} al centro medico   su registro es correcto'
      email = request.form['email']
      enviar_correo2(texto, email)
   else: 
      flash("Hubo un error al registrar al paciente.", "error")

def enviar_correo(codigo_verificacion, email):
   remitente = "aemurillo92@gmail.com"
   contrasenia = "krdcxcrxiypiqwea"
   mensaje = MIMEMultipart()
   mensaje["From"] = remitente
   mensaje["To"]= email
   mensaje["Subject"]= "validador de cuenta"
   cuerpo = f" El codigo de validacion es /n {codigo_verificacion}"
   mensaje.attach(MIMEText(cuerpo, "plain"))

   try:
      server = smtplib.SMTP("smtp.gmail.com",587)
      server.starttls()
      server.login(remitente,contrasenia)
      server.sendmail(remitente,email,mensaje.as_string())
      server.quit()
   except Exception as e:
      print("no se puedo enviar el correo")
   



        
@app.route('/registro', methods = ['GET', 'POST'])
def registro():
   if request.method == 'POST':
      dni = request.form['dni']
      pacienteExiste = PacienteModel.buscar_paciente(dni)
      if (pacienteExiste != None): 
         flash("Ya existe un paciente con este DNI.", "error")
         return render_template('auth/registro.html')
      if not dni.isdigit():
          flash("El DNI debe ser un numero entero.", "error")
          return render_template('auth/registro.html')
      password = request.form['password']
      confirm_password = request.form['password2']
      if password != confirm_password:
         flash ("Las contraseñas no coinciden.", "error")
         return render_template('auth/registro.html')
      #email = request.form['email']
      #codigo_verificacion = str(random.randint(100000,999999))
      #enviar_correo(codigo_verificacion, email)
      crear_registro()
      return render_template('auth/registro.html')
   else: 
      return render_template('auth/registro.html')
   
@app.route('/terminos')
def terminos():
   return render_template('auth/terminos.html')

@app.route('/home')
@login_required
def home(): 
   return render_template('home.html')

def status_401(error):
   return redirect (url_for('login'))

def status_404(error):
   return "<h1> Pagina no encontrada </h1>", 404


@app.route('/recetaMedica')
def recetaMedica():
   return render_template("auth/recetaMedica.html")

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # Obtener los datos del formulario
    nombre = request.form['nombre']
    dni = request.form['dni']
    texto_usuario = request.form['texto_usuario']

    # Crear un objeto de bytes para almacenar el PDF generado
    pdf_bytes = BytesIO()

    # Crear un objeto PDF utilizando ReportLab
    pdf = canvas.Canvas(pdf_bytes)

    # Agregar la cabecera al PDF
    pdf.setFont("Helvetica", 16)
    pdf.drawString(100, 750, "Receta Medica")

    # Agregar el cuerpo al PDF con la información del usuario y el texto ingresado
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 720, f"{nombre}")
    pdf.drawString(100, 700, f" {dni}")
    pdf.drawString(100, 650, f"{texto_usuario}")

    # Guardar el estado del PDF y cerrar el objeto PDF
    pdf.showPage()
    pdf.save()

    # Establecer el cursor del objeto de bytes al principio
    pdf_bytes.seek(0)

   # Guardar el PDF en un archivo temporal
    pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'receta_medica.pdf')
    with open(pdf_filename, 'wb') as pdf_file:
        pdf_file.write(pdf_bytes.read())
   
    # Redirigir a la otra función con la ruta del archivo PDF
    #print("-------CONTROLCONTROL----", pdf_filename)
    return redirect(url_for('proceso', pdf_filename=pdf_filename))
   
   #PARA MOSTRAR POR PANTALLA 
    # Crear una respuesta con el contenido del PDF
    #response = make_response(pdf_bytes.read())
    # Configurar el tipo de contenido como PDF
    #response.headers['Content-Type'] = 'application/pdf'
    # Configurar el nombre del archivo PDF para la descarga
    #response.headers['Content-Disposition'] = 'inline; filename=receta_medica.pdf'
    #return response
@app.route('/proceso')
def proceso():
   return render_template("auth/firmaDigital.html")

@app.route('/procesar',  methods=['POST'])
def procesar():
   #print("----------CONTROL-----------")
   pdf= os.path.join(app.config['UPLOAD_FOLDER'], 'receta_medica.pdf')
   
        
   #pdf = request.args.get('receta_medica.pdf')
   #print(f"PDF: {pdf}")
   #pdf = request.files.get("pdf")
   firma = request.files.get("firma")
   #print("----------FIRMA---------",firma)
   contraseña = request.form.get("palabra_secreta")
   archivo_pdf_para_enviar_al_cliente = io.BytesIO()
   #print("----------ANTES del TRY-----------")
   try:
      print("----------CONTRdsadasdasOL-----------")
      datau, datas = firmar(contraseña, firma, pdf)
      print("----------CONTROL-----------")
      archivo_pdf_para_enviar_al_cliente.write(datau)
      print("---------COntrol1-------------")
      archivo_pdf_para_enviar_al_cliente.write(datas)
      print("---------COntrol2-------------")
      archivo_pdf_para_enviar_al_cliente.seek(0)
      return send_file(archivo_pdf_para_enviar_al_cliente, mimetype="application/pdf",
                        download_name="firmado" + ".pdf",
                        as_attachment=True)
   except ValueError as e:
      return "Error firmando: " + str(e) + " . Se recomienda revisar la contraseña y el certificado"

if __name__ == '__main__':
   app.config.from_object(config['development'])
   csrf.init_app(app)
   app.register_error_handler(401, status_401)
   app.register_error_handler(404, status_404)
   app.run()