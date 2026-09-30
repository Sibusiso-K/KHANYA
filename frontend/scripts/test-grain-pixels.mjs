import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeGrainId} from '../src/grainPixels.js';

test('decodes packed 24-bit grain IDs from lossless RGB pixels', () => {
  assert.equal(decodeGrainId([1, 2, 3, 255]), 197121);
  assert.equal(decodeGrainId([0, 0, 0, 255, 255, 255, 255, 0], 1), 16777215);
});
