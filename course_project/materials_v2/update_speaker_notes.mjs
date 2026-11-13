// Author notes with Artifact Tool, then transplant only those note parts so that
// the reviewed slides, chart workbooks, template and media stay byte-identical.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';
import JSZip from 'jszip';

const root=process.cwd(),here=path.join(root,'course_project/materials_v2');
const build=path.join(here,'build',process.env.NOTES_REVISION??'script_revision');
await fs.mkdir(build,{recursive:true});
const source=process.env.NOTES_REVISION?path.join(root,'output/pptx/FTEC5660_AgentDojo_Final_Presentation.pptx'):path.join(build,'before_FTEC5660_AgentDojo_Final_Presentation.pptx');
const notes=JSON.parse(await fs.readFile(path.join(here,'speaker_notes.json'),'utf8'));
const p=await PresentationFile.importPptx(await FileBlob.load(source));
if(p.slides.items.length!==15||notes.length!==12)throw Error('Unexpected slide count');
for(let i=0;i<12;i++){
  const old=p.slides.items[i].speakerNotes.text;
  const marker='\n\nSources\n',at=old.indexOf(marker);
  if(at<0)throw Error('Missing source notes on slide '+(i+1));
  p.slides.items[i].speakerNotes.text=notes[i].english+'\n\n中文对照\n'+notes[i].chinese+old.slice(at);
}
const authored=path.join(build,'artifact_authored_notes.pptx');
await (await PresentationFile.exportPptx(p)).save(authored);
async function parts(zip){return Object.fromEntries(await Promise.all(Object.values(zip.files).filter(e=>!e.dir).map(async e=>[e.name,await e.async('uint8array')])));}
const originalZip=await JSZip.loadAsync(await fs.readFile(source));
const original=await parts(originalZip);
const edited=await parts(await JSZip.loadAsync(await fs.readFile(authored)));
const digest=b=>createHash('sha256').update(b).digest('hex');
const originalHashes=Object.fromEntries(Object.entries(original).map(([n,b])=>[n,digest(b)]));
const changed=[];
for(let i=1;i<=12;i++){
  const name=`ppt/notesSlides/notesSlide${i}.xml`;
  if(!original[name]||!edited[name])throw Error('Missing note part '+name);
  if(/r:(?:embed|link|id)=/.test(new TextDecoder().decode(edited[name])))throw Error('Unexpected new note relationship');
  original[name]=edited[name];originalZip.file(name,edited[name],{createFolders:false});changed.push(name);
}
const preserved=Object.entries(original).filter(([n])=>!changed.includes(n));
if(!preserved.every(([n,b])=>digest(b)===originalHashes[n]))throw Error('Unrelated package content changed');
const candidate=path.join(build,'candidate.pptx');
await fs.writeFile(candidate,await originalZip.generateAsync({type:'nodebuffer',compression:'DEFLATE',compressionOptions:{level:6}}));

const skill='/Users/Admin1/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11217/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(path.join(build,'validated'),{recursive:true});
const finalPath=path.join(build,'validated/FTEC5660_AgentDojo_Presentation.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,
 pythonExecutable:'/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','18288000,10287000','--validate-heading-fit',...[3,6,7,13,14,15].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:15,requiredNativeTableOwnerSlides:[3,6,7,13,14,15],requiredNativeChartOwnerSlides:[5,9],
 requiredEmbeddedWorkbookChartOwnerSlides:[5,9],fontPolicy:{basis:'design',families:['Arial']},
 verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
const finalZip=await parts(await JSZip.loadAsync(await fs.readFile(finalPath)));
if(Object.keys(finalZip).length!==Object.keys(originalHashes).length)throw Error('Package parts added or removed');
const actualChanged=Object.entries(finalZip).filter(([n,b])=>digest(b)!==originalHashes[n]).map(([n])=>n);
if(actualChanged.length<1||actualChanged.length>12||!actualChanged.every(n=>changed.includes(n)))throw Error('Unexpected final part changes');
const receipt={changed_parts:actualChanged,unchanged_parts:Object.keys(originalHashes).length-actualChanged.length,
 all_visible_slide_and_chart_parts_byte_identical:true,notes_only_edit:true,
 source_sha256:digest(await fs.readFile(source)),final_sha256:digest(await fs.readFile(finalPath))};
await fs.writeFile(path.join(here,'notes_revision.json'),JSON.stringify(receipt,null,2)+'\n');
await fs.writeFile(path.join(here,'build/final/latest_revision.json'),JSON.stringify({rev:'script_revision',build,finalPath,result},null,2));
console.log(JSON.stringify({finalPath,changedNoteParts:actualChanged.length,preservedParts:preserved.length,sha256:result.finalSha256}));
