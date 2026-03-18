# Add project specific ProGuard rules here.
-keepattributes SourceFile,LineNumberTable
-keepattributes *Annotation*
-keepclassmembers class * {
    @dagger.* *;
}
