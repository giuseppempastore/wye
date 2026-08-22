# Environment Configuration - WYE Flutter App

## Development
```dart
// lib/services/api_client.dart - DEV

class ApiConfig {
  // Android Emulator
  static const String baseUrl = 'http://10.0.2.2:8000';
  
  // Per iOS Simulator:
  // static const String baseUrl = 'http://127.0.0.1:8000';
  
  // Per Device Fisico (sostituisci con il tuo IP):
  // static const String baseUrl = 'http://192.168.1.100:8000';
}
```

## Testing Offline (Usa MockApiClient)
```dart
// lib/main.dart

// INVECE DI:
// Provider<ApiClient>(create: (_) => ApiClient()),

// USA:
// Provider<ApiClient>(create: (_) => MockApiClient()),

import 'services/mock_api_client.dart';
```

## Production
```dart
// lib/services/api_client.dart - PROD

class ApiConfig {
  static const String baseUrl = 'https://api.wyeapp.com';
}
```

## Variabili Ambiente Consigliate

Crea un file `.env` (non committare):
```
# .env (non committare a git)
API_BASE_URL=http://10.0.2.2:8000
API_TIMEOUT=30
ENABLE_LOGGING=true
USE_MOCK_API=false
```

Poi carica con `flutter_dotenv`:
```dart
import 'package:flutter_dotenv/flutter_dotenv.dart';

void main() async {
  await dotenv.load();
  runApp(const MyApp());
}

class ApiConfig {
  static String get baseUrl => dotenv.env['API_BASE_URL'] ?? 'http://10.0.2.2:8000';
}
```
