"""Post-hoc output-routing candidate; never hide this as original recovery.

If review proposes no further tool call, retain the actual native answer rather
than replace it with a meta-confirmation. This can also discard a useful purely
textual correction; evaluate that tradeoff, do not claim monotonic improvement.
"""
from copy import deepcopy
from course_project.extension.pipelines import Review
class PreserveAnswerReview(Review):
 def __init__(self,llm,text,events):super().__init__(llm,text);self.events=events
 def query(self,query,runtime,env,messages=(),extra_args=None):
  original=deepcopy(messages[-1]) if messages and messages[-1]['role']=='assistant' and not messages[-1].get('tool_calls') else None
  n=len(messages);result=super().query(query,runtime,env,messages,extra_args);post=result[3][n:]
  keep=bool(original is not None and post and not any(m['role']=='assistant' and m.get('tool_calls') for m in post))
  self.events.append(dict(stage='output_route',retain_native_answer=keep,native_message_index=n-1,rule='No additional assistant tool-call proposal during added review. Actual native answer copied; no fabricated model response.'))
  if keep:
   q,r,e,m,x=result
   return q,r,e,[*m,original],x
  return result
