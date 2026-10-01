import {createContext,useContext,useLayoutEffect,useState,useId,type ReactNode} from 'react';

export type ThemeName='workbench'|'mineral-night'|'field-paper';
export const THEMES:{id:ThemeName;name:string;description:string;swatches:string[]}[]=[
 {id:'workbench',name:'White workbench',description:'The approved white research workspace; blue actions and copper navigation.',swatches:['#f1f4f6','#ffffff','#22578d','#c27543']},
 {id:'mineral-night',name:'Mineral night',description:'Deep slate surfaces with clear instrument text for low-light inspection.',swatches:['#0b151d','#14232e','#9cc9ff','#dfb480']},
 {id:'field-paper',name:'Field paper',description:'Warm paper, forest actions and serif section headings for reading observations.',swatches:['#ede7da','#fbf8f0','#2c6457','#926b45']},
];
type ThemeContextValue={theme:ThemeName;changeTheme:(value:ThemeName)=>void;notice:string};
const ThemeContext=createContext<ThemeContextValue|null>(null);
function storedTheme(key:string):ThemeName{try{const value=localStorage.getItem(key);return THEMES.some(item=>item.id===value)?value as ThemeName:'workbench'}catch{return 'workbench'}}
export function ThemeProvider({storageKey,children}:{storageKey:string;children:ReactNode}){
 const [theme,setTheme]=useState<ThemeName>(()=>storedTheme(storageKey)),[notice,setNotice]=useState('');
 useLayoutEffect(()=>{document.documentElement.dataset.reefTheme=theme;document.documentElement.style.colorScheme=theme==='mineral-night'?'dark':'light'},[theme]);
 function changeTheme(value:ThemeName){if(!THEMES.some(item=>item.id===value))return;setTheme(value);try{localStorage.setItem(storageKey,value);setNotice('Appearance saved on this browser for this account.')}catch{setNotice('Appearance applied for this session. Browser storage is unavailable.')}}
 return <ThemeContext.Provider value={{theme,changeTheme,notice}}>{children}</ThemeContext.Provider>;
}
export function useTheme(){const context=useContext(ThemeContext);if(!context)throw Error('Theme controls require a workspace appearance provider.');return context}
export function ThemePicker({compact=false}:{compact?:boolean}){
 const {theme,changeTheme,notice}=useTheme(),id=useId();
 return <fieldset className={'theme-picker'+(compact?' compact':'')}><legend>Workspace appearance</legend><div className="theme-choices">{THEMES.map(item=><label className={'theme-choice'+(theme===item.id?' selected':'')} key={item.id}><input type="radio" name={id} value={item.id} checked={theme===item.id} onChange={()=>changeTheme(item.id)}/><span className="theme-choice-copy"><strong>{item.name}</strong>{!compact&&<small>{item.description}</small>}</span><span className="theme-swatches" aria-hidden="true">{item.swatches.map(color=><i key={color} style={{background:color}}/>)}</span></label>)}</div>{notice&&<p className="theme-notice" role="status">{notice}</p>}</fieldset>;
}
