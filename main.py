#Importamos las librerias necesarias
import cv2
import pytesseract
import camera
import time
import pio
import resource
import Controls
import RPi.GPIO as GPIO
import qrcode
import threading #para las interrupciones
from wiringpi import Serial
#Para correo
import smtplib
#Para firebase
from firebase import firebase

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
#Creamos la variables de firebase (creo instancia)
firebase = firebase.FirebaseApplication('https://psistemasembebidos-default-rtdb.firebaseio.com/', None)

def peripheral_setup () :
# Peripheral Constructors, los que se van a ejecutar una unica vez
  
  #Codigo para la picamera
  pio.CAM1= camera.RPiCamera()
  pio.IotPhoto1= Controls.Photo("IotPhoto1", )
  #Seteamos la forma de manejar los pines de la raspberry tal cual salen en los terminal labels
  GPIO.setmode(GPIO.BCM)
  pio.bt1= 4#poniendo el boton como global con el pio para llamarlo en otras funciones
  pio.modo= 17     #Si es 1 es Entrada, si es 0 es Salida
  pio.M1P1= 5	   #Para el giro del motor 1, si P1 es False y P2 es True el motor va en sentido antihorario
			   #en cambio si es P1 True y P2 False el motor va en sentido horario
  pio.M1P2=6
  pio.M1PWM=7   #velocidad para el motor1 (entrada)
  pio.ledRojo1= 18 #led rojo en la entrada
  pio.ledVerde1=19 #led verde entrada
  
  pio.M2P1= 12	   #Para el giro del motor 2, si P1 es False y P2 es True el motor va en sentido antihorario
			   #en cambio si es P1 True y P2 False el motor va en sentido horario
  pio.M2P2=13
  pio.M2PWM=16   #velocidad para el motor2 (salida)
  pio.ledRojo2= 20
  pio.ledVerde2=21
  alerta= False	    #variables para entrar a la alerta
  
  GPIO.setup(pio.bt1,GPIO.IN, GPIO.PUD_DOWN)#configuramos el boton como entrada y con la conexion de pull down
  GPIO.setup(pio.modo, GPIO.IN)  #Configuramos el modo como entrada
  GPIO.setup(pio.M1PWM, GPIO.OUT)
  GPIO.setup(pio.M1P1, GPIO.OUT)
  GPIO.setup(pio.M1P2, GPIO.OUT)
  GPIO.setup(pio.M2PWM, GPIO.OUT)
  GPIO.setup(pio.M2P1, GPIO.OUT)
  GPIO.setup(pio.M2P2, GPIO.OUT)
  GPIO.setup(pio.ledRojo1, GPIO.OUT)
  GPIO.setup(pio.ledVerde1, GPIO.OUT)
  GPIO.setup(pio.ledRojo2, GPIO.OUT)
  GPIO.setup(pio.ledVerde2, GPIO.OUT)
  #Creamos las instancias de PWM (canal,frecuencia)
  pio.servo1= GPIO.PWM(pio.M1PWM,50)
  pio.servo2= GPIO.PWM(pio.M2PWM,50)
  pio.servo1.start(0)
  pio.servo2.start(0)
  

def peripheral_loop () :
  #Si el Switch esta en alto entonces es la entrada
  if GPIO.input(pio.modo):
    
    capPlaca()
    GPIO.output(pio.ledRojo1,True)	#Encendemos el led rojo de la entrada

    texto= lecPlaca()
    #ntexto= len(texto) #tamano de la cadena, empieza en 1
    #Extraccion de la parte de interes
    texte= texto.find("-")  #para determinar la ubicacion de la parte de interes se busca el '-'(LLL-1111), empieza en 0 a contar
    texto1= texto[texte-3:] #cortamos la parte de interes
    texto1= '/' + texto1.strip() #concatenamos y borramos posibles espacios existentes
    print(texto1)
    entCarro(texto1)	#funcion que pone la nueva placa en la base de datos
    generacionQR(texto1)
    envioEmail()
    GPIO.output(pio.ledRojo1,False)  #Apagamos el led rojo
    GPIO.output(pio.ledVerde1,True) #Encendemos el led verde
    GPIO.output(pio.M1P1,False)
    GPIO.output(pio.M1P2,True)
    
    pio.servo1.ChangeDutyCycle(10) # Para cambiar el ciclode trabajo de 0 a 10
    threading.Timer(1.35,int1).start()

#Modo salida del parqueo
  else:
    capPlaca()		#capturamos la placa
    global alerta		#variables para lanzar la alerta
    alerta= False
    GPIO.output(pio.ledRojo2,True)	#prendemos el led rojo de la salida
    textoSalida= lecPlaca()
    #Extraccion de la parte de interes
    texts= textoSalida.find("-")  #para determinar la ubicacion de la parte de interes se busca el '-'(LLL-1111), empieza en 0 a contar
    texto2= textoSalida[texts-3:] #cortamos la parte de interes
    texto2= '/' + texto2.strip() #concatenamos y borramos posibles espacios existentes
    print(texto2)
    textQR= lecQR()
    #Si el texto de la placa coincide con el del codigo QR y la placa se encuentra en la base de datos movemos el motor
    #sacarlo de la funcion a ver si funciona
    placaf= firebase.get("/Carro", texto2) #si la placa no esta ref es iguala None
    print(placaf)
    if((texto2 == textQR) and (placaf != None)):
      #firebase.put("/Carro", texto, False)
      print('Son iguales')
      GPIO.output(pio.ledRojo2,False)
      GPIO.output(pio.ledVerde2,True)
      GPIO.output(pio.M2P1,False)
      GPIO.output(pio.M2P2,True)
      pio.servo2.ChangeDutyCycle(10) # Para cambiar el ciclo de trabajo de 0 a 10
      threading.Timer(1.35,int2).start()
    else:
      alerta= True
      threading.Timer(0.5,alerta1).start()
      print('Entramos a la alerta1')
    
# Main function
def main () :
# Setup
 peripheral_setup()                            #llamamos a los perifericos
# Infinite loop
 while 1 :
  peripheral_loop()
  pass
# Command line execution
if __name__ == '__main__' :
   main()


def int1():
  #sleep(3)
  pio.servo1.ChangeDutyCycle(0)
  #sleep(5)		#damos un delay de 5s para que pase el carro
  if(GPIO.input(pio.M1P1)==False and GPIO.input(pio.M1P2)==True):
    #Invertimos el giro
    GPIO.output(pio.M1P1,True)
    GPIO.output(pio.M1P2,False)
    threading.Timer(10,int11).start()	#q se active solo al inicio
  else:
    GPIO.output(pio.ledVerde1,False) #Apagamos el led verde
    GPIO.output(pio.ledRojo1,True)
  
def int11():
  pio.servo1.ChangeDutyCycle(10)
  #sleep(3)
  #servo1.ChangeDutyCycle(0)
  threading.Timer(1.5,int1).start()


def int2():
  pio.servo2.ChangeDutyCycle(0)
  #sleep(5)		#damos un delay de 5s para que pase el carro
  if(GPIO.input(pio.M2P1)==False and GPIO.input(pio.M2P2)==True):
    #Invertimos el giro
    GPIO.output(pio.M2P1,True)
    GPIO.output(pio.M2P2,False)
    threading.Timer(10,int21).start()	#q se active solo al inicio
  else:
    GPIO.output(pio.ledVerde2,False) #Apagamos el led verde
    GPIO.output(pio.ledRojo2,True)

def int21():
  pio.servo2.ChangeDutyCycle(10)
  #sleep(3)
  #servo2.ChangeDutyCycle(0)
  threading.Timer(1.5,int2).start()

def alerta1():
  GPIO.output(pio.ledRojo2,False)	#apagamos el led rojo de la salida
  #Si se pulsa el boton bt1 salimos de la alerta
  if(alerta):
    threading.Timer(0.5,alerta12).start()
  else:
    #Si alerta esta en False, salimos del threading alerta
    GPIO.output(pio.ledRojo2,True)

def alerta12():
  GPIO.output(pio.ledRojo2,True) 	#Prendemos el led verde
  #Si se pulsa el boton bt1 salimos de la alerta
  threading.Timer(0.5,alerta1).start()
  

def envioEmail():
  print('Listo para enviar')
  email_sender= 'and5gua97@gmail.com' #correo desde donde se envia
  email_receiver= 'andres.guapi22@gmail.com' #correo a quien se le envia, profe ttoscanoqui@gmail.com
  subject= 'Proyecto Embebidos'
  msg= MIMEMultipart()
  msg['From']= email_sender
  msg['To']= email_receiver
  msg['Subject']= subject
  body= 'Hola, este correo fue enviado desde python, prueba codigo QR'
  msg.attach(MIMEText(body, 'plain'))
  #Parte del archivo
  filename= 'C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/codigoplaca.jpg'
  attachment= open(filename, 'rb')
  part= MIMEBase('application', 'octet_stream')
  part.set_payload((attachment).read())
  encoders.encode_base64(part)
  part.add_header('Content-Disposition', 'attachment; filename= '+filename)
  msg.attach(part)
  
  text= msg.as_string()
  connection= smtplib.SMTP('smtp.gmail.com', 587)
  connection.starttls()
  connection.login(email_sender, 'sistemasEmbebidosP101')
  connection.sendmail(email_sender, email_receiver, text)
  connection.quit()
  print('Email enviado')
  
def capPlaca2():
  while(True):
        
  #Codigo para abrir la camara y usarla en el proyecto
    cap= cv2.VideoCapture(0) #poder realizar una capturas de un video en tiempo real
    ref, frame= cap.read()#asignamos a dos variables, uno es verdad si la camara esta disponible y la otra es la captura
    time.sleep(3)
  #si la camara esta disponible
    if ref:
      cv2.imshow("imagen",frame) #para mostrarlo en una ventana nueva
      break
        #pio.IotPhoto1.showImage('frame')#,"C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/CodigoQR con OpenCV/lecturacam.jpg")
        #Validamos cuando cerramos la ventana, cuando el usuario digita "y" se guarda la imagen
  return frame
  
def capPlaca():
  while(True):
    if GPIO.input(pio.bt1):
    
      while(True):
        
        #Codigo para abrir la camara y usarla en el proyecto
        cap= cv2.VideoCapture(0) #poder realizar una capturas de un video en tiempo real
        ref, frame= cap.read()#asignamos a dos variables, uno es verdad si la camara esta disponible y la otra es la captura
        time.sleep(3)
	#si la camara esta disponible
        if ref:
          cv2.imshow("imagen",frame) #para mostrarlo en una ventana nueva
          break
        #pio.IotPhoto1.showImage('frame')#,"C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/CodigoQR con OpenCV/lecturacam.jpg")
        #Validamos cuando cerramos la ventana, cuando el usuario digita "y" se guarda la imagen
    if cv2.waitKey(1)& 0xFF == ord('y'):
      cv2.imwrite("C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/cplaca.jpg",frame)
      cv2.destroyAllWindows() #para cerrar las ventanas
      break
  cap.release()#para q nos espere mientras no presione,finalizamos la camara
  

def lecPlaca():
  #Hacemos lectura de la placa
  placa = []           #Array vacio donde se almacena la placa detectada
  image = cv2.imread("C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/cplaca.jpg")
  
  time.sleep(5)
  text = pytesseract.image_to_string(image,lang='spa')#leemos los caracteres poniendo la variable donde esta la imagen
  print('Texto: ',text)
  
  gray= cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #Pasamos de BGR a escalas de grises
  gray= cv2.blur(gray,(3,3))
  cv2.imwrite("C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/placagray.jpg",gray)
  canny= cv2.Canny(gray,150,200) #detector de bordes
  #Mejoraremos lo binario de canny
  canny= cv2.dilate(canny,None,iterations=1)   #engruesa las areas blancas
  #Encontramos los contornos de canny
  cnts,_ = cv2.findContours(canny,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
  
  #Placas ecuador ancho=404mm,alto=154mm
  #aspect ratio placa = ancho/alto= 404/154= 2,62
  
  #Desechamos los contornos no deseados, nos basamos en su area y tratamos de encontrar la forma rectangular de la placa
  for c in cnts:
    area= cv2.contourArea(c) #sabremos el area de un contorno
    x,y,w,h= cv2.boundingRect(c) #nos ayuda a detectar un rectangulo en la imagen,nos ayuda con el aspect ratio del contorno
    epsilon= 0.09*cv2.arcLength(c,True) #parametro necesario para aproxPoly, 9% se determino despues de experimentacion
    approx= cv2.approxPolyDP(c,epsilon,True)#para determinar los vertices del contorno
    
    if (len(approx)==4 and area >9000):
      print("Area: ",area)
      #solo se muestan los contornos mayores a 9000 y los contornos con 4 vertices
      #cv2.drawContours(image,[c],-1,(0,255,0),2)
      #Agregamos el aspect ratio para ser mas precisos
      aspect_ratio= float(w)/h
      #2.4 porque anadimos un margen de error
      if aspect_ratio>2.1:
        placa= gray[y:y+h,x:x+w]
        texto= pytesseract.image_to_string(placa, config='--psm 11')#extraemos el texto especificando el modo de segmentacion de pagina
	
        print('texto en placa= ',texto)
        cv2.imshow('placa',placa) #mostramos
        cv2.moveWindow('placa',780,10) #movemos la imagen a cierta posicion
        cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),3)
        cv2.putText(image,texto,(x-20,y-10),1,2.2,(0,255,0),2)
  
  cv2.imwrite("C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/placacanny.jpg",canny)
  cv2.imwrite("C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/placaimage.jpg",image)
  cv2.imshow('Imagen',image) #para visualizar
  cv2.imshow('Canny',canny)  #visualizamos despues de detectar bordes
  cv2.moveWindow('Image',45,10)
  cv2.waitKey(0)         #el proceso siga hasta presionar alguna letra
  cv2.destroyAllWindows()
  return texto

#Generamos el codigo QR
def generacionQR(texto):
  images= qrcode.make(texto)
  #guardamos en una carpeta nuestro codigo de la placa
  images.save('C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/codigoplaca.jpg')


#Leemos el codigo QR
def lecQR():
  while(True):
    if GPIO.input(pio.bt1):
      while(True):
        
        #Codigo para abrir la camara y usarla en el proyecto
        cap= cv2.VideoCapture(0) #poder realizar una capturas de un video en tiempo real
        ref, frame= cap.read()#asignamos a dos variables, uno es verdad si la camara esta disponible y la otra es la captura
        time.sleep(3)
	#si la camara esta disponible
        if ref:
          cv2.imshow("imagen",frame) #para mostrarlo en una ventana nueva
          break
    if cv2.waitKey(1)& 0xFF == ord('y'):
      cv2.imwrite("C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/QRsalida.jpg",frame)
      cv2.destroyAllWindows() #para cerrar las ventanas
      break
  cap.release()#para q nos espere mientras no presione,finalizamos la camara
  
  print("todo bien")
  d= cv2.QRCodeDetector()#d es un arreglo de 3 variables
  #usamos una funcion de openCV para leer la imagen previamente creada
  val, points, straingh= d.detectAndDecode(cv2.imread('C:/Users/and_g/OneDrive/Documentos/Materias/Sistemas Embebidos/Practico sist embebidos/Proyecto/Proyecto6/QRsalida.jpg'))#cambiamos la direccion a codigop003 para pruebas
  print(val)
  return val
  
def entCarro(texto):
  firebase.put("/Carro", texto, True)
