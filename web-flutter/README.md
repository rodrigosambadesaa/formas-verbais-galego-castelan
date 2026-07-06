# Interface Flutter

Interface alternativa en Flutter Web para explorar os pares de infinitivos castelán-galego do corpus.

## Execución local

```bash
flutter pub get
flutter run -d chrome
```

## Probas

```bash
flutter test
```

## Docker

```bash
docker build -t formas-verbais-flutter ./web-flutter
docker run --rm -p 8081:80 formas-verbais-flutter
```

Logo abre `http://localhost:8081`.
