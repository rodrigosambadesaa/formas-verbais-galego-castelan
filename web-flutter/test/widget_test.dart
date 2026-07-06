import 'package:flutter_test/flutter_test.dart';
import 'package:formas_verbais_flutter/main.dart';

void main() {
  test('parseVerbPairs ignores malformed rows and removes duplicates', () {
    final pairs = parseVerbPairs(
      'amar\tamar\tV\n'
      'amar\tamar\tV\n'
      'comer\tcomer\tV\n'
      'malformed\n'
      '\tandar\tV\n',
    );

    expect(pairs.length, 2);
    expect(pairs.first.es, 'amar');
    expect(pairs.first.gl, 'amar');
    expect(pairs.last.es, 'comer');
    expect(pairs.last.gl, 'comer');
  });
}
