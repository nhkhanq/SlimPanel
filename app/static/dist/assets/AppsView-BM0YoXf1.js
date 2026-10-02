import{u as oe,E as U}from"./use-message-BICuTCqS.js";import{a0 as a,a2 as A,a3 as M,aF as te,b4 as ae,b5 as le,d as se,a6 as W,o as n,c as h,D as ne,A as de,z as ie,M as ce,b6 as ue,O as be,ac as me,g as S,am as D,i as ge,a as g,e as i,u as o,w as t,b as p,f as _,F as E,m as F,k as $,r as T,ao as ve,p as c,B as C,t as m,T as V,at as pe,C as fe,s as G,ar as he}from"./index-DE04bkTa.js";import{G as ye,a as ke}from"./Grid-CxXp2QuP.js";import{P as Ce}from"./Popconfirm-BuYjNu7Z.js";var xe=a([A("table",`
 font-size: var(--n-font-size);
 font-variant-numeric: tabular-nums;
 line-height: var(--n-line-height);
 width: 100%;
 border-radius: var(--n-border-radius) var(--n-border-radius) 0 0;
 text-align: left;
 border-collapse: separate;
 border-spacing: 0;
 overflow: hidden;
 background-color: var(--n-td-color);
 border-color: var(--n-merged-border-color);
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 --n-merged-border-color: var(--n-border-color);
 `,[a("th",`
 white-space: nowrap;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 text-align: inherit;
 padding: var(--n-th-padding);
 vertical-align: inherit;
 text-transform: none;
 border: 0px solid var(--n-merged-border-color);
 font-weight: var(--n-th-font-weight);
 color: var(--n-th-text-color);
 background-color: var(--n-th-color);
 border-bottom: 1px solid var(--n-merged-border-color);
 border-right: 1px solid var(--n-merged-border-color);
 `,[a("&:last-child",`
 border-right: 0px solid var(--n-merged-border-color);
 `)]),a("td",`
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 padding: var(--n-td-padding);
 color: var(--n-td-text-color);
 background-color: var(--n-td-color);
 border: 0px solid var(--n-merged-border-color);
 border-right: 1px solid var(--n-merged-border-color);
 border-bottom: 1px solid var(--n-merged-border-color);
 `,[a("&:last-child",`
 border-right: 0px solid var(--n-merged-border-color);
 `)]),M("bordered",`
 border: 1px solid var(--n-merged-border-color);
 border-radius: var(--n-border-radius);
 `,[a("tr",[a("&:last-child",[a("td",`
 border-bottom: 0 solid var(--n-merged-border-color);
 `)])])]),M("single-line",[a("th",`
 border-right: 0px solid var(--n-merged-border-color);
 `),a("td",`
 border-right: 0px solid var(--n-merged-border-color);
 `)]),M("single-column",[a("tr",[a("&:not(:last-child)",[a("td",`
 border-bottom: 0px solid var(--n-merged-border-color);
 `)])])]),M("striped",[a("tr:nth-of-type(even)",[a("td","background-color: var(--n-td-color-striped)")])]),te("bottom-bordered",[a("tr",[a("&:last-child",[a("td",`
 border-bottom: 0px solid var(--n-merged-border-color);
 `)])])])]),ae(A("table",`
 background-color: var(--n-td-color-modal);
 --n-merged-border-color: var(--n-border-color-modal);
 `,[a("th",`
 background-color: var(--n-th-color-modal);
 `),a("td",`
 background-color: var(--n-td-color-modal);
 `)])),le(A("table",`
 background-color: var(--n-td-color-popover);
 --n-merged-border-color: var(--n-border-color-popover);
 `,[a("th",`
 background-color: var(--n-th-color-popover);
 `),a("td",`
 background-color: var(--n-td-color-popover);
 `)]))]);const ze={...W.props,bordered:{type:Boolean,default:!0},bottomBordered:{type:Boolean,default:!0},singleLine:{type:Boolean,default:!0},striped:Boolean,singleColumn:Boolean,size:String};var _e=se({name:"Table",props:ze,setup(u){const{mergedClsPrefixRef:d,inlineThemeDisabled:b,mergedRtlRef:f,mergedComponentPropsRef:x}=ce(u),y=S(()=>{var v,w;return u.size||((w=(v=x==null?void 0:x.value)==null?void 0:v.Table)==null?void 0:w.size)||"medium"}),z=W("Table","-table",xe,ue,u,d),N=be("Table",f,d),P=S(()=>{const v=y.value,{self:{borderColor:w,tdColor:O,tdColorModal:R,tdColorPopover:I,thColor:L,thColorModal:s,thColorPopover:e,thTextColor:l,tdTextColor:r,borderRadius:B,thFontWeight:j,lineHeight:q,borderColorModal:K,borderColorPopover:J,tdColorStriped:Q,tdColorStripedModal:X,tdColorStripedPopover:Y,[D("fontSize",v)]:Z,[D("tdPadding",v)]:H,[D("thPadding",v)]:ee},common:{cubicBezierEaseInOut:re}}=z.value;return{"--n-bezier":re,"--n-td-color":O,"--n-td-color-modal":R,"--n-td-color-popover":I,"--n-td-text-color":r,"--n-border-color":w,"--n-border-color-modal":K,"--n-border-color-popover":J,"--n-border-radius":B,"--n-font-size":Z,"--n-th-color":L,"--n-th-color-modal":s,"--n-th-color-popover":e,"--n-th-font-weight":j,"--n-th-text-color":l,"--n-line-height":q,"--n-td-padding":H,"--n-th-padding":ee,"--n-td-color-striped":Q,"--n-td-color-striped-modal":X,"--n-td-color-striped-popover":Y}}),k=b?me("table",S(()=>y.value[0]),P,u):void 0;return{rtlEnabled:N,mergedClsPrefix:d,cssVars:b?void 0:P,themeClass:k==null?void 0:k.themeClass,onRender:k==null?void 0:k.onRender}},render(){var d;const{mergedClsPrefix:u}=this;return(d=this.onRender)==null||d.call(this),n(),h("table",{class:ie([`${u}-table`,this.themeClass,{[`${u}-table--rtl`]:this.rtlEnabled,[`${u}-table--bottom-bordered`]:this.bottomBordered,[`${u}-table--bordered`]:this.bordered,[`${u}-table--single-line`]:this.singleLine,[`${u}-table--single-column`]:this.singleColumn,[`${u}-table--striped`]:this.striped}]),style:de(this.cssVars)},[ne(()=>{var b,f;return(f=(b=this.$slots).default)==null?void 0:f.call(b)})],6)}});const we={class:"toolbar"},$e={style:{margin:"0 0 10px","font-size":"14px"}},Pe={class:"muted",style:{margin:"0 0 10px","min-height":"36px"}},Te={key:0,class:"muted mono",style:{margin:"10px 0 0"}},Se={class:"mono"},Re={class:"mono"},Ne={__name:"AppsView",setup(u){const d=oe(),b=T({package_manager:"",apps:[]}),f=T(!1),x=T(""),y=T([]),z=T(!1),N=[{key:"web",label:"Web servers"},{key:"database",label:"Databases"},{key:"runtime",label:"Runtimes"},{key:"container",label:"Containers"},{key:"security",label:"Security"},{key:"tool",label:"Tools"}],P=S(()=>{const s=x.value.trim().toLowerCase();return N.map(e=>({...e,apps:b.value.apps.filter(l=>l.category===e.key&&(!s||l.name.toLowerCase().includes(s)||l.slug.includes(s)))})).filter(e=>e.apps.length)}),k=S(()=>b.value.apps.filter(s=>s.installed).length);async function v(){f.value=!0;try{b.value=await $("/apps")}finally{f.value=!1}}async function w(s){try{const e=await $(`/apps/${s.slug}/install`,{method:"POST"});d.success(`Installing ${s.name} — follow it on the Tasks page (task ${e.id})`)}catch(e){d.error(e.message)}}async function O(s){try{const e=await $(`/apps/${s.slug}/uninstall`,{method:"POST"});d.success(`Removing ${s.name} (task ${e.id})`)}catch(e){d.error(e.message)}}async function R(s,e){if(!s.service)return;const l=await $("/system/services",{method:"POST",body:{name:s.service,action:e}});l.ok?d.success(`${s.service} ${e}`):d.error(l.message),await v()}async function I(){y.value=await $("/apps/system/upgradable"),z.value=!0}async function L(){const s=await $("/apps/system/update",{method:"POST"});d.success(`System update started (task ${s.id})`),z.value=!1}return ge(v),(s,e)=>(n(),h("div",null,[g("div",we,[i(o(ve),{value:x.value,"onUpdate:value":e[0]||(e[0]=l=>x.value=l),placeholder:"Filter software",clearable:"",style:{width:"220px"}},null,8,["value"]),i(o(C),{secondary:"",onClick:I},{default:t(()=>[...e[3]||(e[3]=[c("Check for updates",-1)])]),_:1}),e[5]||(e[5]=g("span",{class:"spacer"},null,-1)),i(o(V),{size:"small",bordered:!1},{default:t(()=>[c(m(k.value)+" installed",1)]),_:1}),b.value.package_manager?(n(),p(o(V),{key:0,size:"small",bordered:!1,type:"info"},{default:t(()=>[c(m(b.value.package_manager),1)]),_:1})):_("",!0),i(o(C),{quaternary:"",loading:f.value,onClick:v},{default:t(()=>[...e[4]||(e[4]=[c("Refresh",-1)])]),_:1},8,["loading"])]),b.value.package_manager?_("",!0):(n(),p(o(pe),{key:0,type:"warning",bordered:!1,style:{"margin-bottom":"12px"}},{default:t(()=>[...e[6]||(e[6]=[c(" No supported package manager was found, so the panel can report what is installed but cannot install anything. ",-1)])]),_:1})),(n(!0),h(E,null,F(P.value,l=>(n(),h("div",{key:l.key,style:{"margin-bottom":"18px"}},[g("h3",$e,m(l.label),1),i(o(ke),{cols:"1 s:2 l:3",responsive:"screen","x-gap":14,"y-gap":14},{default:t(()=>[(n(!0),h(E,null,F(l.apps,r=>(n(),p(o(ye),{key:r.slug},{default:t(()=>[i(o(fe),{size:"small",title:r.name},{"header-extra":t(()=>[i(o(V),{size:"small",bordered:!1,type:r.installed?"success":"default"},{default:t(()=>[c(m(r.installed?r.version||"installed":"not installed"),1)]),_:2},1032,["type"])]),default:t(()=>[g("p",Pe,m(r.description),1),i(o(G),{align:"center",size:6},{default:t(()=>[r.installed?(n(),h(E,{key:1},[r.state?(n(),p(o(V),{key:0,size:"small",bordered:!1,type:r.state==="active"?"success":"default"},{default:t(()=>[c(m(r.state),1)]),_:2},1032,["type"])):_("",!0),r.service?(n(),p(o(C),{key:1,size:"tiny",secondary:"",onClick:B=>R(r,"restart")},{default:t(()=>[...e[8]||(e[8]=[c("Restart",-1)])]),_:1},8,["onClick"])):_("",!0),r.service?(n(),p(o(C),{key:2,size:"tiny",secondary:"",onClick:B=>R(r,r.state==="active"?"stop":"start")},{default:t(()=>[c(m(r.state==="active"?"Stop":"Start"),1)]),_:2},1032,["onClick"])):_("",!0),i(o(Ce),{onPositiveClick:()=>O(r)},{trigger:t(()=>[i(o(C),{size:"tiny",type:"error",secondary:""},{default:t(()=>[...e[9]||(e[9]=[c("Remove",-1)])]),_:1})]),default:t(()=>[c(" The package manager removes "+m(r.name)+". Data directories are left alone. ",1)]),_:2},1032,["onPositiveClick"])],64)):(n(),p(o(C),{key:0,size:"tiny",type:"primary",disabled:!r.installable,onClick:B=>w(r)},{default:t(()=>[...e[7]||(e[7]=[c("Install",-1)])]),_:1},8,["disabled","onClick"]))]),_:2},1024),r.package?(n(),h("p",Te,m(r.package),1)):_("",!0)]),_:2},1032,["title"])]),_:2},1024))),128))]),_:2},1024)]))),128)),!P.value.length&&!f.value?(n(),p(o(U),{key:1,description:"Nothing matches that filter."})):_("",!0),i(o(he),{show:z.value,"onUpdate:show":e[2]||(e[2]=l=>z.value=l),preset:"card",title:"System updates",style:{"max-width":"640px"}},{footer:t(()=>[i(o(G),{justify:"end"},{default:t(()=>[i(o(C),{onClick:e[1]||(e[1]=l=>z.value=!1)},{default:t(()=>[...e[11]||(e[11]=[c("Close",-1)])]),_:1}),i(o(C),{type:"primary",disabled:!y.value.length,onClick:L},{default:t(()=>[c(" Update "+m(y.value.length)+" packages ",1)]),_:1},8,["disabled"])]),_:1})]),default:t(()=>[y.value.length?(n(),p(o(_e),{key:1,size:"small",bordered:!1,striped:""},{default:t(()=>[e[10]||(e[10]=g("thead",null,[g("tr",null,[g("th",null,"Package"),g("th",null,"Candidate")])],-1)),g("tbody",null,[(n(!0),h(E,null,F(y.value,l=>(n(),h("tr",{key:l.name},[g("td",Se,m(l.name),1),g("td",Re,m(l.candidate),1)]))),128))])]),_:1})):(n(),p(o(U),{key:0,description:"Everything is up to date."}))]),_:1},8,["show"])]))}};export{Ne as default};
