import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.dirname(fileURLToPath(import.meta.url));
const index=process.argv.indexOf('--port');
const port=index>=0?Number(process.argv[index+1]):4173;
if(!Number.isInteger(port)||port<1024||port>65535)throw new Error('Geçersiz port');
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8','.ino':'text/plain; charset=utf-8'};
const server=http.createServer(async(req,res)=>{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  try{
    const url=new URL(req.url,'http://localhost');
    if(url.pathname==='/api/health'){res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({app:'temiz-rota',status:'ok'}));return;}
    const relative=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
    const target=path.resolve(root,'.'+relative);
    if(!target.startsWith(root+path.sep)){res.writeHead(403);res.end('Erişim yok');return;}
    const content=await fs.readFile(target);
    res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff'});
    res.end(req.method==='HEAD'?undefined:content);
  }catch(error){res.writeHead(error.code==='ENOENT'?404:400,{'Content-Type':'text/plain; charset=utf-8'});res.end('Dosya bulunamadı veya istek geçersiz.');}
});
server.on('error',error=>{console.error(error.code==='EADDRINUSE'?`${port} portu kullanılıyor. Açık paneli kullanın veya --port 4174 ile başlatın.`:error.message);process.exitCode=1;});
server.listen(port,'127.0.0.1',()=>console.log(`Temiz Rota hazır: http://127.0.0.1:${port}`));
