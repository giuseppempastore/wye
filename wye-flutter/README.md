# WYE Flutter App - Architettura e Setup

## Overview

App mobile **cross-platform** (Android + iOS) per la valutazione della salubrità di prodotti alimentari e cosmetici.

Comunica con un backend Python (FastAPI) per l'analisi e lo scoring.

---

## Struttura Progetto

```
lib/
├── main.dart                    # Entry point app
├── theme/
│   └── app_theme.dart          # Colors, typography, Material 3
├── models/
│   └── product_model.dart       # Product, NutritionFacts, ScanHistory
├── services/
│   └── api_client.dart          # HTTP client per backend Python
├── providers/
│   └── app_providers.dart       # State management (Provider)
├── router/
│   └── app_router.dart          # Go Router navigation
├── screens/
│   ├── home_screen.dart         # Home principale
│   ├── barcode_scanner_screen.dart   # Scanner
│   ├── product_detail_screen.dart    # Dettagli prodotto
│   ├── manual_analysis_screen.dart   # Premium: analisi manuale
│   ├── history_screen.dart      # Storico scansioni
│   └── settings_screen.dart     # Impostazioni
└── widgets/
    └── score_widgets.dart       # Componenti riusabili
```

---

## Setup e Avvio

### 1. Prerequisiti

```bash
flutter --version  # >= 3.0
flutter doctor     # Verifica setup Android/iOS
```

### 2. Installare dipendenze

```bash
cd wye-flutter
flutter pub get
```

### 3. Configurare backend Python

Nel file `lib/services/api_client.dart`, aggiorna l'URL:

```dart
class ApiConfig {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator
  // Su iOS device reale: 'http://YOUR_LOCAL_IP:8000'
  // In produzione: 'https://api.wyeapp.com'
}
```

### 4. Eseguire l'app

**Android:**
```bash
flutter run -d <device_id>
```

**iOS:**
```bash
flutter run -d <device_id>
```

**Entrambi (con hot reload):**
```bash
flutter run
```

---

## Stack Tecnologico

| Layer | Tecnologia |
|-------|-----------|
| **UI/Design** | Flutter, Material Design 3 |
| **State Management** | Provider |
| **Navigation** | Go Router |
| **HTTP** | http, Dio |
| **Camera/Barcode** | mobile_scanner, permission_handler |
| **Local Storage** | Hive, Shared Preferences |
| **Backend** | Python FastAPI |
| **Database** | PostgreSQL (backend) |

---

## Features MVP

### Base (Free)
- ✅ Barcode scanning con camera
- ✅ Lookup prodotti nel database
- ✅ Visualizzazione score (ingredient + nutrition + final)
- ✅ Allergen detection
- ✅ Storico scansioni (local cache)
- ✅ No login obbligatorio

### Premium
- ✅ Manual ingredient analysis
- ✅ Photo upload (OCR ingredienti/nutrizione)
- ✅ User profile (allergie, health conditions)
- ✅ Personalized scoring
- ✅ Advanced warnings

---

## Comunicazione Backend

### Endpoint utilizzati

**GET `/product/{barcode}`**
```json
Request: barcode="8718206..."

Response: {
  "barcode": "8718206...",
  "product_name": "Nutella",
  "brand": "Ferrero",
  "category": "food",
  "ingredient_score": 32,
  "nutrition_score": 65,
  "final_score": 42,
  "risk_level": "moderate",
  "ingredients": [...],
  "nutrition_facts": {...},
  "allergens": [...]
}
```

**POST `/analyze`**
```json
Request: {
  "product_name": "Biscotti",
  "ingredients": "acqua, zucchero, farina...",
  "language": "it",
  "category": "food"
}

Response: (come GET /product)
```

**GET `/health`**
Health check del backend

---

## State Management (Provider)

### BarcodeScannerProvider
Gestisce:
- Prodotto attuale
- Loading state
- Errori
- Storico scansioni

```dart
final provider = context.read<BarcodeScannerProvider>();
await provider.scanBarcode('8718206...');
print(provider.currentProduct?.finalScore);
```

### UserPreferencesProvider
Gestisce:
- Premium status
- User allergies
- Language preference

### AppStateProvider
Gestisce:
- Connectivity state
- App initialization

---

## Design System

### Colori Risk Score
- **0-24**: Critical (Rosso `#D32F2F`)
- **25-39**: Poor (Arancio `#F57C00`)
- **40-59**: Moderate (Giallo `#FBC02D`)
- **60-79**: Low (Verde chiaro `#7CB342`)
- **80-100**: Excellent (Verde scuro `#388E3C`)

### Typography
- **Poppins** font famiglia principale
- Headline 1-3 per titoli
- Body Large/Medium/Small per testo
- Label per tag/badge

### Components
- `ScoreCard`: Visualizza score con colori
- `RiskTag`: Ingrediente a rischio
- `AllergenBadge`: Allergene rilevato
- `InfoSection`: Box informativo

---

## Permissions Required

### Android (AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### iOS (Info.plist)
```xml
<key>NSCameraUsageDescription</key>
<string>L'app ha bisogno di accesso alla camera per scansionare i codici a barre</string>
<key>NSLocalNetworkUsageDescription</key>
<string>L'app ha bisogno di accesso alla rete per contattare il server</string>
```

---

## Testing

### Unit Tests
```bash
flutter test
```

### Integration Tests
```bash
flutter test integration_test/
```

### Build APK (Android)
```bash
flutter build apk --release
```

### Build IPA (iOS)
```bash
flutter build ios --release
```

---

## Next Steps

1. **Implementare mobile_scanner** per camera reale
2. **Aggiungere OCR** per photo upload (google_mlkit_text_recognition)
3. **Implementare local caching** con Hive
4. **Aggiungere autenticazione** Firebase Auth
5. **Push notifications** per alert allergeni
6. **Analytics** Firebase Analytics

---

## Troubleshooting

### App non raggiunge backend
- Verifica che backend Python è in esecuzione
- Su Android emulator: usa `http://10.0.2.2:8000`
- Su device fisico: usa IP locale `http://192.168.x.x:8000`
- Disabilita SSL pinning in dev

### Camera permission denied
- Androi: Settings → App Permissions → Camera
- iOS: Settings → WYE → Camera

### Dipendenze non trovate
```bash
flutter clean
flutter pub get
flutter pub upgrade
```

---

## Resources

- [Flutter Docs](https://flutter.dev/docs)
- [Go Router](https://pub.dev/packages/go_router)
- [Provider State Management](https://pub.dev/packages/provider)
- [Mobile Scanner](https://pub.dev/packages/mobile_scanner)
- [Material Design 3](https://m3.material.io/)
