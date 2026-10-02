import{a2 as u,a4 as f,d as T,a6 as d,o as s,c as i,D as a,bi as v,z as l,a as w,F as B,A as m,M as E,bn as F,O as N,ac as V,g as y}from"./index-DE04bkTa.js";var P=u("statistic",[f("label",`
 font-weight: var(--n-label-font-weight);
 transition: .3s color var(--n-bezier);
 font-size: var(--n-label-font-size);
 color: var(--n-label-text-color);
 `),u("statistic-value",`
 margin-top: 4px;
 font-weight: var(--n-value-font-weight);
 `,[f("prefix",`
 margin: 0 4px 0 0;
 font-size: var(--n-value-font-size);
 transition: .3s color var(--n-bezier);
 color: var(--n-value-prefix-text-color);
 `,[u("icon",{verticalAlign:"-0.125em"})]),f("content",`
 font-size: var(--n-value-font-size);
 transition: .3s color var(--n-bezier);
 color: var(--n-value-text-color);
 `),f("suffix",`
 margin: 0 0 0 4px;
 font-size: var(--n-value-font-size);
 transition: .3s color var(--n-bezier);
 color: var(--n-value-suffix-text-color);
 `,[u("icon",{verticalAlign:"-0.125em"})])])]);const k={...d.props,tabularNums:Boolean,label:String,value:[String,Number]};var O=T({name:"Statistic",props:k,slots:Object,setup(e){const{mergedClsPrefixRef:n,inlineThemeDisabled:r,mergedRtlRef:x}=E(e),b=d("Statistic","-statistic",P,F,e,n),c=N("Statistic",x,n),t=y(()=>{const{self:{labelFontWeight:g,valueFontSize:p,valueFontWeight:z,valuePrefixTextColor:h,labelTextColor:S,valueSuffixTextColor:_,valueTextColor:C,labelFontSize:R},common:{cubicBezierEaseInOut:$}}=b.value;return{"--n-bezier":$,"--n-label-font-size":R,"--n-label-font-weight":g,"--n-label-text-color":S,"--n-value-font-weight":z,"--n-value-font-size":p,"--n-value-prefix-text-color":h,"--n-value-suffix-text-color":_,"--n-value-text-color":C}}),o=r?V("statistic",void 0,t,e):void 0;return{rtlEnabled:c,mergedClsPrefix:n,cssVars:r?void 0:t,themeClass:o==null?void 0:o.themeClass,onRender:o==null?void 0:o.onRender}},render(){var c;const{mergedClsPrefix:e,$slots:{default:n,label:r,prefix:x,suffix:b}}=this;return(c=this.onRender)==null||c.call(this),s(),i("div",{class:l([`${e}-statistic`,this.themeClass,this.rtlEnabled&&`${e}-statistic--rtl`]),style:m(this.cssVars)},[a(()=>v(r,t=>(s(),i("div",{class:l(`${e}-statistic__label`)},[a(()=>this.label||t)],2)))),w("div",{class:l(`${e}-statistic-value`),style:m({fontVariantNumeric:this.tabularNums?"tabular-nums":""})},[a(()=>v(x,t=>t&&(s(),i("span",{class:l(`${e}-statistic-value__prefix`)},[a(()=>t)],2)))),this.value!==void 0?(s(),i("span",{key:0,class:l(`${e}-statistic-value__content`)},[a(()=>this.value)],2)):(s(),i(B,{key:1},[a(()=>v(n,t=>t&&(s(),i("span",{class:l(`${e}-statistic-value__content`)},[a(()=>t)],2))))],64)),a(()=>v(b,t=>t&&(s(),i("span",{class:l(`${e}-statistic-value__suffix`)},[a(()=>t)],2))))],6)],6)}});export{O as S};
