import{a0 as S,a2 as t,aF as oe,a3 as B,a4 as G,b4 as re,b5 as le,d as H,a6 as ee,bp as ne,o as b,c as h,D as m,A as z,z as p,a as M,bq as ae,br as se,M as ie,bs as de,ac as ce,g as j,al as pe,am as L,e as i,w as g,u as s,b as be,f as ue,r as U,p as O,at as me,ap as ge,aq as q,ao as K,s as he,B as W,C as J,F as fe,m as ve,t as Q,an as ye,k as we,q as X,T as Y}from"./index-DE04bkTa.js";import{C as xe,D as Se}from"./DataTable-Djn-MRI4.js";import{u as Ce}from"./composables-BXYo2XIb.js";import{u as ze}from"./use-message-BICuTCqS.js";import"./Select-DtDe4YEc.js";function Z(l,y="default",f=[]){const{children:r}=l;if(r!==null&&typeof r=="object"&&!Array.isArray(r)){const a=r[y];if(typeof a=="function")return a()}return f}var _e=S([t("descriptions",{fontSize:"var(--n-font-size)"},[t("descriptions-separator",`
 display: inline-block;
 margin: 0 8px 0 2px;
 `),t("descriptions-table-wrapper",[t("descriptions-table",[t("descriptions-table-row",[t("descriptions-table-header",{padding:"var(--n-th-padding)"}),t("descriptions-table-content",{padding:"var(--n-td-padding)"})])])]),oe("bordered",[t("descriptions-table-wrapper",[t("descriptions-table",[t("descriptions-table-row",[S("&:last-child",[t("descriptions-table-content",{paddingBottom:0})])])])])]),B("left-label-placement",[t("descriptions-table-content",[S("> *",{verticalAlign:"top"})])]),B("left-label-align",[S("th",{textAlign:"left"})]),B("center-label-align",[S("th",{textAlign:"center"})]),B("right-label-align",[S("th",{textAlign:"right"})]),B("bordered",[t("descriptions-table-wrapper",`
 border-radius: var(--n-border-radius);
 overflow: hidden;
 background: var(--n-merged-td-color);
 border: 1px solid var(--n-merged-border-color);
 `,[t("descriptions-table",[t("descriptions-table-row",[S("&:not(:last-child)",[t("descriptions-table-content",{borderBottom:"1px solid var(--n-merged-border-color)"}),t("descriptions-table-header",{borderBottom:"1px solid var(--n-merged-border-color)"})]),t("descriptions-table-header",`
 font-weight: 400;
 background-clip: padding-box;
 background-color: var(--n-merged-th-color);
 `,[S("&:not(:last-child)",{borderRight:"1px solid var(--n-merged-border-color)"})]),t("descriptions-table-content",[S("&:not(:last-child)",{borderRight:"1px solid var(--n-merged-border-color)"})])])])])]),t("descriptions-header",`
 font-weight: var(--n-th-font-weight);
 font-size: 18px;
 transition: color .3s var(--n-bezier);
 line-height: var(--n-line-height);
 margin-bottom: 16px;
 color: var(--n-title-text-color);
 `),t("descriptions-table-wrapper",`
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[t("descriptions-table",`
 width: 100%;
 border-collapse: separate;
 border-spacing: 0;
 box-sizing: border-box;
 `,[t("descriptions-table-row",`
 box-sizing: border-box;
 transition: border-color .3s var(--n-bezier);
 `,[t("descriptions-table-header",`
 font-weight: var(--n-th-font-weight);
 line-height: var(--n-line-height);
 display: table-cell;
 box-sizing: border-box;
 color: var(--n-th-text-color);
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `),t("descriptions-table-content",`
 vertical-align: top;
 line-height: var(--n-line-height);
 display: table-cell;
 box-sizing: border-box;
 color: var(--n-td-text-color);
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[G("content",`
 transition: color .3s var(--n-bezier);
 display: inline-block;
 color: var(--n-td-text-color);
 `)]),G("label",`
 font-weight: var(--n-th-font-weight);
 transition: color .3s var(--n-bezier);
 display: inline-block;
 margin-right: 14px;
 color: var(--n-th-text-color);
 `)])])])]),t("descriptions-table-wrapper",`
 --n-merged-th-color: var(--n-th-color);
 --n-merged-td-color: var(--n-td-color);
 --n-merged-border-color: var(--n-border-color);
 `),re(t("descriptions-table-wrapper",`
 --n-merged-th-color: var(--n-th-color-modal);
 --n-merged-td-color: var(--n-td-color-modal);
 --n-merged-border-color: var(--n-border-color-modal);
 `)),le(t("descriptions-table-wrapper",`
 --n-merged-th-color: var(--n-th-color-popover);
 --n-merged-td-color: var(--n-td-color-popover);
 --n-merged-border-color: var(--n-border-color-popover);
 `))]);const ke="DESCRIPTION_ITEM_FLAG";function Pe(l){return typeof l=="object"&&l&&!Array.isArray(l)?l.type&&l.type.DESCRIPTION_ITEM_FLAG:!1}const $e=["colspan"],Ie=["colspan"],Te=["colspan"],Ae=["colspan"],De={...ee.props,title:String,column:{type:Number,default:3},columns:Number,labelPlacement:{type:String,default:"top"},labelAlign:{type:String,default:"left"},separator:{type:String,default:":"},size:String,bordered:Boolean,labelClass:String,labelStyle:[Object,String],contentClass:String,contentStyle:[Object,String]};var Re=H({name:"Descriptions",props:De,slots:Object,setup(l){const{mergedClsPrefixRef:y,inlineThemeDisabled:f,mergedComponentPropsRef:r}=ie(l),a=j(()=>{var d,c;return l.size||((c=(d=r==null?void 0:r.value)==null?void 0:d.Descriptions)==null?void 0:c.size)||"medium"}),v=ee("Descriptions","-descriptions",_e,de,l,y),C=j(()=>{const{bordered:d}=l,c=a.value,{common:{cubicBezierEaseInOut:u},self:{titleTextColor:e,thColor:n,thColorModal:P,thColorPopover:V,thTextColor:F,thFontWeight:o,tdTextColor:$,tdColor:N,tdColorModal:x,tdColorPopover:_,borderColor:I,borderColorModal:T,borderColorPopover:k,borderRadius:A,lineHeight:D,[L("fontSize",c)]:R,[L(d?"thPaddingBordered":"thPadding",c)]:E,[L(d?"tdPaddingBordered":"tdPadding",c)]:te}}=v.value;return{"--n-title-text-color":e,"--n-th-padding":E,"--n-td-padding":te,"--n-font-size":R,"--n-bezier":u,"--n-th-font-weight":o,"--n-line-height":D,"--n-th-text-color":F,"--n-td-text-color":$,"--n-th-color":n,"--n-th-color-modal":P,"--n-th-color-popover":V,"--n-td-color":N,"--n-td-color-modal":x,"--n-td-color-popover":_,"--n-border-radius":A,"--n-border-color":I,"--n-border-color-modal":T,"--n-border-color-popover":k}}),w=f?ce("descriptions",j(()=>{let d="";const{bordered:c}=l;return c&&(d+="a"),d+=a.value[0],d}),C,l):void 0;return{mergedClsPrefix:y,cssVars:f?void 0:C,themeClass:w==null?void 0:w.themeClass,onRender:w==null?void 0:w.onRender,compitableColumn:pe(l,["columns","column"]),inlineThemeDisabled:f,mergedSize:a}},render(){const l=this.$slots.default,y=l?ne(l()):[];y.length;const{contentClass:f,labelClass:r,compitableColumn:a,labelPlacement:v,labelAlign:C,mergedSize:w,bordered:d,title:c,cssVars:u,mergedClsPrefix:e,separator:n,onRender:P}=this;P==null||P();const V=y.filter(o=>Pe(o)),F=V.reduce((o,$,N)=>{const x=$.props||{},_=V.length-1===N,I=["label"in x?x.label:Z($,"label")],T=[Z($)],k=x.span||1,A=o.span;o.span+=k;const D=x.labelStyle||x["label-style"]||this.labelStyle,R=x.contentStyle||x["content-style"]||this.contentStyle;if(v==="left")d?o.row.push((b(),h("th",{key:1,class:p([`${e}-descriptions-table-header`,r]),colspan:1,style:z(D)},[m(()=>I)],6)),(b(),h("td",{key:2,class:p([`${e}-descriptions-table-content`,f]),colspan:_?(a-A)*2+1:k*2-1,style:z(R)},[m(()=>T)],14,$e))):o.row.push((b(),h("td",{key:3,class:p(`${e}-descriptions-table-content`),colspan:_?(a-A)*2:k*2},[M("span",{class:p([`${e}-descriptions-table-content__label`,r]),style:z(D)},[m(()=>[...I,n&&(b(),h("span",{key:4,class:p(`${e}-descriptions-separator`)},[m(()=>n)],2))])],6),M("span",{class:p([`${e}-descriptions-table-content__content`,f]),style:z(R)},[m(()=>T)],6)],10,Ie)));else{const E=_?(a-A)*2:k*2;o.row.push((b(),h("th",{key:5,class:p([`${e}-descriptions-table-header`,r]),colspan:E,style:z(D)},[m(()=>I)],14,Te))),o.secondRow.push((b(),h("td",{key:6,class:p([`${e}-descriptions-table-content`,f]),colspan:E,style:z(R)},[m(()=>T)],14,Ae)))}return(o.span>=a||_)&&(o.span=0,o.row.length&&(o.rows.push(o.row),o.row=[]),v!=="left"&&o.secondRow.length&&(o.rows.push(o.secondRow),o.secondRow=[])),o},{span:0,row:[],secondRow:[],rows:[]}).rows.map(o=>(b(),h("tr",{class:p(`${e}-descriptions-table-row`)},[m(()=>o)],2)));return b(),h("div",{style:z(u),class:p([`${e}-descriptions`,this.themeClass,`${e}-descriptions--${v}-label-placement`,`${e}-descriptions--${C}-label-align`,`${e}-descriptions--${w}-size`,d&&`${e}-descriptions--bordered`])},[c||this.$slots.header?(b(),h("div",{key:0,class:p(`${e}-descriptions-header`)},[m(()=>c||ae(this,"header"))],2)):m(()=>null),M("div",{class:p(`${e}-descriptions-table-wrapper`)},[M("table",{class:p(`${e}-descriptions-table`)},[M("tbody",null,[m(()=>v==="top"&&(b(),h("tr",{class:p(`${e}-descriptions-table-row`),style:{visibility:"collapse"}},[m(()=>se(a*2,(b(),h("td"))))],2))),m(()=>F)])],2)],2)],6)}});const Be={label:String,span:{type:Number,default:1},labelClass:String,labelStyle:[Object,String],contentClass:String,contentStyle:[Object,String]};var Me=H({name:"DescriptionsItem",[ke]:!0,props:Be,slots:Object,render(){return null}});const je={__name:"ImportView",setup(l){const y=ze(),f=Ce(),r=ye({panel_dir:"/www/server/panel",cron_dir:"/www/server/cron",activate:!1}),a=U(null),v=U(!1);async function C(u){v.value=!0;try{a.value=await we(`/import/aapanel/${u}`,{method:"POST",body:{...r}})}catch(e){y.error(e.message)}finally{v.value=!1}}function w(){f.warning({title:"Import from aaPanel",content:r.activate?"Imported sites will be served by SlimPanel immediately. Make sure aaPanel's nginx include is removed first.":"Imported sites are parked, so nginx keeps serving aaPanel until you switch over.",positiveText:"Import",negativeText:"Cancel",onPositiveClick:async()=>{await C("apply"),y.success("Import finished")}})}const d=[{title:"Kind",key:"kind",width:110,render:u=>X(Y,{size:"small",bordered:!1},{default:()=>u.kind})},{title:"Name",key:"name",width:220},{title:"Action",key:"action",width:110,render:u=>X(Y,{size:"small",bordered:!1,type:u.action==="import"?"success":"default"},{default:()=>u.action})},{title:"Note",key:"reason",ellipsis:{tooltip:!0}}],c=u=>{var e,n;return((n=(e=a.value)==null?void 0:e.summary)==null?void 0:n[u])||{}};return(u,e)=>(b(),h("div",null,[i(s(me),{type:"info",bordered:!1,style:{"margin-bottom":"14px"}},{default:g(()=>[...e[4]||(e[4]=[O(" aaPanel is only ever read. Preview changes nothing — nothing is written until you press Import. ",-1)])]),_:1}),i(s(J),{size:"small",title:"Source"},{default:g(()=>[i(s(ge),{inline:""},{default:g(()=>[i(s(q),{label:"aaPanel directory"},{default:g(()=>[i(s(K),{value:r.panel_dir,"onUpdate:value":e[0]||(e[0]=n=>r.panel_dir=n),style:{width:"260px"}},null,8,["value"])]),_:1}),i(s(q),{label:"Cron directory"},{default:g(()=>[i(s(K),{value:r.cron_dir,"onUpdate:value":e[1]||(e[1]=n=>r.cron_dir=n),style:{width:"220px"}},null,8,["value"])]),_:1}),i(s(q),null,{default:g(()=>[i(s(xe),{checked:r.activate,"onUpdate:checked":e[2]||(e[2]=n=>r.activate=n)},{default:g(()=>[...e[5]||(e[5]=[O("Serve imported sites immediately",-1)])]),_:1},8,["checked"])]),_:1})]),_:1}),i(s(he),null,{default:g(()=>[i(s(W),{loading:v.value,onClick:e[3]||(e[3]=n=>C("preview"))},{default:g(()=>[...e[6]||(e[6]=[O("Preview",-1)])]),_:1},8,["loading"]),i(s(W),{type:"primary",loading:v.value,disabled:!a.value,onClick:w},{default:g(()=>[...e[7]||(e[7]=[O("Import",-1)])]),_:1},8,["loading","disabled"])]),_:1})]),_:1}),a.value?(b(),be(s(J),{key:0,size:"small",title:"Result",style:{"margin-top":"12px"}},{default:g(()=>[i(s(Re),{column:3,"label-placement":"top",style:{"margin-bottom":"14px"}},{default:g(()=>[(b(),h(fe,null,ve(["site","database","cron"],n=>i(s(Me),{key:n,label:n},{default:g(()=>[O(Q(c(n).import||0)+" to import · "+Q(c(n).skip||0)+" skipped ",1)]),_:2},1032,["label"])),64))]),_:1}),i(s(Se),{columns:d,data:a.value.items,bordered:!1,size:"small"},null,8,["data"])]),_:1})):ue("",!0)]))}};export{je as default};
