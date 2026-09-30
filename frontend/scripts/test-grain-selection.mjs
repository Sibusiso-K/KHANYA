import test from 'node:test';
import assert from 'node:assert/strict';
import {pixelForClick, grainIdAt} from '../src/grainSelection.js';

test('maps a click to source pixels and decodes the known 24-bit grain id', () => {
  const {x,y}=pixelForClick(150, 75, {left:50,top:25,width:200,height:100}, 512, 512);
  assert.deepEqual({x,y},{x:256,y:256});
  assert.equal(grainIdAt([0,0,0,255,7,3,0,255],1),775);
});
