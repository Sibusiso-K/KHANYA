import test from 'node:test';
import assert from 'node:assert/strict';
import {sourcePixel,grainId} from '../src/grainPixels.mjs';
test('packed RGB IDs retain all 24 bits without colour interpretation',()=>{
 for(const id of [0,1,255,256,65535,65536,16777215]){
  const pixel=new Uint8ClampedArray([id&255,(id>>8)&255,(id>>16)&255,255]);
  assert.equal(grainId(pixel,0),id);
 }
});
test('pointer maps resized source pixels without leaking outside image',()=>{
 const rect={left:10,top:20,width:200,height:100};
 assert.deepEqual(sourcePixel(10,20,rect,1000,500),[0,0]);
 assert.deepEqual(sourcePixel(110,70,rect,1000,500),[500,250]);
 assert.deepEqual(sourcePixel(209.99,119.99,rect,1000,500),[999,499]);
 assert.equal(sourcePixel(210,70,rect,1000,500),null);
 assert.equal(sourcePixel(9,70,rect,1000,500),null);
 assert.equal(sourcePixel(50,70,{...rect,width:0},1000,500),null);
});
