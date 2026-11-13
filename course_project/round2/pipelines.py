from course_project.extension.pipelines import build as original,StateObserver
from course_project.round2.contract import ContractPipeline

def build(llm,arm,events,states,context=None):
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
