import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/capture_upload_error.dart';
import 'package:wye/models/capture_upload_models.dart';
import 'package:wye/services/image_metadata_service.dart';

void main() {
  group('Sha256DigestService', () {
    const service = Sha256DigestService();

    test('hashes empty bytes with the standard SHA-256 vector', () {
      expect(
        service.hash(Uint8List(0)),
        'e3b0c44298fc1c149afbf4c8996fb924'
        '27ae41e4649b934ca495991b7852b855',
      );
    });

    test('hashes a small byte sequence deterministically in lowercase', () {
      final bytes = Uint8List.fromList(utf8.encode('abc'));

      expect(
        service.hash(bytes),
        'ba7816bf8f01cfea414140de5dae2223'
        'b00361a396177a9cb410ff61f20015ad',
      );
      expect(service.hash(bytes), matches(RegExp(r'^[0-9a-f]{64}$')));
    });
  });

  group('Sha256ImageMetadataService', () {
    const service = Sha256ImageMetadataService();

    test('derives JPEG metadata from the exact bytes', () async {
      final bytes = Uint8List.fromList([0xff, 0xd8, 0xff, 0x01, 0x02]);
      final metadata = await service.inspect(bytes);

      expect(metadata.mimeType, 'image/jpeg');
      expect(metadata.byteSize, bytes.length);
      expect(
        metadata.sha256,
        const Sha256DigestService().hash(bytes),
      );
    });

    test('recognizes PNG and WebP content signatures', () async {
      final png = Uint8List.fromList(
        [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x01],
      );
      final webp = Uint8List.fromList(
        [
          0x52,
          0x49,
          0x46,
          0x46,
          0x01,
          0x00,
          0x00,
          0x00,
          0x57,
          0x45,
          0x42,
          0x50,
        ],
      );

      expect((await service.inspect(png)).mimeType, 'image/png');
      expect((await service.inspect(webp)).mimeType, 'image/webp');
    });

    test('rejects empty upload input although the digest layer supports it',
        () async {
      await expectLater(
        service.inspect(Uint8List(0)),
        throwsA(
          isA<CaptureUploadException>()
              .having((error) => error.code, 'code', 'empty_image_bytes')
              .having(
                (error) => error.lastStableStep,
                'lastStableStep',
                UploadFlowStep.imageSelected,
              ),
        ),
      );
    });

    test('rejects bytes without a supported image signature', () async {
      await expectLater(
        service.inspect(Uint8List.fromList([1, 2, 3, 4])),
        throwsA(
          isA<CaptureUploadException>().having(
            (error) => error.code,
            'code',
            'unsupported_image_format',
          ),
        ),
      );
    });
  });
}
