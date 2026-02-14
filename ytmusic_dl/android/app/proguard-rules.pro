# Flutter specific rules
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

# MediaKit
-keep class com.media_kit.** { *; }

# Audio Service
-keep class com.ryanheise.audioservice.** { *; }

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}
