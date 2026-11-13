from course_project.extension.pipelines import build as original,StateObserver
from course_project.round2.contract import ContractPipeline

def build(llm,arm,events,states,context=None):
 if arm=='anchored':
  from course_project.extension.pipelines import Gate
  from course_project.round2.anchored import AnchoredExecutor
  from agentdojo.agent_pipeline.tool_execution import ToolsExecutionLoop
  p=original(llm,'guard',events,states,context)
  for e in p.delegate.elements:
   if isinstance(e,ToolsExecutionLoop):e.elements=[AnchoredExecutor(llm,events) if isinstance(x,Gate) else x for x in e.elements]
  p.name='deepseek-flash-anchored-guard'
  return p
 if arm=='preserve':
  from course_project.extension.pipelines import Review
  from course_project.round2.output_policy import PreserveAnswerReview
  p=original(llm,'recovery',events,states,context)
  p.delegate.elements=[PreserveAnswerReview(llm,e.text,events) if isinstance(e,Review) else e for e in p.delegate.elements]
  p.name='deepseek-flash-preserve-answer'
  return p
 if arm!='contract':return original(llm,arm,events,states,context)
 base=original(llm,'baseline',events,[],context).delegate
 return StateObserver(ContractPipeline(base,llm,events),states)
