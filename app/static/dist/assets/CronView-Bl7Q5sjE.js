import{T as _e}from"./Tag-aKNUfOMt.js";import{R as ze,ba as Be,bb as Re,U as ae,X as n,aV as oe,T as q,W as x,aF as ne,d as Ve,Y as de,bc as G,b as S,e as j,C as $,n as p,bd as T,Z as f,k as ie,f as le,u as Fe,aY as Te,r as U,aj as De,a0 as Pe,c as W,am as J,be as je,m as Ue,aS as Ne,b8 as D,p as Z,bf as C,A as Ae,q as Me,N as r,B as u,E as l,O as P,L as M,P as B,G as Oe,ar as Ee,as as Q,at as ee,S as re,au as se,D as Ke,j as O,av as We}from"./index-If5Ucjf1.js";import{D as Le}from"./DataTable-CEHI4og4.js";import{u as Ie}from"./composables-Dkuxj35u.js";import{u as Ye}from"./use-message-BJ_aNqR3.js";import{a as Xe}from"./format-CuWqBo7j.js";function He(t){const{primaryColor:b,opacityDisabled:w,borderRadius:d,textColor3:v}=t;return{...Be,iconColor:v,textColor:"white",loadingColor:b,opacityDisabled:w,railColor:"rgba(0, 0, 0, .14)",railColorActive:b,buttonBoxShadow:"0 1px 4px 0 rgba(0, 0, 0, 0.3), inset 0 0 1px 0 rgba(0, 0, 0, 0.05)",buttonColor:"#FFF",railBorderRadiusSmall:d,railBorderRadiusMedium:d,railBorderRadiusLarge:d,buttonBorderRadiusSmall:d,buttonBorderRadiusMedium:d,buttonBorderRadiusLarge:d,boxShadowFocus:`0 0 0 2px ${Re(b,{alpha:.2})}`}}const qe={common:ze,self:He};var Ge=ae("switch",`
 height: var(--n-height);
 min-width: var(--n-width);
 vertical-align: middle;
 user-select: none;
 -webkit-user-select: none;
 display: inline-flex;
 outline: none;
 justify-content: center;
 align-items: center;
`,[n("children-placeholder",`
 height: var(--n-rail-height);
 display: flex;
 flex-direction: column;
 overflow: hidden;
 pointer-events: none;
 visibility: hidden;
 `),n("rail-placeholder",`
 display: flex;
 flex-wrap: none;
 `),n("button-placeholder",`
 width: calc(1.75 * var(--n-rail-height));
 height: var(--n-rail-height);
 `),ae("base-loading",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 font-size: calc(var(--n-button-width) - 4px);
 color: var(--n-loading-color);
 transition: color .3s var(--n-bezier);
 `,[oe({left:"50%",top:"50%",originalTransform:"translateX(-50%) translateY(-50%)"})]),n("checked, unchecked",`
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
 `),n("checked",`
 right: 0;
 padding-right: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),n("unchecked",`
 left: 0;
 justify-content: flex-end;
 padding-left: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),q("&:focus",[n("rail",`
 box-shadow: var(--n-box-shadow-focus);
 `)]),x("round",[n("rail","border-radius: calc(var(--n-rail-height) / 2);",[n("button","border-radius: calc(var(--n-button-height) / 2);")])]),ne("disabled",[ne("icon",[x("rubber-band",[x("pressed",[n("rail",[n("button","max-width: var(--n-button-width-pressed);")])]),n("rail",[q("&:active",[n("button","max-width: var(--n-button-width-pressed);")])]),x("active",[x("pressed",[n("rail",[n("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])]),n("rail",[q("&:active",[n("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])])])])])]),x("active",[n("rail",[n("button","left: calc(100% - var(--n-button-width) - var(--n-offset))")])]),n("rail",`
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
 `,[n("button-icon",`
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
 `,[oe()]),n("button",`
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
 `)]),x("active",[n("rail","background-color: var(--n-rail-color-active);")]),x("loading",[n("rail",`
 cursor: wait;
 `)]),x("disabled",[n("rail",`
 cursor: not-allowed;
 opacity: .5;
 `)])]);const Je=["aria-checked","tabindex","onClick","onFocus","onBlur","onKeyup","onKeydown"],Ze={...de.props,size:String,value:{type:[String,Number,Boolean],default:void 0},loading:Boolean,defaultValue:{type:[String,Number,Boolean],default:!1},disabled:{type:Boolean,default:void 0},round:{type:Boolean,default:!0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],checkedValue:{type:[String,Number,Boolean],default:!0},uncheckedValue:{type:[String,Number,Boolean],default:!1},railStyle:Function,rubberBand:{type:Boolean,default:!0},spinProps:Object,onChange:[Function,Array]};let K;var Qe=Ve({name:"Switch",props:Ze,slots:Object,setup(t){K===void 0&&(typeof CSS<"u"?typeof CSS.supports<"u"?K=CSS.supports("width","max(1px)"):K=!1:K=!0);const{mergedClsPrefixRef:b,inlineThemeDisabled:w,mergedComponentPropsRef:d}=Fe(t),v=de("Switch","-switch",Ge,qe,t,b),c=Te(t,{mergedSize(o){var V,F;if(t.size!==void 0)return t.size;if(o)return o.mergedSize.value;const R=(F=(V=d==null?void 0:d.value)==null?void 0:V.Switch)==null?void 0:F.size;return R||"medium"}}),{mergedSizeRef:h,mergedDisabledRef:s}=c,m=U(t.defaultValue),y=Ae(t,"value"),k=De(y,m),N=W(()=>k.value===t.checkedValue),a=U(!1),e=U(!1),g=W(()=>{const{railStyle:o}=t;if(o)return o({focused:e.value,checked:N.value})});function i(o){const{"onUpdate:value":R,onChange:V,onUpdateValue:F}=t,{nTriggerFormInput:L,nTriggerFormChange:I}=c;R&&J(R,o),F&&J(F,o),V&&J(V,o),m.value=o,L(),I()}function ue(){const{nTriggerFormFocus:o}=c;o()}function ce(){const{nTriggerFormBlur:o}=c;o()}function he(){t.loading||s.value||(k.value!==t.checkedValue?i(t.checkedValue):i(t.uncheckedValue))}function fe(){e.value=!0,ue()}function be(){e.value=!1,ce(),a.value=!1}function ve(o){t.loading||s.value||o.key===" "&&(k.value!==t.checkedValue?i(t.checkedValue):i(t.uncheckedValue),a.value=!1)}function me(o){t.loading||s.value||o.key===" "&&(o.preventDefault(),a.value=!0)}const te=W(()=>{const{value:o}=h,{self:{opacityDisabled:R,railColor:V,railColorActive:F,buttonBoxShadow:L,buttonColor:I,boxShadowFocus:ge,loadingColor:pe,textColor:we,iconColor:ye,[D("buttonHeight",o)]:_,[D("buttonWidth",o)]:ke,[D("buttonWidthPressed",o)]:xe,[D("railHeight",o)]:z,[D("railWidth",o)]:E,[D("railBorderRadius",o)]:Ce,[D("buttonBorderRadius",o)]:Se},common:{cubicBezierEaseInOut:$e}}=v.value;let Y,X,H;return K?(Y=`calc((${z} - ${_}) / 2)`,X=`max(${z}, ${_})`,H=`max(${E}, calc(${E} + ${_} - ${z}))`):(Y=Z((C(z)-C(_))/2),X=Z(Math.max(C(z),C(_))),H=C(z)>C(_)?E:Z(C(E)+C(_)-C(z))),{"--n-bezier":$e,"--n-button-border-radius":Se,"--n-button-box-shadow":L,"--n-button-color":I,"--n-button-width":ke,"--n-button-width-pressed":xe,"--n-button-height":_,"--n-height":X,"--n-offset":Y,"--n-opacity-disabled":R,"--n-rail-border-radius":Ce,"--n-rail-color":V,"--n-rail-color-active":F,"--n-rail-height":z,"--n-rail-width":E,"--n-width":H,"--n-box-shadow-focus":ge,"--n-loading-color":pe,"--n-text-color":we,"--n-icon-color":ye}}),A=w?Pe("switch",W(()=>h.value[0]),te,t):void 0;return{handleClick:he,handleBlur:be,handleFocus:fe,handleKeyup:ve,handleKeydown:me,mergedRailStyle:g,pressed:a,mergedClsPrefix:b,mergedValue:k,checked:N,mergedDisabled:s,cssVars:w?void 0:te,themeClass:A==null?void 0:A.themeClass,onRender:A==null?void 0:A.onRender}},render(){const{mergedClsPrefix:t,mergedDisabled:b,checked:w,mergedRailStyle:d,onRender:v,$slots:c}=this;v==null||v();const{checked:h,unchecked:s,icon:m,"checked-icon":y,"unchecked-icon":k}=c,N=!(G(m)&&G(y)&&G(k));return S(),j("div",{role:"switch","aria-checked":w,class:f([`${t}-switch`,this.themeClass,N&&`${t}-switch--icon`,w&&`${t}-switch--active`,b&&`${t}-switch--disabled`,this.round&&`${t}-switch--round`,this.loading&&`${t}-switch--loading`,this.pressed&&`${t}-switch--pressed`,this.rubberBand&&`${t}-switch--rubber-band`]),tabindex:this.mergedDisabled?void 0:0,style:le(this.cssVars),onClick:this.handleClick,onFocus:this.handleFocus,onBlur:this.handleBlur,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},[$("div",{class:f(`${t}-switch__rail`),"aria-hidden":"true",style:le(d)},[p(()=>T(h,a=>T(s,e=>a||e?(S(),j("div",{key:4,"aria-hidden":!0,class:f(`${t}-switch__children-placeholder`)},[$("div",{class:f(`${t}-switch__rail-placeholder`)},[$("div",{class:f(`${t}-switch__button-placeholder`)},null,2),p(()=>a)],2),$("div",{class:f(`${t}-switch__rail-placeholder`)},[$("div",{class:f(`${t}-switch__button-placeholder`)},null,2),p(()=>e)],2)],2)):null))),$("div",{class:f(`${t}-switch__button`)},[p(()=>T(m,a=>T(y,e=>T(k,g=>(S(),ie(Ne,null,{default:()=>this.loading?(S(),ie(je,Ue({key:"loading",clsPrefix:t,strokeWidth:20},this.spinProps),null,16,["clsPrefix"])):this.checked&&(e||a)?(S(),j("div",{class:f(`${t}-switch__button-icon`),key:e?"checked-icon":"icon"},[p(()=>e||a)],2)):!this.checked&&(g||a)?(S(),j("div",{class:f(`${t}-switch__button-icon`),key:g?"unchecked-icon":"icon"},[p(()=>g||a)],2)):null},1024)))))),p(()=>T(h,a=>a&&(S(),j("div",{key:"checked",class:f(`${t}-switch__checked`)},[p(()=>a)],2)))),p(()=>T(s,a=>a&&(S(),j("div",{key:"unchecked",class:f(`${t}-switch__unchecked`)},[p(()=>a)],2))))],2)],6)],46,Je)}});const et={class:"toolbar"},tt={class:"mono log-pane"},st={__name:"CronView",setup(t){const b=Ye(),w=Ie(),d=U([]),v=U(!1),c=U(!1),h=U(null),s=We({name:"",schedule:"0 3 * * *",command:""});async function m(){v.value=!0;try{d.value=await P("/cron")}finally{v.value=!1}}async function y(a,e){try{await a(),e&&b.success(e),await m()}catch(g){b.error(g.message)}}function k(){y(async()=>{await P("/cron",{method:"POST",body:{...s}}),c.value=!1,Object.assign(s,{name:"",schedule:"0 3 * * *",command:""})},"Job created")}const N=[{title:"Name",key:"name"},{title:"Schedule",key:"schedule",width:140,render:a=>O("code",{class:"mono"},a.schedule)},{title:"Command",key:"command",ellipsis:{tooltip:!0}},{title:"Last run",key:"last_run_at",width:160,render:a=>Xe(a.last_run_at)||"—"},{title:"Enabled",key:"enabled",width:90,render:a=>O(Qe,{value:a.enabled,size:"small","onUpdate:value":e=>y(()=>P(`/cron/${a.id}`,{method:"PATCH",body:{enabled:e}}))})},{title:"Actions",key:"actions",width:220,render:a=>O(re,{size:6},{default:()=>[O(B,{size:"tiny",secondary:!0,onClick:async()=>{const e=await P(`/cron/${a.id}/run`,{method:"POST"});h.value={title:a.name,text:e.message||"(no output)"},await m()}},{default:()=>"run now"}),O(B,{size:"tiny",secondary:!0,onClick:async()=>{const e=await P(`/cron/${a.id}/logs`);h.value={title:`${a.name} logs`,text:e.lines.join(`
`)||"(empty)"}}},{default:()=>"logs"}),O(B,{size:"tiny",type:"error",secondary:!0,onClick:()=>w.warning({title:`Delete ${a.name}`,positiveText:"Delete",negativeText:"Cancel",onPositiveClick:()=>y(()=>P(`/cron/${a.id}`,{method:"DELETE"}),"Deleted")})},{default:()=>"delete"})]})}];return Me(m),(a,e)=>{var g;return S(),j("div",null,[$("div",et,[r(l(B),{type:"primary",onClick:e[0]||(e[0]=i=>c.value=!0)},{default:u(()=>[...e[8]||(e[8]=[M("Add job",-1)])]),_:1}),r(l(B),{secondary:"",onClick:m},{default:u(()=>[...e[9]||(e[9]=[M("Refresh",-1)])]),_:1}),r(l(B),{secondary:"",onClick:e[1]||(e[1]=i=>y(()=>l(P)("/cron/sync",{method:"POST"}),"Crontab written"))},{default:u(()=>[...e[10]||(e[10]=[M(" Sync crontab ",-1)])]),_:1}),e[12]||(e[12]=$("span",{class:"spacer"},null,-1)),r(l(_e),{size:"small",bordered:!1},{default:u(()=>[...e[11]||(e[11]=[M("written to /etc/cron.d/slimpanel",-1)])]),_:1})]),r(l(Oe),{size:"small"},{default:u(()=>[r(l(Le),{columns:N,data:d.value,loading:v.value,bordered:!1,size:"small"},null,8,["data","loading"])]),_:1}),r(l(se),{show:c.value,"onUpdate:show":e[6]||(e[6]=i=>c.value=i),preset:"card",title:"Add cron job",style:{width:"520px"}},{footer:u(()=>[r(l(re),{justify:"end"},{default:u(()=>[r(l(B),{onClick:e[5]||(e[5]=i=>c.value=!1)},{default:u(()=>[...e[13]||(e[13]=[M("Cancel",-1)])]),_:1}),r(l(B),{type:"primary",onClick:k},{default:u(()=>[...e[14]||(e[14]=[M("Create",-1)])]),_:1})]),_:1})]),default:u(()=>[r(l(Ee),null,{default:u(()=>[r(l(Q),{label:"Name"},{default:u(()=>[r(l(ee),{value:s.name,"onUpdate:value":e[2]||(e[2]=i=>s.name=i),placeholder:"nightly backup"},null,8,["value"])]),_:1}),r(l(Q),{label:"Schedule"},{default:u(()=>[r(l(ee),{value:s.schedule,"onUpdate:value":e[3]||(e[3]=i=>s.schedule=i),placeholder:"0 3 * * *"},null,8,["value"])]),_:1}),r(l(Q),{label:"Command"},{default:u(()=>[r(l(ee),{value:s.command,"onUpdate:value":e[4]||(e[4]=i=>s.command=i),type:"textarea",rows:3},null,8,["value"])]),_:1})]),_:1})]),_:1},8,["show"]),r(l(se),{show:!!h.value,preset:"card",title:(g=h.value)==null?void 0:g.title,style:{width:"760px"},"onUpdate:show":e[7]||(e[7]=i=>h.value=null)},{default:u(()=>{var i;return[$("pre",tt,Ke((i=h.value)==null?void 0:i.text),1)]}),_:1},8,["show","title"])])}}};export{st as default};
