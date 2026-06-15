// Runs the EXACT functions shipped in the published page's <script> to prove
// the in-browser claims hold. Functions copied verbatim from index.html.

/* core */
function makeGrid(n){ return new Int32Array(n*n); }
function sweep(h, n, toppledMask){
  const t = new Int32Array(n*n); let count = 0;
  for(let k=0;k<n*n;k++){ const tk=h[k]>>2; if(tk){ t[k]=tk; count+=tk; } }
  if(count===0) return 0;
  for(let i=0;i<n;i++){ const row=i*n;
    for(let j=0;j<n;j++){ const k=row+j, tk=t[k];
      if(tk){ if(toppledMask) toppledMask[k]=1; h[k]-=4*tk;
        if(i>0) h[k-n]+=tk; if(i<n-1) h[k+n]+=tk; if(j>0) h[k-1]+=tk; if(j<n-1) h[k+1]+=tk; } } }
  return count;
}
function stabilize(h, n){ const mask=new Uint8Array(n*n); let size=0,dur=0,c;
  while((c=sweep(h,n,mask))>0){ size+=c; dur++; }
  let area=0; for(let k=0;k<mask.length;k++) area+=mask[k]; return {size,area,dur}; }

/* identity (section 3) */
function identity(n){ const six=makeGrid(n); six.fill(6);
  const a=Int32Array.from(six); stabilize(a,n);
  const diff=makeGrid(n); for(let k=0;k<n*n;k++) diff[k]=six[k]-a[k];
  stabilize(diff,n); return diff; }

/* verify (section 4) */
function sinkVec(n){ const b=makeGrid(n);
  for(let j=0;j<n;j++){ b[j]+=1; b[(n-1)*n+j]+=1; }
  for(let i=0;i<n;i++){ b[i*n]+=1; b[i*n+n-1]+=1; } return b; }
function isRecurrent(c,n,b){ const a=Int32Array.from(c); for(let k=0;k<n*n;k++) a[k]+=b[k];
  stabilize(a,n); for(let k=0;k<n*n;k++) if(a[k]!==c[k]) return false; return true; }
function countRecurrent(n){ const cells=n*n, b=sinkVec(n); let cnt=0n;
  const total=Math.pow(4,cells), c=makeGrid(n);
  for(let code=0;code<total;code++){ let x=code; for(let k=0;k<cells;k++){ c[k]=x&3; x>>=2; }
    if(isRecurrent(c,n,b)) cnt++; } return cnt; }
function reducedLaplacian(n){ const N=n*n, M=Array.from({length:N},()=>new Array(N).fill(0n));
  const idx=(i,j)=>i*n+j;
  for(let i=0;i<n;i++)for(let j=0;j<n;j++){ const v=idx(i,j); M[v][v]=4n;
    [[-1,0],[1,0],[0,-1],[0,1]].forEach(([di,dj])=>{ const a=i+di,b=j+dj;
      if(a>=0&&a<n&&b>=0&&b<n) M[v][idx(a,b)]-=1n; }); } return M; }
function detBareiss(M){ const n=M.length; let prev=1n, sign=1n;
  for(let k=0;k<n-1;k++){ if(M[k][k]===0n){ let s=-1; for(let i=k+1;i<n;i++) if(M[i][k]!==0n){s=i;break;}
      if(s<0) return 0n; const tmp=M[k];M[k]=M[s];M[s]=tmp; sign=-sign; }
    for(let i=k+1;i<n;i++) for(let j=k+1;j<n;j++) M[i][j]=(M[i][j]*M[k][k]-M[i][k]*M[k][j])/prev;
    prev=M[k][k]; } return sign*M[n-1][n-1]; }

/* ---- TESTS ---- */
const TRUTH = {1:4n,2:192n,3:100352n,4:557568000n,5:32565539635200n,6:19872369301840986112n};
let pass=true;

console.log("A) Verify button (det === brute-force), the page's headline claim:");
for(const n of [1,2,3]){
  const det=detBareiss(reducedLaplacian(n));
  const bf=countRecurrent(n);
  const ok = det===bf && det===TRUTH[n];
  pass &&= ok;
  console.log(`   n=${n}: det=${det}  brute=${bf}  truth=${TRUTH[n]}  ${ok?'OK':'FAIL'}`);
}

console.log("B) detBareiss reproduces table values n=4,5,6 (same code path):");
for(const n of [4,5,6]){
  const det=detBareiss(reducedLaplacian(n));
  const ok = det===TRUTH[n]; pass &&= ok;
  console.log(`   n=${n}: ${det}  ${ok?'OK':'FAIL'}`);
}

console.log("C) Identity is idempotent (e⊕e==e), recurrent, symmetric:");
for(const n of [64,128]){
  const e=identity(n);
  const e2=Int32Array.from(e); for(let k=0;k<n*n;k++) e2[k]+=e[k]; stabilize(e2,n);
  let idem=true; for(let k=0;k<n*n;k++) if(e2[k]!==e[k]){idem=false;break;}
  const b=sinkVec(n); const rec=isRecurrent(e,n,b);
  // 4-fold symmetry check
  let sym=true; for(let i=0;i<n&&sym;i++)for(let j=0;j<n;j++){
    if(e[i*n+j]!==e[(n-1-i)*n+j]||e[i*n+j]!==e[i*n+(n-1-j)]){sym=false;break;} }
  const ok=idem&&rec&&sym; pass &&= ok;
  console.log(`   n=${n}: idempotent=${idem} recurrent=${rec} symmetric=${sym}  ${ok?'OK':'FAIL'}`);
}

console.log("D) Abelian claim: random unstable pile, 4 toppling orders -> same result");
// emulate the page's parallel stabilize vs a serial order; both must agree on final config
function stabilizeSerial(h0,n,pick){ const h=Int32Array.from(h0); let size=0;
  while(true){ const u=[]; for(let k=0;k<n*n;k++) if(h[k]>=4) u.push(k); if(!u.length) break;
    const k=pick(u); const q=h[k]>>2; // topple fully once (matches odometer additivity)
    h[k]-=4; const i=(k/n)|0,j=k%n; if(i>0)h[k-n]++; if(i<n-1)h[k+n]++; if(j>0)h[k-1]++; if(j<n-1)h[k+1]++; size++; }
  return {h,size}; }
{
  const n=6; const h0=makeGrid(n);
  // deterministic pseudo-random fill 0..12
  let s=12345; const rnd=()=>{ s=(1103515245*s+12345)&0x7fffffff; return s; };
  for(let k=0;k<n*n;k++) h0[k]=rnd()%13;
  const par=Int32Array.from(h0); const pr=stabilize(par,n);
  const first=stabilizeSerial(h0,n,u=>u[0]);
  const last =stabilizeSerial(h0,n,u=>u[u.length-1]);
  let eq=true; for(let k=0;k<n*n;k++) if(par[k]!==first.h[k]||par[k]!==last.h[k]){eq=false;break;}
  const eqCount = pr.size===first.size && pr.size===last.size;
  const ok=eq&&eqCount; pass &&= ok;
  console.log(`   final config identical=${eq}  topple-count identical=${eqCount} (par=${pr.size}, first=${first.size}, last=${last.size})  ${ok?'OK':'FAIL'}`);
}

console.log("\n=== SHIPPED-JS TEST: " + (pass?"ALL PASS ✓":"FAILURE ✗") + " ===");
process.exit(pass?0:1);
