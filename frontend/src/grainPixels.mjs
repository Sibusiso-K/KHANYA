/** Map a pointer on an unstretched canvas to its lossless source pixel. */
export function sourcePixel(x,y,rect,width,height){
 if(rect.width<=0||rect.height<=0||x<rect.left||y<rect.top||x>=rect.left+rect.width||y>=rect.top+rect.height)return null;
 return [Math.min(width-1,Math.floor((x-rect.left)*width/rect.width)),Math.min(height-1,Math.floor((y-rect.top)*height/rect.height))];
}
export function grainId(data,offset){return data[offset]+(data[offset+1]<<8)+(data[offset+2]<<16)}
