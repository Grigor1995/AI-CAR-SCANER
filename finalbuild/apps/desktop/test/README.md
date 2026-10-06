# Desktop test notes

The Flutter SDK is not installed in the build environment used to assemble this artifact, so native Dart/Flutter tests cannot be executed here.

Once Flutter is installed:

```text
flutter pub get
flutter analyze
flutter test
```

For a live desktop smoke test, run the FastAPI backend and then:

```text
flutter run -d windows
```
