export function pixelForClick(clientX: number, clientY: number, rect: {left:number;top:number;width:number;height:number}, width: number, height: number): {x:number;y:number};
export function fittedImageRect(rect: {left:number;top:number;width:number;height:number}, imageWidth: number, imageHeight: number, fit?: string): {left:number;top:number;width:number;height:number};
export function grainIdAt(rgba: ArrayLike<number>, pixelIndex: number): number;
export function grainLiberationState(payloadFraction: number): 'NO VALUABLE MINERALS' | 'LOCKED' | 'FREE';
export function formatPayloadPercent(payloadFraction: number): string;
export function liberationExplanation(payloadFraction: number): string;
