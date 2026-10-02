import{T as J}from"./Tag-aKNUfOMt.js";import{g as ce,c as M,Q as Le,R as Ae,T as c,U as D,W as A,X as Y,d as ne,Y as ae,b as v,e as j,Z as F,n as N,f as Q,u as he,q as $e,$ as ee,a0 as Ce,r as _,A as re,a1 as le,v as ve,k as T,a2 as xe,j as U,a3 as Se,m as oe,a4 as fe,a5 as We,a6 as me,a7 as Ve,a8 as Xe,o as Ye,a9 as qe,aa as Ke,z as te,ab as Ge,ac as Qe,ad as Ze,ae as ie,af as Je,ag as et,ah as tt,ai as rt,aj as be,ak as ot,al as nt,am as K,an as at,ao as ge,C as de,H as ue,ap as it,aq as st,N as s,B as f,E as i,O as I,L as G,P as O,G as lt,ar as pe,as as H,at as L,F as Z,S as se,au as ye,I as dt,D as ut,av as we}from"./index-If5Ucjf1.js";import{I as ct}from"./InputGroup-CTUlTvod.js";import{D as ht,S as ft,C as mt}from"./DataTable-CEHI4og4.js";import{u as vt}from"./composables-Dkuxj35u.js";import{u as bt}from"./use-message-BJ_aNqR3.js";import{a as gt}from"./format-CuWqBo7j.js";function pt(e,t){const a=ce(Le,null);return M(()=>e.hljs||(a==null?void 0:a.mergedHljsRef.value))}function yt(e){const{textColor2:t,fontSize:a,fontWeightStrong:p,textColor3:g}=e;return{textColor:t,fontSize:a,fontWeightStrong:p,"mono-3":"#a0a1a7","hue-1":"#0184bb","hue-2":"#4078f2","hue-3":"#a626a4","hue-4":"#50a14f","hue-5":"#e45649","hue-5-2":"#c91243","hue-6":"#986801","hue-6-2":"#c18401",lineNumberTextColor:g}}const wt={common:Ae,self:yt};var $t=c([D("code",`
 font-size: var(--n-font-size);
 font-family: var(--n-font-family);
 `,[A("show-line-numbers",`
 display: flex;
 `),Y("line-numbers",`
 user-select: none;
 padding-right: 12px;
 text-align: right;
 transition: color .3s var(--n-bezier);
 color: var(--n-line-number-text-color);
 `),A("word-wrap",[c("pre",`
 white-space: pre-wrap;
 word-break: break-all;
 `)]),c("pre",`
 margin: 0;
 line-height: inherit;
 font-size: inherit;
 font-family: inherit;
 `),c("[class^=hljs]",`
 color: var(--n-text-color);
 transition: 
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `)]),({props:e})=>{const t=`${e.bPrefix}code`;return[`${t} .hljs-comment,
 ${t} .hljs-quote {
 color: var(--n-mono-3);
 font-style: italic;
 }`,`${t} .hljs-doctag,
 ${t} .hljs-keyword,
 ${t} .hljs-formula {
 color: var(--n-hue-3);
 }`,`${t} .hljs-section,
 ${t} .hljs-name,
 ${t} .hljs-selector-tag,
 ${t} .hljs-deletion,
 ${t} .hljs-subst {
 color: var(--n-hue-5);
 }`,`${t} .hljs-literal {
 color: var(--n-hue-1);
 }`,`${t} .hljs-string,
 ${t} .hljs-regexp,
 ${t} .hljs-addition,
 ${t} .hljs-attribute,
 ${t} .hljs-meta-string {
 color: var(--n-hue-4);
 }`,`${t} .hljs-built_in,
 ${t} .hljs-class .hljs-title {
 color: var(--n-hue-6-2);
 }`,`${t} .hljs-attr,
 ${t} .hljs-variable,
 ${t} .hljs-template-variable,
 ${t} .hljs-type,
 ${t} .hljs-selector-class,
 ${t} .hljs-selector-attr,
 ${t} .hljs-selector-pseudo,
 ${t} .hljs-number {
 color: var(--n-hue-6);
 }`,`${t} .hljs-symbol,
 ${t} .hljs-bullet,
 ${t} .hljs-link,
 ${t} .hljs-meta,
 ${t} .hljs-selector-id,
 ${t} .hljs-title {
 color: var(--n-hue-2);
 }`,`${t} .hljs-emphasis {
 font-style: italic;
 }`,`${t} .hljs-strong {
 font-weight: var(--n-font-weight-strong);
 }`,`${t} .hljs-link {
 text-decoration: underline;
 }`]}]);const Ct={...ae.props,language:String,code:{type:String,default:""},trim:{type:Boolean,default:!0},hljs:Object,uri:Boolean,inline:Boolean,wordWrap:Boolean,showLineNumbers:Boolean,internalFontSize:Number,internalNoHighlight:Boolean};var xt=ne({name:"Code",props:Ct,setup(e,{slots:t}){const{internalNoHighlight:a}=e,{mergedClsPrefixRef:p,inlineThemeDisabled:g}=he(),w=_(null),$=a?{value:void 0}:pt(e),k=(m,u,y)=>{const{value:S}=$;return!S||!(m&&S.getLanguage(m))?null:S.highlight(y?u.trim():u,{language:m}).value},h=M(()=>e.inline||e.wordWrap?!1:e.showLineNumbers),C=()=>{if(t.default)return;const{value:m}=w;if(!m)return;const{language:u}=e,y=e.uri?window.decodeURIComponent(e.code):e.code;if(u){const z=k(u,y,e.trim);if(z!==null){if(e.inline)m.innerHTML=z;else{const W=m.querySelector(".__code__");W&&m.removeChild(W);const R=document.createElement("pre");R.className="__code__",R.innerHTML=z,m.appendChild(R)}return}}if(e.inline){m.textContent=y;return}const S=m.querySelector(".__code__");if(S)S.textContent=y;else{const z=document.createElement("pre");z.className="__code__",z.textContent=y,m.innerHTML="",m.appendChild(z)}};$e(C),ee(re(e,"language"),C),ee(re(e,"code"),C),a||ee($,C);const V=ae("Code","-code",$t,wt,e,p),l=M(()=>{const{common:{cubicBezierEaseInOut:m,fontFamilyMono:u},self:{textColor:y,fontSize:S,fontWeightStrong:z,lineNumberTextColor:W,"mono-3":R,"hue-1":X,"hue-2":P,"hue-3":d,"hue-4":n,"hue-5":r,"hue-5-2":o,"hue-6":x,"hue-6-2":B}}=V.value,{internalFontSize:E}=e;return{"--n-font-size":E?`${E}px`:S,"--n-font-family":u,"--n-font-weight-strong":z,"--n-bezier":m,"--n-text-color":y,"--n-mono-3":R,"--n-hue-1":X,"--n-hue-2":P,"--n-hue-3":d,"--n-hue-4":n,"--n-hue-5":r,"--n-hue-5-2":o,"--n-hue-6":x,"--n-hue-6-2":B,"--n-line-number-text-color":W}}),b=g?Ce("code",M(()=>`${e.internalFontSize||"a"}`),l,e):void 0;return{mergedClsPrefix:p,codeRef:w,mergedShowLineNumbers:h,lineNumbers:M(()=>{let m=1;const u=[];let y=!1;for(const S of e.code)S===`
`?(y=!0,u.push(m++)):y=!1;return y||u.push(m++),u.join(`
`)}),cssVars:g?void 0:l,themeClass:b==null?void 0:b.themeClass,onRender:b==null?void 0:b.onRender}},render(){const{mergedClsPrefix:e,wordWrap:t,mergedShowLineNumbers:a,onRender:p}=this;return p==null||p(),v(),j("code",{class:F([`${e}-code`,this.themeClass,t&&`${e}-code--word-wrap`,a&&`${e}-code--show-line-numbers`]),style:Q(this.cssVars),ref:"codeRef"},[a?(v(),j("pre",{key:0,class:F(`${e}-code__line-numbers`)},[N(()=>this.lineNumbers)],2)):N(()=>null),N(()=>{var g,w;return(w=(g=this.$slots).default)==null?void 0:w.call(g)})],6)}});const St=["onMouseenter","onMouseleave","onMousedown"],kt={key:1,role:"none"};var zt=ne({name:"NDrawerContent",inheritAttrs:!1,props:{blockScroll:Boolean,show:{type:Boolean,default:void 0},displayDirective:{type:String,required:!0},placement:{type:String,required:!0},contentClass:String,contentStyle:[Object,String],nativeScrollbar:{type:Boolean,required:!0},scrollbarProps:Object,trapFocus:{type:Boolean,default:!0},autoFocus:{type:Boolean,default:!0},showMask:{type:[Boolean,String],required:!0},maxWidth:Number,maxHeight:Number,minWidth:Number,minHeight:Number,resizable:Boolean,onClickoutside:Function,onAfterLeave:Function,onAfterEnter:Function,onEsc:Function},setup(e){const t=_(!!e.show),a=_(null),p=ce(me);let g=0,w="",$=null;const k=_(!1),h=_(!1),C=M(()=>e.placement==="top"||e.placement==="bottom"),{mergedClsPrefixRef:V,mergedRtlRef:l}=he(e),b=Ve("Drawer",l,V),m=d,u=o=>{h.value=!0,g=C.value?o.clientY:o.clientX,w=document.body.style.cursor,document.body.style.cursor=C.value?"ns-resize":"ew-resize",document.body.addEventListener("mousemove",P),document.body.addEventListener("mouseleave",m),document.body.addEventListener("mouseup",d)},y=()=>{$!==null&&(window.clearTimeout($),$=null),h.value?k.value=!0:$=window.setTimeout(()=>{k.value=!0},300)},S=()=>{$!==null&&(window.clearTimeout($),$=null),k.value=!1},{doUpdateHeight:z,doUpdateWidth:W}=p,R=o=>{const{maxWidth:x}=e;if(x&&o>x)return x;const{minWidth:B}=e;return B&&o<B?B:o},X=o=>{const{maxHeight:x}=e;if(x&&o>x)return x;const{minHeight:B}=e;return B&&o<B?B:o};function P(o){var x,B;if(h.value)if(C.value){let E=((x=a.value)==null?void 0:x.offsetHeight)||0;const q=g-o.clientY;E+=e.placement==="bottom"?q:-q,E=X(E),z(E),g=o.clientY}else{let E=((B=a.value)==null?void 0:B.offsetWidth)||0;const q=g-o.clientX;E+=e.placement==="right"?q:-q,E=R(E),W(E),g=o.clientX}}function d(){h.value&&(g=0,h.value=!1,document.body.style.cursor=w,document.body.removeEventListener("mousemove",P),document.body.removeEventListener("mouseup",d),document.body.removeEventListener("mouseleave",m))}Xe(()=>{e.show&&(t.value=!0)}),ee(()=>e.show,o=>{o||d()}),Ye(()=>{d()});const n=M(()=>{const{show:o}=e,x=[[ve,o]];return e.showMask||x.push([Ke,e.onClickoutside,void 0,{capture:!0}]),x});function r(){var o;t.value=!1,(o=e.onAfterLeave)==null||o.call(e)}return qe(M(()=>e.blockScroll&&t.value)),te(Ge,a),te(Qe,null),te(Ze,null),{bodyRef:a,rtlEnabled:b,mergedClsPrefix:p.mergedClsPrefixRef,isMounted:p.isMountedRef,mergedTheme:p.mergedThemeRef,displayed:t,transitionName:M(()=>({right:"slide-in-from-right-transition",left:"slide-in-from-left-transition",top:"slide-in-from-top-transition",bottom:"slide-in-from-bottom-transition"})[e.placement]),handleAfterLeave:r,bodyDirectives:n,handleMousedownResizeTrigger:u,handleMouseenterResizeTrigger:y,handleMouseleaveResizeTrigger:S,isDragging:h,isHoverOnResizeTrigger:k}},render(){const{$slots:e,mergedClsPrefix:t}=this;return this.displayDirective==="show"||this.displayed||this.show?le((v(),j("div",kt,[(v(),T(We,{disabled:!this.showMask||!this.trapFocus,active:this.show,autoFocus:this.autoFocus,onEsc:this.onEsc},{default:()=>(v(),T(xe,{name:this.transitionName,appear:this.isMounted,onAfterEnter:this.onAfterEnter,onAfterLeave:this.handleAfterLeave},{default:()=>le(U("div",oe(this.$attrs,{role:"dialog",ref:"bodyRef","aria-modal":"true",class:[`${t}-drawer`,this.rtlEnabled&&`${t}-drawer--rtl`,`${t}-drawer--${this.placement}-placement`,this.isDragging&&`${t}-drawer--unselectable`,this.nativeScrollbar&&`${t}-drawer--native-scrollbar`]}),[this.resizable?(v(),j("div",{key:2,class:F([`${t}-drawer__resize-trigger`,(this.isDragging||this.isHoverOnResizeTrigger)&&`${t}-drawer__resize-trigger--hover`]),onMouseenter:this.handleMouseenterResizeTrigger,onMouseleave:this.handleMouseleaveResizeTrigger,onMousedown:this.handleMousedownResizeTrigger},null,42,St)):null,this.nativeScrollbar?(v(),j("div",{key:3,class:F([`${t}-drawer-content-wrapper`,this.contentClass]),style:Q(this.contentStyle),role:"none"},[N(()=>{var a;return(a=e.default)==null?void 0:a.call(e)})],6)):(v(),T(Se,oe({key:4},this.scrollbarProps,{contentStyle:this.contentStyle,contentClass:[`${t}-drawer-content-wrapper`,this.contentClass],theme:this.mergedTheme.peers.Scrollbar,themeOverrides:this.mergedTheme.peerOverrides.Scrollbar}),fe(e),1040,["contentStyle","contentClass","theme","themeOverrides"]))]),this.bodyDirectives)},1032,["name","appear","onAfterEnter","onAfterLeave"]))},1032,["disabled","active","autoFocus","onEsc"]))])),[[ve,this.displayDirective==="if"||this.displayed||this.show]]):null}});const{cubicBezierEaseIn:_t,cubicBezierEaseOut:jt}=ie;function Bt({duration:e="0.3s",leaveDuration:t="0.2s",name:a="slide-in-from-bottom"}={}){return[c(`&.${a}-transition-leave-active`,{transition:`transform ${t} ${_t}`}),c(`&.${a}-transition-enter-active`,{transition:`transform ${e} ${jt}`}),c(`&.${a}-transition-enter-to`,{transform:"translateY(0)"}),c(`&.${a}-transition-enter-from`,{transform:"translateY(100%)"}),c(`&.${a}-transition-leave-from`,{transform:"translateY(0)"}),c(`&.${a}-transition-leave-to`,{transform:"translateY(100%)"})]}const{cubicBezierEaseIn:Et,cubicBezierEaseOut:Tt}=ie;function Rt({duration:e="0.3s",leaveDuration:t="0.2s",name:a="slide-in-from-left"}={}){return[c(`&.${a}-transition-leave-active`,{transition:`transform ${t} ${Et}`}),c(`&.${a}-transition-enter-active`,{transition:`transform ${e} ${Tt}`}),c(`&.${a}-transition-enter-to`,{transform:"translateX(0)"}),c(`&.${a}-transition-enter-from`,{transform:"translateX(-100%)"}),c(`&.${a}-transition-leave-from`,{transform:"translateX(0)"}),c(`&.${a}-transition-leave-to`,{transform:"translateX(-100%)"})]}const{cubicBezierEaseIn:Pt,cubicBezierEaseOut:Dt}=ie;function Ft({duration:e="0.3s",leaveDuration:t="0.2s",name:a="slide-in-from-right"}={}){return[c(`&.${a}-transition-leave-active`,{transition:`transform ${t} ${Pt}`}),c(`&.${a}-transition-enter-active`,{transition:`transform ${e} ${Dt}`}),c(`&.${a}-transition-enter-to`,{transform:"translateX(0)"}),c(`&.${a}-transition-enter-from`,{transform:"translateX(100%)"}),c(`&.${a}-transition-leave-from`,{transform:"translateX(0)"}),c(`&.${a}-transition-leave-to`,{transform:"translateX(100%)"})]}const{cubicBezierEaseIn:Mt,cubicBezierEaseOut:Ot}=ie;function Ht({duration:e="0.3s",leaveDuration:t="0.2s",name:a="slide-in-from-top"}={}){return[c(`&.${a}-transition-leave-active`,{transition:`transform ${t} ${Mt}`}),c(`&.${a}-transition-enter-active`,{transition:`transform ${e} ${Ot}`}),c(`&.${a}-transition-enter-to`,{transform:"translateY(0)"}),c(`&.${a}-transition-enter-from`,{transform:"translateY(-100%)"}),c(`&.${a}-transition-leave-from`,{transform:"translateY(0)"}),c(`&.${a}-transition-leave-to`,{transform:"translateY(-100%)"})]}var Ut=c([D("drawer",`
 word-break: break-word;
 line-height: var(--n-line-height);
 position: absolute;
 pointer-events: all;
 box-shadow: var(--n-box-shadow);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 background-color: var(--n-color);
 color: var(--n-text-color);
 box-sizing: border-box;
 `,[Ft(),Rt(),Ht(),Bt(),A("unselectable",`
 user-select: none; 
 -webkit-user-select: none;
 `),A("native-scrollbar",[D("drawer-content-wrapper",`
 overflow: auto;
 height: 100%;
 `)]),Y("resize-trigger",`
 position: absolute;
 background-color: #0000;
 transition: background-color .3s var(--n-bezier);
 `,[A("hover",`
 background-color: var(--n-resize-trigger-color-hover);
 `)]),D("drawer-content-wrapper",`
 box-sizing: border-box;
 `),D("drawer-content",`
 height: 100%;
 display: flex;
 flex-direction: column;
 `,[A("native-scrollbar",[D("drawer-body-content-wrapper",`
 height: 100%;
 overflow: auto;
 `)]),D("drawer-body",`
 flex: 1 0 0;
 overflow: hidden;
 `),D("drawer-body-content-wrapper",`
 box-sizing: border-box;
 padding: var(--n-body-padding);
 `),D("drawer-header",`
 font-weight: var(--n-title-font-weight);
 line-height: 1;
 font-size: var(--n-title-font-size);
 color: var(--n-title-text-color);
 padding: var(--n-header-padding);
 transition: border .3s var(--n-bezier);
 border-bottom: 1px solid var(--n-divider-color);
 border-bottom: var(--n-header-border-bottom);
 display: flex;
 justify-content: space-between;
 align-items: center;
 `,[Y("main",`
 flex: 1;
 `),Y("close",`
 margin-left: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `)]),D("drawer-footer",`
 display: flex;
 justify-content: flex-end;
 border-top: var(--n-footer-border-top);
 transition: border .3s var(--n-bezier);
 padding: var(--n-footer-padding);
 `)]),A("right-placement",`
 top: 0;
 bottom: 0;
 right: 0;
 border-top-left-radius: var(--n-border-radius);
 border-bottom-left-radius: var(--n-border-radius);
 `,[Y("resize-trigger",`
 width: 3px;
 height: 100%;
 top: 0;
 left: 0;
 transform: translateX(-1.5px);
 cursor: ew-resize;
 `)]),A("left-placement",`
 top: 0;
 bottom: 0;
 left: 0;
 border-top-right-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `,[Y("resize-trigger",`
 width: 3px;
 height: 100%;
 top: 0;
 right: 0;
 transform: translateX(1.5px);
 cursor: ew-resize;
 `)]),A("top-placement",`
 top: 0;
 left: 0;
 right: 0;
 border-bottom-left-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `,[Y("resize-trigger",`
 width: 100%;
 height: 3px;
 bottom: 0;
 left: 0;
 transform: translateY(1.5px);
 cursor: ns-resize;
 `)]),A("bottom-placement",`
 left: 0;
 bottom: 0;
 right: 0;
 border-top-left-radius: var(--n-border-radius);
 border-top-right-radius: var(--n-border-radius);
 `,[Y("resize-trigger",`
 width: 100%;
 height: 3px;
 top: 0;
 left: 0;
 transform: translateY(-1.5px);
 cursor: ns-resize;
 `)])]),c("body",[c(">",[D("drawer-container",`
 position: fixed;
 `)])]),D("drawer-container",`
 position: relative;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 pointer-events: none;
 `,[c("> *",`
 pointer-events: all;
 `)]),D("drawer-mask",`
 background-color: rgba(0, 0, 0, .3);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `,[A("invisible",`
 background-color: rgba(0, 0, 0, 0)
 `),Je({enterDuration:"0.2s",leaveDuration:"0.2s",enterCubicBezier:"var(--n-bezier-in)",leaveCubicBezier:"var(--n-bezier-out)"})])]);const Nt=["onClick"],It={...ae.props,show:Boolean,width:[Number,String],height:[Number,String],placement:{type:String,default:"right"},maskClosable:{type:Boolean,default:!0},showMask:{type:[Boolean,String],default:!0},to:[String,Object],displayDirective:{type:String,default:"if"},nativeScrollbar:{type:Boolean,default:!0},zIndex:Number,onMaskClick:Function,scrollbarProps:Object,contentClass:String,contentStyle:[Object,String],trapFocus:{type:Boolean,default:!0},onEsc:Function,autoFocus:{type:Boolean,default:!0},closeOnEsc:{type:Boolean,default:!0},blockScroll:{type:Boolean,default:!0},maxWidth:Number,maxHeight:Number,minWidth:Number,minHeight:Number,resizable:Boolean,defaultWidth:{type:[Number,String],default:251},defaultHeight:{type:[Number,String],default:251},onUpdateWidth:[Function,Array],onUpdateHeight:[Function,Array],"onUpdate:width":[Function,Array],"onUpdate:height":[Function,Array],"onUpdate:show":[Function,Array],onUpdateShow:[Function,Array],onAfterEnter:Function,onAfterLeave:Function,drawerStyle:[String,Object],drawerClass:String,target:null,onShow:Function,onHide:Function};var Lt=ne({name:"Drawer",inheritAttrs:!1,props:It,setup(e){const{mergedClsPrefixRef:t,namespaceRef:a,inlineThemeDisabled:p}=he(e),g=tt(),w=ae("Drawer","-drawer",Ut,rt,e,t),$=_(e.defaultWidth),k=_(e.defaultHeight),h=be(re(e,"width"),$),C=be(re(e,"height"),k),V=M(()=>{const{placement:d}=e;return d==="top"||d==="bottom"?"":ge(h.value)}),l=M(()=>{const{placement:d}=e;return d==="left"||d==="right"?"":ge(C.value)}),b=d=>{const{onUpdateWidth:n,"onUpdate:width":r}=e;n&&K(n,d),r&&K(r,d),$.value=d},m=d=>{const{onUpdateHeight:n,"onUpdate:width":r}=e;n&&K(n,d),r&&K(r,d),k.value=d},u=M(()=>[{width:V.value,height:l.value},e.drawerStyle||""]);function y(d){const{onMaskClick:n,maskClosable:r}=e;r&&R(!1),n&&n(d)}function S(d){y(d)}const z=ot();function W(d){var n;(n=e.onEsc)==null||n.call(e),e.show&&e.closeOnEsc&&nt(d)&&(z.value||R(!1))}function R(d){const{onHide:n,onUpdateShow:r,"onUpdate:show":o}=e;r&&K(r,d),o&&K(o,d),n&&!d&&K(n,d)}te(me,{isMountedRef:g,mergedThemeRef:w,mergedClsPrefixRef:t,doUpdateShow:R,doUpdateHeight:m,doUpdateWidth:b});const X=M(()=>{const{common:{cubicBezierEaseInOut:d,cubicBezierEaseIn:n,cubicBezierEaseOut:r},self:{color:o,textColor:x,boxShadow:B,lineHeight:E,headerPadding:q,footerPadding:ke,borderRadius:ze,bodyPadding:_e,titleFontSize:je,titleTextColor:Be,titleFontWeight:Ee,headerBorderBottom:Te,footerBorderTop:Re,closeIconColor:Pe,closeIconColorHover:De,closeIconColorPressed:Fe,closeColorHover:Me,closeColorPressed:Oe,closeIconSize:He,closeSize:Ue,closeBorderRadius:Ne,resizableTriggerColorHover:Ie}}=w.value;return{"--n-line-height":E,"--n-color":o,"--n-border-radius":ze,"--n-text-color":x,"--n-box-shadow":B,"--n-bezier":d,"--n-bezier-out":r,"--n-bezier-in":n,"--n-header-padding":q,"--n-body-padding":_e,"--n-footer-padding":ke,"--n-title-text-color":Be,"--n-title-font-size":je,"--n-title-font-weight":Ee,"--n-header-border-bottom":Te,"--n-footer-border-top":Re,"--n-close-icon-color":Pe,"--n-close-icon-color-hover":De,"--n-close-icon-color-pressed":Fe,"--n-close-size":Ue,"--n-close-color-hover":Me,"--n-close-color-pressed":Oe,"--n-close-icon-size":He,"--n-close-border-radius":Ne,"--n-resize-trigger-color-hover":Ie}}),P=p?Ce("drawer",void 0,X,e):void 0;return{mergedClsPrefix:t,namespace:a,mergedBodyStyle:u,handleOutsideClick:S,handleMaskClick:y,handleEsc:W,mergedTheme:w,cssVars:p?void 0:X,themeClass:P==null?void 0:P.themeClass,onRender:P==null?void 0:P.onRender,isMounted:g}},render(){const{mergedClsPrefix:e}=this;return v(),T(et,{to:this.to,show:this.show},{default:()=>{var t;return(t=this.onRender)==null||t.call(this),le((v(),j("div",{class:F([`${e}-drawer-container`,this.namespace,this.themeClass]),style:Q(this.cssVars),role:"none"},[this.showMask?(v(),T(xe,{key:0,name:"fade-in-transition",appear:this.isMounted},{default:()=>this.show?(v(),j("div",{key:1,"aria-hidden":!0,class:F([`${e}-drawer-mask`,this.showMask==="transparent"&&`${e}-drawer-mask--invisible`]),onClick:this.handleMaskClick},null,10,Nt)):null},1032,["appear"])):N(()=>null),(v(),T(zt,oe(this.$attrs,{class:[this.drawerClass,this.$attrs.class],style:[this.mergedBodyStyle,this.$attrs.style],blockScroll:this.blockScroll,contentStyle:this.contentStyle,contentClass:this.contentClass,placement:this.placement,scrollbarProps:this.scrollbarProps,show:this.show,displayDirective:this.displayDirective,nativeScrollbar:this.nativeScrollbar,onAfterEnter:this.onAfterEnter,onAfterLeave:this.onAfterLeave,trapFocus:this.trapFocus,autoFocus:this.autoFocus,resizable:this.resizable,maxHeight:this.maxHeight,minHeight:this.minHeight,maxWidth:this.maxWidth,minWidth:this.minWidth,showMask:this.showMask,onEsc:this.handleEsc,onClickoutside:this.handleOutsideClick}),fe(this.$slots),1040,["class","style","blockScroll","contentStyle","contentClass","placement","scrollbarProps","show","displayDirective","nativeScrollbar","onAfterEnter","onAfterLeave","trapFocus","autoFocus","resizable","maxHeight","minHeight","maxWidth","minWidth","showMask","onEsc","onClickoutside"]))],6)),[[at,{zIndex:this.zIndex,enabled:this.show}]])}},1032,["to","show"])}});const At={title:String,headerClass:String,headerStyle:[Object,String],footerClass:String,footerStyle:[Object,String],bodyClass:String,bodyStyle:[Object,String],bodyContentClass:String,bodyContentStyle:[Object,String],nativeScrollbar:{type:Boolean,default:!0},scrollbarProps:Object,closable:Boolean};var Wt=ne({name:"DrawerContent",props:At,slots:Object,setup(){const e=ce(me,null);e||st("drawer-content","`n-drawer-content` must be placed inside `n-drawer`.");const{doUpdateShow:t}=e;function a(){t(!1)}return{handleCloseClick:a,mergedTheme:e.mergedThemeRef,mergedClsPrefix:e.mergedClsPrefixRef}},render(){const{title:e,mergedClsPrefix:t,nativeScrollbar:a,mergedTheme:p,bodyClass:g,bodyStyle:w,bodyContentClass:$,bodyContentStyle:k,headerClass:h,headerStyle:C,footerClass:V,footerStyle:l,scrollbarProps:b,closable:m,$slots:u}=this;return v(),j("div",{role:"none",class:F([`${t}-drawer-content`,a&&`${t}-drawer-content--native-scrollbar`])},[u.header||e||m?(v(),j("div",{key:0,class:F([`${t}-drawer-header`,h]),style:Q(C),role:"none"},[de("div",{class:F(`${t}-drawer-header__main`),role:"heading","aria-level":"1"},[u.header!==void 0?(v(),j(ue,{key:0},[N(()=>u.header())],64)):(v(),j(ue,{key:1},[N(()=>e)],64))],2),N(()=>m&&(v(),T(it,{onClick:this.handleCloseClick,clsPrefix:t,class:F(`${t}-drawer-header__close`),absolute:!0},null,8,["onClick","clsPrefix","class"])))],6)):N(()=>null),a?(v(),j("div",{key:2,class:F([`${t}-drawer-body`,g]),style:Q(w),role:"none"},[de("div",{class:F([`${t}-drawer-body-content-wrapper`,$]),style:Q(k),role:"none"},[N(()=>{var y;return(y=u.default)==null?void 0:y.call(u)})],6)],6)):(v(),T(Se,oe({key:3,themeOverrides:p.peerOverrides.Scrollbar,theme:p.peers.Scrollbar},b,{class:`${t}-drawer-body`,contentClass:[`${t}-drawer-body-content-wrapper`,$],contentStyle:k}),fe(u),1040,["themeOverrides","theme","class","contentClass","contentStyle"])),u.footer?(v(),j("div",{key:4,class:F([`${t}-drawer-footer`,V]),style:Q(l),role:"none"},[N(()=>u.footer())],6)):N(()=>null)],2)}});const Vt={class:"toolbar"},Jt={__name:"SitesView",setup(e){const t=bt(),a=vt(),p=_([]),g=_(!1),w=_(!1),$=_(!1),k=_(""),h=_(null),C=_(""),V=[{label:"Static",value:"static"},{label:"PHP",value:"php"},{label:"Reverse proxy",value:"proxy"}],l=we({name:"",site_type:"static",proxy_target:"",php_version:"8.1",root:"",note:""}),b=we({run_path:"",index_files:"",proxy_target:"",php_version:"",note:""});async function m(){g.value=!0;try{p.value=await I("/sites")}finally{g.value=!1}}async function u(n,r){try{await n(),r&&t.success(r),await m()}catch(o){t.error(o.message)}}function y(){const n={name:l.name.trim(),site_type:l.site_type,domains:[l.name.trim()],root:l.root.trim(),note:l.note,proxy_target:l.site_type==="proxy"?l.proxy_target.trim():"",php_version:l.site_type==="php"?l.php_version.trim():""};u(async()=>{await I("/sites",{method:"POST",body:n}),w.value=!1,l.name="",l.proxy_target="",l.root="",l.note=""},"Site created")}async function S(n){h.value=await I(`/sites/${n.id}`),Object.assign(b,{run_path:h.value.run_path,index_files:h.value.index_files,proxy_target:h.value.proxy_target,php_version:h.value.php_version,note:h.value.note})}function z(){u(async()=>{h.value=await I(`/sites/${h.value.id}`,{method:"PATCH",body:{...b}})},"Site updated")}function W(){const n=C.value.trim();n&&u(async()=>{await I(`/sites/${h.value.id}/domains`,{method:"POST",body:{name:n}}),h.value=await I(`/sites/${h.value.id}`),C.value=""},"Domain added")}function R(n){a.info({title:`Issue a certificate for ${n.name}`,content:"Let's Encrypt must be able to reach this domain over port 80.",positiveText:"Issue",negativeText:"Cancel",onPositiveClick:()=>u(()=>I(`/ssl/${n.id}/issue`,{method:"POST",body:{domains:n.domains,force_https:!0}}),"Certificate issued")})}function X(n){const r=_(!1);a.warning({title:`Delete ${n.name}`,content:()=>U(mt,{checked:r.value,"onUpdate:checked":o=>r.value=o},{default:()=>"Also delete the site directory"}),positiveText:"Delete",negativeText:"Cancel",onPositiveClick:()=>u(()=>I(`/sites/${n.id}`,{method:"DELETE",params:{remove_files:r.value}}),"Site deleted")})}async function P(n){const r=await I(`/sites/${n.id}/config`);k.value=r.content||r.rendered,$.value=!0}const d=[{title:"Name",key:"name",render:n=>U(O,{text:!0,onClick:()=>S(n)},{default:()=>n.name})},{title:"Type",key:"site_type",width:110,render:n=>U(J,{size:"small",bordered:!1},{default:()=>n.site_type})},{title:"Domains",key:"domains",render:n=>n.domains.join(", ")},{title:"SSL",key:"ssl_enabled",width:90,render:n=>U(J,{size:"small",bordered:!1,type:n.ssl_enabled?"success":"default"},{default:()=>n.ssl_enabled?"on":"off"})},{title:"Status",key:"enabled",width:110,render:n=>U(J,{size:"small",bordered:!1,type:n.enabled?"success":"warning"},{default:()=>n.enabled?"serving":"parked"})},{title:"Created",key:"created_at",width:180,render:n=>gt(n.created_at)},{title:"Actions",key:"actions",width:300,render:n=>U(se,{size:6},{default:()=>[U(O,{size:"tiny",secondary:!0,onClick:()=>u(()=>I(`/sites/${n.id}/${n.enabled?"stop":"start"}`,{method:"POST"}))},{default:()=>n.enabled?"stop":"start"}),U(O,{size:"tiny",secondary:!0,onClick:()=>R(n)},{default:()=>"ssl"}),U(O,{size:"tiny",secondary:!0,onClick:()=>P(n)},{default:()=>"config"}),U(O,{size:"tiny",secondary:!0,onClick:()=>u(()=>I(`/backups/site/${n.id}`,{method:"POST"}),"Backup created")},{default:()=>"backup"}),U(O,{size:"tiny",type:"error",secondary:!0,onClick:()=>X(n)},{default:()=>"delete"})]})}];return $e(m),(n,r)=>(v(),j("div",null,[de("div",Vt,[s(i(O),{type:"primary",onClick:r[0]||(r[0]=o=>w.value=!0)},{default:f(()=>[...r[17]||(r[17]=[G("Add site",-1)])]),_:1}),s(i(O),{secondary:"",onClick:m},{default:f(()=>[...r[18]||(r[18]=[G("Refresh",-1)])]),_:1})]),s(i(lt),{size:"small"},{default:f(()=>[s(i(ht),{columns:d,data:p.value,loading:g.value,bordered:!1,size:"small"},null,8,["data","loading"])]),_:1}),s(i(ye),{show:w.value,"onUpdate:show":r[8]||(r[8]=o=>w.value=o),preset:"card",title:"Add site",style:{width:"520px"}},{footer:f(()=>[s(i(se),{justify:"end"},{default:f(()=>[s(i(O),{onClick:r[7]||(r[7]=o=>w.value=!1)},{default:f(()=>[...r[19]||(r[19]=[G("Cancel",-1)])]),_:1}),s(i(O),{type:"primary",onClick:y},{default:f(()=>[...r[20]||(r[20]=[G("Create",-1)])]),_:1})]),_:1})]),default:f(()=>[s(i(pe),null,{default:f(()=>[s(i(H),{label:"Domain"},{default:f(()=>[s(i(L),{value:l.name,"onUpdate:value":r[1]||(r[1]=o=>l.name=o),placeholder:"example.com"},null,8,["value"])]),_:1}),s(i(H),{label:"Type"},{default:f(()=>[s(i(ft),{value:l.site_type,"onUpdate:value":r[2]||(r[2]=o=>l.site_type=o),options:V},null,8,["value"])]),_:1}),l.site_type==="proxy"?(v(),T(i(H),{key:0,label:"Upstream"},{default:f(()=>[s(i(L),{value:l.proxy_target,"onUpdate:value":r[3]||(r[3]=o=>l.proxy_target=o),placeholder:"http://127.0.0.1:3000"},null,8,["value"])]),_:1})):Z("",!0),l.site_type==="php"?(v(),T(i(H),{key:1,label:"PHP version"},{default:f(()=>[s(i(L),{value:l.php_version,"onUpdate:value":r[4]||(r[4]=o=>l.php_version=o),placeholder:"8.1"},null,8,["value"])]),_:1})):Z("",!0),s(i(H),{label:"Document root"},{default:f(()=>[s(i(L),{value:l.root,"onUpdate:value":r[5]||(r[5]=o=>l.root=o),placeholder:"leave empty for /www/wwwroot/<domain>"},null,8,["value"])]),_:1}),s(i(H),{label:"Note"},{default:f(()=>[s(i(L),{value:l.note,"onUpdate:value":r[6]||(r[6]=o=>l.note=o)},null,8,["value"])]),_:1})]),_:1})]),_:1},8,["show"]),s(i(ye),{show:$.value,"onUpdate:show":r[9]||(r[9]=o=>$.value=o),preset:"card",title:"nginx configuration",style:{width:"760px"}},{default:f(()=>[s(i(xt),{code:k.value,language:"nginx","word-wrap":"",class:"log-pane"},null,8,["code"])]),_:1},8,["show"]),s(i(Lt),{show:!!h.value,width:520,"onUpdate:show":r[16]||(r[16]=o=>h.value=null)},{default:f(()=>[h.value?(v(),T(i(Wt),{key:0,title:h.value.name,closable:""},{footer:f(()=>[s(i(O),{type:"primary",onClick:z},{default:f(()=>[...r[22]||(r[22]=[G("Save",-1)])]),_:1})]),default:f(()=>[s(i(pe),null,{default:f(()=>[s(i(H),{label:"Run path"},{default:f(()=>[s(i(L),{value:b.run_path,"onUpdate:value":r[10]||(r[10]=o=>b.run_path=o),placeholder:"public"},null,8,["value"])]),_:1}),s(i(H),{label:"Index files"},{default:f(()=>[s(i(L),{value:b.index_files,"onUpdate:value":r[11]||(r[11]=o=>b.index_files=o)},null,8,["value"])]),_:1}),h.value.site_type==="proxy"?(v(),T(i(H),{key:0,label:"Upstream"},{default:f(()=>[s(i(L),{value:b.proxy_target,"onUpdate:value":r[12]||(r[12]=o=>b.proxy_target=o)},null,8,["value"])]),_:1})):Z("",!0),h.value.site_type==="php"?(v(),T(i(H),{key:1,label:"PHP version"},{default:f(()=>[s(i(L),{value:b.php_version,"onUpdate:value":r[13]||(r[13]=o=>b.php_version=o)},null,8,["value"])]),_:1})):Z("",!0),s(i(H),{label:"Note"},{default:f(()=>[s(i(L),{value:b.note,"onUpdate:value":r[14]||(r[14]=o=>b.note=o)},null,8,["value"])]),_:1}),s(i(H),{label:"Domains"},{default:f(()=>[s(i(se),{vertical:"",style:{width:"100%"}},{default:f(()=>[(v(!0),j(ue,null,dt(h.value.domains,o=>(v(),T(i(J),{key:o,size:"small",bordered:!1},{default:f(()=>[G(ut(o),1)]),_:2},1024))),128)),s(i(ct),null,{default:f(()=>[s(i(L),{value:C.value,"onUpdate:value":r[15]||(r[15]=o=>C.value=o),placeholder:"www.example.com"},null,8,["value"]),s(i(O),{onClick:W},{default:f(()=>[...r[21]||(r[21]=[G("Add",-1)])]),_:1})]),_:1})]),_:1})]),_:1})]),_:1})]),_:1},8,["title"])):Z("",!0)]),_:1},8,["show"])]))}};export{Jt as default};
