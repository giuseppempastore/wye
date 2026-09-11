package com.example.wye

import android.content.Context
import android.hardware.camera2.CameraManager
import android.graphics.BitmapFactory
import kotlin.math.sqrt
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val capabilitiesChannel = "wye/device_capabilities"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            capabilitiesChannel,
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "hasCamera" -> {
                    val cameraManager =
                        getSystemService(Context.CAMERA_SERVICE) as CameraManager
                    val hasCamera = try {
                        cameraManager.cameraIdList.isNotEmpty()
                    } catch (_: Exception) {
                        false
                    }
                    result.success(hasCamera)
                }
                "assessPhoto" -> {
                    val path = call.argument<String>("path")
                    if (path.isNullOrBlank()) {
                        result.error("invalid_path", "Photo path is required", null)
                    } else {
                        result.success(assessPhoto(path))
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun assessPhoto(path: String): Map<String, Any> {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(path, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
            return mapOf("ok" to false, "issues" to listOf("unreadable"))
        }
        val issues = mutableListOf<String>()
        if (bounds.outWidth < 900 || bounds.outHeight < 600) issues.add("low_resolution")

        var sampleSize = 1
        while (bounds.outWidth / sampleSize > 256 || bounds.outHeight / sampleSize > 256) {
            sampleSize *= 2
        }
        val bitmap = BitmapFactory.decodeFile(
            path,
            BitmapFactory.Options().apply { inSampleSize = sampleSize },
        ) ?: return mapOf("ok" to false, "issues" to listOf("unreadable"))

        var sum = 0.0
        var sumSquares = 0.0
        var edgeSum = 0.0
        var count = 0
        var edgeCount = 0
        for (y in 0 until bitmap.height step 2) {
            var previous = -1.0
            for (x in 0 until bitmap.width step 2) {
                val pixel = bitmap.getPixel(x, y)
                val luminance = 0.2126 * ((pixel shr 16) and 0xff) +
                    0.7152 * ((pixel shr 8) and 0xff) +
                    0.0722 * (pixel and 0xff)
                sum += luminance
                sumSquares += luminance * luminance
                count++
                if (previous >= 0) {
                    edgeSum += kotlin.math.abs(luminance - previous)
                    edgeCount++
                }
                previous = luminance
            }
        }
        bitmap.recycle()
        val average = if (count == 0) 0.0 else sum / count
        val variance = if (count == 0) 0.0 else (sumSquares / count) - average * average
        val contrast = sqrt(variance.coerceAtLeast(0.0))
        val edge = if (edgeCount == 0) 0.0 else edgeSum / edgeCount
        if (average < 38.0) issues.add("too_dark")
        if (contrast < 20.0 || edge < 7.0) issues.add("possibly_blurred")
        return mapOf(
            "ok" to issues.isEmpty(),
            "issues" to issues,
            "width" to bounds.outWidth,
            "height" to bounds.outHeight,
        )
    }
}
