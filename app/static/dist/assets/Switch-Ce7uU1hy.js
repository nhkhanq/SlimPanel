import{aD as ve,bT as ge,bU as we,a2 as H,a4 as a,aX as Y,a0 as j,a3 as s,aF as q,d as me,a6 as Q,bV as O,o as b,c as _,a as C,D as l,bi as k,z as n,b as G,A as J,M as pe,a_ as ye,r as E,aa as xe,ac as ke,g as K,ae as L,bW as Se,H as Be,aT as _e,am as S,bM as X,bX as c,ag as Ce}from"./index-DE04bkTa.js";function ze(e){const{primaryColor:d,opacityDisabled:f,borderRadius:o,textColor3:v}=e;return{...ge,iconColor:v,textColor:"white",loadingColor:d,opacityDisabled:f,railColor:"rgba(0, 0, 0, .14)",railColorActive:d,buttonBoxShadow:"0 1px 4px 0 rgba(0, 0, 0, 0.3), inset 0 0 1px 0 rgba(0, 0, 0, 0.05)",buttonColor:"#FFF",railBorderRadiusSmall:o,railBorderRadiusMedium:o,railBorderRadiusLarge:o,buttonBorderRadiusSmall:o,buttonBorderRadiusMedium:o,buttonBorderRadiusLarge:o,boxShadowFocus:`0 0 0 2px ${we(d,{alpha:.2})}`}}const $e={common:ve,self:ze};var Re=H("switch",`
 height: var(--n-height);
 min-width: var(--n-width);
 vertical-align: middle;
 user-select: none;
 -webkit-user-select: none;
 display: inline-flex;
 outline: none;
 justify-content: center;
 align-items: center;
`,[a("children-placeholder",`
 height: var(--n-rail-height);
 display: flex;
 flex-direction: column;
 overflow: hidden;
 pointer-events: none;
 visibility: hidden;
 `),a("rail-placeholder",`
 display: flex;
 flex-wrap: none;
 `),a("button-placeholder",`
 width: calc(1.75 * var(--n-rail-height));
 height: var(--n-rail-height);
 `),H("base-loading",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 font-size: calc(var(--n-button-width) - 4px);
 color: var(--n-loading-color);
 transition: color .3s var(--n-bezier);
 `,[Y({left:"50%",top:"50%",originalTransform:"translateX(-50%) translateY(-50%)"})]),a("checked, unchecked",`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 box-sizing: border-box;
 position: absolute;
 white-space: nowrap;
 top: 0;
 bottom: 0;
 display: flex;
 align-items: center;
 line-height: 1;
 `),a("checked",`
 right: 0;
 padding-right: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),a("unchecked",`
 left: 0;
 justify-content: flex-end;
 padding-left: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),j("&:focus",[a("rail",`
 box-shadow: var(--n-box-shadow-focus);
 `)]),s("round",[a("rail","border-radius: calc(var(--n-rail-height) / 2);",[a("button","border-radius: calc(var(--n-button-height) / 2);")])]),q("disabled",[q("icon",[s("rubber-band",[s("pressed",[a("rail",[a("button","max-width: var(--n-button-width-pressed);")])]),a("rail",[j("&:active",[a("button","max-width: var(--n-button-width-pressed);")])]),s("active",[s("pressed",[a("rail",[a("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])]),a("rail",[j("&:active",[a("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])])])])])]),s("active",[a("rail",[a("button","left: calc(100% - var(--n-button-width) - var(--n-offset))")])]),a("rail",`
 overflow: hidden;
 height: var(--n-rail-height);
 min-width: var(--n-rail-width);
 border-radius: var(--n-rail-border-radius);
 cursor: pointer;
 position: relative;
 transition:
 opacity .3s var(--n-bezier),
 background .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-rail-color);
 `,[a("button-icon",`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 font-size: calc(var(--n-button-height) - 4px);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 display: flex;
 justify-content: center;
 align-items: center;
 line-height: 1;
 `,[Y()]),a("button",`
 align-items: center; 
 top: var(--n-offset);
 left: var(--n-offset);
 height: var(--n-button-height);
 width: var(--n-button-width-pressed);
 max-width: var(--n-button-width);
 border-radius: var(--n-button-border-radius);
 background-color: var(--n-button-color);
 box-shadow: var(--n-button-box-shadow);
 box-sizing: border-box;
 cursor: inherit;
 content: "";
 position: absolute;
 transition:
 background-color .3s var(--n-bezier),
 left .3s var(--n-bezier),
 opacity .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 `)]),s("active",[a("rail","background-color: var(--n-rail-color-active);")]),s("loading",[a("rail",`
 cursor: wait;
 `)]),s("disabled",[a("rail",`
 cursor: not-allowed;
 opacity: .5;
 `)])]);const Ve=["aria-checked","tabindex","onClick","onFocus","onBlur","onKeyup","onKeydown"],Fe={...Q.props,size:String,value:{type:[String,Number,Boolean],default:void 0},loading:Boolean,defaultValue:{type:[String,Number,Boolean],default:!1},disabled:{type:Boolean,default:void 0},round:{type:Boolean,default:!0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],checkedValue:{type:[String,Number,Boolean],default:!0},uncheckedValue:{type:[String,Number,Boolean],default:!1},railStyle:Function,rubberBand:{type:Boolean,default:!0},spinProps:Object,onChange:[Function,Array]};let F;var De=me({name:"Switch",props:Fe,slots:Object,setup(e){F===void 0&&(typeof CSS<"u"?typeof CSS.supports<"u"?F=CSS.supports("width","max(1px)"):F=!1:F=!0);const{mergedClsPrefixRef:d,inlineThemeDisabled:f,mergedComponentPropsRef:o}=pe(e),v=Q("Switch","-switch",Re,$e,e,d),g=ye(e,{mergedSize(t){var y,x;if(e.size!==void 0)return e.size;if(t)return t.mergedSize.value;const p=(x=(y=o==null?void 0:o.value)==null?void 0:y.Switch)==null?void 0:x.size;return p||"medium"}}),{mergedSizeRef:z,mergedDisabledRef:w}=g,$=E(e.defaultValue),T=Ce(e,"value"),m=xe(T,$),D=K(()=>m.value===e.checkedValue),i=E(!1),r=E(!1),R=K(()=>{const{railStyle:t}=e;if(t)return t({focused:r.value,checked:D.value})});function P(t){const{"onUpdate:value":p,onChange:y,onUpdateValue:x}=e,{nTriggerFormInput:M,nTriggerFormChange:W}=g;p&&L(p,t),x&&L(x,t),y&&L(y,t),$.value=t,M(),W()}function Z(){const{nTriggerFormFocus:t}=g;t()}function ee(){const{nTriggerFormBlur:t}=g;t()}function te(){e.loading||w.value||(m.value!==e.checkedValue?P(e.checkedValue):P(e.uncheckedValue))}function ae(){r.value=!0,Z()}function ie(){r.value=!1,ee(),i.value=!1}function oe(t){e.loading||w.value||t.key===" "&&(m.value!==e.checkedValue?P(e.checkedValue):P(e.uncheckedValue),i.value=!1)}function ne(t){e.loading||w.value||t.key===" "&&(t.preventDefault(),i.value=!0)}const I=K(()=>{const{value:t}=z,{self:{opacityDisabled:p,railColor:y,railColorActive:x,buttonBoxShadow:M,buttonColor:W,boxShadowFocus:re,loadingColor:le,textColor:se,iconColor:ce,[S("buttonHeight",t)]:u,[S("buttonWidth",t)]:de,[S("buttonWidthPressed",t)]:ue,[S("railHeight",t)]:h,[S("railWidth",t)]:V,[S("railBorderRadius",t)]:he,[S("buttonBorderRadius",t)]:be},common:{cubicBezierEaseInOut:fe}}=v.value;let U,A,N;return F?(U=`calc((${h} - ${u}) / 2)`,A=`max(${h}, ${u})`,N=`max(${V}, calc(${V} + ${u} - ${h}))`):(U=X((c(h)-c(u))/2),A=X(Math.max(c(h),c(u))),N=c(h)>c(u)?V:X(c(V)+c(u)-c(h))),{"--n-bezier":fe,"--n-button-border-radius":be,"--n-button-box-shadow":M,"--n-button-color":W,"--n-button-width":de,"--n-button-width-pressed":ue,"--n-button-height":u,"--n-height":A,"--n-offset":U,"--n-opacity-disabled":p,"--n-rail-border-radius":he,"--n-rail-color":y,"--n-rail-color-active":x,"--n-rail-height":h,"--n-rail-width":V,"--n-width":N,"--n-box-shadow-focus":re,"--n-loading-color":le,"--n-text-color":se,"--n-icon-color":ce}}),B=f?ke("switch",K(()=>z.value[0]),I,e):void 0;return{handleClick:te,handleBlur:ie,handleFocus:ae,handleKeyup:oe,handleKeydown:ne,mergedRailStyle:R,pressed:i,mergedClsPrefix:d,mergedValue:m,checked:D,mergedDisabled:w,cssVars:f?void 0:I,themeClass:B==null?void 0:B.themeClass,onRender:B==null?void 0:B.onRender}},render(){const{mergedClsPrefix:e,mergedDisabled:d,checked:f,mergedRailStyle:o,onRender:v,$slots:g}=this;v==null||v();const{checked:z,unchecked:w,icon:$,"checked-icon":T,"unchecked-icon":m}=g,D=!(O($)&&O(T)&&O(m));return b(),_("div",{role:"switch","aria-checked":f,class:n([`${e}-switch`,this.themeClass,D&&`${e}-switch--icon`,f&&`${e}-switch--active`,d&&`${e}-switch--disabled`,this.round&&`${e}-switch--round`,this.loading&&`${e}-switch--loading`,this.pressed&&`${e}-switch--pressed`,this.rubberBand&&`${e}-switch--rubber-band`]),tabindex:this.mergedDisabled?void 0:0,style:J(this.cssVars),onClick:this.handleClick,onFocus:this.handleFocus,onBlur:this.handleBlur,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},[C("div",{class:n(`${e}-switch__rail`),"aria-hidden":"true",style:J(o)},[l(()=>k(z,i=>k(w,r=>i||r?(b(),_("div",{key:4,"aria-hidden":!0,class:n(`${e}-switch__children-placeholder`)},[C("div",{class:n(`${e}-switch__rail-placeholder`)},[C("div",{class:n(`${e}-switch__button-placeholder`)},null,2),l(()=>i)],2),C("div",{class:n(`${e}-switch__rail-placeholder`)},[C("div",{class:n(`${e}-switch__button-placeholder`)},null,2),l(()=>r)],2)],2)):null))),C("div",{class:n(`${e}-switch__button`)},[l(()=>k($,i=>k(T,r=>k(m,R=>(b(),G(_e,null,{default:()=>this.loading?(b(),G(Se,Be({key:"loading",clsPrefix:e,strokeWidth:20},this.spinProps),null,16,["clsPrefix"])):this.checked&&(r||i)?(b(),_("div",{class:n(`${e}-switch__button-icon`),key:r?"checked-icon":"icon"},[l(()=>r||i)],2)):!this.checked&&(R||i)?(b(),_("div",{class:n(`${e}-switch__button-icon`),key:R?"unchecked-icon":"icon"},[l(()=>R||i)],2)):null},1024)))))),l(()=>k(z,i=>i&&(b(),_("div",{key:"checked",class:n(`${e}-switch__checked`)},[l(()=>i)],2)))),l(()=>k(w,i=>i&&(b(),_("div",{key:"unchecked",class:n(`${e}-switch__unchecked`)},[l(()=>i)],2))))],2)],6)],46,Ve)}});export{De as S};
