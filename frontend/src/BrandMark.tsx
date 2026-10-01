export default function BrandMark({className='',size=48}:{className?:string;size?:number}){
 return <svg className={'reef-brand-mark '+className} width={size} height={size+3} viewBox="0 0 40 42" aria-hidden="true"><path className="reef-brand-upper" d="m3 13 17-10 17 10-17 9z" fill="currentColor"/><path className="reef-brand-lower" d="M3 22l17 9 17-9v8L20 40 3 30z" fill="currentColor"/></svg>;
}
