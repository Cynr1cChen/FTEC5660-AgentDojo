import fs from 'node:fs/promises';
import {Presentation, FileBlob, PresentationFile} from '@oai/artifact-tool';
const root=process.cwd();
const p=await PresentationFile.importPptx(await FileBlob.load(root+'/output/pptx/FTEC5660_Template_Slim.pptx'));
const o={slides:p.slides.items.map((s,i)=>({index:i+1,id:s.id,size:s.size,shapes:s.shapes.items.map(x=>({id:x.id,name:x.name,geometry:x.geometry,text:String(x.text),position:x.position})),images:s.images.items.map(x=>({id:x.id,alt:x.alt,frame:x.frame}))})),masters:p.masters.items.map(x=>({id:x.id,name:x.name}))};
await fs.writeFile(root+'/course_project/materials_v2/build/final/template_inspection.json',JSON.stringify(o,null,2));
console.log(JSON.stringify(o.slides.map(s=>({index:s.index,shapes:s.shapes.length,images:s.images.length,text:s.shapes.filter(x=>x.geometry==='textbox').map(x=>({id:x.id,name:x.name,text:x.text.slice(0,55),position:x.position}))})),null,2));
