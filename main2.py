import cv2
from roboflow import Roboflow
import time
import threading

# --- CONFIGURAÇÃO ---
API_KEY = "9hbb9I8dsbwD982mK1dj"  # Cuidado: Não mostre isso em vídeo
PROJECT_NAME = "ppe-fruwx-fjbxs"
VERSION_NUMBER = 1

# --- VARIÁVEIS GLOBAIS (Compartilhadas entre a Webcam e a IA) ---
current_predictions = []  # Guarda as ultimas caixas detectadas
frame_to_process = None  # Guarda o frame atual para a IA ler
lock = threading.Lock()  # Segurança para as duas threads não brigarem

# Mapa de classes
CLASS_MAPPING = {
    "helmet": "capacete", "helmet on": "capacete",
    "vest": "colete",
    "no helmet": "sem_capacete", "no vest": "sem_colete", "person": "pessoa"
}

# Cores
COLOR_SAFE = (0, 255, 0)
COLOR_DANGER = (0, 0, 255)
COLOR_NEUTRAL = (255, 0, 0)

# --- FUNÇÃO DA IA (RODA EM SEGUNDO PLANO) ---


def run_inference():
    global current_predictions, frame_to_process

    # Conecta ao Roboflow apenas uma vez
    print("Iniciando Thread da IA...")
    rf = Roboflow(api_key=API_KEY)
    project = rf.workspace().project(PROJECT_NAME)
    model = project.version(VERSION_NUMBER).model
    print("IA Pronta e rodando em segundo plano!")

    while True:
        # Se tiver um frame novo esperando...
        if frame_to_process is not None:
            try:
                # Pegamos o frame de forma segura
                with lock:
                    # Reduzimos o frame ANTES de enviar para ser mais rápido (upload menor)
                    # O modelo treina em 640x640, não precisa enviar HD
                    small_frame = cv2.resize(frame_to_process, (640, 640))

                # Envia para a nuvem
                result = model.predict(
                    small_frame, confidence=40, overlap=30).json()

                # Atualiza as predições globais
                new_predictions = result['predictions']

                # Precisamos ajustar a escala, pois enviamos pequeno (640) mas desenhamos no grande (1280)
                # Fator de escala: 1280 / 640 = 2
                scale_factor = 1280 / 640

                for box in new_predictions:
                    box['x'] = box['x'] * scale_factor
                    box['y'] = box['y'] * scale_factor
                    box['width'] = box['width'] * scale_factor
                    box['height'] = box['height'] * scale_factor

                current_predictions = new_predictions

            except Exception as e:
                print(f"Erro na conexão: {e}")

            # Pequena pausa para não explodir a CPU
            time.sleep(0.05)
        else:
            time.sleep(0.1)

# --- FUNÇÃO PRINCIPAL (RODA O VÍDEO) ---


def main():
    global frame_to_process

    # 1. Inicia a IA em uma Thread separada (paralela)
    ai_thread = threading.Thread(target=run_inference)
    ai_thread.daemon = True  # Faz a thread morrer quando fechar o programa
    ai_thread.start()

    # 2. Configura Webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Iniciando vídeo...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Atualiza o frame que a IA vai ler (sem travar o video)
        with lock:
            frame_to_process = frame.copy()

        # --- DESENHAR (Usa a última previsão disponível) ---
        # Note que aqui não chamamos o model.predict, apenas lemos a variável
        tem_capacete = False
        tem_colete = False

        for box in current_predictions:
            original_class = box['class']
            label = CLASS_MAPPING.get(original_class, original_class)

            x = int(box['x'])
            y = int(box['y'])
            w = int(box['width'])
            h = int(box['height'])

            x1 = int(x - w/2)
            y1 = int(y - h/2)
            x2 = int(x + w/2)
            y2 = int(y + h/2)

            color = COLOR_NEUTRAL
            if label == "capacete":
                color = COLOR_SAFE
                tem_capacete = True
            elif label == "colete":
                color = COLOR_SAFE
                tem_colete = True
            elif label in ["sem_capacete", "sem_colete"]:
                color = COLOR_DANGER

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # --- HUD ---
        status_text = "BUSCANDO..."
        status_color = (200, 200, 200)

        if tem_capacete and tem_colete:
            status_text = "APROVADO: ACESSO LIBERADO"
            status_color = COLOR_SAFE
        elif not tem_capacete or not tem_colete:
            status_text = "ALERTA: EPI INCOMPLETO"
            status_color = COLOR_DANGER

        # Interface Bonita
        cv2.rectangle(frame, (0, 0), (1280, 80), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)

        cv2.imshow("Auditor de EPI - Threading Otimizado", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
