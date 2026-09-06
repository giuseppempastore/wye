import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:wye/services/photo_capture_recovery_service.dart';
import 'package:wye/services/photo_field_mapper.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('lost Android camera result retains its explicit photo purpose',
      () async {
    final marker = PhotoCaptureRecoveryService(
      retrieveLostData: () async => LostDataResponse.empty(),
    );
    await marker.begin(ProductPhotoPurpose.ingredients);

    final recovery = PhotoCaptureRecoveryService(
      retrieveLostData: () async => LostDataResponse(
        file: XFile('temporary-camera-result.jpg'),
      ),
    );
    await recovery.initialize();

    expect(recovery.hasRecoveredPhoto, isTrue);
    final recovered = recovery.takeRecovered();
    expect(recovery.hasRecoveredPhoto, isFalse);
    expect(recovered, isNotNull);
    expect(recovered!.purpose, ProductPhotoPurpose.ingredients);
    expect(recovered.file.path, 'temporary-camera-result.jpg');
    expect(recovery.safeRecoveryCode, 'photo_capture_recovered');
    expect(recovery.takeRecovered(), isNull);
    await recovery.clearPending();
  });

  test('empty recovery does not invent a photo or purpose', () async {
    final recovery = PhotoCaptureRecoveryService(
      retrieveLostData: () async => LostDataResponse.empty(),
    );

    await recovery.initialize();

    expect(recovery.takeRecovered(), isNull);
    expect(recovery.safeRecoveryCode, isNull);
  });
}
