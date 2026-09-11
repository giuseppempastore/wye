import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/product_acquisition_draft.dart';
import 'package:wye/services/database_service.dart';

void main() {
  test('persisted draft survives database close and reopen', () async {
    final root = await Directory.systemTemp.createTemp('wye_draft_test_');
    addTearDown(() async {
      if (await root.exists()) await root.delete(recursive: true);
    });
    final draft = ProductAcquisitionDraft(
      id: 'draft_persistence_1',
      currentStep: 2,
      barcode: '4006381333931',
      barcodeLookupCompleted: true,
      ingredients: 'water',
      labelExtractions: const {
        'ingredients': {'raw_text': 'Ingredients: water'}
      },
      updatedAt: DateTime.now().toUtc(),
    );

    final first = DatabaseService(hivePath: root.path);
    await first.init();
    await first.saveAcquisitionDraft(draft);
    await first.close();

    final second = DatabaseService(hivePath: root.path);
    await second.init();
    final restored = second.getActiveAcquisitionDraft();
    expect(restored?.id, draft.id);
    expect(restored?.currentStep, 2);
    expect(restored?.barcode, draft.barcode);
    expect(restored?.labelExtractions['ingredients']?['raw_text'], isNotEmpty);
    await second.close();
  });

  test('deleting one draft cleans only its retained media', () async {
    final root = await Directory.systemTemp.createTemp('wye_draft_media_test_');
    addTearDown(() async {
      if (await root.exists()) await root.delete(recursive: true);
    });
    final sourceOne = File('${root.path}${Platform.pathSeparator}one.jpg');
    final sourceTwo = File('${root.path}${Platform.pathSeparator}two.jpg');
    await sourceOne.writeAsBytes([1, 2, 3]);
    await sourceTwo.writeAsBytes([4, 5, 6]);
    final database = DatabaseService(hivePath: root.path);
    await database.init();
    final retainedOne = await database.retainDraftImage(
      draftId: 'draft_delete_1',
      documentType: 'product_front',
      sourcePath: sourceOne.path,
    );
    final retainedTwo = await database.retainDraftImage(
      draftId: 'draft_delete_2',
      documentType: 'product_front',
      sourcePath: sourceTwo.path,
    );
    await database.saveAcquisitionDraft(ProductAcquisitionDraft(
      id: 'draft_delete_1',
      localImagePaths: {'product_front': retainedOne},
      updatedAt: DateTime.now().toUtc(),
    ));
    await database.saveAcquisitionDraft(ProductAcquisitionDraft(
      id: 'draft_delete_2',
      localImagePaths: {'product_front': retainedTwo},
      updatedAt: DateTime.now().toUtc(),
    ));

    await database.deleteAcquisitionDraft('draft_delete_1');
    expect(File(retainedOne).existsSync(), isFalse);
    expect(File(retainedTwo).existsSync(), isTrue);
    expect(
      database.getAcquisitionDrafts().map((item) => item.id),
      contains('draft_delete_2'),
    );
    await database.close();
  });
}
