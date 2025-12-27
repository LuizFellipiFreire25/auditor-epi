// --- CÓDIGO ARDUINO ---
int pinoOK = 12;
int pinoNOT = 13;
int pinoBuzzer = 9;

void setup() {
  Serial.begin(9600);       // Inicia comunicação serial
  pinMode(pinoOK, OUTPUT);
  pinMode(pinoBuzzer, OUTPUT);
  pinMode(pinoNOT, OUTPUT);

  
  // Teste rápido ao ligar
  digitalWrite(pinoOK, HIGH);
  delay(200);
  digitalWrite(pinoOK, LOW);
  delay(100);
  digitalWrite(pinoNOT, HIGH);
  delay(200);
  digitalWrite(pinoNOT, LOW);
}

void loop() {
  // Verifica se o Python mandou alguma coisa
  if (Serial.available() > 0) {
    char comando = Serial.read(); // Lê o caractere recebido

    if (comando == '1') {
      // COMANDO DE ACESSO negado
      digitalWrite(pinoNOT, LOW);
      digitalWrite(pinoOK, HIGH); // Liga LED
      tone(pinoBuzzer, 1000);      // Liga Buzzer (1000Hz)
    } 
    else if (comando == '0') {
      // COMANDO DE BLOQUEIO/ESPERA
      digitalWrite(pinoOK, LOW);  // Desliga LED
      digitalWrite(pinoNOT, HIGH);
      noTone(pinoBuzzer);          // Para o som
    }
  }
}