import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';

class ProductImage extends StatelessWidget {
  final String? imageUrl;
  final double? width;
  final double? height;
  final BorderRadius borderRadius;

  const ProductImage({
    super.key,
    required this.imageUrl,
    this.width,
    this.height,
    this.borderRadius = const BorderRadius.all(Radius.circular(12)),
  });

  @override
  Widget build(BuildContext context) {
    final value = imageUrl?.trim();
    Widget image;
    if (value == null || value.isEmpty) {
      image = _placeholder(context);
    } else if (value.startsWith('data:image')) {
      image = _memoryImage(context, value);
    } else {
      final uri = Uri.tryParse(value);
      image = uri != null &&
              uri.hasScheme &&
              (uri.scheme == 'http' || uri.scheme == 'https')
          ? Image.network(
              value,
              width: width,
              height: height,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => _placeholder(context),
              loadingBuilder: (context, child, progress) => progress == null
                  ? child
                  : _placeholder(context, loading: true),
            )
          : _placeholder(context);
    }

    return ClipRRect(
      borderRadius: borderRadius,
      child: SizedBox(width: width, height: height, child: image),
    );
  }

  Widget _memoryImage(BuildContext context, String value) {
    try {
      final separator = value.indexOf(',');
      if (separator < 0) return _placeholder(context);
      final Uint8List bytes = base64Decode(value.substring(separator + 1));
      return Image.memory(
        bytes,
        width: width,
        height: height,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => _placeholder(context),
      );
    } on FormatException {
      return _placeholder(context);
    }
  }

  Widget _placeholder(BuildContext context, {bool loading = false}) {
    final color = Theme.of(context).colorScheme.outline;
    return ColoredBox(
      color: color.withOpacity(0.1),
      child: Center(
        child: loading
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Icon(Icons.image_not_supported_outlined, color: color),
      ),
    );
  }
}
