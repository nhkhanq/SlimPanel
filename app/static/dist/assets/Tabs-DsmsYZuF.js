import{c3 as At,c4 as ve,c5 as Et,d as oe,j as It,bj as Ot,bk as jt,r as I,bn as Oe,aB as Ht,C as Z,a as Ft,b as s,e as v,n as h,f as Q,Z as S,g as Ge,aq as Mt,m as he,H as M,k as A,bp as Dt,ap as Nt,c as ne,bI as Vt,aG as qe,U as r,T as y,W as l,X as k,aF as Ut,P as Xt,b_ as Gt,Y as Ye,t as we,bd as je,V as Se,u as qt,a7 as Yt,c6 as Kt,aj as Zt,$ as ie,q as Jt,c7 as Qt,a8 as ea,a0 as ta,bQ as He,a1 as aa,a4 as Fe,aZ as se,b8 as G,bu as ue,v as ra,c8 as na,x as oa,z as ia,A as q,am as pe}from"./index-If5Ucjf1.js";import{A as sa}from"./Add-B5LFbj5N.js";var la=/\s/;function da(e){for(var n=e.length;n--&&la.test(e.charAt(n)););return n}var ca=/^\s+/;function ba(e){return e&&e.slice(0,da(e)+1).replace(ca,"")}var Me=NaN,fa=/^[-+]0x[0-9a-f]+$/i,ua=/^0b[01]+$/i,pa=/^0o[0-7]+$/i,va=parseInt;function De(e){if(typeof e=="number")return e;if(At(e))return Me;if(ve(e)){var n=typeof e.valueOf=="function"?e.valueOf():e;e=ve(n)?n+"":n}if(typeof e!="string")return e===0?e:+e;e=ba(e);var i=ua.test(e);return i||pa.test(e)?va(e.slice(2),i?2:8):fa.test(e)?Me:+e}var Te=function(){return Et.Date.now()},ha="Expected a function",ga=Math.max,ma=Math.min;function xa(e,n,i){var u,c,T,f,b,g,m=0,O=!1,P=!1,E=!0;if(typeof e!="function")throw new TypeError(ha);n=De(n)||0,ve(i)&&(O=!!i.leading,P="maxWait"in i,T=P?ga(De(i.maxWait)||0,n):T,E="trailing"in i?!!i.trailing:E);function j(p){var $=u,V=c;return u=c=void 0,m=p,f=e.apply(V,$),f}function B(p){return m=p,b=setTimeout(L,n),O?j(p):f}function z(p){var $=p-g,V=p-m,H=n-$;return P?ma(H,T-V):H}function D(p){var $=p-g,V=p-m;return g===void 0||$>=n||$<0||P&&V>=T}function L(){var p=Te();if(D(p))return Y(p);b=setTimeout(L,z(p))}function Y(p){return b=void 0,E&&u?j(p):(u=c=void 0,f)}function J(){b!==void 0&&clearTimeout(b),m=0,u=g=c=b=void 0}function X(){return b===void 0?f:Y(Te())}function N(){var p=Te(),$=D(p);if(u=arguments,c=this,g=p,$){if(b===void 0)return B(g);if(P)return clearTimeout(b),b=setTimeout(L,n),j(g)}return b===void 0&&(b=setTimeout(L,n)),f}return N.cancel=J,N.flush=X,N}var ya="Expected a function";function Ca(e,n,i){var u=!0,c=!0;if(typeof e!="function")throw new TypeError(ya);return ve(i)&&(u="leading"in i?!!i.leading:u,c="trailing"in i?!!i.trailing:c),xa(e,n,{leading:u,maxWait:n,trailing:c})}const wa=Oe(".v-x-scroll",{overflow:"auto",scrollbarWidth:"none"},[Oe("&::-webkit-scrollbar",{width:0,height:0})]),Sa=oe({name:"XScroll",props:{disabled:Boolean,onScroll:Function},setup(){const e=I(null);function n(c){!(c.currentTarget.offsetWidth<c.currentTarget.scrollWidth)||c.deltaY===0||(c.currentTarget.scrollLeft+=c.deltaY+c.deltaX,c.preventDefault())}const i=Ot();return wa.mount({id:"vueuc/x-scroll",head:!0,anchorMetaName:jt,ssr:i}),Object.assign({selfRef:e,handleWheel:n},{scrollTo(...c){var T;(T=e.value)===null||T===void 0||T.scrollTo(...c)}})},render(){return It("div",{ref:"selfRef",onScroll:this.onScroll,onWheel:this.disabled?void 0:this.handleWheel,class:"v-x-scroll"},this.$slots)}});var Ta=oe({name:"ChevronLeft",render(){return(()=>{const e=Ht("dfe229c2639b2082");return e[0]||(e[0]=Z("svg",{viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg"},[Z("path",{d:"M10.3536 3.14645C10.5488 3.34171 10.5488 3.65829 10.3536 3.85355L6.20711 8L10.3536 12.1464C10.5488 12.3417 10.5488 12.6583 10.3536 12.8536C10.1583 13.0488 9.84171 13.0488 9.64645 12.8536L5.14645 8.35355C4.95118 8.15829 4.95118 7.84171 5.14645 7.64645L9.64645 3.14645C9.84171 2.95118 10.1583 2.95118 10.3536 3.14645Z",fill:"currentColor"})],-1))})()}});const ke=Ft("n-tabs"),Ke={tab:[String,Number,Object,Function],name:{type:[String,Number],required:!0},disabled:Boolean,displayDirective:{type:String,default:"if"},closable:{type:Boolean,default:void 0},tabProps:Object,label:[String,Number,Object,Function]};var La=oe({__TAB_PANE__:!0,name:"TabPane",alias:["TabPanel"],props:Ke,slots:Object,setup(e){const n=Ge(ke,null);return n||Mt("tab-pane","`n-tab-pane` must be placed inside `n-tabs`."),{style:n.paneStyleRef,class:n.paneClassRef,mergedClsPrefix:n.mergedClsPrefixRef}},render(){return s(),v("div",{class:S([`${this.mergedClsPrefix}-tab-pane`,this.class]),style:Q(this.style)},[h(()=>{var e,n;return(n=(e=this.$slots).default)==null?void 0:n.call(e)})],6)}});const Ra=["data-name","data-disabled"],za={internalLeftPadded:Boolean,internalAddable:Boolean,internalCreatedByPane:Boolean,...Vt(Ke,["displayDirective"])};var $e=oe({__TAB__:!0,inheritAttrs:!1,name:"Tab",props:za,setup(e){const{mergedClsPrefixRef:n,valueRef:i,typeRef:u,closableRef:c,tabStyleRef:T,addTabStyleRef:f,tabClassRef:b,addTabClassRef:g,tabChangeIdRef:m,onBeforeLeaveRef:O,triggerRef:P,handleAdd:E,activateTab:j,handleClose:B}=Ge(ke);return{trigger:P,mergedClosable:ne(()=>{if(e.internalAddable)return!1;const{closable:z}=e;return z===void 0?c.value:z}),style:T,addStyle:f,tabClass:b,addTabClass:g,clsPrefix:n,value:i,type:u,handleClose(z){z.stopPropagation(),!e.disabled&&B(e.name)},activateTab(){if(e.disabled)return;if(e.internalAddable){E();return}const{name:z}=e,D=++m.id;if(z!==i.value){const{value:L}=O;L?Promise.resolve(L(e.name,i.value)).then(Y=>{Y&&m.id===D&&j(z)}):j(z)}}}},render(){const{internalAddable:e,clsPrefix:n,name:i,disabled:u,label:c,tab:T,value:f,mergedClosable:b,trigger:g,$slots:{default:m}}=this,O=c??T;return s(),v("div",{class:S(`${n}-tabs-tab-wrapper`)},[this.internalLeftPadded?(s(),v("div",{key:0,class:S(`${n}-tabs-tab-pad`)},null,2)):h(()=>null),(s(),v("div",he({key:i,"data-name":i,"data-disabled":u?!0:void 0},he({class:[`${n}-tabs-tab`,f===i&&`${n}-tabs-tab--active`,u&&`${n}-tabs-tab--disabled`,b&&`${n}-tabs-tab--closable`,e&&`${n}-tabs-tab--addable`,e?this.addTabClass:this.tabClass],onClick:g==="click"?this.activateTab:void 0,onMouseenter:g==="hover"?this.activateTab:void 0,style:e?this.addStyle:this.style},this.internalCreatedByPane?this.tabProps||{}:this.$attrs)),[Z("span",{class:S(`${n}-tabs-tab__label`)},[e?(s(),v(M,{key:0},[Z("div",{class:S(`${n}-tabs-tab__height-placeholder`)}," ",2),(s(),A(qe,{clsPrefix:n},{default:()=>(s(),A(sa))},1032,["clsPrefix"]))],64)):(s(),v(M,{key:1},[m?(s(),v(M,{key:0},[h(()=>m())],64)):(s(),v(M,{key:1},[typeof O=="object"?(s(),v(M,{key:0},[h(()=>O)],64)):(s(),v(M,{key:1},[h(()=>Dt(O??i))],64))],64))],64))],2),b&&this.type==="card"?(s(),A(Nt,{key:0,clsPrefix:n,class:S(`${n}-tabs-tab__close`),onClick:this.handleClose,disabled:u},null,8,["clsPrefix","class","onClick","disabled"])):h(()=>null)],16,Ra))],2)}}),$a=r("tabs",`
 box-sizing: border-box;
 width: 100%;
 display: flex;
 flex-direction: column;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
`,[y("&.transition-disabled",[r("tabs-tab",`
 transition: none !important;
 `),r("tabs-nav-scroll-content",`
 transition: none !important;
 `),r("tabs-tab-pad",`
 transition: none !important;
 `)]),l("segment-type",[r("tabs-rail",[y("&.transition-disabled",[r("tabs-capsule",`
 transition: none;
 `)])])]),l("top",[r("tab-pane",`
 padding: var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left);
 `)]),l("left",[r("tab-pane",`
 padding: var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left) var(--n-pane-padding-top);
 `)]),l("left, right",`
 flex-direction: row;
 `,[r("tabs-bar",`
 width: 2px;
 right: 0;
 transition:
 top .2s var(--n-bezier),
 max-height .2s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `),r("tabs-tab",`
 padding: var(--n-tab-padding-vertical); 
 `)]),l("right",`
 flex-direction: row-reverse;
 `,[r("tab-pane",`
 padding: var(--n-pane-padding-left) var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom);
 `),r("tabs-bar",`
 left: 0;
 `)]),l("bottom",`
 flex-direction: column-reverse;
 justify-content: flex-end;
 `,[r("tab-pane",`
 padding: var(--n-pane-padding-bottom) var(--n-pane-padding-right) var(--n-pane-padding-top) var(--n-pane-padding-left);
 `),r("tabs-bar",`
 top: 0;
 `)]),r("tabs-rail",`
 position: relative;
 padding: 3px;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 background-color: var(--n-color-segment);
 transition: background-color .3s var(--n-bezier);
 display: flex;
 align-items: center;
 `,[r("tabs-capsule",`
 border-radius: var(--n-tab-border-radius);
 position: absolute;
 left: 0;
 top: 0;
 pointer-events: none;
 background-color: var(--n-tab-color-segment);
 box-shadow: 0 1px 3px 0 rgba(0, 0, 0, .08);
 transition: transform 0.3s var(--n-bezier);
 `),r("tabs-tab-wrapper",`
 flex-basis: 0;
 flex-grow: 1;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[r("tabs-tab",`
 overflow: hidden;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[l("active",`
 font-weight: var(--n-font-weight-strong);
 color: var(--n-tab-text-color-active);
 `),y("&:hover",`
 color: var(--n-tab-text-color-hover);
 `)])])]),l("flex",[r("tabs-nav",`
 width: 100%;
 position: relative;
 `,[r("tabs-wrapper",`
 width: 100%;
 `,[r("tabs-tab",`
 margin-right: 0;
 `)])])]),r("tabs-nav",`
 box-sizing: border-box;
 line-height: 1.5;
 display: flex;
 transition: border-color .3s var(--n-bezier);
 `,[k("prefix, suffix",`
 display: flex;
 align-items: center;
 `),k("prefix","padding-right: 16px;"),k("suffix","padding-left: 16px;")]),l("top, bottom",[y(">",[r("tabs-nav",[r("tabs-nav-scroll-wrapper",[y("&::before",`
 top: 0;
 bottom: 0;
 left: 0;
 width: 20px;
 `),y("&::after",`
 top: 0;
 bottom: 0;
 right: 0;
 width: 20px;
 `),l("shadow-start",[y("&::before",`
 box-shadow: inset 10px 0 8px -8px rgba(0, 0, 0, .12);
 `)]),l("shadow-end",[y("&::after",`
 box-shadow: inset -10px 0 8px -8px rgba(0, 0, 0, .12);
 `)])])])])]),l("left, right",[r("tabs-nav-scroll-content",`
 flex-direction: column;
 `),y(">",[r("tabs-nav",[r("tabs-nav-scroll-wrapper",[y("&::before",`
 top: 0;
 left: 0;
 right: 0;
 height: 20px;
 `),y("&::after",`
 bottom: 0;
 left: 0;
 right: 0;
 height: 20px;
 `),l("shadow-start",[y("&::before",`
 box-shadow: inset 0 10px 8px -8px rgba(0, 0, 0, .12);
 `)]),l("shadow-end",[y("&::after",`
 box-shadow: inset 0 -10px 8px -8px rgba(0, 0, 0, .12);
 `)])])])])]),r("tabs-nav-scroll-wrapper",`
 flex: 1;
 position: relative;
 overflow: hidden;
 `,[r("tabs-nav-y-scroll",`
 height: 100%;
 width: 100%;
 overflow-y: auto; 
 scrollbar-width: none;
 `,[y("&::-webkit-scrollbar, &::-webkit-scrollbar-track-piece, &::-webkit-scrollbar-thumb",`
 width: 0;
 height: 0;
 display: none;
 `)]),y("&::before, &::after",`
 transition: box-shadow .3s var(--n-bezier);
 pointer-events: none;
 content: "";
 position: absolute;
 z-index: 1;
 `),y("&.transition-disabled",[y("&::before, &::after",`
 transition: none;
 `)])]),r("tabs-nav-scroll-content",`
 display: flex;
 position: relative;
 min-width: 100%;
 min-height: 100%;
 width: fit-content;
 box-sizing: border-box;
 `),r("tabs-wrapper",`
 display: inline-flex;
 flex-wrap: nowrap;
 position: relative;
 `),r("tabs-tab-wrapper",`
 display: flex;
 flex-wrap: nowrap;
 flex-shrink: 0;
 flex-grow: 0;
 `),r("tabs-tab",`
 cursor: pointer;
 white-space: nowrap;
 flex-wrap: nowrap;
 display: inline-flex;
 align-items: center;
 color: var(--n-tab-text-color);
 font-size: var(--n-tab-font-size);
 background-clip: padding-box;
 padding: var(--n-tab-padding);
 transition:
 box-shadow .3s var(--n-bezier),
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[l("disabled",{cursor:"not-allowed"}),k("close",`
 margin-inline-start: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),k("label",`
 display: flex;
 align-items: center;
 z-index: 1;
 `)]),r("tabs-bar",`
 position: absolute;
 bottom: 0;
 height: 2px;
 border-radius: 1px;
 background-color: var(--n-bar-color);
 transition:
 left .2s var(--n-bezier),
 max-width .2s var(--n-bezier),
 opacity .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `,[y("&.transition-disabled",`
 transition: none;
 `),l("disabled",`
 background-color: var(--n-tab-text-color-disabled)
 `)]),r("tabs-pane-wrapper",`
 position: relative;
 overflow: hidden;
 transition: max-height .2s var(--n-bezier);
 `),r("tab-pane",`
 color: var(--n-pane-text-color);
 width: 100%;
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 opacity .2s var(--n-bezier);
 left: 0;
 right: 0;
 top: 0;
 `,[y("&.next-transition-leave-active, &.prev-transition-leave-active, &.next-transition-enter-active, &.prev-transition-enter-active",`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 transform .2s var(--n-bezier),
 opacity .2s var(--n-bezier);
 `),y("&.next-transition-leave-active, &.prev-transition-leave-active",`
 position: absolute;
 `),y("&.next-transition-enter-from, &.prev-transition-leave-to",`
 transform: translateX(32px);
 opacity: 0;
 `),y("&.next-transition-leave-to, &.prev-transition-enter-from",`
 transform: translateX(-32px);
 opacity: 0;
 `),y("&.next-transition-leave-from, &.next-transition-enter-to, &.prev-transition-leave-from, &.prev-transition-enter-to",`
 transform: translateX(0);
 opacity: 1;
 `)]),r("tabs-tab-pad",`
 box-sizing: border-box;
 width: var(--n-tab-gap);
 flex-grow: 0;
 flex-shrink: 0;
 `),l("line-type, bar-type",[r("tabs-tab",`
 font-weight: var(--n-tab-font-weight);
 box-sizing: border-box;
 vertical-align: bottom;
 `,[y("&:hover",{color:"var(--n-tab-text-color-hover)"}),l("active",`
 color: var(--n-tab-text-color-active);
 font-weight: var(--n-tab-font-weight-active);
 `),l("disabled",{color:"var(--n-tab-text-color-disabled)"})])]),r("tabs-nav",[k("prefix, suffix",`
 border-color: var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-color: var(--n-tab-border-color);
 `),l("line-type",[l("top",[k("prefix, suffix",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 bottom: -1px;
 `)]),l("left",[k("prefix, suffix",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 right: -1px;
 `)]),l("right",[k("prefix, suffix",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 left: -1px;
 `)]),l("bottom",[k("prefix, suffix",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 top: -1px;
 `)]),k("prefix, suffix",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-nav-scroll-content",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-bar",`
 border-radius: 0;
 `)]),l("card-type",[k("prefix, suffix",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-pad",`
 flex-grow: 1;
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-tab-pad",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-tab",`
 font-weight: var(--n-tab-font-weight);
 border: 1px solid var(--n-tab-border-color);
 background-color: var(--n-tab-color);
 box-sizing: border-box;
 position: relative;
 vertical-align: bottom;
 display: flex;
 justify-content: space-between;
 font-size: var(--n-tab-font-size);
 color: var(--n-tab-text-color);
 `,[l("addable",`
 padding-left: 8px;
 padding-right: 8px;
 font-size: 16px;
 justify-content: center;
 `,[k("height-placeholder",`
 width: 0;
 font-size: var(--n-tab-font-size);
 `),Ut("disabled",[y("&:hover",`
 color: var(--n-tab-text-color-hover);
 `)])]),l("closable","padding-inline-end: 8px;"),l("active",`
 background-color: #0000;
 font-weight: var(--n-tab-font-weight-active);
 color: var(--n-tab-text-color-active);
 `),l("disabled","color: var(--n-tab-text-color-disabled);")])]),l("left, right",`
 flex-direction: column; 
 `,[k("prefix, suffix",`
 padding: var(--n-tab-padding-vertical);
 `),r("tabs-wrapper",`
 flex-direction: column;
 `),r("tabs-tab-wrapper",`
 flex-direction: column;
 `,[r("tabs-tab-pad",`
 height: var(--n-tab-gap-vertical);
 width: 100%;
 `)])]),l("top",[l("card-type",[r("tabs-scroll-padding","border-bottom: 1px solid var(--n-tab-border-color);"),k("prefix, suffix",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-top-left-radius: var(--n-tab-border-radius);
 border-top-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-bottom: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `)])]),l("left",[l("card-type",[r("tabs-scroll-padding","border-right: 1px solid var(--n-tab-border-color);"),k("prefix, suffix",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-top-left-radius: var(--n-tab-border-radius);
 border-bottom-left-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-right: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-right: 1px solid var(--n-tab-border-color);
 `)])]),l("right",[l("card-type",[r("tabs-scroll-padding","border-left: 1px solid var(--n-tab-border-color);"),k("prefix, suffix",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-top-right-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-left: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-left: 1px solid var(--n-tab-border-color);
 `)])]),l("bottom",[l("card-type",[r("tabs-scroll-padding","border-top: 1px solid var(--n-tab-border-color);"),k("prefix, suffix",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-bottom-left-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-top: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-top: 1px solid var(--n-tab-border-color);
 `)])])]),r("tabs-scroll-button",[l("start",`
 padding-left: 10px;
 padding-right: 6px;
 `),l("end",`
 padding-right: 10px;
 padding-left: 6px;
 `),l("up",`
 padding-bottom: 10px;
 `),l("down",`
 padding-top: 10px;
 `)])]),Ne=oe({name:"TabsButton",props:{type:{type:String,default:"next"},mergedClsPrefix:{type:String,required:!0},vertical:Boolean,disabled:Boolean,rtl:Boolean,theme:Object,themeOverrides:Object,onClick:Function},setup(e){return{handleClick:()=>{var i;e.disabled||(i=e.onClick)==null||i.call(e,e.type)}}},render(){const{mergedClsPrefix:e,disabled:n,type:i,vertical:u,rtl:c,theme:T,themeOverrides:f,handleClick:b}=this,g=i==="next",m=u?g:c?!g:g;return s(),A(Xt,{text:!0,disabled:n,size:"small",theme:T,themeOverrides:f,onClick:b,class:S([`${e}-tabs-scroll-button`,!u&&i==="prev"&&`${e}-tabs-scroll-button--start`,!u&&i==="next"&&`${e}-tabs-scroll-button--end`,u&&i==="prev"&&`${e}-tabs-scroll-button--up`,u&&i==="next"&&`${e}-tabs-scroll-button--down`])},{icon:()=>(s(),A(qe,{clsPrefix:e,style:Q(u?{transform:"rotate(90deg)"}:void 0)},{default:()=>m?(s(),A(Gt,{key:1})):(s(),A(Ta,{key:2}))},1032,["clsPrefix","style"]))},1032,["disabled","theme","themeOverrides","onClick","class"])}});const Re=Ca,ka={...Ye.props,value:[String,Number],defaultValue:[String,Number],trigger:{type:String,default:"click"},type:{type:String,default:"bar"},closable:Boolean,justifyContent:String,size:String,placement:{type:String,default:"top"},tabStyle:[String,Object],tabClass:String,addTabStyle:[String,Object],addTabClass:String,barWidth:Number,paneClass:String,paneStyle:[String,Object],paneWrapperClass:String,paneWrapperStyle:[String,Object],addable:[Boolean,Object],tabsPadding:{type:Number,default:0},animated:Boolean,onBeforeLeave:Function,onAdd:Function,"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],onClose:[Function,Array],labelSize:String,activeName:[String,Number],onActiveNameChange:[Function,Array],showScrollButton:Boolean,centerActiveTab:Boolean};var Wa=oe({name:"Tabs",props:ka,slots:Object,setup(e,{slots:n}){var Ee,Ie;const{mergedClsPrefixRef:i,inlineThemeDisabled:u,mergedComponentPropsRef:c,mergedRtlRef:T}=qt(e),f=Yt("Tabs",T,i),b=ne(()=>{const{placement:t}=e;return t==="start"?f!=null&&f.value?"right":"left":t==="end"?f!=null&&f.value?"left":"right":t}),g=Ye("Tabs","-tabs",$a,Kt,e,i),m=I(null),O=I(null),P=I(null),E=I(null),j=I(null),B=I(null),z=I(null),D=I(!0),L=I(!0),Y=He(e,["labelSize","size"]),J=ne(()=>{var a,o;if(Y.value)return Y.value;const t=(o=(a=c==null?void 0:c.value)==null?void 0:a.Tabs)==null?void 0:o.size;return t||"medium"}),X=He(e,["activeName","value"]),N=I(X.value??e.defaultValue??(n.default?(Ie=(Ee=we(n.default())[0])==null?void 0:Ee.props)==null?void 0:Ie.name:null)),p=Zt(X,N),$={id:0},V=ne(()=>{if(!(!e.justifyContent||e.type==="card"))return{display:"flex",justifyContent:e.justifyContent}});ie(p,()=>{$.id=0,W(),se(()=>{ge()})});function H(){var a;const{value:t}=p;return t===null?null:(a=m.value)==null?void 0:a.querySelector(`[data-name="${t}"]`)}function le(t){if(e.type==="card")return;const{value:a}=P;if(!a)return;const o=a.style.opacity==="0";if(t){const d=`${i.value}-tabs-bar--disabled`,{barWidth:x}=e,R=b.value;if(t.dataset.disabled==="true"?a.classList.add(d):a.classList.remove(d),["top","bottom"].includes(R)){if(C(["top","maxHeight","height"]),typeof x=="number"&&t.offsetWidth>=x){const w=Math.floor((t.offsetWidth-x)/2)+t.offsetLeft;a.style.left=`${w}px`,a.style.maxWidth=`${x}px`}else a.style.left=`${t.offsetLeft}px`,a.style.maxWidth=`${t.offsetWidth}px`;a.style.width="8192px",o&&(a.style.transition="none"),a.offsetWidth,o&&(a.style.transition="",a.style.opacity="1")}else{if(C(["left","maxWidth","width"]),typeof x=="number"&&t.offsetHeight>=x){const w=Math.floor((t.offsetHeight-x)/2)+t.offsetTop;a.style.top=`${w}px`,a.style.maxHeight=`${x}px`}else a.style.top=`${t.offsetTop}px`,a.style.maxHeight=`${t.offsetHeight}px`;a.style.height="8192px",o&&(a.style.transition="none"),a.offsetHeight,o&&(a.style.transition="",a.style.opacity="1")}}}function U(){if(e.type==="card")return;const{value:t}=P;t&&(t.style.opacity="0")}function C(t){const{value:a}=P;if(a)for(const o of t)a.style[o]=""}function W(){if(e.type==="card")return;const t=H();t?le(t):U()}function ee(t,a,o,d){const x=t.getBoundingClientRect(),R=a.getBoundingClientRect(),w=o?"left":"top",_=o?"right":"bottom";let F=0;d?F=(R[w]+R[_])/2-(x[w]+x[_])/2:R[w]<x[w]?F=R[w]-x[w]:R[_]>x[_]&&(F=R[_]-x[_]),F!==0&&t.scrollBy({[w]:F,behavior:"smooth"})}function ge(){var o;const t=["top","bottom"].includes(b.value),a=H();if(a)if(t){const d=(o=B.value)==null?void 0:o.$el;if(!d)return;ee(d,a,t,e.centerActiveTab)}else{const{value:d}=z;if(!d)return;ee(d,a,t,e.centerActiveTab)}}const de=I(null);let me=0,K=null;function Ze(t){const a=de.value;if(a){me=t.getBoundingClientRect().height;const o=`${me}px`,d=()=>{a.style.height=o,a.style.maxHeight=o};K?(d(),K(),K=null):K=d}}function Je(t){const a=de.value;if(a){const o=t.getBoundingClientRect().height,d=()=>{document.body.offsetHeight,a.style.maxHeight=`${o}px`,a.style.height=`${Math.max(me,o)}px`};K?(K(),K=null,d()):K=d}}function Qe(){const t=de.value;if(t){t.style.maxHeight="",t.style.height="";const{paneWrapperStyle:a}=e;if(typeof a=="string")t.style.cssText=a;else if(a){const{maxHeight:o,height:d}=a;o!==void 0&&(t.style.maxHeight=o),d!==void 0&&(t.style.height=d)}}}const Pe={value:[]},Be=I("next");function et(t){const a=p.value;let o="next";for(const d of Pe.value){if(d===a)break;if(d===t){o="prev";break}}Be.value=o,tt(t)}function tt(t){const{onActiveNameChange:a,onUpdateValue:o,"onUpdate:value":d}=e;a&&pe(a,t),o&&pe(o,t),d&&pe(d,t),N.value=t}function at(t){const{onClose:a}=e;a&&pe(a,t)}function rt(t){if(["top","bottom"].includes(b.value)){const{value:a}=B;if(!a)return;const o=a.$el;if(!o)return;const d=o.offsetWidth,x=!!(f!=null&&f.value),R=t==="next"?d:-d;o.scrollBy({left:x?-R:R,behavior:"smooth"})}else{const{value:a}=z;if(!a)return;const o=a.offsetHeight,d=t==="next"?a.scrollTop+o:a.scrollTop-o;a.scrollTo({top:d,left:0,behavior:"smooth"})}}let xe=!0;function ye(){const{value:t}=P;if(!t)return;xe&&(xe=!1);const a="transition-disabled";t.classList.add(a),W(),t.classList.remove(a)}const te=I(null);function ce({transitionDisabled:t}){const a=m.value;if(!a)return;t&&a.classList.add("transition-disabled");const o=H();o&&te.value&&(te.value.style.width=`${o.offsetWidth}px`,te.value.style.height=`${o.offsetHeight}px`,te.value.style.transform=`translate(${o.offsetLeft}px, ${o.offsetTop}px)`,t&&te.value.offsetWidth),t&&a.classList.remove("transition-disabled")}ie([p],()=>{e.type==="segment"&&se(()=>{ce({transitionDisabled:!1})})}),Jt(()=>{e.type==="segment"&&ce({transitionDisabled:!0})});let Le=0;function nt(t){var o;if(t.contentRect.width===0&&t.contentRect.height===0||Le===t.contentRect.width)return;Le=t.contentRect.width;const{type:a}=e;(a==="line"||a==="bar")&&(xe||(o=e.justifyContent)!=null&&o.startsWith("space"))&&ye(),a!=="segment"&&be(_e())}const ot=Re(nt,64);function We(){const{type:t}=e;t==="line"||t==="bar"?ye():t==="segment"&&ce({transitionDisabled:!0})}ie([()=>e.justifyContent,()=>e.size],()=>{se(()=>{(e.type==="line"||e.type==="bar")&&ye()})}),ie([b,()=>f==null?void 0:f.value],()=>{se(()=>{We(),be(_e(),{instantly:!0})})}),ie(()=>e.type,()=>{se(()=>{const t=O.value;t&&(t.classList.add("transition-disabled"),We(),t.offsetWidth,t.classList.remove("transition-disabled"))})});const ae=I(!1);function it(t){var _;const{target:a,contentRect:{width:o,height:d}}=t,x=a.parentElement.parentElement.offsetWidth,R=a.parentElement.parentElement.offsetHeight,w=b.value;if(!ae.value)w==="top"||w==="bottom"?x<o&&(ae.value=!0):R<d&&(ae.value=!0);else{const{value:F}=j;if(!F)return;w==="top"||w==="bottom"?x-o>F.$el.offsetWidth&&(ae.value=!1):R-d>F.$el.offsetHeight&&(ae.value=!1)}be(((_=B.value)==null?void 0:_.$el)||null)}const st=Re(it,64);function lt(){const{onAdd:t}=e;t&&t()}const Ce=I(!1);function _e(){var a;const t=b.value;return(t==="top"||t==="bottom"?(a=B.value)==null?void 0:a.$el:z.value)||null}function be(t,a={instantly:!1}){if(!t)return;const o=a.instantly?E.value:null;o&&o.classList.add("transition-disabled");const d=1,x=b.value;if(x==="top"||x==="bottom"){const{scrollLeft:R,scrollWidth:w,offsetWidth:_}=t,F=Math.abs(R);D.value=F<=d,L.value=F+_>=w-d,Ce.value=_<w-d}else{const{scrollTop:R,scrollHeight:w,offsetHeight:_}=t;D.value=R<=d,L.value=R+_>=w-d,Ce.value=_<w-d}o&&(o.offsetWidth,o.classList.remove("transition-disabled"))}const dt=Re(t=>{be(t.target)},64);ia(ke,{triggerRef:q(e,"trigger"),tabStyleRef:q(e,"tabStyle"),tabClassRef:q(e,"tabClass"),addTabStyleRef:q(e,"addTabStyle"),addTabClassRef:q(e,"addTabClass"),paneClassRef:q(e,"paneClass"),paneStyleRef:q(e,"paneStyle"),mergedClsPrefixRef:i,typeRef:q(e,"type"),closableRef:q(e,"closable"),valueRef:p,tabChangeIdRef:$,onBeforeLeaveRef:q(e,"onBeforeLeave"),activateTab:et,handleClose:at,handleAdd:lt}),Qt(()=>{W(),ge()}),ea(()=>{const{value:t}=E;if(!t)return;const{value:a}=i,o=`${a}-tabs-nav-scroll-wrapper--shadow-start`,d=`${a}-tabs-nav-scroll-wrapper--shadow-end`;D.value?t.classList.remove(o):t.classList.add(o),L.value?t.classList.remove(d):t.classList.add(d)});const ct={syncBarPosition:()=>{W()},scrollToCurrentTab:()=>{ge()}},bt=()=>{ce({transitionDisabled:!0})},Ae=ne(()=>{const{value:t}=J,{type:a}=e,o=`${t}${{card:"Card",bar:"Bar",line:"Line",segment:"Segment"}[a]}`,{self:{barColor:d,closeIconColor:x,closeIconColorHover:R,closeIconColorPressed:w,tabColor:_,tabBorderColor:F,paneTextColor:ft,tabFontWeight:ut,tabBorderRadius:pt,tabFontWeightActive:vt,colorSegment:ht,fontWeightStrong:gt,tabColorSegment:mt,closeSize:xt,closeIconSize:yt,closeColorHover:Ct,closeColorPressed:wt,closeBorderRadius:St,[G("panePadding",t)]:fe,[G("tabPadding",o)]:Tt,[G("tabPaddingVertical",o)]:Rt,[G("tabGap",o)]:zt,[G("tabGap",`${o}Vertical`)]:$t,[G("tabTextColor",a)]:kt,[G("tabTextColorActive",a)]:Pt,[G("tabTextColorHover",a)]:Bt,[G("tabTextColorDisabled",a)]:Lt,[G("tabFontSize",t)]:Wt},common:{cubicBezierEaseInOut:_t}}=g.value;return{"--n-bezier":_t,"--n-color-segment":ht,"--n-bar-color":d,"--n-tab-font-size":Wt,"--n-tab-text-color":kt,"--n-tab-text-color-active":Pt,"--n-tab-text-color-disabled":Lt,"--n-tab-text-color-hover":Bt,"--n-pane-text-color":ft,"--n-tab-border-color":F,"--n-tab-border-radius":pt,"--n-close-size":xt,"--n-close-icon-size":yt,"--n-close-color-hover":Ct,"--n-close-color-pressed":wt,"--n-close-border-radius":St,"--n-close-icon-color":x,"--n-close-icon-color-hover":R,"--n-close-icon-color-pressed":w,"--n-tab-color":_,"--n-tab-font-weight":ut,"--n-tab-font-weight-active":vt,"--n-tab-padding":Tt,"--n-tab-padding-vertical":Rt,"--n-tab-gap":zt,"--n-tab-gap-vertical":$t,"--n-pane-padding-left":ue(fe,"left"),"--n-pane-padding-right":ue(fe,"right"),"--n-pane-padding-top":ue(fe,"top"),"--n-pane-padding-bottom":ue(fe,"bottom"),"--n-font-weight-strong":gt,"--n-tab-color-segment":mt}}),re=u?ta("tabs",ne(()=>`${J.value[0]}${e.type[0]}`),Ae,e):void 0;return{mergedClsPrefix:i,mergedValue:p,renderedNames:new Set,segmentCapsuleElRef:te,tabsPaneWrapperRef:de,tabsElRef:m,selfElRef:O,barElRef:P,addTabInstRef:j,xScrollInstRef:B,scrollWrapperElRef:E,addTabFixed:ae,tabWrapperStyle:V,handleNavResize:ot,mergedSize:J,handleScroll:dt,handleTabsResize:st,cssVars:u?void 0:Ae,themeClass:re==null?void 0:re.themeClass,animationDirection:Be,renderNameListRef:Pe,yScrollElRef:z,handleSegmentResize:bt,onAnimationBeforeLeave:Ze,onAnimationEnter:Je,onAnimationAfterEnter:Qe,onRender:re==null?void 0:re.onRender,startReachedRef:D,endReachedRef:L,isOverflow:Ce,handleButtonClick:rt,mergedTheme:g,rtlEnabled:f,mergedPlacement:b,...ct}},render(){const{mergedClsPrefix:e,type:n,mergedPlacement:i,addTabFixed:u,addable:c,mergedSize:T,renderNameListRef:f,onRender:b,paneWrapperClass:g,paneWrapperStyle:m,startReachedRef:O,endReachedRef:P,isOverflow:E,showScrollButton:j,handleButtonClick:B,mergedTheme:z,rtlEnabled:D,$slots:{default:L,prefix:Y,suffix:J}}=this;b==null||b();const X=L?we(L()).filter(C=>C.type.__TAB_PANE__===!0):[],N=L?we(L()).filter(C=>C.type.__TAB__===!0):[],p=!N.length,$=n==="card",V=n==="segment",H=!$&&!V&&this.justifyContent;f.value=[];const le=()=>{const C=(s(),v("div",{style:Q(this.tabWrapperStyle),class:S(`${e}-tabs-wrapper`)},[H?h(()=>null):(s(),v("div",{key:1,class:S(`${e}-tabs-scroll-padding`),style:Q(i==="top"||i==="bottom"?{width:`${this.tabsPadding}px`}:{height:`${this.tabsPadding}px`})},null,6)),p?(s(),v(M,{key:2},[h(()=>X.map((W,ee)=>(f.value.push(W.props.name),ze((s(),A($e,he(W.props,{internalCreatedByPane:!0,internalLeftPadded:ee!==0&&(!H||H==="center"||H==="start"||H==="end")}),Fe(W.children?{default:W.children.tab}:void 0),1040,["internalLeftPadded"]))))))],64)):(s(),v(M,{key:3},[h(()=>N.map((W,ee)=>(f.value.push(W.props.name),ze(ee!==0&&!H?Xe(W):W))))],64)),!u&&c&&$?(s(),v(M,{key:4},[h(()=>Ue(c,(p?X.length:N.length)!==0))],64)):h(()=>null),H?h(()=>null):(s(),v("div",{key:7,class:S(`${e}-tabs-scroll-padding`),style:Q({width:`${this.tabsPadding}px`})},null,6)),$?h(()=>null):(s(),v("div",{key:9,ref:"barElRef",class:S(`${e}-tabs-bar`)},null,2))],6));return s(),v("div",{ref:"tabsElRef",class:S(`${e}-tabs-nav-scroll-content`)},[$&&c?(s(),A(Se,{key:0,onResize:this.handleTabsResize},{default:()=>C},1032,["onResize"])):(s(),v(M,{key:1},[h(()=>C)],64)),$?(s(),v("div",{key:2,class:S(`${e}-tabs-pad`)},null,2)):h(()=>null)],2)},U=V?"top":i;return s(),v("div",{ref:"selfElRef",class:S([`${e}-tabs`,this.themeClass,`${e}-tabs--${n}-type`,`${e}-tabs--${T}-size`,H&&`${e}-tabs--flex`,`${e}-tabs--${U}`,D&&`${e}-tabs--rtl`]),style:Q(this.cssVars)},[Z("div",{class:S([`${e}-tabs-nav--${n}-type`,`${e}-tabs-nav--${U}`,`${e}-tabs-nav`])},[h(()=>je(Y,C=>C&&(s(),v("div",{class:S(`${e}-tabs-nav__prefix`)},[h(()=>C)],2)))),V?(s(),A(Se,{key:0,onResize:this.handleSegmentResize},{default:()=>(s(),v("div",{class:S(`${e}-tabs-rail`),ref:"tabsElRef"},[Z("div",{class:S(`${e}-tabs-capsule`),ref:"segmentCapsuleElRef"},[Z("div",{class:S(`${e}-tabs-wrapper`)},[Z("div",{class:S(`${e}-tabs-tab`)},null,2)],2)],2),p?(s(),v(M,{key:0},[h(()=>X.map((C,W)=>(f.value.push(C.props.name),s(),A($e,he(C.props,{internalCreatedByPane:!0,internalLeftPadded:W!==0}),Fe(C.children?{default:C.children.tab}:void 0),1040,["internalLeftPadded"]))))],64)):(s(),v(M,{key:1},[h(()=>N.map((C,W)=>(f.value.push(C.props.name),W===0?C:Xe(C))))],64))],2))},1032,["onResize"])):(s(),v(M,{key:1},[h(()=>j&&E&&(s(),A(Ne,{mergedClsPrefix:e,type:"prev",vertical:U==="left"||U==="right",disabled:O,rtl:!!D,theme:z.peers.Button,themeOverrides:z.peerOverrides.Button,onClick:B},null,8,["mergedClsPrefix","vertical","disabled","rtl","theme","themeOverrides","onClick"]))),(s(),A(Se,{onResize:this.handleNavResize},{default:()=>(s(),v("div",{class:S(`${e}-tabs-nav-scroll-wrapper`),ref:"scrollWrapperElRef"},[["top","bottom"].includes(U)?(s(),A(Sa,{key:0,ref:"xScrollInstRef",onScroll:this.handleScroll},{default:le},1032,["onScroll"])):(s(),v("div",{key:1,class:S(`${e}-tabs-nav-y-scroll`),onScroll:this.handleScroll,ref:"yScrollElRef"},[h(()=>le())],42,["onScroll"]))],2))},1032,["onResize"])),h(()=>j&&E&&(s(),A(Ne,{mergedClsPrefix:e,type:"next",vertical:U==="left"||U==="right",disabled:P,rtl:!!D,theme:z.peers.Button,themeOverrides:z.peerOverrides.Button,onClick:B},null,8,["mergedClsPrefix","vertical","disabled","rtl","theme","themeOverrides","onClick"])))],64)),u&&c&&$?(s(),v(M,{key:2},[h(()=>Ue(c,!0))],64)):h(()=>null),h(()=>je(J,C=>C&&(s(),v("div",{class:S(`${e}-tabs-nav__suffix`)},[h(()=>C)],2))))],2),h(()=>p&&(this.animated&&(U==="top"||U==="bottom")?(s(),v("div",{key:1,ref:"tabsPaneWrapperRef",style:Q(m),class:S([`${e}-tabs-pane-wrapper`,g])},[h(()=>Ve(X,this.mergedValue,this.renderedNames,this.onAnimationBeforeLeave,this.onAnimationEnter,this.onAnimationAfterEnter,this.animationDirection))],6)):Ve(X,this.mergedValue,this.renderedNames)))],6)}});function Ve(e,n,i,u,c,T,f){const b=[];return e.forEach(g=>{const{name:m,displayDirective:O,"display-directive":P}=g.props,E=B=>O===B||P===B,j=n===m;if(g.key!==void 0&&(g.key=m),j||E("show")||E("show:lazy")&&i.has(m)){i.has(m)||i.add(m);const B=!E("if");b.push(B?aa(g,[[ra,j]]):g)}}),f?(s(),A(na,{name:`${f}-transition`,onBeforeLeave:u,onEnter:c,onAfterEnter:T},{default:()=>b},1032,["name","onBeforeLeave","onEnter","onAfterEnter"])):b}function Ue(e,n){return s(),A($e,{ref:"addTabInstRef",key:"__addable",name:"__addable",internalCreatedByPane:!0,internalAddable:!0,internalLeftPadded:n,disabled:typeof e=="object"&&e.disabled},null,8,["internalLeftPadded","disabled"])}function Xe(e){const n=oa(e);return n.props?n.props.internalLeftPadded=!0:n.props={internalLeftPadded:!0},n}function ze(e){return Array.isArray(e.dynamicProps)?e.dynamicProps.includes("internalLeftPadded")||e.dynamicProps.push("internalLeftPadded"):e.dynamicProps=["internalLeftPadded"],e}export{La as T,Wa as a};
