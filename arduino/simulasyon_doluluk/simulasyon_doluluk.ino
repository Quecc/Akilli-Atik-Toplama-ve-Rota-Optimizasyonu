/*
  Akilli Atik Toplama - Adim 1 - Tinkercad Simulasyonu
  Arduino Uno + HC-SR04. Harici kutuphane gerekmez.

  HC-SR04 VCC -> Uno 5V
  HC-SR04 GND -> Uno GND
  HC-SR04 TRIG -> Uno D9
  HC-SR04 ECHO -> Uno D10

  Seri Monitor: 9600 baud.
  Bu surumde ornek 200/20 cm ile simulasyon icin yuzde hesabi aciktir.
  Fiziksel kurulum icin doluluk_sensoru.ino dosyasini kullanin.
  Sanal sensorun mesafesini 200, 150, 80 ve 20 cm olarak degistirin.
  Bu dosyada CALIBRATED zaten true olarak ayarlanmistir.
*/

const byte TRIG_PIN = 9;
const byte ECHO_PIN = 10;
const byte SAMPLE_COUNT = 5;
const byte MIN_VALID_SAMPLES = 3;
const unsigned long ECHO_TIMEOUT_US = 30000UL;

// Bunlar ORNEK degerlerdir; gercek kutunuzun olculeri degildir.
const float EMPTY_DISTANCE_CM = 200.0f;
const float FULL_DISTANCE_CM = 20.0f;
const float COLLECTION_THRESHOLD_PERCENT = 50.0f;
const bool CALIBRATED = true;

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  const unsigned long duration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (duration == 0) {
    return -1.0f; // Yanki yok veya zaman asimi.
  }

  const float distance = duration / 58.0f;
  if (distance < 2.0f || distance > 400.0f) {
    return -1.0f; // Sensorun belirtilen olcum araligi disinda.
  }
  return distance;
}

bool readMedianDistanceCm(float &distance) {
  float samples[SAMPLE_COUNT];
  byte count = 0;

  for (byte i = 0; i < SAMPLE_COUNT; ++i) {
    const float sample = readDistanceCm();
    if (sample >= 0.0f) {
      samples[count++] = sample;
    }
    // HC-SR04 olcumleri arasinda 60 ms'den fazla sure birakilir.
    delay(70);
  }

  if (count < MIN_VALID_SAMPLES) {
    return false;
  }

  // En fazla 5 sayiyi sirala; ortadaki olcumu kullan.
  for (byte i = 1; i < count; ++i) {
    const float value = samples[i];
    int j = i - 1;
    while (j >= 0 && samples[j] > value) {
      samples[j + 1] = samples[j];
      --j;
    }
    samples[j + 1] = value;
  }

  if (count % 2 == 0) {
    distance = (samples[count / 2 - 1] + samples[count / 2]) / 2.0f;
  } else {
    distance = samples[count / 2];
  }
  return true;
}

bool calibrationIsValid() {
  return FULL_DISTANCE_CM >= 2.0f
      && EMPTY_DISTANCE_CM <= 400.0f
      && EMPTY_DISTANCE_CM > FULL_DISTANCE_CM
      && COLLECTION_THRESHOLD_PERCENT >= 0.0f
      && COLLECTION_THRESHOLD_PERCENT <= 100.0f;
}

float fillPercentFromDistance(float distance) {
  const float fill = 100.0f * (EMPTY_DISTANCE_CM - distance)
      / (EMPTY_DISTANCE_CM - FULL_DISTANCE_CM);
  if (fill < 0.0f) return 0.0f;
  if (fill > 100.0f) return 100.0f;
  return fill;
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  Serial.begin(9600);
  delay(100);

  Serial.println(F("Akilli Atik - Arduino Uno + HC-SR04"));
  Serial.print(F("MOD: SIMULASYON | Bos: "));
  Serial.print(EMPTY_DISTANCE_CM, 1);
  Serial.print(F(" cm, dolu: "));
  Serial.print(FULL_DISTANCE_CM, 1);
  Serial.println(F(" cm (ornek)"));
  if (!CALIBRATED) {
    Serial.println(F("Once mesafeyi kontrol edin. Doluluk icin kalibrasyon gerekli."));
  }
}

void loop() {
  float distance;
  if (!readMedianDistanceCm(distance)) {
    Serial.println(F("HATA: Gecerli mesafe yok. Doluluk ve toplama durumu bilinmiyor."));
    delay(650);
    return;
  }

  Serial.print(F("Mesafe: "));
  Serial.print(distance, 1);
  Serial.print(F(" cm"));

  if (!CALIBRATED) {
    Serial.println(F(" | Doluluk: KALIBRASYON GEREKIYOR"));
  } else if (!calibrationIsValid()) {
    Serial.println(F(" | HATA: Bos/dolu mesafelerini ve esik ayarini kontrol edin."));
  } else {
    const float fill = fillPercentFromDistance(distance);
    Serial.print(F(" | Yaklasik doluluk: %"));
    Serial.print(fill, 1);
    // Kullanici senaryosu: yalnizca %50'NIN UZERI toplama adayi.
    if (fill > COLLECTION_THRESHOLD_PERCENT) {
      Serial.println(F(" | TOPLAMA ADAYI"));
    } else {
      Serial.println(F(" | ESIGIN UZERINDE DEGIL"));
    }
  }
  delay(650);
}
