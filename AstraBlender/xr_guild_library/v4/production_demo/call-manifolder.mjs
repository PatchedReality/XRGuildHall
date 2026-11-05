import fs from 'node:fs/promises';
import {Client} from '/Users/poshaughnessey/dev/PatchedReality/Metaverse/ManifolderMCP/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '/Users/poshaughnessey/dev/PatchedReality/Metaverse/ManifolderMCP/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
const root='/Users/poshaughnessey/dev/PatchedReality/Metaverse/ManifolderMCP';
const transport=new StdioClientTransport({command:process.execPath,args:[root+'/dist/index.js'],cwd:root,stderr:'pipe'});
const client=new Client({name:'xr-guild-library-scene-publish',version:'1.0.0'},{capabilities:{}});
try{
 await client.connect(transport);
 const calls=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
 for(const call of calls){
  const result=await client.callTool(call,undefined,{timeout:180000});
  console.log(JSON.stringify({name:call.name,result}));
  if(result.isError)throw new Error('Tool failed: '+call.name);
 }
}finally{await client.close();}
