"""Recompute research-stage acceptance from audited records, without API calls."""
from pathlib import Path
from course_project.stage1 import ROOT,read,write,sha,stamp
from course_project.round2.runner import prior_spending,BASELINE_BOUND

def main():
 here=ROOT/'course_project/round2';cohorts=[]
 for f in sorted((ROOT/'runs/round2').glob('*/*/summary.json')):
  d=f.parent;s=read(f);a=read(d/'audit.json');assert a['passed']
  assert a['rows']==[r for r in s['rows'] if r['status']=='completed']
  cohorts.append(dict(run=str(d.relative_to(ROOT)),completed=s['completed'],planned=s['expected_episodes'],requests=a['requests'],known_period_cny=a['known_recorded_period_cny'],peak_upper_cny=a['peak_upper_cny'],unknown_reservation_cny=a['unknown_reservation_cny'],peak_starts=a['peak_request_starts'],audit_sha256=sha(d/'audit.json')))
 assert len(cohorts)==12 and sum(x['completed'] for x in cohorts)==677
 upper=BASELINE_BOUND+sum(x['peak_upper_cny'] for x in cohorts)
 assert abs(upper-prior_spending())<1e-9 and upper<=150
 package=read(here/'package_verification.json');assert package['passed'] and len(package['verified'])==12
 assert not package['technical_attempts_not_replayed']
 fresh=read(here/'fresh_environment.json');assert fresh['fresh_virtual_environment'] and fresh['round2_archive_replayed']
 assert '55 passed' in (here/'verification_logs/tests_final.log').read_text()
 original=read(ROOT/'course_project/materials/delivery_validation.json')['artifacts'];artifacts={}
 for path,item in original.items():
  assert sha(ROOT/path)==item['sha256'];artifacts[path]=item['sha256']
 merged=read(here/'anchored_merged_results.json');assert merged['episodes']==153
 z=read(here/'gate_diagnosis.json');ws=z['hard_denial_witnesses'];assert len(ws)==7 and all(x['goal_transition_if_executed'] and not x['actual_execution'] and x['native_tool_error'] is None for x in ws)
 def metrics(name):
  result=read(here/(name+'_results.json'))
  assert result['audit_hashes']==[sha(ROOT/path/'audit.json') for path in result['runs']]
  return {arm:x['metrics'] for arm,x in result['arms'].items()}
 out=dict(created_utc=stamp(),status='research_complete_before_report_and_deck_authoring',paid_sampling_stopped=True,cohorts=cohorts,round2_completed=677,round2_recorded_requests=sum(x['requests'] for x in cohorts),round2_known_recorded_period_cny=sum(x['known_period_cny'] for x in cohorts),round2_unknown_reservation_cny=sum(x['unknown_reservation_cny'] for x in cohorts),round2_peak_upper_cny=sum(x['peak_upper_cny'] for x in cohorts),project_conservative_upper_cny=upper,cumulative_authorized_cny=150,peak_continuation_authorized_cap_cny=10,authorized_peak_request_starts=sum(x['peak_starts'] for x in cohorts),cost_is_provider_statement=False,tests_passed=55,fresh_environment_verified=True,all_three_archives_verified=True,round2_archive_sha256=package['archive_sha256'],original_materials_unchanged=artifacts,metrics={n:metrics(n) for n in ['slack_broader','travel_broader','travel_output_followup','contract_formal','anchored_merged','anchored_positive_controls']},hard_denials_with_native_goal_counterfactual=7,limitations=['Post-hoc output and parameter-policy candidates; fixed same-task repetitions, not unseen-task generalization.','No broad cross-scene recovery gain. Complex Travel exposes answer replacement harm.','Hard account restriction imposes an explicit authority policy on ambiguous delegated data. No document authentication.','Seven actual hard-rule denials do not imply twelve end-to-end rescued tasks. Rent safe completion remains0/12.','Password rule has engineering tests and legitimate controls, but no observed baseline password attack success to reduce.','One interrupted request has no saved response; reserve retained, original failed attempt not scored.','Last60 cases ran in a later authorized peak period; provider alias is not immutable model weights.','Fresh installation uses local cached packages on the same OS; no other-OS claim.'],pending_after_this_stage=['User review and final argument selection','Update English report, PPT and Chinese script using all relevant evidence','Identity fields','Authorized GitHub publication','Actual Zoom recording and access check','Blackboard submission'])
 out['analysis_source_hashes']={str(f.relative_to(ROOT)):sha(f) for f in sorted(here.glob('*.py'))}
 write(here/'acceptance.json',out)
 print('Research accepted:',out['round2_completed'],'episodes;',out['round2_recorded_requests'],'requests; upper CNY',upper)
if __name__=='__main__':main()
