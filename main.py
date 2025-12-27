# este codigo abre a camera do pc, identifica pessoas sem epi (equipamento de protecao individual) e exibe na tela, se tiver com o epi exibe a mensagem "Acesso Liberado"
# o codigo tambem se conecta a um arduino via serial e aciona um led vermelho e uma sirene caso a pessoa esteja sem epi
import cv2
from roboflow import Roboflow
import time
import threading
import serial

# --- CONFIGURAÇÃO ROBOFLOW ---
API_KEY = "9hbb9I8dsbwD982mK1dj"  # Cuidado com isso em vídeo
PROJECT_NAME = "ppe-fruwx-fjbxs"
VERSION_NUMBER = 1

# --- CONFIGURAÇÃO ARDUINO ---
SERIAL_PORT = 'COM7'  # Confirme sua porta
BAUD_RATE = 9600

# --- VARIÁVEIS GLOBAIS ---
current_predictions = []
frame_to_process = None
lock = threading.Lock()

# Mapa de classes
CLASS_MAPPING = {
    "helmet": "capacete", "helmet on": "capacete",
    "vest": "colete",
    "no helmet": "sem_capacete", "no vest": "sem_colete", "person": "pessoa"
}

# Cores (B, G, R)
COLOR_SAFE = (0, 255, 0)      # Verde
COLOR_DANGER = (0, 0, 255)    # Vermelho
COLOR_NEUTRAL = (255, 0, 0)   # Azul
COLOR_GRAY = (128, 128, 128)  # Cinza para "Nenhuma deteccaoo"

# --- FUNÇÃO DA IA (RODA EM SEGUNDO PLANO) ---


def run_inference():
    global current_predictions, frame_to_process

    print("Iniciando Thread da IA...")
    rf = Roboflow(api_key=API_KEY)
    project = rf.workspace().project(PROJECT_NAME)
    model = project.version(VERSION_NUMBER).model
    print("IA Pronta!")

    while True:
        if frame_to_process is not None:
            try:
                with lock:
                    small_frame = cv2.resize(frame_to_process, (640, 640))

                # Ajuste a confiança se necessário (ex: confidence=50)
                result = model.predict(
                    small_frame, confidence=40, overlap=30).json()
                new_predictions = result['predictions']

                scale_factor = 1280 / 640
                for box in new_predictions:
                    box['x'] = box['x'] * scale_factor
                    box['y'] = box['y'] * scale_factor
                    box['width'] = box['width'] * scale_factor
                    box['height'] = box['height'] * scale_factor

                current_predictions = new_predictions
            except Exception as e:
                print(f"Erro na conexão IA: {e}")
            time.sleep(0.05)
        else:
            time.sleep(0.1)

# --- FUNÇÃO PRINCIPAL ---


def main():
    global frame_to_process

    # 1. Tenta conectar com o Arduino
    try:
        print(f"Conectando ao Arduino na porta {SERIAL_PORT}...")
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("Arduino Conectado!")
    except Exception as e:
        print(f"ERRO ARDUINO: {e}")
        arduino = None

    # 2. Inicia Thread IA
    ai_thread = threading.Thread(target=run_inference)
    ai_thread.daemon = True
    ai_thread.start()

    # 3. Configura Webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Iniciando vídeo...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        with lock:
            frame_to_process = frame.copy()

        # Variáveis para este frame
        tem_pessoa = False
        tem_capacete = False
        tem_colete = False

        # --- PROCESSA AS DETECÇÕES ---
        for box in current_predictions:
            original_class = box['class']
            label = CLASS_MAPPING.get(original_class, original_class)

            # Verifica o que foi detectado
            if label == "pessoa":
                tem_pessoa = True
            elif label == "capacete":
                tem_capacete = True
            elif label == "colete":
                tem_colete = True

            # Coordenadas para desenho
            x, y, w, h = int(box['x']), int(box['y']), int(
                box['width']), int(box['height'])
            x1, y1 = int(x - w/2), int(y - h/2)
            x2, y2 = int(x + w/2), int(y + h/2)

            # Define cor da caixa baseado no item
            box_color = COLOR_NEUTRAL
            if label == "capacete" or label == "colete":
                box_color = COLOR_SAFE
            elif "sem_" in label:  # sem_capacete, sem_colete
                box_color = COLOR_DANGER

            # Desenha a caixa e o texto
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

        # --- LÓGICA DE DECISÃO (HUD + ARDUINO) ---

        # CASO 1: Ninguém na tela
        if not tem_pessoa:
            status_text = "NENHUMA DETECCAO"
            status_color = COLOR_GRAY  # Ou COLOR_SAFE se preferir verde

            # Envia '0' para deixar apenas o LED VERDE ligado (standby)
            if arduino:
                arduino.write(b'0')

        # CASO 2: Pessoa detectada, agora verifica EPIs
        else:
            if tem_capacete and tem_colete:
                status_text = "APROVADO: ACESSO LIBERADO"
                status_color = COLOR_SAFE
                # Envia '0' para LED VERDE
                if arduino:
                    arduino.write(b'0')
            else:
                status_text = "ALERTA: EPI INCOMPLETO"
                status_color = COLOR_DANGER
                # Envia '1' para SIRENE/LED VERMELHO
                if arduino:
                    arduino.write(b'1')

        # Desenha a barra de status superior
        cv2.rectangle(frame, (0, 0), (1280, 80), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)

        cv2.imshow("Auditor EPI", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if arduino:
        arduino.write(b'0')  # Garante estado seguro ao sair
        arduino.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
