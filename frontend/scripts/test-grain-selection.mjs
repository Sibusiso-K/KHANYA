import test from 'node:test';
import assert from 'node:assert/strict';
import {pixelForClick, fittedImageRect, grainIdAt, grainLiberationState, formatPayloadPercent, liberationExplanation} from '../src/grainSelection.js';

test('maps a click to source pixels and decodes the known 24-bit grain id', () => {
  const {x,y}=pixelForClick(150, 75, {left:50,top:25,width:200,height:100}, 512, 512);
  assert.deepEqual({x,y},{x:256,y:256});
  assert.equal(grainIdAt([0,0,0,255,7,3,0,255],1),775);
});

test('maps clicks through object-fit contain letterboxing to the displayed source pixels', () => {
  const rect=fittedImageRect({left:10,top:20,width:349,height:340},1540,1026);
  assert.equal(rect.left,10);
  assert.ok(Math.abs(rect.top-73.7422)<.001);
  assert.equal(rect.width,349);
  assert.ok(Math.abs(rect.height-232.5156)<.001);
});

test('distinguishes absent payload, locked and free grains at the advisor threshold', () => {
  assert.equal(grainLiberationState(0), 'NO VALUABLE MINERALS');
  assert.equal(grainLiberationState(0.0004), 'LOCKED');
  assert.equal(formatPayloadPercent(0.0004), '0.04');
  assert.equal(grainLiberationState(0.49), 'LOCKED');
  assert.equal(grainLiberationState(0.5), 'FREE');
  assert.match(liberationExplanation(0), /No valuable mineral is present/);
  assert.match(liberationExplanation(0.0004), /below the 50%/);
  assert.match(liberationExplanation(0.5), /At least 50%/);
});
