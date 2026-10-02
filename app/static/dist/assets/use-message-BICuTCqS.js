import{d as v,aA as B,a as p,a2 as S,a4 as m,a0 as b,a6 as z,o,c as i,z as d,F as f,D as r,b as h,aG as D,A as M,M as R,ct as $,aI as H,ac as N,g as u,am as y,aj as j,K as A,cu as T}from"./index-DE04bkTa.js";var Z=v({name:"Empty",render(){return(()=>{const e=B("15c1a247ae156450");return e[0]||(e[0]=p("svg",{viewBox:"0 0 28 28",fill:"none",xmlns:"http://www.w3.org/2000/svg"},[p("path",{d:"M26 7.5C26 11.0899 23.0899 14 19.5 14C15.9101 14 13 11.0899 13 7.5C13 3.91015 15.9101 1 19.5 1C23.0899 1 26 3.91015 26 7.5ZM16.8536 4.14645C16.6583 3.95118 16.3417 3.95118 16.1464 4.14645C15.9512 4.34171 15.9512 4.65829 16.1464 4.85355L18.7929 7.5L16.1464 10.1464C15.9512 10.3417 15.9512 10.6583 16.1464 10.8536C16.3417 11.0488 16.6583 11.0488 16.8536 10.8536L19.5 8.20711L22.1464 10.8536C22.3417 11.0488 22.6583 11.0488 22.8536 10.8536C23.0488 10.6583 23.0488 10.3417 22.8536 10.1464L20.2071 7.5L22.8536 4.85355C23.0488 4.65829 23.0488 4.34171 22.8536 4.14645C22.6583 3.95118 22.3417 3.95118 22.1464 4.14645L19.5 6.79289L16.8536 4.14645Z",fill:"currentColor"}),p("path",{d:"M25 22.75V12.5991C24.5572 13.0765 24.053 13.4961 23.5 13.8454V16H17.5L17.3982 16.0068C17.0322 16.0565 16.75 16.3703 16.75 16.75C16.75 18.2688 15.5188 19.5 14 19.5C12.4812 19.5 11.25 18.2688 11.25 16.75L11.2432 16.6482C11.1935 16.2822 10.8797 16 10.5 16H4.5V7.25C4.5 6.2835 5.2835 5.5 6.25 5.5H12.2696C12.4146 4.97463 12.6153 4.47237 12.865 4H6.25C4.45507 4 3 5.45507 3 7.25V22.75C3 24.5449 4.45507 26 6.25 26H21.75C23.5449 26 25 24.5449 25 22.75ZM4.5 22.75V17.5H9.81597L9.85751 17.7041C10.2905 19.5919 11.9808 21 14 21L14.215 20.9947C16.2095 20.8953 17.842 19.4209 18.184 17.5H23.5V22.75C23.5 23.7165 22.7165 24.5 21.75 24.5H6.25C5.2835 24.5 4.5 23.7165 4.5 22.75Z",fill:"currentColor"})],-1))})()}}),F=S("empty",`
 display: flex;
 flex-direction: column;
 align-items: center;
 font-size: var(--n-font-size);
`,[m("icon",`
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 line-height: var(--n-icon-size);
 color: var(--n-icon-color);
 transition:
 color .3s var(--n-bezier);
 `,[b("+",[m("description",`
 margin-top: 8px;
 `)])]),m("description",`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),m("extra",`
 text-align: center;
 transition: color .3s var(--n-bezier);
 margin-top: 12px;
 color: var(--n-extra-text-color);
 `)]);const K={...z.props,description:String,showDescription:{type:Boolean,default:!0},showIcon:{type:Boolean,default:!0},size:{type:String,default:"medium"},renderIcon:Function};var O=v({name:"Empty",props:K,slots:Object,setup(e){const{mergedClsPrefixRef:n,inlineThemeDisabled:a,mergedComponentPropsRef:c}=R(e),x=z("Empty","-empty",F,$,e,n),{localeRef:g}=H("Empty"),w=u(()=>{var t,s;return e.description??((s=(t=c==null?void 0:c.value)==null?void 0:t.Empty)==null?void 0:s.description)}),L=u(()=>{var t,s;return((s=(t=c==null?void 0:c.value)==null?void 0:t.Empty)==null?void 0:s.renderIcon)||(()=>(o(),h(Z)))}),C=u(()=>{const{size:t}=e,{common:{cubicBezierEaseInOut:s},self:{[y("iconSize",t)]:E,[y("fontSize",t)]:I,textColor:V,iconColor:_,extraTextColor:k}}=x.value;return{"--n-icon-size":E,"--n-font-size":I,"--n-bezier":s,"--n-text-color":V,"--n-icon-color":_,"--n-extra-text-color":k}}),l=a?N("empty",u(()=>{let t="";const{size:s}=e;return t+=s[0],t}),C,e):void 0;return{mergedClsPrefix:n,mergedRenderIcon:L,localizedDescription:u(()=>w.value||g.value.description),cssVars:a?void 0:C,themeClass:l==null?void 0:l.themeClass,onRender:l==null?void 0:l.onRender}},render(){const{$slots:e,mergedClsPrefix:n,onRender:a}=this;return a==null||a(),o(),i("div",{class:d([`${n}-empty`,this.themeClass]),style:M(this.cssVars)},[this.showIcon?(o(),i("div",{key:0,class:d(`${n}-empty__icon`)},[e.icon?(o(),i(f,{key:0},[r(()=>e.icon())],64)):(o(),h(D,{key:1,clsPrefix:n},{default:this.mergedRenderIcon},1032,["clsPrefix"]))],2)):r(()=>null),this.showDescription?(o(),i("div",{key:2,class:d(`${n}-empty__description`)},[e.default?(o(),i(f,{key:0},[r(()=>e.default())],64)):(o(),i(f,{key:1},[r(()=>this.localizedDescription)],64))],2)):r(()=>null),e.extra?(o(),i("div",{key:4,class:d(`${n}-empty__extra`)},[r(()=>e.extra())],2)):r(()=>null)],6)}});function q(){const e=A(T,null);return e===null&&j("use-message","No outer <n-message-provider /> founded. See prerequisite in https://www.naiveui.com/en-US/os-theme/components/message for more details. If you want to use `useMessage` outside setup, please check https://www.naiveui.com/zh-CN/os-theme/components/message#Q-&-A."),e}export{O as E,q as u};
