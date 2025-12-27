# 👷 Auditor de EPIs com Visão Computacional e Arduino

Este projeto é um sistema de visão computacional capaz de identificar em tempo real se um colaborador está utilizando os Equipamentos de Proteção Individual (EPIs) corretos (Capacete e Colete). O sistema se comunica com um Arduino para liberar acesso (LED Verde) ou emitir alertas (Buzzer/LED Vermelho).

## 🚀 Funcionalidades
- **Detecção em Tempo Real:** Uso de modelo YOLOv8 treinado no Roboflow.
- **Multithreading:** Processamento de IA em segundo plano para manter o vídeo fluido.
- **Integração com Hardware:** Comunicação Serial com Arduino.
- **Lógica de Segurança:**
  - ✅ **Verde:** Acesso Liberado (Capacete + Colete detectados).
  - ⚠️ **Vermelho:** Alerta (EPI incompleto).
  - 💤 **Standby:** Nenhuma detecção (Led Verde/Seguro).

## 🛠️ Tecnologias Utilizadas
- **Linguagem:** Python 3.x
- **Bibliotecas:** OpenCV, Roboflow, PySerial, Threading
- **Hardware:** Arduino Uno/Nano (LED + Buzzer)

## 📦 Como rodar este projeto

### 1. Clone o repositório
```bash
git clone [https://github.com/LuizFellipiFreire25/auditor-epi.git](https://github.com/LuizFellipiFreire25/auditor-epi.git)
cd auditor-epi
